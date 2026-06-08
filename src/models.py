from pydantic import BaseModel, ConfigDict
import numpy as np

class SimulationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed = True)
    college_name: str
    probability_of_shortfall: float
    average_total_cost: float
    percentile_05: float
    percentile_95: float
    max_debt: float
    simulation_trials: int
    all_trial_results: np.ndarray