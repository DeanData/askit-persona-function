#!/usr/bin/env python3
"""Export the Claude Code session transcript for this project into sessions/.

Reads the raw session JSONL that Claude Code keeps under
~/.claude/projects/<encoded-cwd>/<session-id>.jsonl and renders it as a
readable Markdown transcript: user turns, assistant text, assistant
reasoning, and tool calls/results, in order. Dead ends are kept — nothing
is dropped for looking bad. Only two kinds of content are altered:

  - secret-shaped strings (API keys, tokens) are replaced with [REDACTED]
  - very large / binary-looking blobs (e.g. a base64 PDF read back from a
    tool result) are replaced with a short placeholder, since the source
    file is already in the repo and the raw bytes add nothing to a human
    reading the transcript

Re-run this at checkpoints; it overwrites the one file per session, so the
transcript in the repo always reflects the session up to the last run.
"""
import json
import re
import sys
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUT_DIR = Path(__file__).resolve().parent.parent / "sessions"
MAX_INLINE_CHARS = 3000

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"sk-proj-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[oprsu]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{20,}"),
]


def redact(text: str) -> str:
    for pat in SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def looks_binary(text: str) -> bool:
    if len(text) < 500:
        return False
    sample = text[:2000]
    printable = sum(c.isprintable() or c in "\n\r\t" for c in sample)
    return printable / max(len(sample), 1) < 0.85


def shrink(text: str) -> str:
    text = redact(text)
    if looks_binary(text):
        return f"[binary/base64 content omitted, {len(text)} chars — source is elsewhere in the repo]"
    if len(text) > MAX_INLINE_CHARS:
        return text[:MAX_INLINE_CHARS] + f"\n... [truncated, {len(text)} chars total]"
    return text


def find_session_file(session_id: str) -> Path:
    matches = list(CLAUDE_PROJECTS_DIR.glob(f"*/{session_id}.jsonl"))
    if not matches:
        sys.exit(f"no session file found for {session_id} under {CLAUDE_PROJECTS_DIR}")
    return matches[0]


def render_content_block(block: dict) -> str:
    btype = block.get("type")
    if btype == "text":
        return shrink(block.get("text", ""))
    if btype == "thinking":
        thinking = shrink(block.get("thinking", ""))
        return f"*(internal reasoning)*\n\n> {thinking.replace(chr(10), chr(10) + '> ')}"
    if btype == "tool_use":
        name = block.get("name", "?")
        try:
            inp = json.dumps(block.get("input", {}), indent=2)
        except TypeError:
            inp = str(block.get("input"))
        return f"**tool call: `{name}`**\n```json\n{shrink(inp)}\n```"
    if btype == "tool_result":
        content = block.get("content", "")
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c.get("text", ""))
                else:
                    parts.append(str(c))
            content = "\n".join(parts)
        elif not isinstance(content, str):
            content = json.dumps(content)
        return f"**tool result:**\n```\n{shrink(content)}\n```"
    return f"[unhandled content block type: {btype}]"


def render_record(rec: dict) -> str:
    role = rec.get("message", {}).get("role", rec.get("type", "?"))
    ts = rec.get("timestamp", "")
    content = rec.get("message", {}).get("content", "")
    if isinstance(content, str):
        body = shrink(content)
    elif isinstance(content, list):
        body = "\n\n".join(render_content_block(b) for b in content if isinstance(b, dict))
    else:
        body = ""
    header = f"## {role} — {ts}"
    return f"{header}\n\n{body}\n"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: export_session_log.py <session-id>")
    session_id = sys.argv[1]
    session_file = find_session_file(session_id)

    records = []
    with open(session_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") in ("user", "assistant"):
                records.append(rec)

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / f"session_{session_id}.md"
    with open(out_path, "w") as f:
        f.write(f"# Claude Code session transcript — {session_id}\n\n")
        f.write(
            "Rendered from the raw Claude Code session log. Dead ends included. "
            "Secret-shaped strings are redacted; very large/binary tool output is "
            "replaced with a short placeholder. Everything else is as it happened.\n\n"
        )
        f.write("---\n\n")
        for rec in records:
            f.write(render_record(rec))
            f.write("\n---\n\n")

    print(f"wrote {out_path} ({len(records)} records)")


if __name__ == "__main__":
    main()
