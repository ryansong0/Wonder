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

    model_config = {"frozen": True}

class CollegeData(BaseModel):
    #The data for each institution
    college_name: str
    tuition_free_threshold: float = Field(ge = 0)
    endowment_size: Optional[float] = Field(default = None, gt = 0)
    cost_of_attendance: float = Field(gt = 0)
    average_aid_percentage: Optional[float] = Field(default = None, ge = 0, le = 1)
    requires_css_profile: bool = False

    # Real published net price by household income bracket, sourced from the
    # College Scorecard API (src/build_college_dataset.py). None when a school
    # hasn't been calibrated yet; the engine falls back to the formula estimate.
    net_price_0_30k: Optional[float] = Field(default = None, ge = 0)
    net_price_30k_48k: Optional[float] = Field(default = None, ge = 0)
    net_price_48k_75k: Optional[float] = Field(default = None, ge = 0)
    net_price_75k_110k: Optional[float] = Field(default = None, ge = 0)
    net_price_110k_plus: Optional[float] = Field(default = None, ge = 0)

    # Real state + the real dollar gap between out-of-state and in-state
    # sticker tuition, both from College Scorecard. Lets the engine add the
    # out-of-state premium for students who don't live in the school's state;
    # naturally 0 for private schools, which charge everyone the same.
    state: Optional[str] = None
    out_of_state_tuition_premium: Optional[float] = Field(default = None, ge = 0)

    model_config = {"frozen": True}
