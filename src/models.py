from pydantic import BaseModel, Field

class SimulationResult(BaseModel):
    college_name: str
    probability_of_shortfall: float = Field(ge = 0, le = 1)
    average_total_cost: float
    max_debt_burden: float
    simulation_trials: int