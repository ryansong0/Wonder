#pydantic - industry standard for Data Validation
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Full US state/territory name -> 2-letter code, so a student can type either
# "NY" or "New York" and have it resolve to the same value a college's own
# "state" field uses (College Scorecard reports state as a 2-letter code).
US_STATE_NAME_TO_CODE = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "district of columbia": "DC",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID", "illinois": "IL",
    "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA",
    "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
US_STATE_CODES = set(US_STATE_NAME_TO_CODE.values())

#blueprint for what the student is
class StudentProfile(BaseModel):
    #The data a user enters once.
    #... means a value must be provided, which is greater than 0
    household_income: float = Field(..., gt = 0)
    # Liquid, spendable assets only (savings, checking, taxable investment
    # accounts) - not home equity, retirement accounts, or personal property.
    # The federal aid formula excludes those too, and the simulation assumes
    # this figure can actually be spent paying tuition.
    liquid_assets: float = Field(..., ge = 0) #ge=0 (greater than or equal to 0)
    family_size: int = Field(..., gt = 0)
    #gt=0 (greater than 0) ensures the code rejects any nonsensical data (like a negative income)
    state_of_residence: str

    @field_validator("state_of_residence")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned.upper() in US_STATE_CODES:
            return cleaned.upper()
        code = US_STATE_NAME_TO_CODE.get(cleaned.lower())
        if code:
            return code
        raise ValueError(f"'{value}' is not a recognized US state or territory")

    model_config = {"frozen": True}

class CollegeData(BaseModel):
    #The data for each institution
    college_name: str
    cost_of_attendance: float = Field(gt = 0)
    requires_css_profile: bool = False

    # Real published net price by household income bracket, sourced from the
    # College Scorecard API (src/build_college_dataset.py). Every school in
    # the current dataset has at least 2 of these; calculate_net_price requires
    # it and errors otherwise rather than guessing.
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
