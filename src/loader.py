import pandas as pd
from src.schemas import CollegeData

def load_college_data(file_path: str) -> list[CollegeData]:
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