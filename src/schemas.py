#pydantic - industry standard for Data Validation
from pydantic import BaseModel, Field
from typing import Optional

#blueprint for what the student is
class StudentProfile(BaseModel):
    #The data a user enters once.
    #... means a value must be provided, which is greater than 0
    household_income: float
    assets: Optional[float] = 0
    size: Optional[int] = 4
    state: Optional[str] = "AK"

class CollegeData(BaseModel):
    name: str
    tuition: float
