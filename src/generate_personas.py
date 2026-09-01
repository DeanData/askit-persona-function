#!/usr/bin/env python3
"""Generate the fixed persona roster: ~40 personas per audience, structured schema,
rendered into one templated sentence per persona.

Locked design (see WORKLOG.md / persona-format decision):
  - Structured fields (not free text) are the actual representation; the rendered
    sentence is just the surface form handed to the model.
  - Fields: age, occupation (age-conditioned), region, family_status, and one
    open-ended "detail" field for idiosyncratic color.
  - No field restates the audience's defining trait (risk-orientation /
    sophistication) — the occupation pool deliberately excludes finance-professional
    titles for this reason, and the detail pool is deliberately non-finance, so
    audience voice has to come from the model's use of the audience description,
    not from a demographic proxy baked into the sampler.
  - Core demographic fields (age, region, family_status, detail) are drawn from the
    SAME shared distributions regardless of audience, on purpose: this isolates the
    audience description as the only systematically-varying input besides context,
    the same "hold everything else fixed" logic already used for contexts.
  - Fixed seed, roster generated once and committed — baseline and improvement runs
    use the identical roster (paired comparison).
"""
import json
import random
from pathlib import Path

AUDIENCES = ["personalfinance", "wallstreetbets", "fatFIRE", "thetagang", "povertyfinance"]
N_PER_AUDIENCE = 40
SEED = 42

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "personas"

# Occupation pool, deliberately generic and finance-profession-free, bucketed only by
# age (not audience) so it never correlates with the audience's defining trait.
OCCUPATIONS_BY_AGE = {
    "early": [  # 22-29
        "a barista", "a retail associate", "a warehouse worker", "a junior graphic designer",
        "an administrative assistant", "a line cook", "an elementary school teacher",
        "an IT support technician", "a veterinary assistant", "a delivery driver",
    ],
    "mid": [  # 30-44
        "a nurse", "a middle school teacher", "a software engineer", "an electrician",
        "a landscaping business owner", "a marketing coordinator", "a physical therapist",
        "a restaurant manager", "a dental hygienist", "a truck driver",
    ],
    "late": [  # 45-64
        "a high school principal", "a general contractor", "a senior software engineer",
        "a nurse practitioner", "a shop owner", "a regional sales manager",
        "a mechanical engineer", "an office manager", "a paralegal", "a plumber",
    ],
}

REGIONS = [
    "Columbus, Ohio", "Sacramento, California", "a suburb outside Atlanta, Georgia",
    "Pittsburgh, Pennsylvania", "a small town in rural Minnesota", "Austin, Texas",
    "Tampa, Florida", "Portland, Oregon", "a suburb of Chicago, Illinois",
    "Richmond, Virginia", "Boise, Idaho", "Charlotte, North Carolina",
    "Albuquerque, New Mexico", "a rural area outside Des Moines, Iowa",
    "Seattle, Washington", "Louisville, Kentucky",
]

FAMILY_STATUSES = [
    "single, no kids", "married, no kids", "married with two young kids",
    "divorced, shares custody of one child", "engaged", "single parent raising a teenager",
    "long-term partner, no kids yet", "recently widowed",
]

DETAILS = [
    "Recently adopted a rescue dog.", "Training for a half marathon this spring.",
    "Has been renovating the kitchen on weekends.", "Started taking pottery classes recently.",
    "Helping a sibling move across the country next week.", "Just got back from a camping trip.",
    "Has been binge-watching a new true crime series.", "Recently started a vegetable garden.",
    "Learning to play guitar in spare time.", "Just switched to a new gym routine.",
    "Has been dealing with a leaky roof since last week.",
    "Planning a small backyard wedding for next summer.",
    "Has been volunteering at a local food bank on weekends.", "Recently took up rock climbing.",
]


def age_bucket(age):
    if age <= 29:
        return "early"
    if age <= 44:
        return "mid"
    return "late"


def make_persona(rng, audience, idx):
    age = rng.randint(22, 64)
    occupation = rng.choice(OCCUPATIONS_BY_AGE[age_bucket(age)])
    region = rng.choice(REGIONS)
    family_status = rng.choice(FAMILY_STATUSES)
    detail = rng.choice(DETAILS)

    text = f"{age}, {family_status}, lives in {region}, works as {occupation}. {detail}"

    return {
        "id": f"{audience}_{idx:02d}",
        "audience": audience,
        "age": age,
        "occupation": occupation,
        "region": region,
        "family_status": family_status,
        "detail": detail,
        "text": text,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for audience in AUDIENCES:
        # per-audience Random instance, deterministic but independent field draws
        rng = random.Random(f"{SEED}-{audience}")
        personas = [make_persona(rng, audience, i) for i in range(N_PER_AUDIENCE)]

        out_path = OUT_DIR / f"{audience}.jsonl"
        with open(out_path, "w") as f:
            for p in personas:
                f.write(json.dumps(p) + "\n")
        print(f"{audience}: wrote {len(personas)} personas -> {out_path}")


if __name__ == "__main__":
    main()
