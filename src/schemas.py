from pydantic import BaseModel, Field
from typing import Optional

class StudentProfile(BaseModel):
    #The data a user enters once.
    household_income: float = Field(..., gt = 0)
    total_assets: float = Field(..., ge = 0)
    family_size: int = Field(..., gt = 0)
    state_of_residence: str

class CollegeData(BaseModel):
    #The data for each institution
    college_name: str
    endowment_size: float
    cost_of_attendance: float
    average_aid_percentage: float = Field(..., ge = 0, le = 1)
