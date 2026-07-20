import os

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import StudentProfile
from src.loader import load_college_data
from src.engine import MonteCarloEngine
from src.config import YEARS_OF_COLLEGE, NUM_TRIALS

app = FastAPI(title = "Wonder")

# Comma-separated list of origins allowed to call this API, e.g.
# "https://wonder.example.com,https://staging.wonder.example.com". Defaults to
# the local Vite dev server only, so a deployment has to opt in explicitly
# rather than accepting requests from any origin.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

_colleges_by_name = {c.college_name.lower(): c for c in load_college_data()}
_engine = MonteCarloEngine()

MAX_COMPARISON_SIZE = 6


def build_explanation(college, student, result) -> str:
    """Generates the plain-language summary directly from the simulation output,
    instead of routing it through an LLM."""
    if college.requires_css_profile:
        methodology_note = "uses the CSS Profile, which weighs discretionary factors like home equity and non-custodial income beyond a fixed formula, so its aid offers are harder to predict"
    else:
        methodology_note = "relies on the federal methodology (FAFSA) only, which follows a fixed, public formula, so its aid offers are comparatively predictable"

    data_source_note = (
        "This is centered on the school's own reported net price for your income level, "
        "published to the federal College Scorecard."
        if result.calibrated_with_real_data else
        "This school hasn't reported detailed net price data yet, so it's estimated from a general aid formula."
    )

    return (
        f"{college.college_name} {methodology_note}. Across {result.simulation_trials:,} simulated "
        f"scenarios for a household earning ${student.household_income:,.0f} over {YEARS_OF_COLLEGE} years, "
        f"there is a {result.probability_of_shortfall * 100:.0f}% chance of a funding shortfall, with a "
        f"typical shortfall between ${result.percentile_05:,.0f} and ${result.percentile_95:,.0f}. {data_source_note}"
    )


def simulate_one(college, student: StudentProfile, runs: int) -> dict:
    simulation_engine = _engine if runs == _engine.trials else MonteCarloEngine(trials = runs)
    result = simulation_engine.run_simulation(college, student)

    return {
        "college_evaluated": result.college_name,
        "methodology": "CSS Profile / Institutional" if college.requires_css_profile else "Federal Methodology Only",
        "summary": {
            "probability_of_shortfall": result.probability_of_shortfall,
            "average_shortfall": result.average_total_cost,
            "shortfall_range_low": result.percentile_05,
            "shortfall_range_high": result.percentile_95,
            "worst_case_shortfall": result.max_debt,
            "calibrated_with_real_data": result.calibrated_with_real_data,
        },
        "explanation": build_explanation(college, student, result),
    }


@app.get("/api/colleges")
def list_colleges():
    return [
        {
            "college_name": college.college_name,
            "cost_of_attendance": college.cost_of_attendance,
            "requires_css_profile": college.requires_css_profile,
        }
        for college in _colleges_by_name.values()
    ]


@app.post("/api/simulate")
def execute_simulation(college_name: str = Body(...), student: StudentProfile = Body(...), runs: int = Body(NUM_TRIALS)):
    college = _colleges_by_name.get(college_name.lower().strip())
    if college is None:
        raise HTTPException(status_code = 404, detail = f"No aid data available for '{college_name}'.")

    return simulate_one(college, student, runs)


@app.post("/api/simulate/batch")
def execute_batch_simulation(college_names: list[str] = Body(...), student: StudentProfile = Body(...), runs: int = Body(NUM_TRIALS)):
    if len(college_names) > MAX_COMPARISON_SIZE:
        raise HTTPException(status_code = 400, detail = f"Compare at most {MAX_COMPARISON_SIZE} colleges at a time.")

    results = []
    not_found = []
    for name in college_names:
        college = _colleges_by_name.get(name.lower().strip())
        if college is None:
            not_found.append(name)
            continue
        results.append(simulate_one(college, student, runs))

    return {"results": results, "not_found": not_found}
