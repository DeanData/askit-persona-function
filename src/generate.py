#!/usr/bin/env python3
"""Run f(audience description, persona description) -> text via the OpenAI API.

Backend: OpenAI gpt-4o-mini via OPENAI_API_KEY, called directly over HTTPS (stdlib
urllib, no new dependency). Originally planned to use Claude Code's own `claude -p`
CLI mode (no key needed, since the session is already authenticated) — switched
after the pilot found the headless CLI daemon on this machine was in an
`auth_required` state unrelated to this interactive session's own auth, and
`/login` turned out to be an interactive-REPL-only command with no non-interactive
equivalent (confirmed via `claude --help`, no wasted retries). Logged as a dead end
in WORKLOG.md. Model is fixed across baseline and improvement conditions for a fair
paired comparison.

Two conditions:
  - baseline: audience description + persona description + context only (naive).
  - fewshot:  same, plus a fixed per-audience style-primer block drawn from
              data/finance_forums/fewshot/ (disjoint from the eval pool used for
              metric ground truth — see WORKLOG.md for why that split exists).

Same persona roster and same contexts are used for both conditions (paired
comparison) — see data/personas/*.jsonl and data/contexts.json, both already
locked and committed.
"""
import argparse
import concurrent.futures
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path):
    """Minimal .env loader (no python-dotenv dependency). .env deliberately
    overrides any pre-existing environment variable of the same name -- a
    stale OPENAI_API_KEY exported from ~/.zshrc was silently shadowing a
    corrected .env value, so project-local config wins here on purpose."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and value:
            os.environ[key] = value


load_dotenv(ROOT / ".env")

AUDIENCES_PATH = ROOT / "data" / "audiences.json"
CONTEXTS_PATH = ROOT / "data" / "contexts.json"
PERSONAS_DIR = ROOT / "data" / "personas"
FEWSHOT_DIR = ROOT / "data" / "finance_forums" / "fewshot"

MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
FEWSHOT_TEXT_CHARS = 300

SYSTEM_PROMPT = (
    "You are role-playing as a single specific individual, described below. "
    "Respond entirely in character, in first person, as if posting online. "
    "Output ONLY the persona's response text -- no preamble, no meta-commentary, "
    "no acknowledgement of these instructions, no surrounding quotation marks. "
    "Keep the response a natural length for the situation, roughly 2-6 sentences."
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def build_fewshot_block(audience):
    examples = load_jsonl(FEWSHOT_DIR / f"{audience}.jsonl")
    lines = []
    for ex in examples:
        text = f"{ex['title']}. {ex['selftext']}".replace("\n", " ").strip()
        if len(text) > FEWSHOT_TEXT_CHARS:
            text = text[:FEWSHOT_TEXT_CHARS] + "..."
        lines.append(f"- {text}")
    joined = "\n".join(lines)
    return (
        "Here are a few real posts written by members of this audience, to give a "
        "sense of their typical voice (do not copy them, use them only as a style "
        f"reference):\n{joined}\n\n"
    )


def build_prompt(audience_desc, persona_text, context_prompt, fewshot_block=None):
    prefix = fewshot_block or ""
    return (
        f"{prefix}"
        f"Audience: {audience_desc}\n\n"
        f"Persona: {persona_text}\n\n"
        f"Situation: {context_prompt}\n\n"
        f"Write this person's response."
    )


def call_openai(user_prompt):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY not set"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 1.0,
    }
    req = urllib.request.Request(
        OPENAI_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            parsed = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:500]}"
    except urllib.error.URLError as e:
        return None, f"URL error: {e}"

    try:
        text = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return None, f"unexpected response shape: {json.dumps(parsed)[:300]}"
    if not text:
        return None, f"empty content: {json.dumps(parsed)[:300]}"
    return text.strip(), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=["baseline", "fewshot"], required=True)
    ap.add_argument("--audiences", required=True, help="comma-separated audience names")
    ap.add_argument("--contexts", required=True, help="comma-separated context keys")
    ap.add_argument("--n", type=int, default=None, help="limit personas per audience (pilot use)")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    audiences = load_json(AUDIENCES_PATH)
    contexts = load_json(CONTEXTS_PATH)
    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for aud_name in args.audiences.split(","):
        aud = audiences[aud_name]
        personas = load_jsonl(PERSONAS_DIR / f"{aud_name}.jsonl")
        if args.n:
            personas = personas[: args.n]
        fewshot_block = build_fewshot_block(aud_name) if args.condition == "fewshot" else None

        for ctx_key in args.contexts.split(","):
            ctx = contexts[ctx_key]
            for persona in personas:
                prompt = build_prompt(aud["description"], persona["text"], ctx["prompt"], fewshot_block)
                jobs.append({
                    "audience": aud_name, "context": ctx_key, "persona_id": persona["id"],
                    "prompt": prompt,
                })

    print(f"running {len(jobs)} generation calls (condition={args.condition}, concurrency={args.concurrency})")

    results = []
    errors = []

    def run_job(job):
        text, err = call_openai(job["prompt"])
        return job, text, err

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for job, text, err in pool.map(run_job, jobs):
            if err:
                errors.append({**{k: v for k, v in job.items() if k != "prompt"}, "error": err})
                print(f"ERROR {job['audience']}/{job['context']}/{job['persona_id']}: {err}")
            else:
                results.append({
                    "audience": job["audience"], "context": job["context"],
                    "persona_id": job["persona_id"], "condition": args.condition,
                    "model": MODEL, "text": text,
                })
                print(f"ok    {job['audience']}/{job['context']}/{job['persona_id']}: {text[:80]!r}")

    out_path = out_dir / f"{args.condition}.jsonl"
    with open(out_path, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    if errors:
        err_path = out_dir / f"{args.condition}_errors.jsonl"
        with open(err_path, "a") as f:
            for e in errors:
                f.write(json.dumps(e) + "\n")

    print(f"\ndone: {len(results)} ok, {len(errors)} errors -> {out_path}")


if __name__ == "__main__":
    main()
