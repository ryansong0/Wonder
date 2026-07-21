from pydantic import BaseModel, ConfigDict
import numpy as np

class SimulationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed = True)
    college_name: str
    # probability_of_shortfall, average_total_cost, percentile_05/95, and
    # max_debt all describe the shortfall (money the family can't cover from
    # assets), not the sticker cost itself. A family with enough assets to pay
    # any price shows $0 here even when the school is genuinely expensive -
    # see average_net_price below for the actual estimated cost.
    probability_of_shortfall: float
    average_total_cost: float
    percentile_05: float
    percentile_95: float
    max_debt: float
    simulation_trials: int
    all_trial_results: np.ndarray
    calibrated_with_real_data: bool = False

    # The actual estimated total cost over the whole program, after aid,
    # regardless of whether the family's assets can cover it. This is what
    # distinguishes "genuinely inexpensive" from "expensive but affordable."
    average_net_price: float = 0.0
    net_price_percentile_05: float = 0.0
    net_price_percentile_95: float = 0.0