"""
One-off script: enriches data/colleges.csv with real published net-price-by-income
data from the College Scorecard API, so the simulation engine can center its
distribution on a school's own reported numbers instead of our formula wherever
that data exists.

Usage:
    Set COLLEGE_SCORECARD_API_KEY in a .env file at the project root, then:
    python -m src.calibrate_from_scorecard
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

# colleges.csv uses common/informal names; College Scorecard requires an exact
# match against a school's official IPEDS name (multi-campus systems in
# particular - "Rutgers University" isn't a record, "Rutgers University-New
# Brunswick" is). Mapped by hand after checking each one actually resolves
# to a single record.
SCORECARD_NAME_ALIASES = {
    "MIT": "Massachusetts Institute of Technology",
    "Columbia University": "Columbia University in the City of New York",
    "University of Michigan": "University of Michigan-Ann Arbor",
    "Washington University in St. Louis": "Washington University in St Louis",
    "University of Virginia": "University of Virginia-Main Campus",
    "UNC Chapel Hill": "University of North Carolina at Chapel Hill",
    "University of Texas at Austin": "The University of Texas at Austin",
    "University of Pittsburgh": "University of Pittsburgh-Pittsburgh Campus",
    "Pennsylvania State University": "Pennsylvania State University-Main Campus",
    "Georgia Institute of Technology": "Georgia Institute of Technology-Main Campus",
    "University of California Berkeley": "University of California-Berkeley",
    "University of California San Diego": "University of California-San Diego",
    "University of California Irvine": "University of California-Irvine",
    "University of California Davis": "University of California-Davis",
    "University of California Los Angeles": "University of California-Los Angeles",
    "Tulane University": "Tulane University of Louisiana",
    "University of Maryland": "University of Maryland-College Park",
    "Ohio State University": "Ohio State University-Main Campus",
    "Purdue University": "Purdue University-Main Campus",
    "Arizona State University": "Arizona State University Campus Immersion",
    "Texas A&M University": "Texas A&M University-College Station",
    "University of Nebraska Lincoln": "University of Nebraska-Lincoln",
    "Rutgers University": "Rutgers University-New Brunswick",
    "Indiana University": "Indiana University-Bloomington",
    "University of Minnesota": "University of Minnesota-Twin Cities",
    "University of Washington": "University of Washington-Seattle Campus",
    "Louisiana State University": "Louisiana State University and Agricultural & Mechanical College",
    "University of Oklahoma": "University of Oklahoma-Norman Campus",
    "University of Alabama": "The University of Alabama",
    "North Carolina State University": "North Carolina State University at Raleigh",
    "University of Missouri": "University of Missouri-Columbia",
    "University of Cincinnati": "University of Cincinnati-Main Campus",
}


def fetch_net_price_by_income(api_key: str, college_name: str) -> dict | None:
    search_name = SCORECARD_NAME_ALIASES.get(college_name, college_name)
    response = requests.get(
        API_URL,
        params = {"api_key": api_key, "school.name": search_name, "per_page": 20},
        timeout = 20,
    )
    response.raise_for_status()
    results = response.json().get("results", [])

    # school.name is a relevance-ranked search, not an exact filter - e.g. a
    # query for "University of Florida" can rank "Florida State University"
    # first. Only accept a case-insensitive exact name match; anything else
    # falls back to the formula rather than risk silently calibrating a
    # school with a different school's data.
    record = next(
        (r for r in results if r.get("school", {}).get("name", "").lower() == search_name.lower()),
        None,
    )
    if record is None:
        return None

    sector = OWNERSHIP_TO_SECTOR.get(record.get("school", {}).get("ownership"))
    if sector is None:
        return None

    by_income_level = (
        record.get("latest", {})
        .get("cost", {})
        .get("net_price", {})
        .get(sector, {})
        .get("by_income_level", {})
    )
    values = {column: by_income_level.get(bracket_key) for bracket_key, column in BRACKETS}
    if all(v is None for v in values.values()):
        return None
    # A handful of schools report a negative net price (aid exceeding the
    # modeled cost components for a small sample) - clip to 0, since a
    # negative cost isn't meaningful for the simulation.
    return {column: (max(0, v) if v is not None else None) for column, v in values.items()}


def main():
    api_key = os.environ.get("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
    if api_key in ("DEMO_KEY", "paste_your_key_here"):
        print("No COLLEGE_SCORECARD_API_KEY set in .env — falling back to DEMO_KEY, which is heavily rate-limited.")

    df = pd.read_csv(CSV_PATH)
    for _, column in BRACKETS:
        if column not in df.columns:
            df[column] = None

    matched, no_data, errors = 0, [], []
    for idx, row in df.iterrows():
        college_name = row["college_name"]
        try:
            values = fetch_net_price_by_income(api_key, college_name)
        except requests.RequestException as exc:
            errors.append(f"{college_name}: {exc}")
            continue

        if values is None:
            no_data.append(college_name)
            continue

        for column, value in values.items():
            df.at[idx, column] = value
        matched += 1
        time.sleep(0.15)

    df.to_csv(CSV_PATH, index = False)

    print(f"Calibrated {matched}/{len(df)} schools with real net-price-by-income data.")
    if no_data:
        print(f"No Scorecard net-price data found for {len(no_data)} schools:", ", ".join(no_data))
    if errors:
        print(f"{len(errors)} requests failed:")
        for error in errors:
            print(f"  {error}")


if __name__ == "__main__":
    main()
