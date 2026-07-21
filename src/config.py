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

# Aid Methodology Uncertainty
# CSS Profile / institutional-methodology schools weigh dozens of discretionary,
# non-public factors (home equity, non-custodial income, sibling counts, etc.), so
# the same income/assets can yield a materially different EFC than the federal
# formula predicts. Federal-methodology-only schools are bound to the public,
# mechanical FAFSA formula, so real-world variance is much tighter.
EFC_SIGMA_CSS_PROFILE = config['aid_uncertainty'].get('css_profile_sigma', 0.20)
EFC_SIGMA_FEDERAL_ONLY = config['aid_uncertainty'].get('federal_only_sigma', 0.07)

# Asset Treatment
# The real net-price-by-income data has no way to reflect a family's assets,
# since College Scorecard only publishes net price broken out by income. This
# rate is the federal Student Aid Index formula's published parent-asset
# assessment rate: for every dollar of assets, this fraction is added to the
# expected annual contribution. It's applied uniformly rather than modeling
# CSS Profile's broader asset base (home equity, business assets) separately,
# since a single "total_assets" figure can't distinguish those asset types.
ASSET_ASSESSMENT_RATE = config['asset_treatment'].get('assessment_rate', 0.0564)