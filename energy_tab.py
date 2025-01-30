# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 12:58:34 2025

@author: IsaacSchultz
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import os
# Create checkboxes for 'Scenario'

def load_data(file_path):
    return pd.read_pickle(file_path)

def energy_consumption_tab():
    # File path for your data
    data_file = os.path.join(os.path.dirname(__file__), "full consumption.pkl")
    df = load_data(data_file)
    
    st.header("Energy Consumption by Year and Scenario")
    st.write("Visualize energy consumption trends from 2011 to 2027 for different scenarios, end uses, and building types.")
    
    # Layout with columns for filters
    col1, col2, col3 = st.columns(3)

    # Scenarios Filter
    with col1:
        st.subheader("Select Scenarios:")
        scenarios = df['Scenario'].unique()
        selected_scenarios = [
            scenario for scenario in scenarios if st.checkbox(f"Include {scenario}", value=True, key=f"scenario_{scenario}")
        ]

    # End Use Filter
    with col2:
        st.subheader("Select End Uses:")
        end_uses = df['End Use'].unique()
        selected_end_uses = [
            end_use for end_use in end_uses if st.checkbox(f"Include {end_use}", value=True, key=f"end_use_{end_use}")
        ]

    # Building Type Filter
    with col3:
        st.subheader("Select Building Types:")
        building_types = df['Building Type'].unique()
        selected_building_types = [
            building_type for building_type in building_types if st.checkbox(f"Include {building_type}", value=True, key=f"building_type_{building_type}")
        ]

    
    # Apply Filters to the DataFrame
    filtered_df = df[
        (df['Scenario'].isin(selected_scenarios)) &
        (df['End Use'].isin(selected_end_uses)) &
        (df['Building Type'].isin(selected_building_types))
    ]

    filtered_df_table = df[
       
        (df['End Use'].isin(selected_end_uses)) &
        (df['Building Type'].isin(selected_building_types))]
    
    st.header("Energy Consumption by Year and Scenario")
    st.write("Visualize energy consumption trends from 2011 to 2027 for different scenarios.")

    # Filter data for years 2021 to 2027
    start_year, end_year = 2011, 2027
    filtered_df = filtered_df[(filtered_df['year'] >= start_year) & (filtered_df['year'] <= end_year)]

    # Aggregate data by year and scenario
    grouped_df = filtered_df.groupby(['year', 'Scenario'])['Energy Consumption'].sum().reset_index()

    # Filters specific to this tab
    st.subheader("Filters")
    year_range = st.slider(
        "Select Year Range:", 
        start_year, 
        end_year, 
        (start_year, end_year), 
        key="tab1_year"
    )


    # Apply year range filter
    filtered_df = grouped_df[
        (grouped_df['year'] >= year_range[0]) & 
        (grouped_df['year'] <= year_range[1]) 
    ]

    # Visualization: Line chart
    st.subheader("Energy Consumption by Scenario Over Time")
    
    # Dynamic Default Y-axis Values
    if not filtered_df.empty:
        y_min_default = int(filtered_df['Energy Consumption'].min() / 100 ) * 100
        y_max_default = int(filtered_df['Energy Consumption'].max() / 100 ) * 100
    else:
        y_min_default = 0
        y_max_default = 100  # Provide a fallback max value for empty data

    # Responsive Layout for Y-axis Inputs
    col1, col2 = st.columns(2)
    with col1:
        min_y = st.number_input(
            "Set Minimum Y-axis Value:",
            min_value=0,
            max_value=y_max_default,
            value=y_min_default,
            step=100,
        )
    with col2:
        max_y = st.number_input(
            "Set Maximum Y-axis Value:",
            min_value=min_y,
            max_value=y_max_default * 2 if y_max_default > 0 else 200,
            value=y_max_default,
            step=100,
        )
    
    # Update Plotly Chart with Dynamic Y-Axis
    fig = px.line(
        filtered_df,
        x='year',
        y='Energy Consumption',
        color='Scenario',
        title="Energy Consumption Trends",
    )
    
    fig.update_yaxes(range=[min_y, max_y])  # Set dynamic Y-axis range
    st.plotly_chart(fig)
    
    # Display Data Table Below the Chart
    st.subheader("Energy Consumption Data Table")
    tab1_table = filtered_df_table.copy()
    
    
    tab1_table = tab1_table.groupby(['year','Scenario']).agg({'Energy Consumption':'sum'}).reset_index()
    
    tab1_table['year'] = tab1_table['year'].astype(str)
    tab1_table['Energy Consumption'] = tab1_table['Energy Consumption'].astype(float).round(1)
    
   # Handle the case when no data matches the filters
    if tab1_table.empty:
        st.warning("No data available for the selected filters.")
    else:
        # Use pivot_table to handle duplicates
        tab1_table = tab1_table.pivot_table(
            values='Energy Consumption',
            columns='Scenario',
            index='year',
            aggfunc='sum',
            fill_value=0  # Fill missing values with 0
        )
    
        # Ensure all expected scenarios are present
        expected_columns = ['Baseline', 'Market', 'Program']
        for col in expected_columns:
            if col not in tab1_table.columns:
                tab1_table[col] = 0  # Add missing scenarios with default value
    
        # Reorder columns to match expected order
        tab1_table = tab1_table[expected_columns]
    
        # Reset index to make 'year' a column
        tab1_table.reset_index(inplace=True)
    
        # Rename columns
        tab1_table.columns = ['Year', 'Baseline Consumption', 'Market Consumption', 'Program Consumption']
    
        # Display the table
        st.write("Below is the data used in the chart:")
        st.dataframe(tab1_table, use_container_width=True)