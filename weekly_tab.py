# -*- coding: utf-8 -*-
"""
Weekly Tab - Bonus points, question responses, and team accuracy
"""

import streamlit as st
import pandas as pd
import plotly.express as px

def weekly_tab():
    st.header("Weekly Bonus Questions")

    season = st.session_state["season"]

    # --- Load bonus points ---
    def load_weekly_picks():
        if season == 'Season 47':
            return pd.read_excel("data/PointsScored_Survivor_47.xlsx", sheet_name="Weekly_Pick_Scores")
        if season == 'Season 48':
            return pd.read_excel("data/PointsScored_Survivor_48.xlsx", sheet_name="Weekly_Pick_Scores")

    df = load_weekly_picks()
    df = df.fillna(0)  # 👈 convert any missing values to 0
    df["Week"] = df["Week"].astype(str)  # 👈 make Week a string so it's consistent

    st.markdown("These are bonus points awarded to teams each week based on prediction questions or other bonuses.")

    # --- Toggle for bonus chart view ---
    view_type = st.radio("Bonus Chart View", ["Weekly", "Cumulative"], horizontal=True)
    st.subheader(f"{view_type} Bonus Points by Team")
    
    df["Week"] = df["Week"].astype(str)
    df_long = df.melt(id_vars="Week", var_name="Team", value_name="Bonus Points")
    df_long["Week"] = df_long["Week"].astype(str)

    if view_type == "Cumulative":
        df_long["Bonus Points"] = df_long.sort_values("Week").groupby("Team")["Bonus Points"].cumsum()

    fig = px.bar(
        df_long,
        x="Week",
        y="Bonus Points",
        color="Team",
        barmode="group",
        text="Bonus Points"
    )
    fig.update_layout(height=450, xaxis=dict(type='category'))
    st.plotly_chart(fig, use_container_width=True)

    # --- Raw bonus table with totals ---
    st.subheader("Bonus Points Table")

    df_display = df.copy()
    df_display = df_display.fillna(0)  # 👈 again just to be safe
    df_display["Week"] = df_display["Week"].astype(str)
    totals = df_display.drop(columns="Week").sum().to_frame().T
    totals["Week"] = "Total"
    df_full = pd.concat([df_display, totals], ignore_index=True)
    st.dataframe(df_full.set_index("Week"), use_container_width=True)

    # --- Weekly Question Responses ---
    st.subheader("Team Answers to Weekly Questions")

    def load_question_answers():
        if season == 'Season 47':
            return pd.read_excel("data/PointsScored_Survivor_47.xlsx", sheet_name="Weekly_Questions")
        if season == 'Season 48':
            return pd.read_excel("data/PointsScored_Survivor_48.xlsx", sheet_name="Weekly_Questions")

    qa_df = load_question_answers()
    qa_df["Is Voided"] = qa_df["Is Voided"].fillna(False)
    teams = [col for col in qa_df.columns if col not in ["Week", "Question", "Correct Answer", "Is Voided"]]
    qa_df["Week"] = qa_df["Week"].astype(str)

    # Week selector
    selected_week = st.selectbox("Select a week", sorted(qa_df["Week"].unique()))
    week_df = qa_df[qa_df["Week"] == selected_week].copy()
    week_df = week_df.sort_values("Question")

    # --- Style answers ---
    full_week_df = week_df.copy()
    week_display = full_week_df.drop(columns=["Is Voided",'Week'])

    def highlight_answers(row):
        styles = []
        is_voided = full_week_df.loc[row.name, "Is Voided"]
        correct_answer = full_week_df.loc[row.name, "Correct Answer"]

        for col in row.index:
            if is_voided:
                styles.append("background-color: lightgray")
            elif col in teams:
                if row[col] == correct_answer:
                    styles.append("background-color: lightgreen")
                else:
                    styles.append("background-color: lightcoral")
            else:
                styles.append("")
        return styles

    styled = week_display.style.apply(highlight_answers, axis=1).set_table_styles(
        [{"selector": "td", "props": [("font-size", "12px")]}]
    )
    st.table(styled)

    # --- Overall Accuracy Chart (Single Bar per Team) ---
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
