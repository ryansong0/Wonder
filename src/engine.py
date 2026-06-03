import random
# rules for input data format
from src.schemas import CollegeData
# rules for final output
from src.models import SimulationResult

class MonteCarloEngine:
    def __init__(self, trials: int = 1000):
        self.trials = trials

    def run_simulation(self, college: CollegeData) -> SimulationResult:
        # store the cost of every trial ran
        results = []

        for _ in range(self.trials):
            current_debt = 0
            annual_tuition = college.cost_of_attendance
        
            for year in range(4):
                inflation_rate = random.uniform(0.02, 0.05)
                annual_tuition *= (1 + inflation_rate)
                current_debt += annual_tuition
            
        results.append(current_debt)

        # organize the random results into this format
        return SimulationResult(
            college_name = college.college_name,
            # probability the student runs out of funds
            probability_of_shortfall = 0.15, #current placeholder
            average_total_cost = sum(results) / len(results),
            max_debt = max(results), # worst case scenario
            simulation_trials = self.trials # number of trials ran
        )