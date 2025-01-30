# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 13:03:00 2025

@author: IsaacSchultz
"""
import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_saturations_data():
    """Load preprocessed saturations data from a pickle file."""
    return pd.read_pickle('sats_df.pkl')

def create_pie_chart(df, end_use, scenario, year):
    """
    Create a pie chart showing equipment saturations for a specific year.
    
    Parameters:
    - df: DataFrame containing the saturations data.
    - end_use: "Cooling" or "Heating".
    - scenario: Selected scenario (e.g., "Baseline", "Program").
    - year: Specific year to visualize.

    Returns:
    - A Plotly figure object.
    """
    # Filter the data for the given end use, scenario, and year
    filtered_data = df[
      
        (df['Scenario'] == scenario) & 
        (df['year'] == year)
    ]

    # Create a pie chart
    fig = px.pie(
        filtered_data,
        names='EquipType',
        values='Quantity',
        title=f"Equipment Saturations - {end_use} - {scenario} - {year}",
        labels={'Quantity': 'Percentage'},
    )
    fig.update_traces(textinfo='percent+label')  # Show percentages and labels on the chart
    return fig

def saturations_tab():
    """Define the saturations tab in Streamlit."""
    st.header("Equipment Saturations")
    st.write("View the percentage of homes with specific equipment types for heating or cooling.")

    # Load the data
    sats_df = load_saturations_data()

    # Add End Use filter
    end_use_override = st.radio(
        "Select End Use (overrides the global filter):",
        options=["Cooling", "Heating"],
        index=0,
        key="end_use_override"
    )

    # Filter the data by End Use
    filtered_data = sats_df[sats_df['End Use'] == end_use_override]

    # Add Scenario filter
    selected_scenario = st.selectbox(
        "Select Scenario:",
        options=filtered_data['Scenario'].unique(),
        index=0,
        key="selected_scenario"
    )

    # Add Year filter
    selected_year = st.selectbox(
        "Select Year:",
        options=filtered_data['year'].unique(),
        index=0,
        key="selected_year"
    )

    # Display Pie Chart
    st.subheader(f"Equipment Saturations Pie Chart ({end_use_override}, {selected_scenario}, {selected_year})")
    if not filtered_data.empty:
        fig = create_pie_chart(filtered_data, end_use_override, selected_scenario, selected_year)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")
