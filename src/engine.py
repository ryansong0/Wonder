import random
from src.config import NUM_TRIALS, MARKET_RETURN_MIN, MARKET_RETURN_MAX, INFLATION_MIN, INFLATION_MAX
# rules for input data format
from src.schemas import CollegeData, StudentProfile
# rules for final output
from src.models import SimulationResult

class MonteCarloEngine:
    def __init__(self, trials: int = NUM_TRIALS):
        self.trials = trials

    def run_simulation(self, college: CollegeData, student: StudentProfile) -> SimulationResult:
        # store the cost of every trial ran
        results = []
        shortfall_trials = 0

        for _ in range(self.trials):
            # student initial assets
            current_assets = student.total_assets
            annual_tuition = college.cost_of_attendance
            trial_debt = 0
        
            for year in range(4):
                # assets grow (about 6% every year)
                current_assets *= (1 + random.uniform(MARKET_RETURN_MIN, MARKET_RETURN_MAX))

                # apply inflation to tuition
                inflation_rate = random.uniform(INFLATION_MIN, INFLATION_MAX)
                annual_tuition *= (1 + inflation_rate)

                # pay tuition from the assets
                if current_assets >= annual_tuition:
                    current_assets -= annual_tuition
                else:
                    # calculate debt shortfall if not enough assets for tuition
                    shortfall = annual_tuition - current_assets
                    trial_debt += shortfall
                    current_assets = 0
            # count the trial as a shortfall if any debt accumulated
            if trial_debt > 0:
                shortfall_trials += 1
            
            results.append(trial_debt)
            
        # organize the random results into this format
        return SimulationResult(
            college_name = college.college_name,
            # probability the student runs out of funds
            probability_of_shortfall = shortfall_trials / self.trials,
            average_total_cost = sum(results) / len(results),
            max_debt = max(results), # worst case scenario
            simulation_trials = self.trials # number of trials ran
        )