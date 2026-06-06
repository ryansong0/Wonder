import pytest
from src.engine import MonteCarloEngine
from src.schemas import CollegeData, StudentProfile

def test_simulation_bounds():
    engine = MonteCarloEngine(trials = 100)
    college = CollegeData(
        college_name = "Fake University", 
        cost_of_attendance = 50000,
        tuition_free_threshold = 0,
        average_aid_percentage = 0.1,
        endowment_size = 100000000
        )
    student = StudentProfile(
        household_income = 50000, 
        total_assets = 100000, 
        family_size = 4, 
        state_of_residence = "NC"
        )

    result = engine.run_simulation(college, student)

    assert 0 <= result.probability_of_shortfall <= 1.0
    assert result.average_total_cost > 0