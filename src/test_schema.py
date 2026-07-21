import pytest
from pydantic import ValidationError

from src.schemas import StudentProfile


def test_state_code_is_accepted_as_is():
    student = StudentProfile(household_income = 75000, total_assets = 20000, family_size = 4, state_of_residence = "nc")
    assert student.state_of_residence == "NC"


def test_full_state_name_is_normalized_to_its_code():
    student = StudentProfile(household_income = 75000, total_assets = 20000, family_size = 4, state_of_residence = "New York")
    assert student.state_of_residence == "NY"


def test_unrecognized_state_is_rejected():
    with pytest.raises(ValidationError):
        StudentProfile(household_income = 75000, total_assets = 20000, family_size = 4, state_of_residence = "Atlantis")
