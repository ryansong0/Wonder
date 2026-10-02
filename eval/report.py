"""
Renders eval/RESULTS.md from eval/results/baseline.json and, if present,
eval/results/after_fixes.json. Every number in RESULTS.md comes from those
files; nothing is typed in by hand.

    python -m eval.report
"""
import json

from eval.common import EVAL_DIR, RESULTS_DIR

RUNS = [("baseline", "Baseline"), ("after_fixes", "After fixes")]


def load_runs() -> list[tuple[str, dict]]:
    runs = []
    for label, title in RUNS:
        path = RESULTS_DIR / f"{label}.json"
        if path.exists():
            runs.append((title, json.loads(path.read_text())))
    return runs


def usd(v) -> str:
    return f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}"


def pct(v) -> str:
    return f"{v:.1f}%"


def table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def get(d: dict, path: str):
    for key in path.split("."):
        d = d[key]
    return d


def headline(runs) -> str:
    metrics = [
        ("Leave-one-bracket-out coverage, p10-p90 band (target 80%)", "validation.leave_one_bracket_out.annual_band.coverage_p10_p90_pct", pct),
        ("Leave-one-bracket-out MAE vs simulated median", "validation.leave_one_bracket_out.annual_band.mae_vs_median_usd", usd),
        ("Leave-one-bracket-out weighted abs. % error", "validation.leave_one_bracket_out.annual_band.wape_pct", pct),
        ("1-year time holdout coverage, p10-p90 (2023 -> 2024)", "validation.time_holdout.2023.forecast_band.coverage_p10_p90_pct", pct),
        ("1-year time holdout MAE vs simulated median", "validation.time_holdout.2023.forecast_band.mae_vs_median_usd", usd),
        ("Sanity check only (circular): coverage, p10-p90", "validation.sanity_check_circular.annual_band.coverage_p10_p90_pct", pct),
        ("Raw Scorecard records excluded at ingestion", "data_quality.ingestion.excluded_pct", pct),
        ("Kept schools with a missing or inconsistent field", "data_quality.kept_dataset.schools_with_any_issue_pct", pct),
        ("1,000 scenarios, one school (engine)", "performance.one_school.engine_ms", lambda v: f"{v:.2f} ms"),
        ("1,000 scenarios x all schools (engine loop)", "performance.all_schools.engine_loop_s", lambda v: f"{v:.2f} s"),
        ("1,000 scenarios x all schools (batched NumPy)", "performance.all_schools.batched_numpy_s", lambda v: f"{v:.2f} s"),
        ("Speedup: engine vs pure Python", "performance.all_schools.speedup_engine_vs_pure_python", lambda v: f"{v:.1f}x"),
        ("Speedup: batched NumPy vs engine loop", "performance.all_schools.speedup_batched_vs_engine_loop", lambda v: f"{v:.1f}x"),
    ]
    return table(["Metric"] + [title for title, _ in runs],
                 [[name] + [fmt(get(r, path)) for _, r in runs] for name, path, fmt in metrics])


def coverage_rows(label: str, s: dict) -> list:
    return [label, s["n"], pct(s["coverage_p10_p90_pct"]), pct(s["coverage_p05_p95_pct"]),
            pct(s["below_p10_pct"]), pct(s["above_p90_pct"]), usd(s["mae_vs_median_usd"]),
            usd(s["median_abs_error_usd"]), usd(s["bias_median_minus_published_usd"]), pct(s["wape_pct"])]


COVERAGE_HEADER = ["Slice", "n", "In p10-p90", "In p05-p95", "Below p10", "Above p90",
                   "MAE vs median", "Median abs. error", "Bias (median - published)", "WAPE"]

BRACKET_NAMES = {
    "net_price_0_30k": "$0-30k", "net_price_30k_48k": "$30-48k", "net_price_48k_75k": "$48-75k",
    "net_price_75k_110k": "$75-110k", "net_price_110k_plus": "$110k+",
}


