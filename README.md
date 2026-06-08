# Stochastic College Financial Aid Engine

### The Problem
In today's age, where private institutions' annual cost of attendance can range to upwards of $100,000 annually, students and parents face significant financial uncertainty. Currently, colleges have their own independent cost of attendance calculators that force students to re-input their financial profiles for every potential college to predict their aid at each school. For instance, if a student planed to apply to 17 schools, that student would need to plug in his/her information in all 17 college calculators to see how much the cost of attendance would be at each school. This time-consuming and repetitive process should not be what students worry about. Rather, they should be spending their time focusing on their critical college applications. As financial aid is determined by a combination of the institution's endowment size for its available funding for scholarships and grants, as well historical enrollment and aid-required data for an estimation to the incoming class, each college's aid package varies greatly from each other, which can make static estimates misleading.

### The Solution
This project provides a centralized financial aid engine that eliminates the redundant data entry process that is currently ongoing. Creating a unified ingestion layer and a high-throughput modeling framework, my system simultaneously generates stochastic financial aid projections for 100+ institutions. This replaces a manual, multi-step workflow with a single, optimized user interaction. Additionally, instead of providing a single (and often misleading) estimation value, my engine uses Monte Carlo simulations to present a range of probable values, providing a more transparent view of potential net costs for each university. My hope is that students and parents can avoid wasting their time inputting their information repeatedly for each school (which is something that I had to do during my senior year of high school, as I applied to 15+ schools), and can instead use my project as a resource to be more time-efficient during the college application season!

## Performance 
The project uses NumPy vectorization to process simulation trials in batches at the same time, which allows the system to scale 1,000,000+ trials fast.

## Results
The tests were performed using an optimized vector-based execution model.

| Simulation Trials | Processing Time | Throughput |
| :--- | :--- | :--- |
| 10,000 | 0.042s | 238,000 trials/sec |
| 100,000 | 0.058s | 1,724,000 trials/sec |
| 1,000,000 | 0.412s | 2,427,000 trials/sec |


### Getting Started

#### 1. Setup Environment

First, clone the repository and set up the virtual environment:
```bash
# Create and activate the environment
python -m venv venv

# For Windows: 
venv\Scripts\activate

# For macOS/Linux:
source venv/bin/activate

# Install
pip install -r requirements.txt
```
#### 2. Run Simulation:
python scripts/plot_results.py

#### 3. Run Test:
pytest