# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 11:53:21 2025

@author: IsaacSchultz
"""
from utils_cache import read_excel, read_csv, cache_df, cache_obj
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def standings_tab():
    league = st.session_state["league"]
    season = st.session_state["season"]
    paths  = st.session_state["paths"]
    scores_file_path = paths["scores"]
    images_path      = paths["images"]
    point_values_src = paths["point_values"]
    st.header("Standings and Team Rosters")
    def overlay_red_x(image_url):
        key = f"redx|{image_url}"
        cached = cache_obj(key, None)
        if cached is not None:
            return cached
    
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    
        draw = ImageDraw.Draw(img)
        width, height = img.size
        line_width = int(width * 0.08)
        draw.line((0, 0, width, height), fill=(255, 0, 0, 255), width=line_width)
        draw.line((width, 0, 0, height), fill=(255, 0, 0, 255), width=line_width)
    
        return cache_obj(key, img)

    
    
    # --- Pull global state from sidebar ---
    season = st.session_state["season"]
    league = st.session_state["league"]
    

    def load_data(scores_file_path, images_path, league, point_values_src):
        raw_scores   = read_excel(scores_file_path, "PointsScored_Survivor")
        bonus_scores = read_excel(scores_file_path, "Weekly_Pick_Scores")
        bonus_scores = bonus_scores.drop(columns=["Week"])
        bonus_scores.columns = bonus_scores.columns.str.strip()
    
        if league == "Bi-coastal Elites":
            point_values = read_excel(point_values_src, "PointValues_Survivor")
        else:
            point_values = read_csv("data/PointValues_Survivor.csv")
    
        player_images = read_excel(images_path, "Images")
        return raw_scores, bonus_scores, point_values, player_images



    raw_scores, bonus_scores, point_values, player_images = load_data(
        scores_file_path, images_path, league, point_values_src
    )



    # --- Roster definitions ---
    def get_all_rosters(season):
        if season == "Season 49":
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Savannah','Steven','Jawan','Sage'],
                    "Brackie": ['MC','Rizo','Matt','Shannon' ],
                    "Polron":  ['Sophie S','Nate','Jason','Kristina'],
                    'Kanna':   ['Alex','Jeremiah','Sophi B','Jake']}),
                    
                    "Bi-coastal Elites": pd.DataFrame({
                        'Jena':            ['Matt','Sophie S','Rizo'],
                        'Schultz & Big P': ['Kristina','Alex','Savannah' ],
                        'Isaac':           ['Jawan','Jeremiah','Steven'],
                        'Mike':            ['Nate','Jake','Sage'],
                        'Nick':            ['MC','Nicole','Annie'],
                        'Eric':            ['Jason','Sophi B','Shannon']})
                
            }
        
        if season == "Season 48":
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Eva','Mitch','Mary','Sai'],
                    "Brackie": [ 'Kamilla','Kyle','Chrissy','Cedrek'],
                    "Polron": ['Joe','Thomas','Bianca','Charity'],
                    'Kanna':['Shauhin','Justin','Star','David']
                })
            }
        if season == 'Season 47':
            return {
                "NE Portland": pd.DataFrame({
                    "Picasso": ['Sam','Sierra','Genevieve','Sue','Caroline'],
                    "Brackie": ['Kyle','Rome','Sol','Anika','Kishan'],
                    "Polron": ['Teeny','Rachel','Andy','Gabe','Tiyana']
                })
            }

    all_rosters = get_all_rosters(season)
    roster_df = all_rosters[league]
    #teams = roster_df.columns.tolist()

    # --- Scoring Functions ---
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

    def get_team_totals(scoreboard, roster_df, bonus_scores):
        player_totals = scoreboard.groupby("Player")["total"].sum()
        team_totals = {}
        for team in roster_df.columns:
            players = roster_df[team].dropna()
            player_total = player_totals.loc[players].sum()
            bonus_total = bonus_scores[team].sum() if team in bonus_scores.columns else 0
            team_totals[team] = player_total + bonus_total
        return pd.DataFrame.from_dict(team_totals, orient='index', columns=["Total Points"]).sort_values("Total Points", ascending=False)


    def get_team_scores_by_week(scoreboard, roster_df):
        weeks = sorted(scoreboard["Week"].unique())
        team_data = { "Week": weeks }

        for team in roster_df.columns:
            team_week_scores = []
            for w in weeks:
                week_df = scoreboard[scoreboard["Week"] == w]
                players = roster_df[team].dropna()
                total = week_df[week_df["Player"].isin(players)]["total"].sum()
                team_week_scores.append(total)
            team_data[team] = pd.Series(team_week_scores).cumsum()

        return pd.DataFrame(team_data)

    # --- Process Scoring ---
    scored, _ = apply_point_values(raw_scores, point_values)
    key_scored = f"{league}|{season}|scored"
    scored = cache_df(key_scored, scored)

    scoreboard = get_scoreboard(scored)
    key_scoreboard = f"{league}|{season}|scoreboard"
    scoreboard = cache_df(key_scoreboard, scoreboard)    
    
    standings_df = get_team_totals(scoreboard, roster_df, bonus_scores)
    key_standings = f"{league}|{season}|standings"
    standings_df = cache_df(key_standings, standings_df)

#####################################################################################
    # --- Line Chart: Team Scores by Week ---
    # --- Team Scores Chart Options ---
    chart_type = st.radio("Show Team Scores as:", ["Cumulative Line Chart", "Weekly Bar Chart"])
    
    # --- Cumulative Line Chart ---
    def get_cumulative_team_scores(scoreboard, roster_df, bonus_scores):
        weeks = sorted(scoreboard["Week"].unique())
        team_data = { "Week": weeks }
    
        for team in roster_df.columns:
            team_week_scores = []
            for w in weeks:
                week_df = scoreboard[scoreboard["Week"] == w]
                players = roster_df[team].dropna()
                player_total = week_df[week_df["Player"].isin(players)]["total"].sum()
                
                # Grab bonus for that week
                bonus = 0
                if team in bonus_scores.columns:
                    try:
                        bonus = bonus_scores.iloc[w - 1][team]
                    except Exception:
                        pass  # In case week index mismatch
    
                team_week_scores.append(player_total + bonus)
    
            team_data[team] = pd.Series(team_week_scores).cumsum()
    
        return pd.DataFrame(team_data)
    
    # --- Weekly (Non-Cumulative) Scores ---
    def get_weekly_team_scores(scoreboard, roster_df, bonus_scores):
        weeks = sorted(scoreboard["Week"].unique())
        team_data = { "Week": weeks }
    
        for team in roster_df.columns:
            team_week_scores = []
            for w in weeks:
                week_df = scoreboard[scoreboard["Week"] == w]
                players = roster_df[team].dropna()
                player_total = week_df[week_df["Player"].isin(players)]["total"].sum()
    
                # Grab bonus for that week
                bonus = 0
                if team in bonus_scores.columns:
                    try:
                        bonus = bonus_scores.iloc[w - 1][team]
                    except Exception:
                        pass
    
                team_week_scores.append(player_total + bonus)
    
            team_data[team] = team_week_scores
    
        return pd.DataFrame(team_data)
    
    if chart_type == "Cumulative Line Chart":
        st.subheader("Team Scores by Week (Cumulative)")
        team_week_df = get_cumulative_team_scores(scoreboard, roster_df, bonus_scores)
        key_cum = f"{league}|{season}|team_week_cumulative"
        team_week_df = cache_df(key_cum, team_week_df)
        team_long = team_week_df.melt(id_vars="Week", var_name="Team", value_name="Score")
        fig = px.line(team_long, x="Week", y="Score", color="Team", markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Weekly Bar Chart":
        st.subheader("Team Scores by Week (Non-Cumulative)")
        team_week_df = get_weekly_team_scores(scoreboard, roster_df, bonus_scores)
        key_weekly = f"{league}|{season}|team_week_weekly"
        team_week_df = cache_df(key_weekly, team_week_df)
        team_long = team_week_df.melt(id_vars="Week", var_name="Team", value_name="Score")
        fig = px.bar(team_long, x="Week", y="Score", color="Team", text="Score")
        fig.update_layout(barmode="group", height=450, xaxis=dict(type='category'))

        st.plotly_chart(fig, use_container_width=True)
####################################################################################
    # --- Standings Table ---
    st.subheader("Team Standings")
    st.dataframe(standings_df.style.format("{:.1f}"))

    # --- Team Rosters with Images ---
    st.subheader("Team Rosters")

    for team in roster_df.columns:
        st.markdown(f"### {team}")
        players = roster_df[team].dropna().tolist()
        cols = st.columns(len(players))

        for i, player in enumerate(players):
            info = player_images[player_images["Player"] == player]
            if not info.empty:
                url = info["Image"].values[0]
                eliminated = info["Eliminated"].values[0] == "Yes"
                with cols[i]:
                    if eliminated:
                        img = overlay_red_x(url)
                        st.image(img, caption=player, width=130)
                    else:
                        st.image(url, caption=player, width=130)