def validation_section(title: str, r: dict) -> str:
    v = r["validation"]
    lobo = v["leave_one_bracket_out"]
    rows = [coverage_rows("All held-out brackets", lobo["annual_band"])]
    rows += [coverage_rows(f"Position: {k}", s) for k, s in lobo["annual_band_by_position"].items()]
    rows += [coverage_rows(f"Methodology: {k}", s) for k, s in lobo["annual_band_by_methodology"].items()]
    rows += [coverage_rows(f"Bracket: {BRACKET_NAMES[k]}", lobo["annual_band_by_bracket"][k]) for k in BRACKET_NAMES]
    rows.append(coverage_rows("4-year total / 4 (includes inflation)", lobo["four_year_total_div_4"]))

    th_rows = []
    for year, t in v["time_holdout"].items():
        f, p = t["forecast_band"], t["persistence_baseline"]
        th_rows.append([f"{t['base_year']} -> {t['target_year']} ({t['horizon_years']} yr)", f["n"],
                        pct(f["coverage_p10_p90_pct"]), pct(f["coverage_p05_p95_pct"]),
                        usd(f["mae_vs_median_usd"]), usd(p["mae_usd"]),
                        usd(f["bias_median_minus_published_usd"]), usd(p["bias_usd"])])
        for k, s in t["forecast_band_by_methodology"].items():
            th_rows.append([f"&nbsp;&nbsp;{k}", s["n"], pct(s["coverage_p10_p90_pct"]), pct(s["coverage_p05_p95_pct"]),
                            usd(s["mae_vs_median_usd"]), "", usd(s["bias_median_minus_published_usd"]), ""])

    circ = v["sanity_check_circular"]
    return "\n\n".join([
        f"### {title}",
        f"**Leave-one-bracket-out (main metric).** {lobo['schools']:,} schools with at least 3 reported brackets; "
        "each reported bracket is hidden in turn and predicted from the rest. Annual aid band unless noted.",
        table(COVERAGE_HEADER, rows),
        "**Time holdout.** Simulated from an older Scorecard release, scored against the 2024 release. "
        "\"Persistence\" is the naive forecast that last published value doesn't change.",
        table(["Base -> target", "n", "In p10-p90", "In p05-p95", "Model MAE", "Persistence MAE",
               "Model bias", "Persistence bias"], th_rows),
        "**Sanity check only (circular).** The published value is the simulation's own center input, so "
        "near-100% coverage is guaranteed by construction and is not evidence of accuracy.",
        table(COVERAGE_HEADER, [coverage_rows("Annual band", circ["annual_band"]),
                                coverage_rows("4-year total / 4", circ["four_year_total_div_4"])]),
    ])


def data_quality_section(runs) -> str:
    r = runs[-1][1]["data_quality"]
    ing, kept = r["ingestion"], r["kept_dataset"]
    ing_rows = [["Raw records returned by the API", ing["raw_records"], ""],
                ["Kept in colleges.csv", ing["kept"], pct(100 * ing["kept"] / ing["raw_records"])]]
    ing_rows += [[f"Excluded: {k}", v["count"], pct(v["pct_of_raw"])] for k, v in ing["exclusion_reasons"].items()]
    ing_rows += [["Kept schools with a negative net price clipped to $0", ing["kept_with_negative_net_price_clipped_to_0"], ""],
                 ["Negative net price values clipped", ing["negative_net_price_values_clipped"], ""]]
    issue_rows = [[i["issue"], i["count"], pct(i["pct"]), i["handling"]] for i in kept["issues"]]
    issue_rows.append(["**Any of the above**", kept["schools_with_any_issue"], pct(kept["schools_with_any_issue_pct"]), ""])
    own = r["ownership_of_kept_schools"]

    css_rows = [[title, run["data_quality"]["kept_dataset"]["requires_css_profile_true"]] for title, run in runs]
    return "\n\n".join([
        f"Raw pull fetched {r['raw_fetched_on']}. Ingestion (`src/build_college_dataset.py`):",
        table(["", "Count", "% of raw"], ing_rows),
        f"Within the {kept['schools']:,} kept schools:",
        table(["Issue", "Schools", "% of kept", "How the code handles it"], issue_rows),
        f"Reported brackets per kept school: " + ", ".join(f"{k} brackets: {v:,}" for k, v in kept["bracket_count_distribution"].items()) + ".",
        f"Ownership of kept schools: {own.get('public', 0):,} public, {own.get('private nonprofit', 0):,} private nonprofit, "
        f"{own.get('private for-profit', 0):,} private for-profit. Schools labeled CSS Profile:",
        table(["Run", "Labeled CSS Profile"], css_rows),
    ])


