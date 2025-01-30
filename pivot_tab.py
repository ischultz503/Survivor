# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 15:16:52 2025

@author: IsaacSchultz
"""
import streamlit as st
import pandas as pd

def load_data(file_path):
    """Load data from a pickle file and pre-process it."""
    df = pd.read_pickle(file_path)
    df = df.groupby(
        ['Scenario', 'End Use', 'Building Type', 'EquipType', 'Efficiency Tier', 'year']
    ).agg({
        'Quantity': 'sum',
        'Energy Consumption': 'sum'
    }).reset_index()
    return df


def filter_efficiency_tiers(df):
    """Filter Efficiency Tier to only apply to ASHP, DHP, and CAC."""
    df = df.rename(columns={"MSHP": "DHP"})  # Rename MSHP to DHP
    df = df[
        (df["EquipType"].isin(["ASHP", "DHP", "CAC"])) |
        (df["Efficiency Tier"].isna())
    ]
    # Ensure CAC is filtered to Cooling only
    df = df[~((df["EquipType"] == "CAC") & (df["End Use"] != "Cooling"))]
    return df


def pivot_tab():
    # Load and filter data
    data_file = os.path.join(os.path.dirname(__file__), "full consumption.pkl")

    #data_file = "c:/users/isaacschultz/documents/litapp/full consumption.pkl"
    df = load_data(data_file)
    df = filter_efficiency_tiers(df)

    st.header("Model Output: Grouped Data Display")
    st.write("Filter data using the options below and display grouped results.")

    # Year Slider
    st.subheader("Filter by Year")
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    selected_years = st.slider("Select Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

    # Apply Year Filter
    df = df[(df['year'] >= selected_years[0]) & (df['year'] <= selected_years[1])]

    # Filters in Expander
    with st.expander("Filters"):
        col1, col2 = st.columns(2)
        with col1:
            scenario = st.radio("Select Scenario", options=df["Scenario"].unique().tolist())
        with col2:
            end_use = st.radio("Select End Use", options=df["End Use"].unique().tolist())

    # Apply Filters
    df = df[df["Scenario"] == scenario]
    df = df[df["End Use"] == end_use]

    # Metric Selection
    st.subheader("Metric")
    metric = st.radio("Select Metric", options=["Quantity", "Saturation"], horizontal=True)

    # Calculate Saturation if Selected
    if metric == "Saturation":
        df['Total Quantity'] = df.groupby(['Building Type', 'EquipType', 'year'])['Quantity'].transform('sum')
        df['Saturation'] = df['Quantity'] / df['Total Quantity']
        df = df.drop(columns=['Total Quantity'])

    # Row Selection
    st.subheader("Row Options")
    row_option = st.radio(
        "Group Rows By:",
        options=["EquipType", "EquipType with Efficiency Tier"],
        horizontal=True
    )

    if row_option == "EquipType with Efficiency Tier":
        group_by = ['EquipType', 'Efficiency Tier']
        df = df[df["EquipType"].isin(["ASHP", "DHP", "CAC"])]  # Filter only for efficiency tier-related techs
    else:
        group_by = ['EquipType']

    # Group the Data
    grouped_data = df.groupby(group_by + ['year']).agg({metric: 'sum'}).reset_index()

    # Pivot the Data
    pivoted_data = grouped_data.pivot_table(
        values=metric,
        index=group_by,
        columns='year',
        fill_value=0,
        aggfunc='sum'
    ).reset_index()

    # Normalize Saturations to 100%
    if metric == "Saturation":
        pivoted_data.iloc[:, 1:] = pivoted_data.iloc[:, 1:].div(pivoted_data.iloc[:, 1:].sum(axis=0), axis=1)

    # Formatting the Data
    if metric == "Saturation":
        pivoted_data = pivoted_data.style.format({col: "{:.2%}" for col in pivoted_data.columns if isinstance(col, int)})
    else:
        pivoted_data = pivoted_data.style.format({col: "{:.0f}" for col in pivoted_data.columns if isinstance(col, int)})

    # Display the Data
    st.write("### Grouped and Pivoted Results")
    st.dataframe(pivoted_data)

if __name__ == "__main__":
    pivot_tab()
