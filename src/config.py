import json
from pathlib import Path

def load_config():
    path = Path(__file__).resolve().parent.parent / "config.json"
    with open(path, 'r') as f:
        return json.load(f)
    
config = load_config()


# Simulation Constants
NUM_TRIALS = config['simulation'].get('trials', 1000)
YEARS_OF_COLLEGE = config['simulation'].get('years_of_college', 4)

# Financial Projections
MARKET_RETURN_MIN = config['simulation'].get('market_return_min', 0.04)
MARKET_RETURN_MAX = config['simulation'].get('market_return_max', 0.08)

INFLATION_MIN = config['simulation'].get('inflation_min', 0.02)
INFLATION_MAX = config['simulation'].get('inflation_max', 0.05)

# Calculation Weights (used in EFC calculation)
INCOME_WEIGHT = config['simulation'].get('income_weight', 0.10)
ASSET_WEIGHT = config['simulation'].get('asset_weight', 0.05)