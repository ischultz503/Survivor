import streamlit as st
import pandas as pd
import plotly.express as px
from energy_tab import energy_consumption_tab
from saturations_tab import saturations_tab
from cooling_adoption_tab import cooling_adoption_tab
from pivot_tab import pivot_tab
import os

# Sidebar Information
st.sidebar.header("About This App")
st.sidebar.write("""
This app explores equipment saturations for residential HVAC systems.
- Navigate between tabs to view data visualizations and tables.
- Filters are specific to each tab for better control.
""")

st.sidebar.subheader("Key Definitions")
st.sidebar.write("""
**Cooling**: Includes central air conditioners, heat pumps, and other cooling systems.  
**Heating**: Includes furnaces, and heat pumps and other heating technologies.  
**Scenarios**:  
- Baseline: Represents the current state.  
- Program: Represents a hypothetical program implementation.
""")

# Create tabs for different sections
tab1, tab2 , tab3 , tab4 = st.tabs(["Energy Consumption", "Equipment Saturations","Cooling Adoption",'Pivot Table'])

with tab1:
    energy_consumption_tab()
with tab2:
    saturations_tab()
with tab3:
    cooling_adoption_tab()
with tab4:
    pivot_tab()

