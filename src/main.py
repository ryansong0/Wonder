from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import StudentProfile
from src.loader import load_college_data
from src.engine import MonteCarloEngine
from src.config import YEARS_OF_COLLEGE, NUM_TRIALS

app = FastAPI(title = "Wonder")

# allows frontend to communicate with your backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

_colleges_by_name = {c.college_name.lower(): c for c in load_college_data()}
_engine = MonteCarloEngine()


def build_explanation(college, student, result) -> str:
    """Generates the plain-language summary directly from the simulation output,
    instead of routing it through an LLM."""
    if college.requires_css_profile:
        methodology_note = "uses the CSS Profile, which weighs discretionary factors like home equity and non-custodial income beyond a fixed formula, so its aid offers are harder to predict"
    else:
        methodology_note = "relies on the federal methodology (FAFSA) only, which follows a fixed, public formula, so its aid offers are comparatively predictable"

    return (
        f"{college.college_name} {methodology_note}. Across {result.simulation_trials:,} simulated "
        f"scenarios for a household earning ${student.household_income:,.0f} over {YEARS_OF_COLLEGE} years, "
        f"there is a {result.probability_of_shortfall * 100:.0f}% chance of a funding shortfall, with a "
        f"typical shortfall between ${result.percentile_05:,.0f} and ${result.percentile_95:,.0f}."
    )


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
        },
        "explanation": build_explanation(college, student, result),
    }
