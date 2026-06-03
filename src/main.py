from src.schemas import CollegeData
from src.engine import MonteCarloEngine

def main():
    sample_college = CollegeData(
        college_name = "State University",
        cost_of_attendance = 50000.0,
    )
    engine = MonteCarloEngine(trials = 1000)

    result = engine.run_simulation(sample_college)

    print(f"--- Simulation Results for {result.college_name} ---")
    print(f"Average Cost: ${result.average_total_cost:,.2f}")
    print(f"Max Debt: ${result.max_debt:,.2f}")
    print(f"Probability of Shortfall: {result.probability_of_shortfall * 100}%")

if __name__ == "__main__":
    main()