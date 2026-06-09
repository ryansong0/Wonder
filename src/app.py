import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from src.engine import MonteCarloEngine
from src.schemas import StudentProfile
from src.loader import load_college_data

st.set_page_config(page_title = "Financial Aid Simulation", layout = "wide")
st.title("College Financial Aid Simulator")

colleges = load_college_data('colleges.csv')
college_names = [c.college_name for c in colleges]

st.sidebar.header("Student Profile")
income = st.sidebar.number_input("Household Income ($)")
assets = st.sidebar.number_input("Total Assets ($)")
family_size = st.sidebar.slider("Family Size")
state = st.sidebar.text_input("State", "NC")

chosen_college_name = st.selectbox("Select Institution", college_names)
chosen_college = next(c for c in colleges if c.college_name == chosen_college_name)

if st.button("Run Simulation"):
    student = StudentProfile(
        household_income = income,
        total_assets = assets,
        family_size = family_size,
        state_of_residence = state
    )

    engine = MonteCarloEngine(trials = 1000)
    result = engine.run_simulation(chosen_college, student)