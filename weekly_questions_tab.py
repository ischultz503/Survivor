# -*- coding: utf-8 -*-
"""
Weekly Tab - Bonus points, question responses, and team accuracy
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from utils_cache import read_excel, cache_df
import numpy as np

def clean_week_column(series: pd.Series) -> pd.Series:
    wk = pd.to_numeric(pd.Series(series).astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    return wk.astype("Int64")  # keep as nullable int for all joins/filters/sorts

def weekly_questions_tab():
    scores_file_path = st.session_state["paths"]["scores"]
    
    season = st.session_state["season"]
    league = st.session_state["league"]

    st.header("Weekly Bonus Questions")

    # ---------- LOAD: Weekly bonus ----------
    def load_weekly_picks():
        if season == 'Season 47':
            return read_excel("data/PointsScored_Survivor_47.xlsx", "Weekly_Pick_Scores")
        if season == 'Season 48':
            return read_excel("data/PointsScored_Survivor_48.xlsx", "Weekly_Pick_Scores")
        if season == 'Season 49':
            if league == 'Bi-coastal Elites':
                return read_excel("data/east/Survivor_49_East.xlsx", "Weekly_Pick_Scores")
            else:
                return read_excel("data/PointsScored_Survivor_49.xlsx", "Weekly_Pick_Scores")

    df = load_weekly_picks().copy()
    df = df.fillna(0)
    df["Week"] = clean_week_column(df["Week"])
    team_cols = [c for c in df.columns if c != "Week"]
    df[team_cols] = df[team_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    st.markdown("Points earned for correct answers to the weekly questions")

    # Toggle for bonus chart view
    view_type = st.radio("Bonus Chart View", ["Weekly", "Cumulative"], horizontal=True, key="wq_view_type")
    st.subheader(f"{view_type} Bonus Points by Team")

    # Use a display label for x-axis but keep numeric Week underneath
    df_long = df.melt(id_vars="Week", var_name="Team", value_name="Bonus Points")
    key_bonus_long = f"{league}|{season}|bonus_long"
    df_long = cache_df(key_bonus_long, df_long, file_path=scores_file_path)


    if view_type == "Cumulative":
        df_long = df_long.sort_values(["Team", "Week"])
        df_long["Bonus Points"] = df_long.groupby("Team")["Bonus Points"].cumsum()

    fig = px.bar(
        df_long.assign(WeekLabel=lambda x: x["Week"].astype("Int64").astype(str)),
        x="WeekLabel",
        y="Bonus Points",
        color="Team",
        barmode="group",
        text="Bonus Points"
    )
    fig.update_layout(height=450, xaxis=dict(type='category'))
    st.plotly_chart(fig, use_container_width=True)

    # Raw bonus table + totals
    st.subheader("Bonus Points Table")
    df_display = df.copy()
    totals = df_display.drop(columns="Week").sum().to_frame().T
    totals["Week"] = pd.NA
    df_full = pd.concat([df_display, totals], ignore_index=True)
    df_full = df_full.assign(WeekLabel=lambda x: x["Week"].astype("Int64").astype(str).where(x["Week"].notna(), "Total"))
    st.dataframe(df_full.drop(columns=["Week"]).set_index("WeekLabel"), use_container_width=True)

    # ---------- LOAD: Weekly Q&A ----------
    st.subheader("Answers to Weekly Questions")

    def load_question_answers():
        if season == 'Season 47':
            return read_excel("data/PointsScored_Survivor_47.xlsx", "Weekly_Questions")
        if season == 'Season 48':
            return read_excel("data/PointsScored_Survivor_48.xlsx", "Weekly_Questions")
        if season == 'Season 49':
            if league == 'Bi-coastal Elites':
                return read_excel("data/east/Survivor_49_East.xlsx", "Weekly_Questions")
            else:
                return read_excel("data/PointsScored_Survivor_49.xlsx", "Weekly_Questions")

    qa_df = load_question_answers().copy()

    # Clean weeks ONCE, keep as Int64
    qa_df["Week"] = clean_week_column(qa_df["Week"])

    # Team columns, flags, and normalization
    qa_df = qa_df.rename(columns=lambda c: c.strip())
    non_team_cols = ["Week", "Question", "Correct Answer", "Is Voided"]
    teams = [c for c in qa_df.columns if c not in non_team_cols]

    qa_df["Is Voided"] = (
        qa_df["Is Voided"]
        .astype(str).str.strip().str.lower()
        .map({"yes": True, "y": True, "true": True, "1": True,
              "no": False, "n": False, "false": False, "0": False})
        .fillna(False)
    )

    # --- Week selector (SINGLE widget; keep weeks numeric) ---
    week_options = (
        qa_df["Week"].dropna().astype(int).sort_values().unique().tolist()
    )
    selected_week = st.selectbox(
        "Select a week",
        week_options,
        index=(len(week_options) - 1) if week_options else 0,
        key="wq_week_select"
    )
    wk = int(selected_week)

    # Filter data for the chosen week
    week_df = qa_df.loc[qa_df["Week"] == wk].copy().sort_values("Question")

    # ---------- Style answers ----------
    def _normalize_answers(val):
        if pd.isna(val):
            return set()
        if isinstance(val, (list, tuple, set)):
            return {str(x).strip() for x in val}
        if isinstance(val, str):
            parts = [p.strip() for p in re.split(r"[,/;]", val) if p.strip()]
            return set(parts if parts else [val.strip()])
        return {str(val).strip()}

    full_week_df = week_df.copy()
    display_df = week_df.drop(columns=["Is Voided", "Week"])

    def highlight_answers(row):
        styles = []
        is_voided = bool(full_week_df.loc[row.name, "Is Voided"])
        correct_list = _normalize_answers(full_week_df.loc[row.name, "Correct Answer"])
        for col in row.index:
            if is_voided:
                styles.append("background-color: lightgray")
            elif col in teams:
                cell = str(row[col]).strip()
                styles.append("background-color: lightgreen" if cell in correct_list
                              else "background-color: lightcoral")
            else:
                styles.append("")
        return styles

    styled = display_df.style.apply(highlight_answers, axis=1).set_table_styles(
        [{"selector": "td", "props": [("font-size", "12px")]}]
    )
    st.table(styled)

    # ---------- Overall Accuracy ----------
    st.subheader("Overall Team Accuracy")
    valid_df = qa_df[qa_df["Is Voided"] == False].copy()
    team_accuracy = (
        valid_df[teams]
        .eq(valid_df["Correct Answer"], axis=0)
        .sum()
        .reset_index(name="Correct")
        .rename(columns={"index": "Team"})
    )
    team_accuracy["Total"] = len(valid_df)
    team_accuracy["Accuracy"] = team_accuracy["Correct"] / team_accuracy["Total"]

    fig3 = px.bar(
        team_accuracy,
        x="Team",
        y="Accuracy",
        text=team_accuracy["Accuracy"].apply(lambda x: f"{x:.0%}"),
        color="Team"
    )
    fig3.update_layout(yaxis_tickformat=".0%", height=400)
    st.plotly_chart(fig3, use_container_width=True)
