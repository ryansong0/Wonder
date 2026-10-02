"""
Shared helpers for the evaluation scripts: fixed seeding, a cached raw pull
from the College Scorecard API, and building CollegeData objects from any
Scorecard year using the same record_to_row logic as the real dataset build.

The API key is read from COLLEGE_SCORECARD_API_KEY (environment first, then
the project's .env, matching build_college_dataset.py). It is never written
to disk or printed.
"""
import json
import os
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

from src.build_college_dataset import API_URL, BRACKETS, PER_PAGE, record_to_row
from src.engine import INCOME_BRACKET_MIDPOINTS
from src.loader import load_college_data
from src.schemas import CollegeData, StudentProfile, US_STATE_CODES

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
CACHE_PATH = EVAL_DIR / "cache" / "scorecard_raw.json"
RESULTS_DIR = EVAL_DIR / "results"

SEED = 20261001
TRIALS = 1000

# Years pulled for the time holdout. "latest" is the current release and is
# what colleges.csv is built from; HOLDOUT_YEARS are older releases used as
# the simulation's inputs, scored against the latest published values.
LATEST_YEAR = 2024
HOLDOUT_YEARS = [2023, 2021]

BRACKET_COLUMNS = [column for _, column in BRACKETS]
MIDPOINT_BY_COLUMN = {column: income for income, column in INCOME_BRACKET_MIDPOINTS}

_YEAR_FIELD_SUFFIXES = (
    ["school.name", "school.state", "school.ownership"]
    + ["cost.attendance.academic_year", "cost.tuition.in_state", "cost.tuition.out_of_state"]
    + [f"cost.net_price.{sector}.by_income_level.{key}" for sector in ("public", "private") for key, _ in BRACKETS]
)


def _fields() -> str:
    fields = ["id", "school.name", "school.state", "school.ownership"]
    for prefix in ["latest", str(LATEST_YEAR)] + [str(y) for y in HOLDOUT_YEARS]:
        fields += [f"{prefix}.{suffix}" for suffix in _YEAR_FIELD_SUFFIXES if not suffix.startswith("school.")]
    return ",".join(fields)


def school_seed(*parts: int) -> int:
    """A stable per-(school, bracket, ...) seed, so every simulation is
    reproducible and independent of iteration order, without every school
    sharing the exact same random draws."""
    return int(np.random.SeedSequence([SEED, *parts]).generate_state(1)[0])


def fetch_raw(refresh: bool = False) -> dict:
    """Pulls every record the dataset build considers (same filters as
    build_college_dataset.fetch_all_pages), plus older-year fields, and caches
    the raw JSON so the evaluation is reproducible offline."""
    if CACHE_PATH.exists() and not refresh:
        return json.loads(CACHE_PATH.read_text())

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("COLLEGE_SCORECARD_API_KEY")
    if not api_key or api_key in ("DEMO_KEY", "paste_your_key_here"):
        raise RuntimeError("Set COLLEGE_SCORECARD_API_KEY (environment or .env) to fetch raw Scorecard data.")

    records, page = [], 0
    while True:
        response = requests.get(
            API_URL,
            params = {
                "api_key": api_key,
                "school.operating": 1,
                "school.degrees_awarded.predominant": 3,
                "fields": _fields(),
                "per_page": PER_PAGE,
                "page": page,
            },
            timeout = 60,
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

    payload = {"fetched_on": date.today().isoformat(), "records": records}
    CACHE_PATH.parent.mkdir(parents = True, exist_ok = True)
    CACHE_PATH.write_text(json.dumps(payload))
    return payload


def as_year(record: dict, year: int | str) -> dict:
    """Re-keys a raw record so `{year}.cost...` fields appear as `latest.cost...`,
    letting the unmodified record_to_row build a row from an older release."""
    out = {k: v for k, v in record.items() if k.startswith("school.") or k == "id"}
    prefix = f"{year}."
    for k, v in record.items():
        if k.startswith(prefix):
            out["latest." + k[len(prefix):]] = v
    return out


def rows_to_colleges(rows: list[dict]) -> dict[int, CollegeData]:
    """Keyed by Scorecard unit id so different years line up exactly."""
    return {row.pop("_id"): CollegeData(**row) for row in rows}


def build_colleges_for_year(records: list[dict], year: int | str) -> dict[int, CollegeData]:
    rows = []
    for record in records:
        row = record_to_row(as_year(record, year))
        if row is not None:
            row["_id"] = record["id"]
            rows.append(row)
    return rows_to_colleges(rows)


def load_current_colleges() -> list[CollegeData]:
    return load_college_data()


def in_state_student(college: CollegeData, income: float) -> StudentProfile:
    """A zero-asset, in-state household at the given income, so the comparison
    isolates the aid model: no asset add-on and no out-of-state premium. Schools
    in territories (PR, GU, VI) can't be matched by a validated StudentProfile,
    since it only accepts states + DC, so those bypass validation here."""
    fields = dict(household_income = income, liquid_assets = 0.0, family_size = 4, state_of_residence = college.state)
    if college.state in US_STATE_CODES:
        return StudentProfile(**fields)
    return StudentProfile.model_construct(**fields)


def known_brackets(college: CollegeData) -> list[str]:
    return [c for c in BRACKET_COLUMNS if getattr(college, c) is not None]


def colleges_frame(colleges) -> pd.DataFrame:
    return pd.DataFrame([c.model_dump() for c in colleges])
