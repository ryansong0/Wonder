import logging
from src.loader import load_college_data
from src.schemas import CollegeData
from src.engine import MonteCarloEngine

def main():
    # initialize logger
    logging.basicConfig(level = logging.INFO, filename = 'simulation.log', filemode = 'w',
                        format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.info("System initializing...")

    try:
        college_list = load_college_data('colleges.csv')
    except FileNotFoundError:
        print("Error: Could not find 'data/colleges.csv'. Please make sure that the file exists.")
        return
    except Exception as e:
        logging.critical(f"System failed to load data: {e}")
        print(f"An unexpected error occurred while loading data. Check 'simulation.log' for details.")
        return
    
    logging.info(f"Loaded {len(college_list)} colleges succesffully.")
    logging.info("Starting simulation...")

    engine = MonteCarloEngine(trials = 1000)

    print(f"{'College Name':<30} | {'Shortfall Prob':<15} | {'Avg Debt'}")
    print("-" * 60)

    for college in college_list:
        result = engine.run_simulation(college)
        print(f"{result.college_name:<30} | {result.probability_of_shortfall * 100:>13.1f}% | ${result.average_total_cost:>12,.2f}")

    logging.info("Simulation completed.")

if __name__ == "__main__":
    main()