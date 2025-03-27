# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 13:37:47 2025

@author: IsaacSchultz
"""

import streamlit as st
import pandas as pd
import plotly.express as px

def trends_tab():
    st.header("Player Trends")

    # Load from session state
    season = st.session_state["season"]
    league = st.session_state["league"]

    # File paths
    if season == "Season 47":
        scores_file = "data/PointsScored_Survivor_47.xlsx"
    elif season == "Season 48":
        scores_file = "data/PointsScored_Survivor_48.xlsx"

    point_values = pd.read_csv("data/PointValues_Survivor.csv")

    # --- Load and process data ---
    def clean_data(df):
        df.columns = df.columns.str.replace(" ", "_").str.replace(".", "_", regex=False)
        return df.fillna(0)

    def apply_point_values(raw_scores, point_values):
        raw_scores = raw_scores.copy()
        point_values = point_values.copy()
    
        # Don't rename anything — match original column names exactly
        raw_scores = raw_scores.fillna(0)
        point_values["Event"] = point_values["Event"].str.strip()
        raw_scores.columns = raw_scores.columns.str.strip()
        for _, row in point_values.iterrows():
            event = row["Event"]
            if event in raw_scores.columns:
                raw_scores[event] *= row["Points"]
    
        event_cols = [col for col in point_values["Event"] if col in raw_scores.columns]
        raw_scores["total"] = raw_scores[event_cols].sum(axis=1)
        return raw_scores, event_cols

    def get_scoreboard(raw_scores):
        scoreboard = raw_scores[["Player", "Week", "total"]].copy()
        scoreboard["rolling_total"] = scoreboard.groupby("Player")["total"].cumsum()
        return scoreboard

    # Load and score

    raw_scores = pd.read_excel(scores_file, sheet_name="PointsScored_Survivor")
    raw_scores, event_cols = apply_point_values(raw_scores, point_values)
    scoreboard = get_scoreboard(raw_scores)

    # --- Controls ---
    player_list = sorted(raw_scores["Player"].unique())  # Alphabetized
    selected_players = st.multiselect("Select Players", player_list, default=player_list[:1])

    view_type = st.radio("Score View", ["Cumulative", "Weekly"], horizontal=True)

    filtered = scoreboard[scoreboard["Player"].isin(selected_players)]

    # --- Chart ---
    st.subheader("Weekly Score Chart")

    if view_type == "Cumulative":
        fig = px.line(
            filtered,
            x="Week",
            y="rolling_total",
            color="Player",
            markers=True,
            labels={"rolling_total": "Cumulative Score"}
        )
    else:
        fig = px.bar(
            filtered,
            x="Week",
            y="total",
            color="Player",
            barmode="group",
            labels={"total": "Weekly Score"}
        )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- Event Table (Long Format) ---
    st.subheader("Scoring Breakdown by Event")

    score_detail = raw_scores[raw_scores["Player"].isin(selected_players)].copy()
    score_detail = score_detail[["Player", "Week"] + event_cols]

    # Melt to long format
    long_scores = score_detail.melt(id_vars=["Player", "Week"], var_name="Event", value_name="Points")

    # Filter for actual scoring events
    long_scores = long_scores[long_scores["Points"] != 0]

    # Clean and sort
    long_scores["Event"] = long_scores["Event"].str.replace("_", " ").str.title()
    long_scores = long_scores.sort_values(["Week", "Player",'Points'], ascending=[True, True, False])

    # Show table with horizontal bar in Points
    st.dataframe(
        long_scores.style
            .bar(subset=["Points"], color='#85C1E9')
            .format({"Points": "{:.0f}"}),
        use_container_width=True
    )
