import requests
import os

# Using a public endpoint for the test
# For production, use your actual API Key from data.gov
BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

def test_api_connection():
    # Searching for Duke as our test case
    # TODO: Move API_KEY to a secure .env file before production
    params = {
        "api_key": "DEMO_KEY",  # 'DEMO_KEY' is provided by data.gov for testing
        "school.name": "Duke University",
        "fields": "id,school.name,latest.aid.net_price.overall"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        print("Success! Connection established.")
        print(f"Data received: {data['results'][0]}")
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    test_api_connection()