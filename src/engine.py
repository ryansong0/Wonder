import random
import numpy as np  
from src.config import NUM_TRIALS, YEARS_OF_COLLEGE, MARKET_RETURN_MIN, MARKET_RETURN_MAX, INFLATION_MIN, INFLATION_MAX, INCOME_WEIGHT, ASSET_WEIGHT
# rules for input data format
from src.schemas import CollegeData, StudentProfile
# rules for final output
from src.models import SimulationResult

class MonteCarloEngine:
    def __init__(self, trials: int = NUM_TRIALS):
        self.trials = trials

    def run_simulation(self, college: CollegeData, student: StudentProfile) -> SimulationResult:
        # creating random values for every trial
        market_returns = np.random.uniform(MARKET_RETURN_MIN, MARKET_RETURN_MAX, (self.trials, YEARS_OF_COLLEGE))
        inflation_rates = np.random.uniform(INFLATION_MIN, INFLATION_MAX, (self.trials, YEARS_OF_COLLEGE))

        # pre-calculate cumulative inflation multipliers for all years
        inflation_multipliers = np.cumprod(1 + inflation_rates, axis = 1)

        assets = np.full(self.trials, student.total_assets, dtype = float)

        # net tuition after aid
        net_tuition_annual = college.cost_of_attendance * (1 - (college.average_aid_percentage or 0))
        
        # tracking total debt accumulated per trial
        total_debt = np.zeros(self.trials)

        
        for year in range(YEARS_OF_COLLEGE):
                # assets grow for all trials
                assets *= (1 + market_returns[:, year])

                # inflate tuition for this year
                current_tuition = net_tuition_annual * np.prod(1 + inflation_rates[:, :year + 1], axis = 1)

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
            simulation_trials = self.trials # number of trials ran
        )
    
    def calculate_net_price(student: StudentProfile, college: CollegeData) -> float:
        """Calculates the expected cost after applying the college's specific financial aid policy."""
        # Tuition-Free Policy
        # in this model, if a student is below the threshold, the student pays $0 tuition
        if student.household_income <= college.tuition_free_threshold:
              # assuming that there are still basic fees (about 5% of Cost of Attendance)
              return college.cost_of_attendance * 0.05
        # Need-Based Aid
        else:
            # Federal Methodology approximation for Family Contribution
             efc = (student.household_income * 0.15) (student.total_assets * 0.05)
             need = max(0, college.cost_of_attendance - efc)

             # applying a college's specific aid generosity factor
             aid = need * (college.average_aid_percentage or 0.0)
             return max(0, college.cost_of_attendance - aid)
          