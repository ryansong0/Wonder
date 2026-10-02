"""
Data quality of the College Scorecard ingestion: how many raw records were
dropped and why, and how many kept schools have missing or internally
inconsistent fields, alongside how the code handles each case.
"""
from collections import Counter

import pandas as pd

from eval.common import BRACKET_COLUMNS, BRACKETS, colleges_frame, fetch_raw, load_current_colleges
from src.build_college_dataset import OWNERSHIP_TO_SECTOR, record_to_row
from src.schemas import US_STATE_CODES


def _pct(n: int, d: int) -> float:
    return round(100 * n / d, 2) if d else 0.0


def raw_exclusions(records: list[dict]) -> dict:
    """Mirrors record_to_row's filters in order, counting why each record is dropped."""
    reasons = Counter()
    negative_clipped_schools = 0
    negative_clipped_values = 0
    premium_clipped = 0
    for r in records:
        sector = OWNERSHIP_TO_SECTOR.get(r.get("school.ownership"))
        if sector is None:
            reasons["unknown ownership"] += 1
            continue
        if r.get("latest.cost.attendance.academic_year") is None:
            reasons["missing cost of attendance"] += 1
            continue
        values = [r.get(f"latest.cost.net_price.{sector}.by_income_level.{key}") for key, _ in BRACKETS]
        known = [v for v in values if v is not None]
        if len(known) < 2:
            reasons[f"only {len(known)} net-price bracket(s)"] += 1
            continue
        reasons["kept"] += 1
        negatives = sum(v < 0 for v in known)
        negative_clipped_values += negatives
        negative_clipped_schools += negatives > 0
        in_state, out_state = r.get("latest.cost.tuition.in_state"), r.get("latest.cost.tuition.out_of_state")
        if in_state is not None and out_state is not None and out_state < in_state:
            premium_clipped += 1

    total = len(records)
    kept = reasons.pop("kept", 0)
    return {
        "raw_records": total,
        "kept": kept,
        "excluded": total - kept,
        "excluded_pct": _pct(total - kept, total),
        "exclusion_reasons": {k: {"count": v, "pct_of_raw": _pct(v, total)} for k, v in reasons.most_common()},
        "kept_with_negative_net_price_clipped_to_0": negative_clipped_schools,
        "negative_net_price_values_clipped": negative_clipped_values,
        "kept_with_out_of_state_below_in_state_tuition": premium_clipped,
        "missing_ownership_raw": sum(r.get("school.ownership") is None for r in records),
    }


def kept_quality(df: pd.DataFrame) -> dict:
    n = len(df)
    b = df[BRACKET_COLUMNS]
    known_count = b.notna().sum(axis = 1)
    # Relative drop between consecutive *reported* brackets, so a gap in the
    # middle doesn't hide a decrease.
    def max_relative_drop(row):
        vals = row.dropna().to_numpy()
        drops = [(a - c) / a for a, c in zip(vals[:-1], vals[1:]) if a > 0]
        return max(drops) if drops else 0.0
    rel_drop = b.apply(max_relative_drop, axis = 1)

    missing_any = int((known_count < 5).sum())
    nonmono_any = int((rel_drop > 0).sum())
    nonmono_10 = int((rel_drop > 0.10).sum())
    flat_top = int(df["net_price_110k_plus"].isna().sum())
    flat_bottom = int(df["net_price_0_30k"].isna().sum())
    territories = int((~df["state"].isin(US_STATE_CODES)).sum())
    zero_bracket = int((b == 0).any(axis = 1).sum())
    above_coa = int((b.max(axis = 1) > df["cost_of_attendance"]).sum())
    missing_premium = int(df["out_of_state_tuition_premium"].isna().sum())
    # Any issue at all: missing a bracket, any bracket decreasing as income
    # rises, a $0 bracket, a territory state, or a missing premium.
    any_issue = int(((known_count < 5) | (rel_drop > 0) | (b == 0).any(axis = 1)
                     | ~df["state"].isin(US_STATE_CODES) | df["out_of_state_tuition_premium"].isna()).sum())

    issues = [
        ("Missing at least one income bracket", missing_any,
         "Kept if >= 2 brackets; engine interpolates between the reported brackets (np.interp)."),
        ("Missing the 110k+ bracket", flat_top,
         "np.interp holds the 75-110k value flat for all higher incomes (likely understates cost)."),
        ("Missing the 0-30k bracket", flat_bottom,
         "np.interp holds the lowest reported bracket flat for lower incomes."),
        ("Net price falls as income rises (any drop)", nonmono_any,
         "Not handled; interpolated as-is."),
        ("Net price falls >10% as income rises", nonmono_10,
         "Not handled; interpolated as-is."),
        ("A bracket reported as exactly $0", zero_bracket,
         "Kept; negative raw values were clipped to 0 at build time."),
        ("A bracket above cost of attendance", above_coa,
         "Engine caps the point estimate at cost of attendance."),
        ("School in a territory (PR, GU, VI)", territories,
         "No student can match its state (StudentProfile rejects territories), so the out-of-state premium is always added; it is $0 for all but public schools."),
        ("Missing out-of-state tuition premium", missing_premium,
         "Treated as no premium."),
    ]
    return {
        "schools": n,
        "bracket_count_distribution": {int(k): int(v) for k, v in known_count.value_counts().sort_index().items()},
        "schools_with_any_issue": any_issue,
        "schools_with_any_issue_pct": _pct(any_issue, n),
        "missing_by_column": {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().any()},
        "issues": [{"issue": name, "count": count, "pct": _pct(count, n), "handling": handling} for name, count, handling in issues],
        "requires_css_profile_true": int(df["requires_css_profile"].sum()),
    }


def ownership_mix(records: list[dict]) -> dict:
    """Ownership of the schools that survive ingestion; for-profits are labeled
    CSS Profile only if the label is 'is private'."""
    labels = {1: "public", 2: "private nonprofit", 3: "private for-profit"}
    counts = Counter(labels[r["school.ownership"]] for r in records if record_to_row(r) is not None)
    return dict(counts)


def run() -> dict:
    payload = fetch_raw()
    records = payload["records"]
    df = colleges_frame(load_current_colleges())
    return {
        "raw_fetched_on": payload["fetched_on"],
        "ingestion": raw_exclusions(records),
        "kept_dataset": kept_quality(df),
        "ownership_of_kept_schools": ownership_mix(records),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent = 2))
