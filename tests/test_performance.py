import time
#from src.baseline_engine import BaselineEngine
from src.engine import MonteCarloEngine as OptimizedEngine
from src.loader import load_college_data
from src.schemas import StudentProfile

student = StudentProfile(household_income = 100000, total_assets = 50000, family_size = 4, state_of_residence = "NC")
colleges = load_college_data('data/colleges.csv')
num_trials = 10000

# measure baseline
#base = BaselineEngine(trials = num_trials)
#start = time.perf_counter()
#for c in colleges: base.run_simulation(c, student)
#base_time = time.perf_counter() - start

# measure optimized
opt = OptimizedEngine(trials = num_trials)
start = time.perf_counter()
for c in colleges: 
    opt.run_simulation(c, student)
opt_time = time.perf_counter() - start

#print(f"Baseline (Iterative): {base_time:.4f}s")
print(f"Optimized (Vectorized): {opt_time:.4f}s")
#print(f"Performance Gain: {base_time / opt_time:.1f}x speedup")