from src.engine import MonteCarloEngine
from src.schemas import StudentProfile, CollegeData

def compare_situations():
    engine = MonteCarloEngine()

    # define two types of institutions
    ivy_league = CollegeData(college_name = "Columbia University",
                             cost_of_attendance = 90000,
                            tuition_free_threshold = 90000,
                            average_aid_percentage = 0.9, 
                            endowment_size = 16000000000
                            )
    public_school = CollegeData(college_name = "University of Michigan",
                                cost_of_attendance = 30000,
                                tuition_free_threshold = 50000,
                                average_aid_percentage = 0.4,
                                endowment_size = 21000000000)
    student = StudentProfile(household_income = 50000,
                             total_assets = 20000,
                             family_size = 4,
                             state_of_residence = "CA"
                             )
    ivy_result = engine.run_simulation(ivy_league, student)
    public_result = engine.run_simulation(public_school, student)

    if __name__ == "__main__":
        compare_situations()