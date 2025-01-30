# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 11:58:32 2025

@author: IsaacSchultz
"""
import streamlit as st
import pandas as pd
import plotly.express as px

def load_data(file_path):
    """Load data from a pickle file."""
    return pd.read_pickle(file_path)

def cooling_adoption_tab():
    # File path for your data
    data_file = os.path.join(os.path.dirname(__file__), "cooling_adoption.pkl")

   # data_file = "c:/users/isaacschultz/documents/litapp/cooling_adoption.pkl"
    df = load_data(data_file)

    st.header("Cooling Adoption over Time")
    st.write("As the climate warms and the cooling load in the PNW increases, more and more homes have added cooling.")

    # Filters Layout
    st.subheader("Select Building Types for Line Chart:")
    building_types = df['Building Type'].unique()
    selected_building_types = [
        building_type for i, building_type in enumerate(building_types)
        if st.checkbox(f"Include {building_type}", value=True, key=f"building_type_{i}")
    ]

    # Apply Filters for Line Chart
    filtered_df = df[df['Building Type'].isin(selected_building_types)]

    # Check if data exists after filtering
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return

    # Aggregate Data to Calculate Cooling Percentage Across All Selected Building Types
    no_cooling_df = filtered_df[filtered_df['EquipType'] == "No Cooling"]
    no_cooling_grouped = no_cooling_df.groupby('year')['Quantity'].sum()

    total_quantity_grouped = filtered_df.groupby('year')['Quantity'].sum()

    # Align indices and calculate Cooling Percentage
    cooling_percentage = (1 - no_cooling_grouped / total_quantity_grouped).reset_index()
    cooling_percentage.columns = ['year', 'Cooling Percentage']

    # Add Year Range Slider
    start_year, end_year = int(cooling_percentage['year'].min()), int(cooling_percentage['year'].max())
    st.subheader("Select Year Range for the Chart:")
    year_range = st.slider("Year Range:", start_year, end_year, (start_year, end_year), step=1)

    # Filter by Year Range
    cooling_percentage = cooling_percentage[
        (cooling_percentage['year'] >= year_range[0]) & 
        (cooling_percentage['year'] <= year_range[1])
    ]

    # Check if filtered data exists
    if cooling_percentage.empty:
        st.warning("No data available for the selected filters and year range.")
        return

    # Visualization: Line Chart with Fixed Y-Axis
    st.subheader("Percentage of Homes with Cooling Over Time")
    fig = px.line(
        cooling_percentage,
        x='year',
        y='Cooling Percentage',
        title="Cooling Adoption Trends",
        labels={
            'year': 'Year',
            'Cooling Percentage': 'Percentage of Homes with Cooling',
        }
    )
    fig.update_layout(
        yaxis=dict(range=[0, 1], tickformat=".0%"),  # Fixed Y-axis from 0 to 100%
        xaxis=dict(title="Year"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Radio Button for Pie Chart Building Type Selection
    st.subheader("Select Building Type for Pie Chart:")
    building_type_for_pie = st.radio(
        "Building Type:", 
        options=["All"] + list(building_types),  # Add "All" option
        index=0
    )

    # Dropdown for Pie Chart Year Selection
    st.subheader("Select Year for Cooling Equipment Type Breakout:")
    selected_year = st.selectbox("Year:", df['year'].unique())

    # Filter Data for Pie Chart
    if building_type_for_pie == "All":
        pie_chart_data = df[
            (df['year'] == selected_year) & (df['EquipType'] != "No Cooling")
        ].groupby('EquipType')['Quantity'].sum().reset_index()
        percentage_with_cooling = 1 - (
            df[(df['year'] == selected_year) & (df['EquipType'] == "No Cooling")]['Quantity'].sum() /
            df[df['year'] == selected_year]['Quantity'].sum()
        )
    else:
        pie_chart_data = df[
            (df['year'] == selected_year) & 
            (df['EquipType'] != "No Cooling") &
            (df['Building Type'] == building_type_for_pie)
        ].groupby('EquipType')['Quantity'].sum().reset_index()
        percentage_with_cooling = 1 - (
            df[(df['year'] == selected_year) & (df['EquipType'] == "No Cooling") & (df['Building Type'] == building_type_for_pie)]['Quantity'].sum() /
            df[(df['year'] == selected_year) & (df['Building Type'] == building_type_for_pie)]['Quantity'].sum()
        )

    # Pie Chart
    st.subheader(f"Cooling Equipment Type Breakout for {selected_year}")
    if not pie_chart_data.empty:
        pie_chart = px.pie(
            pie_chart_data,
            names='EquipType',
            values='Quantity',
            title=f"Cooling Equipment Distribution ({selected_year}) - {building_type_for_pie}",
            labels={'Quantity': 'Share of Homes'},
        )
        st.plotly_chart(pie_chart, use_container_width=True)

        # Display Percentage of Homes with Cooling
        st.subheader(f"**{percentage_with_cooling:.1%}** of the homes in building type: **{building_type_for_pie}** have cooling in **{selected_year}**.")
    else:
        st.warning(f"No data available for {building_type_for_pie} in {selected_year}.")
