"""
Performance of the Monte Carlo engine at 1,000 trials: one school, and every
school in the dataset, compared against a pure-Python scalar loop (no NumPy)
and a batched NumPy version that simulates all schools as one matrix.

Timings call _run_simulation directly, bypassing run_simulation's lru_cache,
which would otherwise time a cache lookup. Each figure is the median of
several repeats on one process (NumPy elementwise ops are single-threaded).
"""
import os
import platform
import random
import time

import numpy as np

from eval.batched import draw, point_estimates, simulate_batched, simulate_scalar
from eval.common import SEED, TRIALS, load_current_colleges, school_seed
from src.engine import MonteCarloEngine
from src.models import SimulationResult
from src.schemas import StudentProfile

STUDENT = StudentProfile(household_income = 85000, liquid_assets = 40000, family_size = 4, state_of_residence = "NY")
FIELDS = ["probability_of_shortfall", "average_total_cost", "max_debt", "percentile_05", "percentile_95",
          "average_net_price", "net_price_percentile_05", "net_price_percentile_95"]


def timed(fn, repeats: int) -> dict:
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    times = np.array(times)
    return {"median_s": float(np.median(times)), "min_s": float(times.min()), "repeats": repeats}


def check_batched_matches_engine(engine, colleges) -> dict:
    """Feeds the batched version the exact random draws the engine makes for
    each school (same seed, same draw order) and compares every output."""
    centers, scales = point_estimates(colleges, STUDENT)
    lr, inf, z = [], [], []
    expected = {f: [] for f in FIELDS}
    for i, college in enumerate(colleges):
        seed = school_seed(4, i)
        np.random.seed(seed)
        result = engine._run_simulation(college, STUDENT)
        for f in FIELDS:
            expected[f].append(getattr(result, f))
        np.random.seed(seed)
        a, b, c = draw(1, engine.trials)
        lr.append(a[0]); inf.append(b[0]); z.append(c[0])
    got = simulate_batched(centers, scales, STUDENT.liquid_assets, np.stack(lr), np.stack(inf), np.stack(z))
    max_rel = 0.0
    for f in FIELDS:
        e = np.array(expected[f])
        rel = np.abs(got[f] - e) / np.maximum(np.abs(e), 1.0)
        max_rel = max(max_rel, float(rel.max()))
    return {"schools_compared": len(colleges), "max_relative_difference": max_rel, "matches": max_rel < 1e-9}


def run() -> dict:
    colleges = load_current_colleges()
    engine = MonteCarloEngine(trials = TRIALS)
    one = next(c for c in colleges if c.net_price_110k_plus is not None)
    n = len(colleges)

    equivalence = check_batched_matches_engine(engine, colleges)

    np.random.seed(SEED)
    engine_one = timed(lambda: engine._run_simulation(one, STUDENT), 300)
    engine_all = timed(lambda: [engine._run_simulation(c, STUDENT) for c in colleges], 5)

    # Share of a single engine call spent building the pydantic result
    # (percentiles + model construction) rather than simulating.
    sample = engine._run_simulation(one, STUDENT)
    payload = sample.model_dump()
    result_build = timed(lambda: SimulationResult(**payload), 300)

    centers, scales = point_estimates(colleges, STUDENT)
    rng = random.Random(SEED)
    scalar_one = timed(lambda: simulate_scalar(centers[0], scales[0], STUDENT.liquid_assets, TRIALS, rng), 30)
    scalar_all = timed(lambda: [simulate_scalar(c, s, STUDENT.liquid_assets, TRIALS, rng) for c, s in zip(centers, scales)], 2)

    def batched_all():
        c, s = point_estimates(colleges, STUDENT)
        return simulate_batched(c, s, STUDENT.liquid_assets, *draw(n, TRIALS))
    batched_one = timed(lambda: simulate_batched(centers[:1], scales[:1], STUDENT.liquid_assets, *draw(1, TRIALS)), 300)
    batched_all_t = timed(batched_all, 5)

    def per_school_ms(t, schools): return round(1000 * t["median_s"] / schools, 4)

    return {
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "trials_per_school": TRIALS,
        "schools": n,
        "student": "income $85,000, liquid assets $40,000, NY resident",
        "batched_equivalence_check": equivalence,
        "one_school": {
            "engine_ms": round(1000 * engine_one["median_s"], 3),
            "engine_best_ms": round(1000 * engine_one["min_s"], 3),
            "engine_result_construction_ms": round(1000 * result_build["median_s"], 3),
            "pure_python_ms": round(1000 * scalar_one["median_s"], 3),
            "batched_numpy_ms": round(1000 * batched_one["median_s"], 3),
            "batched_numpy_best_ms": round(1000 * batched_one["min_s"], 3),
            "speedup_engine_vs_pure_python": round(scalar_one["median_s"] / engine_one["median_s"], 1),
        },
        "all_schools": {
            "engine_loop_s": round(engine_all["median_s"], 3),
            "engine_loop_best_s": round(engine_all["min_s"], 3),
            "pure_python_s": round(scalar_all["median_s"], 3),
            "batched_numpy_s": round(batched_all_t["median_s"], 3),
            "batched_numpy_best_s": round(batched_all_t["min_s"], 3),
            "engine_loop_per_school_ms": per_school_ms(engine_all, n),
            "batched_per_school_ms": per_school_ms(batched_all_t, n),
            "speedup_engine_vs_pure_python": round(scalar_all["median_s"] / engine_all["median_s"], 1),
            "speedup_batched_vs_engine_loop": round(engine_all["median_s"] / batched_all_t["median_s"], 1),
            "speedup_batched_vs_pure_python": round(scalar_all["median_s"] / batched_all_t["median_s"], 1),
            "scenarios_per_second_engine_loop": round(n * TRIALS / engine_all["median_s"]),
            "scenarios_per_second_batched": round(n * TRIALS / batched_all_t["median_s"]),
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent = 2))
