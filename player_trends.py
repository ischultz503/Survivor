# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 13:37:47 2025

@author: IsaacSchultz
"""
from utils_cache import read_excel, read_csv, cache_df
import streamlit as st
import pandas as pd
import plotly.express as px


def trends_tab():
    def get_all_rosters(season):
        if season == "Season 49":
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Savannah','Steven','Jawan','Sage'],
                    "Brackie": ['MC','Rizo','Matt','Shannon' ],
                    "Polron":  ['Sophie S','Nate','Jason','Kristina'],
                    "Kanna":   ['Alex','Jeremiah','Sophi B','Jake']
                }),
                "Bi-coastal Elites": pd.DataFrame({
                    "Jena":            ['Matt','Sophie S','Rizo'],
                    "Schultz & Big P": ['Kristina','Alex','Savannah'],
                    "Isaac":           ['Jawan','Jeremiah','Steven'],
                    "Mike":            ['Nate','Jake','Sage'],
                    "Nick":            ['MC','Nicole','Annie'],
                    "Eric":            ['Jason','Sophi B','Shannon']
                })
            }
        if season == "Season 48":
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Eva','Mitch','Mary','Sai'],
                    "Brackie": ['Kamilla','Kyle','Chrissy','Cedrek'],
                    "Polron":  ['Joe','Thomas','Bianca','Charity'],
                    "Kanna":   ['Shauhin','Justin','Star','David']
                })
            }
        if season == "Season 47":
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Sam','Sierra','Genevieve','Sue','Caroline'],
                    "Brackie": ['Kyle','Rome','Sol','Anika','Kishan'],
                    "Polron":  ['Teeny','Rachel','Andy','Gabe','Tiyana']
                })
            }

    st.header("Player Trends")

    # Load from session state
    season = st.session_state["season"]
    league = st.session_state["league"]
    
        # File paths
    if season == "Season 47":
        scores_file = "data/PointsScored_Survivor_47.xlsx"
    elif season == "Season 48":
        scores_file = "data/PointsScored_Survivor_48.xlsx"
    elif season == "Season 49":
        if league == 'Bi-coastal Elites':
            scores_file = "data/east/Survivor_49_East.xlsx"
        else:
            scores_file = "data/PointsScored_Survivor_49.xlsx"
    
    if league == 'Bi-coastal Elites':
        point_values = pd.read_excel("data/east/Survivor_49_East.xlsx", sheet_name="PointValues_Survivor")
    else:
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
    key_rs = f"{league}|{season}|raw_scores"
    raw_scores = cache_df(key_rs, raw_scores, file_path=scores_file)

    
    raw_scores, event_cols = apply_point_values(raw_scores, point_values)
    key_scored = f"{league}|{season}|scored_trends"
    raw_scores = cache_df(key_scored, raw_scores, file_path=scores_file)

    
    scoreboard = get_scoreboard(raw_scores)
    key_board = f"{league}|{season}|scoreboard_trends"
    scoreboard = cache_df(key_board, scoreboard, file_path=scores_file)


    # --- Team filter (optional) ---
    rosters = get_all_rosters(season)
    roster_df = rosters.get(league)
    
    # Build the team list if we have rosters for this league; otherwise just default to All teams
    team_options = ["All teams"] + (roster_df.columns.tolist() if isinstance(roster_df, pd.DataFrame) else [])
    selected_team = st.selectbox("Team (optional)", team_options, index=0)



    # --- Controls ---
    player_list = sorted(raw_scores["Player"].unique())  # all players in the season
    if selected_team != "All teams" and isinstance(roster_df, pd.DataFrame):
        team_players = roster_df[selected_team].dropna().tolist()
        # Default to everyone on the chosen team
        default_players = team_players if len(team_players) > 0 else player_list[:1]
        help_txt = f"Showing players on {selected_team}. You can add/remove players."
    else:
        default_players = player_list[:1]
        help_txt = "Pick any players to compare."
    
    selected_players = st.multiselect("Select Players", player_list, default=default_players, help=help_txt)
    
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
            .format({"Points": "{:.1f}"}),
        use_container_width=True
    )