def performance_section(runs) -> str:
    rows = []
    for title, r in runs:
        p = r["performance"]
        one, every = p["one_school"], p["all_schools"]
        rows += [
            [title, "One school", f"{one['engine_ms']:.2f} ms (best {one['engine_best_ms']:.2f})",
             f"{one['pure_python_ms']:.2f} ms", f"{one['batched_numpy_ms']:.2f} ms", f"{one['speedup_engine_vs_pure_python']:.1f}x", "-"],
            [title, f"All {p['schools']:,} schools", f"{every['engine_loop_s']:.2f} s (best {every['engine_loop_best_s']:.2f})",
             f"{every['pure_python_s']:.2f} s", f"{every['batched_numpy_s']:.2f} s (best {every['batched_numpy_best_s']:.2f})",
             f"{every['speedup_engine_vs_pure_python']:.1f}x", f"{every['speedup_batched_vs_engine_loop']:.1f}x"],
        ]
    p = runs[-1][1]["performance"]
    m, eq = p["machine"], p["batched_equivalence_check"]
    return "\n\n".join([
        f"1,000 scenarios per school, student: {p['student']}. Median of repeated runs.",
        table(["Run", "Workload", "Engine (as shipped)", "Pure Python loop", "Batched NumPy", "Engine vs pure Python", "Batched vs engine"], rows),
        f"The batched version was checked against the engine draw-for-draw on all {eq['schools_compared']:,} schools: "
        f"max relative difference {eq['max_relative_difference']:.1e}.",
        f"Machine: {m['processor']}, {m['logical_cpus']} logical CPUs, {m['platform']}, Python {m['python']}, NumPy {m['numpy']}. "
        "Single process; timings on a laptop vary run to run, so best-of-N is shown next to the median.",
    ])


def render() -> str:
    runs = load_runs()
    meta = table(["Run", "Commit", "Date", "Seed"], [[t, f"`{r['git_commit']}`", r["run_on"], r["seed"]] for t, r in runs])
    return "\n\n".join([
        "# Evaluation results",
        "Generated by `python -m eval.report` from `eval/results/*.json`. Reproduce with "
        "`python -m eval.run_all --label <name>` (needs `COLLEGE_SCORECARD_API_KEY` for the first raw pull, then uses the cache).",
        meta,
        "## Headline",
        headline(runs),
        "## 1. Validation",
        "Published net price by income is the simulation's own input, so the fair tests hide the value being predicted: "
        "leave-one-bracket-out (main metric) and a time holdout. Every simulation uses an in-state household with $0 liquid "
        "assets at the bracket's income midpoint, which isolates the aid model. The annual band is the per-trial aid samples "
        "before inflation; a well-calibrated p10-p90 band should contain the published value about 80% of the time.",
        *[validation_section(title, r) for title, r in runs],
        "## 2. Data quality",
        data_quality_section(runs),
        "## 3. Performance",
        performance_section(runs),
    ]) + "\n"


if __name__ == "__main__":
    out = EVAL_DIR / "RESULTS.md"
    out.write_text(render(), encoding = "utf-8")
    print(f"wrote {out}")
