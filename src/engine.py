import numpy as np
import functools
from src.config import NUM_TRIALS, YEARS_OF_COLLEGE, MARKET_RETURN_MIN, MARKET_RETURN_MAX, INFLATION_MIN, INFLATION_MAX, EFC_SIGMA_CSS_PROFILE, EFC_SIGMA_FEDERAL_ONLY
# rules for input data format
from src.schemas import CollegeData, StudentProfile
# rules for final output
from src.models import SimulationResult

# Midpoints of the College Scorecard's published income brackets, used to
# interpolate a school's real net price at a household's exact income. The
# top bracket ("110001-plus") is open-ended, so 130000 is an approximation,
# not a midpoint.
INCOME_BRACKET_MIDPOINTS = [
    (15000, "net_price_0_30k"),
    (39000, "net_price_30k_48k"),
    (61500, "net_price_48k_75k"),
    (92500, "net_price_75k_110k"),
    (130000, "net_price_110k_plus"),
]

class MonteCarloEngine:
    def __init__(self, trials: int = NUM_TRIALS):
        self.trials = trials
        self.run_simulation = functools.lru_cache(maxsize = 128)(self._run_simulation)

    def _run_simulation(self, college: CollegeData, student: StudentProfile) -> SimulationResult:
        mu, sigma = 0.07, 0.15
        log_returns = np.random.normal(mu, sigma, (self.trials, YEARS_OF_COLLEGE))
        market_returns = np.exp(log_returns) - 1

        inflation_rates = np.random.uniform(INFLATION_MIN, INFLATION_MAX, (self.trials, YEARS_OF_COLLEGE))

        assets = np.full(self.trials, student.total_assets, dtype = float)

        # net tuition after aid
        net_tuition_annual = self.calculate_net_price(student, college)

        # tracking total debt accumulated per trial
        total_debt = np.zeros(self.trials)


        for year in range(YEARS_OF_COLLEGE):
                # assets grow for all trials
                assets *= (1 + market_returns[:, year])

                # add cumulative inflation to base tuition
                inflation_multiplier = np.prod(1 + inflation_rates[:, :year + 1], axis = 1)

                # inflate tuition for this year
                current_tuition = net_tuition_annual * inflation_multiplier

                # calculate shortfall for all trials simultaneously
                shortfall = np.maximum(0, current_tuition - assets)
                total_debt += shortfall

                # deduct from assets (note: not below zero)
                assets = np.maximum(0, assets - current_tuition)

        # organize the random results into this format
        return SimulationResult(
            college_name = college.college_name,
            # probability the student runs out of funds
            probability_of_shortfall = np.mean(total_debt > 0),
            average_total_cost = np.mean(total_debt),
            max_debt = np.max(total_debt), # worst case scenario
            percentile_05 = np.percentile(total_debt, 5),
            percentile_95 = np.percentile(total_debt, 95),
            simulation_trials = self.trials, # number of trials ran
            all_trial_results = total_debt,
            calibrated_with_real_data = self.real_net_price_estimate(college, student.household_income) is not None,
        )

    def real_net_price_estimate(self, college: CollegeData, household_income: float) -> float | None:
        """Interpolates a school's own published net price (College Scorecard) at
        the household's exact income. Returns None if the school hasn't been
        calibrated with real data yet, so callers can fall back to the formula."""
        known_brackets = [
            (income, getattr(college, field))
            for income, field in INCOME_BRACKET_MIDPOINTS
            if getattr(college, field) is not None
        ]
        if len(known_brackets) < 2:
            return None
        xs, ys = zip(*known_brackets)
        return float(np.interp(household_income, xs, ys))

    def calculate_net_price(self, student: StudentProfile, college: CollegeData) -> np.ndarray:
        """Returns a per-trial array of expected net cost, sampling around a point
        estimate instead of returning one fixed number. This is what lets the
        simulation reflect the real-world fact that the same income/assets produce a
        different aid offer at every college, not just a different sticker price.
        The point estimate is always the school's own reported net price
        (calibrated from College Scorecard) - every school in the dataset is
        required to have it (see build_college_dataset.py's bracket-count filter)."""
        real_estimate = self.real_net_price_estimate(college, student.household_income)
        if real_estimate is None:
            raise ValueError(
                f"'{college.college_name}' has fewer than two net-price-by-income brackets; "
                "cannot simulate without real published net-price data."
            )
        point_estimate = real_estimate

        # The net-price data above is blended across in-state and out-of-state
        # students, which understates cost for anyone paying out-of-state
        # tuition (often a large, largely need-aid-independent premium at
        # public schools). Add the school's own reported dollar gap on top
        # when the student's residency doesn't match the school's state.
        # Naturally a no-op for private schools, which charge everyone the same.
        if college.state and college.out_of_state_tuition_premium and student.state_of_residence.upper() != college.state.upper():
            point_estimate += college.out_of_state_tuition_premium

        # CSS Profile / institutional-methodology schools weigh dozens of discretionary,
        # non-public factors, so the same income/assets can yield a materially different
        # aid offer than a federal-methodology-only school, whose formula is public and
        # mechanical. That gap in predictability is what the uncertainty band represents,
        # regardless of whether the center point came from real data or our formula.
        sigma_fraction = EFC_SIGMA_CSS_PROFILE if college.requires_css_profile else EFC_SIGMA_FEDERAL_ONLY
        samples = np.random.normal(point_estimate, point_estimate * sigma_fraction, self.trials)
        return np.maximum(0, samples)
