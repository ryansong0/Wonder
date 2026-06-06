import pytest
from src.ingestor import DataIngestor

def test_ingestor_filter():
    ingestor = DataIngestor()

    raw_data = [
        {
            "college_name": "Good School", 
        "endowment_size": 10000, 
        "cost_of_attendance": 20000, 
        "average_aid_percentage": 0.5,
        "tuition_free_threshold": 0
        },
        {
            "college_name": "Bad School", 
            "endowment_size": 100000, 
            "cost_of_attendance": 20000, 
            "average_aid_percentage": 0.5,
            "tuition_free_threshold": 0
            }
    ]

    ingestor.ingest_data(raw_data)

    results = ingestor.get_data()

    if len(results) != 2:
        raise ValueError(f"Expected 2 result, but got {len(results)}")


