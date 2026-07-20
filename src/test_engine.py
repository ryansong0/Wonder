import numpy as np
from src.engine import MonteCarloEngine
from src.schemas import CollegeData, StudentProfile


def test_css_profile_schools_have_wider_aid_uncertainty_than_federal_only():
    engine = MonteCarloEngine(trials = 20000)
    student = StudentProfile(
        household_income = 150000,
        total_assets = 40000,
        family_size = 4,
        state_of_residence = "NC",
    )
    shared_kwargs = dict(
        tuition_free_threshold = 50000,
        cost_of_attendance = 80000,
        average_aid_percentage = 0.85,
    )
    css_profile_school = CollegeData(college_name = "CSS Profile U", requires_css_profile = True, **shared_kwargs)
    federal_only_school = CollegeData(college_name = "Federal Only U", requires_css_profile = False, **shared_kwargs)

    css_prices = engine.calculate_net_price(student, css_profile_school)
    federal_prices = engine.calculate_net_price(student, federal_only_school)

    assert css_prices.shape == (engine.trials,)
    assert np.all(css_prices >= 0)
    assert np.std(css_prices) > np.std(federal_prices)


def test_income_below_threshold_pays_flat_fee_with_no_variance():
    engine = MonteCarloEngine(trials = 500)
    student = StudentProfile(household_income = 40000, total_assets = 0, family_size = 4, state_of_residence = "NC")
    college = CollegeData(
        college_name = "Generous U",
        tuition_free_threshold = 100000,
        cost_of_attendance = 80000,
        average_aid_percentage = 0.9,
        requires_css_profile = True,
    )

    prices = engine.calculate_net_price(student, college)

    assert np.allclose(prices, college.cost_of_attendance * 0.05)
