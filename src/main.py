from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.engine import run_simulation
from src.schemas import CollegeData, StudentData

app = FastAPI(title = "Wonder")

# allows frontend to communicate with your backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.post("/api/simulate")
def execute_simulation(college: CollegeData, student: StudentData, runs: int = 5000):
    """
    Exposes the Monte Carlo vectorized engine over a REST API.
    Splits out the raw statistics for frontend chart rendering.
    """
    # trigger optimized NumPy simulation
    results = run_simulation(college, student, num_runs = runs)
    
    # return structured JSON for the frontend to consume
    return {
        "status": "success",
        "summary": {
            "mean_out_of_pocket": float(results.mean()),
            "median_out_of_pocket": float(results.median()),
            "risk_of_shortfall": float(results.shortfall_probability)
        },
        "distribution": results.raw_distribution.tolist() # convert NumPy array to standard JSON list
    }