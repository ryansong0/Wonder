"""
Validation of the simulated net-price band against College Scorecard's
published net price by income.

Net price by income is the *input* that centers every simulation, so simply
checking whether the published value falls inside the simulated band is
circular. That check is still reported, labeled as a sanity check only.
The real metrics hide the value being predicted from the simulation:

  1. Leave-one-bracket-out (main metric): for each school with >= 3 reported
     brackets, drop one bracket, simulate at that bracket's income midpoint
     using only the remaining brackets, and score the hidden published value.
  2. Time holdout: build each school from an older Scorecard release (2023,
     2021), simulate forward with the engine's own inflation model, and score
     against the latest (2024) published value.

Every simulation uses a zero-asset, in-state household so the asset add-on
and out-of-state premium don't apply; this isolates the aid model. Two bands
are reported: the annual aid band before inflation (calculate_net_price's
per-trial samples, the primary band since Scorecard values are annual), and
the engine's full 4-year total divided by 4 (all_net_price_trials / 4, which
also carries inflation).
"""
import numpy as np
import pandas as pd

from eval.common import (
    BRACKET_COLUMNS, HOLDOUT_YEARS, LATEST_YEAR, MIDPOINT_BY_COLUMN, TRIALS,
    build_colleges_for_year, fetch_raw, in_state_student, known_brackets, school_seed,
)
from src.config import INFLATION_MAX, INFLATION_MIN, YEARS_OF_COLLEGE
from src.engine import MonteCarloEngine

PERCENTILES = [5, 10, 50, 90, 95]


def _band(samples: np.ndarray) -> dict:
    p05, p10, p50, p90, p95 = np.percentile(samples, PERCENTILES)
    return {"p05": p05, "p10": p10, "p50": p50, "p90": p90, "p95": p95}


def simulate_annual(engine: MonteCarloEngine, college, student, seed: int) -> dict:
    np.random.seed(seed)
    return _band(engine.calculate_net_price(student, college))


def simulate_total_per_year(engine: MonteCarloEngine, college, student, seed: int) -> dict:
    np.random.seed(seed)
    # _run_simulation, not run_simulation: the lru_cache would otherwise
    # return a stale result regardless of the seed.
    result = engine._run_simulation(college, student)
    return _band(result.all_net_price_trials / YEARS_OF_COLLEGE)


def summarize(df: pd.DataFrame, band: str = "") -> dict:
    """Coverage and error of the published value against one band's columns
    (prefixed by `band`)."""
    pub = df["published"]
    p = {k: df[f"{band}{k}"] for k in ("p05", "p10", "p50", "p90", "p95")}
    err = p["p50"] - pub
    return {
        "n": int(len(df)),
        "coverage_p10_p90_pct": round(100 * float(((pub >= p["p10"]) & (pub <= p["p90"])).mean()), 2),
        "coverage_p05_p95_pct": round(100 * float(((pub >= p["p05"]) & (pub <= p["p95"])).mean()), 2),
        "below_p10_pct": round(100 * float((pub < p["p10"]).mean()), 2),
        "above_p90_pct": round(100 * float((pub > p["p90"]).mean()), 2),
        "mae_vs_median_usd": round(float(err.abs().mean()), 0),
        "median_abs_error_usd": round(float(err.abs().median()), 0),
        "bias_median_minus_published_usd": round(float(err.mean()), 0),
        "wape_pct": round(100 * float(err.abs().sum() / pub.sum()), 2),
        "mean_published_usd": round(float(pub.mean()), 0),
        "mean_p10_p90_width_usd": round(float((p["p90"] - p["p10"]).mean()), 0),
    }


def grouped(df: pd.DataFrame, by: str, band: str = "") -> dict:
    return {str(k): summarize(g, band) for k, g in df.groupby(by)}


def _row(college, column, published, annual, total, **extra) -> dict:
    return {
        "college_name": college.college_name,
        "bracket": column,
        "methodology": "CSS label" if college.requires_css_profile else "federal-only label",
        "published": published,
        **annual,
        **{f"total_{k}": v for k, v in total.items()},
        **extra,
    }


def circular_check(engine: MonteCarloEngine, colleges) -> pd.DataFrame:
    rows = []
    for i, college in enumerate(colleges):
        for j, column in enumerate(known_brackets(college)):
            student = in_state_student(college, MIDPOINT_BY_COLUMN[column])
            seed = school_seed(1, i, BRACKET_COLUMNS.index(column))
            rows.append(_row(college, column, getattr(college, column),
                             simulate_annual(engine, college, student, seed),
                             simulate_total_per_year(engine, college, student, seed)))
    return pd.DataFrame(rows)


