import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from src.engine import MonteCarloEngine
from src.schemas import StudentProfile
from src.loader import load_college_data

st.set_page_config(page_title = "Financial Aid Simulation", layout = "wide")
st.title("College Financial Aid Simulator")

colleges = load_college_data('colleges.csv')
colleges_names = [c.college_name for c in colleges]

st.sidebar.header("Student Profile")
income = st.sidebar.number_input("Household Income ($)")
assets = st.sidebar.number_input("Total Assets ($)")
family_size = st.sidebar.slider("Family Size")
state = st.sidebar.text_input("State", "NC")