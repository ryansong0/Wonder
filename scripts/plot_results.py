import matplotlib.pyplot as plt
import numpy as np
from src.engine import MonteCarloEngine
from src.schemas import StudentProfile, CollegeData

def plot_visual(college: CollegeData, student: StudentProfile):
    engine = MonteCarloEngine()

    # returns a list of individual trial results (debt outcomes)
    results = [engine.run_simulation(college, student).average_total_cost for _ in range(1000)]

    # visualization
    plt.figure(figsize = (10, 6))
    plt.hist(results, bins = 30, color = 'skyblue', edgecolor = 'black', alpha = 0.7)

    # title
    plt.title(f"Projected Unmet Financial Need: {college.college_name}", fontsize = 14)

if __name__ == "__main__":
    my_college = CollegeData(
        college_name = "Duke University".
        cost_of_attendance = 90000
        tuition_free_threshold = 85000,
        average_aid_percentage = 0.9,
        endowment_size = 10000000000
    )
    my_student = StudentProfile(
        household_income = 40000,
        total_assets = 0,
        family_size = 4,
        state_of_residence = "MA"
    )

    plot_visual(my_college, my_student)