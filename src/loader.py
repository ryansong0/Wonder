import logging
import pandas as pd
from pathlib import Path
from src.schemas import CollegeData

def load_college_data(file_name: str = 'colleges.csv') -> list[CollegeData]:
    # __file__ is the current file
    # .parent.parent moves up to the project root directory
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "data" / file_name

    if not file_path.exists():
        logging.error(f"Data file missing at: {file_path}")
        raise FileNotFoundError(f"Could not find the data file at: {file_path}")
    
    logging.info(f"Successfully loaded data from {file_path}")

    # read the csv file into a pandas DataFrame
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    colleges = []

    # iterate through each row in csv file
    for _, row in df.iterrows():
        # captures every column header in csv file
        row_dict = row.to_dict()

        # replaces empty cells with "None"
        clean_data = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

        college = CollegeData(**clean_data)
        
        colleges.append(college)
    return colleges