# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 11:51:16 2025

@author: IsaacSchultz
"""

import streamlit as st
import pandas as pd

def rules_tab():
    st.header("Scoring System")
    st.markdown("""
    This is a season-long game where teams draft players and score points weekly based on those players successes and failures.
    Those points are awarded per contestant based on the scoring system laid out below. 
    Points are also scored for each team based on correct answers to the weekly questions. 
    """)
    
    # Example: load the point values table
    df = pd.read_csv("data/table.csv")
    st.subheader("Point Values")
    st.table(df)
