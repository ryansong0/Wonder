import numpy as np
import pytest
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
        cost_of_attendance = 80000,
        net_price_75k_110k = 40000,
        net_price_110k_plus = 55000,
    )
    css_profile_school = CollegeData(college_name = "CSS Profile U", requires_css_profile = True, **shared_kwargs)
    federal_only_school = CollegeData(college_name = "Federal Only U", requires_css_profile = False, **shared_kwargs)

    css_prices = engine.calculate_net_price(student, css_profile_school)
    federal_prices = engine.calculate_net_price(student, federal_only_school)

    assert css_prices.shape == (engine.trials,)
    assert np.all(css_prices >= 0)
    assert np.std(css_prices) > np.std(federal_prices)


def test_out_of_state_student_pays_the_real_tuition_premium():
    engine = MonteCarloEngine(trials = 20000)
    college = CollegeData(
        college_name = "State U",
        cost_of_attendance = 30000,
        requires_css_profile = False,
        state = "NC",
        out_of_state_tuition_premium = 20000,
        net_price_0_30k = 10000,
        net_price_30k_48k = 12000,
    )
    in_state_student = StudentProfile(household_income = 40000, total_assets = 5000, family_size = 4, state_of_residence = "NC")
    out_of_state_student = StudentProfile(household_income = 40000, total_assets = 5000, family_size = 4, state_of_residence = "CA")

    in_state_prices = engine.calculate_net_price(in_state_student, college)
    out_of_state_prices = engine.calculate_net_price(out_of_state_student, college)

    assert np.mean(out_of_state_prices) - np.mean(in_state_prices) == pytest.approx(20000, rel = 0.05)


def test_private_school_premium_is_a_no_op_regardless_of_residency():
    engine = MonteCarloEngine(trials = 20000)
    college = CollegeData(
        college_name = "Private U",
        cost_of_attendance = 60000,
        requires_css_profile = True,
        state = "NC",
        out_of_state_tuition_premium = 0,
        net_price_0_30k = 15000,
        net_price_30k_48k = 18000,
    )
    in_state_student = StudentProfile(household_income = 40000, total_assets = 5000, family_size = 4, state_of_residence = "NC")
    out_of_state_student = StudentProfile(household_income = 40000, total_assets = 5000, family_size = 4, state_of_residence = "CA")

    in_state_prices = engine.calculate_net_price(in_state_student, college)
    out_of_state_prices = engine.calculate_net_price(out_of_state_student, college)

    assert np.mean(out_of_state_prices) == pytest.approx(np.mean(in_state_prices), rel = 0.05)


def test_school_without_enough_real_data_raises_instead_of_guessing():
    engine = MonteCarloEngine(trials = 500)
    student = StudentProfile(household_income = 40000, total_assets = 0, family_size = 4, state_of_residence = "NC")
    college = CollegeData(
        college_name = "Uncalibrated U",
        cost_of_attendance = 80000,
        requires_css_profile = True,
        net_price_0_30k = 5000,
    )

    with pytest.raises(ValueError):
        engine.calculate_net_price(student, college)
