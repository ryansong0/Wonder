import pandas as pd
from pathlib import Path
from src.schemas import CollegeData

def load_college_data(file_name: str = 'colleges.csv') -> list[CollegeData]:
    # __file__ is the current file
    # .parent.parent moves up to the project root directory
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "data" / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Could not find the data file at: {file_path}")
    
    # read the csv file into a pandas DataFrame
    df = pd.read_csv(file_path)
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    colleges = []

    # iterate through each row in csv file
    for _, row in df.iterrows():
        # extract raw value
        raw_value = row.get('endowment_size')
        # convert to float if data exists
        if raw_value:
            endowment_size = float(raw_value)
        else:
            endowment_size = None
        # create a CollegeData object for every row
        college = CollegeData(
            college_name = row['college_name'],
            cost_of_attendance = float(row['cost_of_attendance']),
        )
        colleges.append(college)
    return colleges