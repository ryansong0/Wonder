from src.loader import load_college_data
from src.schemas import CollegeData, StudentProfile
from src.engine import MonteCarloEngine

def get_user_input():
    print("--- Financial Aid Profile ---")
    while True:
        try:
            income= float(input("Enter your annual household income: "))
            assets = float(input("Enter total household assets: "))
            size = int(input("Enter number of people in family: "))
            state = input("Enter your state of residence (e.g., NC): ")
            return StudentProfile(household_income = income, total_assets = assets, family_size = size, state_of_residence = state)
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def get_cost_risk_balance(results):
    """
    Returns a college that is both cheaper and has a lower probability of shortfall than another college. It is considered 'dominated'.
    """
    balance = []
    for college in results:
        is_dominated = False
        for college_list in results:
            if (college_list.average_total_cost <= college.average_total_cost and college_list.probability_of_shortfall <= college.probability_of_shortfall and college != college_list):
                is_dominated = True
                break
        if not is_dominated:
            balance.append(college)
    return balance


def get_average_cost(result):
    return result.average_total_cost

def main():
    try:
        college_list = load_college_data('data/colleges.csv')
    except FileNotFoundError:
        print("Error: Could not find 'data/colleges.csv'. Please make sure that the file exists.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        return
    current_student = get_user_input()
    engine = MonteCarloEngine(trials = 1000)

    print(f"{'College Name':<30} | {'Shortfall Prob':<15} | {'Avg Debt'}")
    print("-" * 60)

    results_list = []
    for college in college_list:
        result = engine.run_simulation(college, current_student)
        results_list.append(result)
        print(f"{result.college_name:<30} | {result.probability_of_shortfall * 100:>13.1f}% | ${result.average_total_cost:>12,.2f}")

    print("\n--- Summary ---")
    if results_list:
        cheapest_college = min(results_list, key = get_average_cost)
        print(f"Based on your profile, {cheapest_college.college_name} is your most affordable option.")
        print(f"Expected average debt: ${cheapest_college.average_total_cost:,.2f}")

    print("\n--- Best Risk/Reward Options) ---")
    optimal_risk_reward = get_cost_risk_balance(results_list)
    for college in optimal_risk_reward:
        print(f"{college.college_name:<30} | Cost: ${college.average_total_cost:>12,.0f} | Risk: {college.probability_of_shortfall:>6.1%}")


if __name__ == "__main__":
    main()