def leave_one_bracket_out(engine: MonteCarloEngine, colleges) -> pd.DataFrame:
    rows = []
    for i, college in enumerate(colleges):
        known = known_brackets(college)
        if len(known) < 3:
            continue
        for column in known:
            held_out = college.model_copy(update = {column: None})
            student = in_state_student(college, MIDPOINT_BY_COLUMN[column])
            seed = school_seed(2, i, BRACKET_COLUMNS.index(column))
            # Interior: the hidden bracket sits between two reported ones, so
            # np.interp truly interpolates. Edge: it's the lowest or highest
            # reported bracket, so np.interp holds the nearest value flat.
            position = "interior" if known[0] != column and known[-1] != column else "edge"
            rows.append(_row(college, column, getattr(college, column),
                             simulate_annual(engine, held_out, student, seed),
                             simulate_total_per_year(engine, held_out, student, seed),
                             position = position))
    return pd.DataFrame(rows)


def time_holdout(engine: MonteCarloEngine, records: list[dict], base_year: int) -> pd.DataFrame:
    """Simulates from the base_year release and scores against the latest
    release. The forecast for the latest year applies the engine's own
    inflation model for (LATEST_YEAR - base_year) years, the same way
    _run_simulation inflates year 1 of college relative to the data year."""
    horizon = LATEST_YEAR - base_year
    base = build_colleges_for_year(records, base_year)
    target = build_colleges_for_year(records, "latest")
    rows = []
    for unit_id, latest in target.items():
        college = base.get(unit_id)
        if college is None:
            continue
        for column in known_brackets(latest):
            student = in_state_student(college, MIDPOINT_BY_COLUMN[column])
            np.random.seed(school_seed(3, base_year, unit_id, BRACKET_COLUMNS.index(column)))
            aid_samples = engine.calculate_net_price(student, college)
            inflation = np.prod(1 + np.random.uniform(INFLATION_MIN, INFLATION_MAX, (engine.trials, horizon)), axis = 1)
            band = _band(aid_samples * inflation)
            rows.append({
                "college_name": latest.college_name,
                "bracket": column,
                "methodology": "CSS label" if college.requires_css_profile else "federal-only label",
                "published": getattr(latest, column),
                # Naive baseline: assume last published value doesn't change.
                "persistence": engine.real_net_price_estimate(college, student.household_income),
                **band,
            })
    return pd.DataFrame(rows)


def persistence_summary(df: pd.DataFrame) -> dict:
    err = df["persistence"] - df["published"]
    return {
        "mae_usd": round(float(err.abs().mean()), 0),
        "median_abs_error_usd": round(float(err.abs().median()), 0),
        "bias_usd": round(float(err.mean()), 0),
        "wape_pct": round(100 * float(err.abs().sum() / df["published"].sum()), 2),
    }


def run() -> tuple[dict, dict[str, pd.DataFrame]]:
    engine = MonteCarloEngine(trials = TRIALS)
    records = fetch_raw()["records"]
    colleges = list(build_colleges_for_year(records, "latest").values())
    colleges.sort(key = lambda c: c.college_name)

    circ = circular_check(engine, colleges)
    lobo = leave_one_bracket_out(engine, colleges)
    holdouts = {year: time_holdout(engine, records, year) for year in HOLDOUT_YEARS}

    results = {
        "trials_per_simulation": TRIALS,
        "student": "in-state, $0 liquid assets, income = bracket midpoint",
        "leave_one_bracket_out": {
            "schools": int(lobo["college_name"].nunique()),
            "annual_band": summarize(lobo),
            "annual_band_by_position": grouped(lobo, "position"),
            "annual_band_by_methodology": grouped(lobo, "methodology"),
            "annual_band_by_bracket": grouped(lobo, "bracket"),
            "four_year_total_div_4": summarize(lobo, "total_"),
        },
        "sanity_check_circular": {
            "note": "Published net price is the simulation's center input; near-full coverage is expected by construction and is NOT evidence of accuracy.",
            "schools": int(circ["college_name"].nunique()),
            "annual_band": summarize(circ),
            "four_year_total_div_4": summarize(circ, "total_"),
        },
        "time_holdout": {
            str(year): {
                "base_year": year,
                "target_year": LATEST_YEAR,
                "horizon_years": LATEST_YEAR - year,
                "schools": int(df["college_name"].nunique()),
                "forecast_band": summarize(df),
                "forecast_band_by_methodology": grouped(df, "methodology"),
                "persistence_baseline": persistence_summary(df),
            }
            for year, df in holdouts.items()
        },
    }
    frames = {"leave_one_bracket_out": lobo, "sanity_check_circular": circ,
              **{f"time_holdout_{y}": df for y, df in holdouts.items()}}
    return results, frames


if __name__ == "__main__":
    import json
    print(json.dumps(run()[0], indent = 2))
