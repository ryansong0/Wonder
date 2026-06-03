#What ingestor.py does
#Ingestor scrapes the web, downloads raw data, then tries to fit into CollegeData blueprint

from typing import List, Dict, Any
from src.schemas import CollegeData
class DataIngestor:
    def __init__(self):
#name of variable, type hint (tells Python that this variable only contains a List where every item inside is a CollegeData object)
        self.processed_colleges: List[CollegeData] = []

    def ingest_data(self, raw_data_list: List[Dict[str, Any]]):
        """
        Loops through raw data and converts valid items into CollegeData objects.
        """
        for entry in raw_data_list:
            try:
            #This line attempts to convert the raw dict into a CollegeData object.
            #If the data doesn't match the schema, Pydantic raises a ValidationError.
                college = CollegeData(**entry) #checks every value against schemas.py rules.
                self.processed_colleges.append(college)
            except Exception as e:
                #If data is missing or wrong (e.g. a negative endowment), it is caught here.
                print(f"Skipping {entry.get('college_name', 'Unknown')}: {e}")

    def get_data(self) -> List[CollegeData]:
        return self.processed_colleges