from pydantic import BaseModel, Field

class SimulationResult(BaseModel):
    college_name: str
    probability_of_shortfall: float
    average_total_cost: float
    percentile_05: float
    percentile_95: float
    max_debt: float
    simulation_trials: int