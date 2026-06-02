from src.schemas import StudentProfile

user = StudentProfile(
    household_income = 75000, 
    total_assets = 20000, 
    family_size = 4, 
    state_of_residence = "NC"
)
print(f"Schema validated: {user.household_income}")