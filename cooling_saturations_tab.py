# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 13:03:00 2025

@author: IsaacSchultz
"""
import streamlit as st
import pandas as pd
import plotly.express as px

def saturations_tab(df):
    st.header("Equipment Saturations")
    st.write("View the percentage of homes with specific equipment types. The values for each scenario will add to 100%.")

    # Filter for Cooling End Use
    tab_data = df[df['End Use'] == 'Cooling']
    
    # Calculate Percentages
    saturation_df = (
        tab_data.groupby(['EquipType', 'Scenario', 'year'])
        .agg({'Quantity': 'sum'})
        .div(tab_data.groupby(['Scenario', 'year']).agg({'Quantity': 'sum'}))
    )
    saturation_df.reset_index(inplace=True)

    # Pivot the Table for Visualization
    saturation_df = saturation_df.pivot(index=['EquipType', 'year'], columns='Scenario', values='Quantity')
    saturation_df.reset_index(inplace=True)

    # Order Equipment Types
    tech_order_c = ['RAC', 'No Cooling', 'CAC', 'DHP', 'GSHP', 'PTAC', 'ASHP', 'Evaporative Cooler', 'PTHP']
    saturation_df['EquipType'] = pd.Categorical(saturation_df['EquipType'], categories=tech_order_c, ordered=True)
    saturation_df.sort_values(['EquipType'], inplace=True)

    # Display the Table
    st.subheader("Equipment Saturations Table")
    st.dataframe(saturation_df, use_container_width=True)

    # Visualization: Stacked Bar Chart
    st.subheader("Equipment Saturations by Year")
    if not saturation_df.empty:
        for scenario in saturation_df.columns[2:]:  # Skip 'EquipType' and 'year'
            fig = px.bar(
                saturation_df,
                x='year',
                y=scenario,
                color='EquipType',
                title=f"Equipment Saturations ({scenario})",
                labels={'year': 'Year', scenario: 'Percentage'},
                text_auto='.0%'  # Display percentages as text
            )
            fig.update_layout(barmode='stack', yaxis=dict(tickformat=".0%"))
            st.plotly_chart(fig)
    else:
        st.warning("No data available for the selected filters.")
