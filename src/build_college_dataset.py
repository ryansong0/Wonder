"""
Rebuilds data/colleges.csv from scratch by bulk-pulling every currently-operating,
predominantly bachelor's-degree-granting US institution from the College Scorecard
API. Supersedes hand-picking and hand-typing a school list: cost of attendance and
net price by income come directly from what each school reports to the federal
government, for every school that reports it - not just a curated 98.

A school is only included if it has both a reported cost of attendance and at
least two of the five net-price-by-income brackets, since that's the minimum the
simulation engine needs to interpolate a real point estimate
(see MonteCarloEngine.real_net_price_estimate). Schools missing that data are
left out rather than backfilled with guessed aid-generosity numbers.

Usage:
    Set COLLEGE_SCORECARD_API_KEY in a .env file at the project root, then:
    python -m src.build_college_dataset
"""
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "colleges.csv"
PER_PAGE = 100

# (bracket key in the Scorecard API) -> (column name in colleges.csv)
BRACKETS = [
    ("0-30000", "net_price_0_30k"),
    ("30001-48000", "net_price_30k_48k"),
    ("48001-75000", "net_price_48k_75k"),
    ("75001-110000", "net_price_75k_110k"),
    ("110001-plus", "net_price_110k_plus"),
]

# school.ownership: 1 = public, 2 = private nonprofit, 3 = private for-profit
OWNERSHIP_TO_SECTOR = {1: "public", 2: "private", 3: "private"}

FIELDS = ",".join(
    [
        "school.name", "school.state", "school.ownership",
        "latest.cost.attendance.academic_year",
        "latest.cost.tuition.in_state", "latest.cost.tuition.out_of_state",
    ]
    + [f"latest.cost.net_price.public.by_income_level.{key}" for key, _ in BRACKETS]
    + [f"latest.cost.net_price.private.by_income_level.{key}" for key, _ in BRACKETS]
)


def fetch_all_pages(api_key: str) -> list[dict]:
    records = []
    page = 0
    while True:
        response = requests.get(
            API_URL,
            params = {
                "api_key": api_key,
                "school.operating": 1,
                "school.degrees_awarded.predominant": 3,
                "fields": FIELDS,
                "per_page": PER_PAGE,
                "page": page,
            },
            timeout = 30,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        records.extend(results)
        page += 1
        if page * PER_PAGE >= data["metadata"]["total"]:
            break
        time.sleep(0.2)

    return records


def record_to_row(record: dict) -> dict | None:
    sector = OWNERSHIP_TO_SECTOR.get(record.get("school.ownership"))
    coa = record.get("latest.cost.attendance.academic_year")
    if sector is None or coa is None:
        return None

    brackets = {
        column: record.get(f"latest.cost.net_price.{sector}.by_income_level.{bracket_key}")
        for bracket_key, column in BRACKETS
    }
    known_bracket_count = sum(v is not None for v in brackets.values())
    if known_bracket_count < 2:
        return None

    # A handful of schools report a negative net price (aid exceeding the
    # modeled cost components for a small sample) - clip to 0.
    brackets = {column: (max(0, v) if v is not None else None) for column, v in brackets.items()}

    in_state_tuition = record.get("latest.cost.tuition.in_state")
    out_of_state_tuition = record.get("latest.cost.tuition.out_of_state")
    out_of_state_premium = None
    if in_state_tuition is not None and out_of_state_tuition is not None:
        # For private schools these are equal (or missing), so the premium is
        # naturally 0 - no need to special-case by sector.
        out_of_state_premium = max(0, out_of_state_tuition - in_state_tuition)

    return {
        "college_name": record["school.name"],
        "state": record.get("school.state"),
        "cost_of_attendance": coa,
        "out_of_state_tuition_premium": out_of_state_premium,
        # Real per-bracket data already reflects how generous a school is at
        # low incomes, so there's no need for a separately curated "pays
        # nothing below this income" override the way the original hand-typed
        # list had - leaving this at 0 lets the real data speak for itself.
        "tuition_free_threshold": 0,
        # Not derivable from Scorecard and unused once real bracket data
        # exists (see MonteCarloEngine.calculate_net_price's formula-fallback
        # branch, which is what this would otherwise feed).
        "average_aid_percentage": None,
        "endowment_size": None,
        # Scorecard doesn't report which aid methodology a school uses. This
        # is the same ownership-based proxy used for the original hand-picked
        # list: private institutions (nonprofit or for-profit) skew toward
        # CSS Profile / institutional methodology, public toward federal-only.
        # It's a heuristic, not a verified per-school fact.
        "requires_css_profile": sector == "private",
        **brackets,
    }


def main():
    api_key = os.environ.get("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
    if api_key in ("DEMO_KEY", "paste_your_key_here"):
        print("No COLLEGE_SCORECARD_API_KEY set in .env — falling back to DEMO_KEY, which is heavily rate-limited.")

    print("Fetching all currently-operating, predominantly bachelor's-degree institutions...")
    records = fetch_all_pages(api_key)
    print(f"Fetched {len(records)} raw records.")

    rows = [row for row in (record_to_row(r) for r in records) if row is not None]
    df = pd.DataFrame(rows)

    # A handful of school names exist in more than one state (e.g. Westminster
    # College is a real, different school in MO, PA, and UT). Disambiguate
    # only those with their state in the name; "state" is also kept as its own
    # column so the engine can compare it against a student's residency.
    is_duplicate_name = df["college_name"].duplicated(keep = False)
    df.loc[is_duplicate_name, "college_name"] = df.loc[is_duplicate_name, "college_name"] + " (" + df.loc[is_duplicate_name, "state"] + ")"
    df = df.sort_values("college_name")

    df.to_csv(CSV_PATH, index = False)

    print(f"Wrote {len(df)} schools with usable net-price data to {CSV_PATH}")
    print(f"({len(records) - len(df)} schools were excluded for missing cost of attendance or insufficient net-price brackets)")


if __name__ == "__main__":
    main()
