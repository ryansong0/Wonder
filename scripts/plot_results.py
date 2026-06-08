import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import numpy as np
from src.engine import MonteCarloEngine
from src.schemas import StudentProfile, CollegeData

def plot_visual(college: CollegeData, student: StudentProfile):
    engine = MonteCarloEngine()

    # returns a list of individual trial results (debt outcomes)
    result = engine.run_simulation(college, student)

    # visualization
    plt.figure(figsize = (10, 6))
    plt.hist(result.all_trial_results, bins = 50, color = 'skyblue', edgecolor = 'black', alpha = 0.7)

    # title
    plt.title(f"Projected Unmet Financial Need: {college.college_name}", fontsize = 14)
    plt.xlabel("Total Unmet Need at Graduation ($)", fontsize = 12)
    plt.ylabel("Frequency (Number of SImulations)", fontsize = 12)
    plt.grid(axis = 'y', linestyle = '--', alpha = 0.7)

    # mean line to represent the "Expected" financial gap
    mean_val = np.mean(result.all_trial_results)
    plt.axvline(mean_val, color = 'red', linestyle = 'dashed', linewidth = 2, label = f"Expected Unmet Need: ${mean_val:,.0f}")
    plt.legend()

    plt.show()

if __name__ == "__main__":
    my_college = CollegeData(
        college_name = "Duke University",
        cost_of_attendance = 90000,
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