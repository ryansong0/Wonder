"""
Reference implementations of MonteCarloEngine._run_simulation used only for
benchmarking: a batched NumPy version that simulates every school at once as
a (schools, trials) matrix, and a pure-Python scalar version that loops over
every trial. Both reproduce the engine's model exactly; benchmark.py checks
the batched one against the engine draw-for-draw before timing anything.
"""
import math
import random

import numpy as np

from src import config
from src.config import ASSET_ASSESSMENT_RATE, EFC_SIGMA_CSS_PROFILE, EFC_SIGMA_FEDERAL_ONLY, INFLATION_MAX, INFLATION_MIN, YEARS_OF_COLLEGE
from src.engine import MonteCarloEngine

# Log-return parameters. Before the market-return fix these were literals
# inside _run_simulation (0.07, 0.15); afterwards they live in config.
MARKET_LOG_MEAN = getattr(config, "MARKET_LOG_RETURN_MEAN", 0.07)
MARKET_LOG_SIGMA = getattr(config, "MARKET_LOG_RETURN_VOLATILITY", 0.15)


def point_estimates(colleges, student) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The deterministic part of calculate_net_price, per school: center,
    full-price ceiling (already applied), and sigma fraction."""
    engine = MonteCarloEngine(trials = 1)
    centers, sigmas = [], []
    for college in colleges:
        center = engine.real_net_price_estimate(college, student.household_income)
        ceiling = college.cost_of_attendance
        if college.state and college.out_of_state_tuition_premium and student.state_of_residence.upper() != college.state.upper():
            center += college.out_of_state_tuition_premium
            ceiling += college.out_of_state_tuition_premium
        center = min(center + student.liquid_assets * ASSET_ASSESSMENT_RATE, ceiling)
        centers.append(center)
        sigmas.append(EFC_SIGMA_CSS_PROFILE if college.requires_css_profile else EFC_SIGMA_FEDERAL_ONLY)
    centers = np.array(centers)
    return centers, centers * np.array(sigmas)


def draw(schools: int, trials: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    log_returns = np.random.normal(MARKET_LOG_MEAN, MARKET_LOG_SIGMA, (schools, trials, YEARS_OF_COLLEGE))
    inflation = np.random.uniform(INFLATION_MIN, INFLATION_MAX, (schools, trials, YEARS_OF_COLLEGE))
    z = np.random.standard_normal((schools, trials))
    return log_returns, inflation, z


def simulate_batched(centers, scales, liquid_assets, log_returns, inflation, z) -> dict[str, np.ndarray]:
    """Same math as _run_simulation, with a leading schools axis."""
    market_returns = np.exp(log_returns) - 1
    # legacy np.random.normal(loc, scale) is exactly loc + scale * standard_normal
    net_annual = np.maximum(0, centers[:, None] + scales[:, None] * z)
    inflation_multiplier = np.cumprod(1 + inflation, axis = 2)

    assets = np.full(net_annual.shape, float(liquid_assets))
    total_debt = np.zeros(net_annual.shape)
    total_net_price = np.zeros(net_annual.shape)
    for year in range(YEARS_OF_COLLEGE):
        assets *= 1 + market_returns[:, :, year]
        tuition = net_annual * inflation_multiplier[:, :, year]
        total_net_price += tuition
        total_debt += np.maximum(0, tuition - assets)
        assets = np.maximum(0, assets - tuition)

    debt_p05, debt_p95 = np.percentile(total_debt, [5, 95], axis = 1)
    price_p05, price_p95 = np.percentile(total_net_price, [5, 95], axis = 1)
    return {
        "probability_of_shortfall": (total_debt > 0).mean(axis = 1),
        "average_total_cost": total_debt.mean(axis = 1),
        "max_debt": total_debt.max(axis = 1),
        "percentile_05": debt_p05,
        "percentile_95": debt_p95,
        "average_net_price": total_net_price.mean(axis = 1),
        "net_price_percentile_05": price_p05,
        "net_price_percentile_95": price_p95,
    }


def _percentile(sorted_values: list[float], q: float) -> float:
    """numpy's default (linear) percentile on an already-sorted list."""
    pos = (len(sorted_values) - 1) * q / 100
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def simulate_scalar(center: float, scale: float, liquid_assets: float, trials: int, rng: random.Random) -> dict[str, float]:
    """One school, one trial at a time, in plain Python."""
    debts, prices = [], []
    for _ in range(trials):
        net_annual = max(0.0, rng.gauss(center, scale))
        assets = liquid_assets
        multiplier = 1.0
        debt = price = 0.0
        for _ in range(YEARS_OF_COLLEGE):
            assets *= math.exp(rng.gauss(MARKET_LOG_MEAN, MARKET_LOG_SIGMA))
            multiplier *= 1 + rng.uniform(INFLATION_MIN, INFLATION_MAX)
            tuition = net_annual * multiplier
            price += tuition
            debt += max(0.0, tuition - assets)
            assets = max(0.0, assets - tuition)
        debts.append(debt)
        prices.append(price)
    debts.sort()
    prices.sort()
    return {
        "probability_of_shortfall": sum(d > 0 for d in debts) / trials,
        "average_total_cost": sum(debts) / trials,
        "max_debt": debts[-1],
        "percentile_05": _percentile(debts, 5),
        "percentile_95": _percentile(debts, 95),
        "average_net_price": sum(prices) / trials,
        "net_price_percentile_05": _percentile(prices, 5),
        "net_price_percentile_95": _percentile(prices, 95),
    }
