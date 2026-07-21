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


def test_higher_assets_increase_the_estimated_net_price():
    engine = MonteCarloEngine(trials = 20000)
    college = CollegeData(
        college_name = "State U",
        cost_of_attendance = 90000,
        requires_css_profile = False,
        net_price_0_30k = 10000,
        net_price_30k_48k = 12000,
    )
    modest_assets = StudentProfile(household_income = 40000, total_assets = 20000, family_size = 4, state_of_residence = "NC")
    large_assets = StudentProfile(household_income = 40000, total_assets = 500000, family_size = 4, state_of_residence = "NC")

    modest_prices = engine.calculate_net_price(modest_assets, college)
    large_prices = engine.calculate_net_price(large_assets, college)

    assert np.mean(large_prices) > np.mean(modest_prices)


def test_very_large_assets_are_capped_at_the_schools_full_price():
    engine = MonteCarloEngine(trials = 20000)
    college = CollegeData(
        college_name = "State U",
        cost_of_attendance = 90000,
        requires_css_profile = False,
        state = "NC",
        out_of_state_tuition_premium = 15000,
        net_price_0_30k = 10000,
        net_price_30k_48k = 12000,
    )
    wealthy_out_of_state = StudentProfile(household_income = 40000, total_assets = 10000000, family_size = 4, state_of_residence = "CA")

    prices = engine.calculate_net_price(wealthy_out_of_state, college)

    # Full price for an out-of-state student is cost_of_attendance plus the
    # real tuition premium, not a number that grows without bound.
    assert np.max(prices) <= (college.cost_of_attendance + college.out_of_state_tuition_premium) * 1.5


def test_net_price_stays_visible_even_when_assets_prevent_any_shortfall():
    engine = MonteCarloEngine(trials = 20000)
    college = CollegeData(
        college_name = "Expensive Private U",
        cost_of_attendance = 90000,
        requires_css_profile = True,
        net_price_0_30k = 500,
        net_price_30k_48k = 1000,
    )
    wealthy_student = StudentProfile(household_income = 20000, total_assets = 2000000, family_size = 4, state_of_residence = "NC")

    result = engine.run_simulation(college, wealthy_student)

    # This family can cover any price from savings, so there's no shortfall...
    assert result.probability_of_shortfall == 0
    assert result.average_total_cost == 0
    # ...but the school is still genuinely expensive for them, and that has
    # to show up somewhere, or the UI would look like the school is free.
    assert result.average_net_price > 100000


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
