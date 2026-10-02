"""
Runs the full evaluation and saves the raw numbers to eval/results/<label>.json.

    python -m eval.run_all --label baseline
    python -m eval.run_all --label after_fixes
    python -m eval.report            # regenerates eval/RESULTS.md

The first run fetches raw College Scorecard data (needs
COLLEGE_SCORECARD_API_KEY) and caches it in eval/cache/; later runs reuse it.
"""
import argparse
import json
import subprocess
from datetime import date

from eval import benchmark, data_quality, validate
from eval.common import RESULTS_DIR, SEED, fetch_raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required = True)
    parser.add_argument("--refresh", action = "store_true", help = "re-fetch raw Scorecard data instead of using the cache")
    args = parser.parse_args()

    fetch_raw(refresh = args.refresh)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output = True, text = True).stdout.strip()

    print("data quality...")
    quality = data_quality.run()
    print("validation...")
    validation, _ = validate.run()
    print("benchmark...")
    performance = benchmark.run()

    results = {
        "label": args.label,
        "run_on": date.today().isoformat(),
        "git_commit": commit,
        "seed": SEED,
        "data_quality": quality,
        "validation": validation,
        "performance": performance,
    }
    RESULTS_DIR.mkdir(parents = True, exist_ok = True)
    path = RESULTS_DIR / f"{args.label}.json"
    path.write_text(json.dumps(results, indent = 2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
