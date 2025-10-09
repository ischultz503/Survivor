# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 11:51:16 2025

@author: IsaacSchultz
"""

import streamlit as st
import pandas as pd
from utils_cache import read_excel, read_csv


def rules_tab():
    st.header("Scoring System")
    st.markdown("""
    This is a season-long game where teams draft players and score points weekly based on those players' successes and failures.
    Those points are awarded per contestant based on the scoring system laid out below. 
    Points are also scored for each team based on correct answers to the weekly questions. 
    """)
    
    # Load the point values table
    league = st.session_state.get("league")
    
    if league == 'Bi-coastal Elites':
        df = read_excel("data/east/Survivor_49_East.xlsx", "Scoreboard_Table")
    else:
        df = read_csv("data/scoreboard_table.csv")
    st.subheader("Point Values")
    
    # Apply formatting to only certain events
    def format_conditionally(df):
        def custom_formatter(val, row):
            # Define which events should show one decimal place
            format_events = ["Complaining", "Autism Awareness Warrior","Text Effects"]
            if row["Event"] in format_events:
                return f"{val:.1f}"
            else:
                return f"{int(val)}" if float(val).is_integer() else f"{val}"

        # Apply row-wise formatting
        formatted = df.copy()
        formatted["Points"] = [custom_formatter(val, row) for val, (_, row) in zip(df["Points"], df.iterrows())]
        return formatted

    formatted_df = format_conditionally(df)
    st.dataframe(formatted_df.style.hide(axis='index'), use_container_width=True)
