import numpy as np
import functools
from src.config import NUM_TRIALS, YEARS_OF_COLLEGE, MARKET_RETURN_MIN, MARKET_RETURN_MAX, INFLATION_MIN, INFLATION_MAX, INCOME_WEIGHT, ASSET_WEIGHT, EFC_SIGMA_CSS_PROFILE, EFC_SIGMA_FEDERAL_ONLY
# rules for input data format
from src.schemas import CollegeData, StudentProfile
# rules for final output
from src.models import SimulationResult

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
            all_trial_results = total_debt
        )
    
    def calculate_net_price(self, student: StudentProfile, college: CollegeData) -> np.ndarray:
        """Returns a per-trial array of expected net cost, sampling the family's EFC
        from a distribution instead of a single point estimate. This is what lets the
        simulation reflect the real-world fact that the same income/assets produce a
        different aid offer at every college, not just a different sticker price."""
        # Tuition-Free Policy
        # in this model, if a student is below the threshold, the student pays $0 tuition
        if student.household_income <= college.tuition_free_threshold:
              # assuming that there are still basic fees (about 5% of Cost of Attendance)
              return np.full(self.trials, college.cost_of_attendance * 0.05)

        # Federal Methodology approximation for Family Contribution
        efc_point_estimate = (student.household_income * INCOME_WEIGHT) + (student.total_assets * ASSET_WEIGHT)

        sigma_fraction = EFC_SIGMA_CSS_PROFILE if college.requires_css_profile else EFC_SIGMA_FEDERAL_ONLY
        efc_samples = np.random.normal(efc_point_estimate, efc_point_estimate * sigma_fraction, self.trials)
        efc_samples = np.maximum(0, efc_samples)

        need = np.maximum(0, college.cost_of_attendance - efc_samples)

        # applying a college's specific aid generosity factor
        aid = need * (college.average_aid_percentage or 0.0)
        return np.maximum(0, college.cost_of_attendance - aid)
