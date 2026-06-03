#pydantic - industry standard for Data Validation
from pydantic import BaseModel, Field
from typing import Optional

#blueprint for what the student is
class StudentProfile(BaseModel):
    #The data a user enters once.
    #... means a value must be provided, which is greater than 0
    household_income: float = Field(..., gt = 0)
    total_assets: float = Field(..., ge = 0) #ge=0 (greater than or equal to 0)
    family_size: int = Field(..., gt = 0)
    #gt=0 (greater than 0) ensures the code rejects any nonsensical data (like a negative income)
    state_of_residence: str

class CollegeData(BaseModel):
    #The data for each institution
    college_name: str
    endowment_size: float = Field(gt = 0)
    cost_of_attendance: float = Field(gt = 0)
    average_aid_percentage: float = Field(..., ge = 0, le = 1)
