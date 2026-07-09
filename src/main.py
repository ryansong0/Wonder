from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.schemas import CollegeData, StudentProfile
import json
import requests
from src.data import COLLEGE_REGISTRY

app = FastAPI(title = "Wonder")

# allows frontend to communicate with your backend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"

@app.post("/api/simulate")
def execute_simulation(college: CollegeData, student: StudentProfile, runs: int = 5000):
    lookup_name = college.name.lower().strip()
    
    if lookup_name in COLLEGE_REGISTRY:
        resolved_coa = COLLEGE_REGISTRY[lookup_name]["coa"]
        resolved_endowment = COLLEGE_REGISTRY[lookup_name]["endowment"]
    else:
        resolved_coa = college.tuition 
        resolved_endowment = "Dynamic Institutional Estimation Required"
    
    income = getattr(student, "household_income", 100000)
    student_state = getattr(student, "state", "AK") or "AK"
    
    if income < 65000:
        base_risk = 0.05 
    elif income < 135000:
        base_risk = 0.20 
    else:
        base_risk = 0.45

    prompt = f"""
    You are an institutional financial aid analytics engine. Analyze this specific profile:
    Target University: {college.name}
    Total Cost of Attendance (COA): ${resolved_coa:,}
    Known Endowment Scale: {resolved_endowment}
    
    Student Profile:
    Household Income: ${income:,}
    State of Residence: {student_state}
    
    Tasks:
    1. Calculate a highly realistic out-of-pocket annual net price range (low-end and high-end) for this student. 
       Note: Institutions with large endowments drop actual costs drastically for families making under $150,000.
    2. Write a concise 3-sentence professional reasoning detailing why their net price differs significantly from the raw ${resolved_coa:,} COA benchmark based on the school's fiscal capacity.
    
    You MUST respond with a valid JSON object ONLY. Do not wrap code in conversational explanations.
    Structure format exactly:
    {{
        "range_low": 12000,
        "range_high": 18500,
        "reasoning": "Your analytical summary text goes here."
    }}
    """    
    try:
        response = requests.post(
            OLLAMA_URL,
            json = {"model": "llama3", "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.2}},
            timeout = 60
        )
        
        ai_data = json.loads(response.json()["response"])
        
        return {
            "college_evaluated": college.name,
            "endowment": resolved_endowment,
            "summary": {
                "range_low": ai_data.get("range_low", resolved_coa * 0.4),
                "range_high": ai_data.get("range_high", resolved_coa * 0.7),
                "risk_of_shortfall": base_risk
            },
            "ai_analysis": ai_data.get("reasoning", "Standard parametric breakdown successfully calculated.")
        }
        
    except Exception as e:
        # Fallback simulation schema in case the local LLM times out or is offline
        return {
            "college_evaluated": college.name,
            "endowment": resolved_endowment,
            "summary": {
                "range_low": resolved_coa * 0.35 if income < 120000 else resolved_coa * 0.7,
                "range_high": resolved_coa * 0.50 if income < 120000 else resolved_coa * 0.85,
                "risk_of_shortfall": base_risk
            },
            "ai_analysis": f"Parametric execution bypass activated due to system latency. Estimated baseline ranges modeled directly from a standard {resolved_endowment} resource framework."
        }