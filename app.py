import streamlit as st
import plotly.express as px

from fantasy_backend import (
    assign_team,
    authenticate_user,
    build_team_dashboard,
    init_db,
    list_all_teams,
    list_league_season_options_for_user,
    register_user,
)

st.set_page_config(page_title="Fantasy Survivor", page_icon="🏝️", layout="wide")
init_db(force_seed=True)

st.title("🏝️ Fantasy Survivor League Hub")
st.caption("A modern fantasy dashboard for standings, player/team performance, bonuses, and eliminations.")

if "user" not in st.session_state:
    st.session_state.user = None


def login_panel() -> None:
    tab_login, tab_register = st.tabs(["Login", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign in")
        if submit:
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome back, {user['username']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("New username")
            password = st.text_input("New password", type="password")
            submit = st.form_submit_button("Create account")
        if submit:
            ok, msg = register_user(username, password)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


if st.session_state.user is None:
    login_panel()
    st.stop()

user = st.session_state.user
with st.sidebar:
    st.header(f"👋 {user['username']}")
    if st.button("Log out"):
        st.session_state.user = None
        st.rerun()

user_teams = list_league_season_options_for_user(user["id"])
if user_teams.empty:
    st.warning("You do not have a team assigned yet. Ask an admin to link your team, or self-link below.")
    with st.expander("Link an existing team to your account"):
        team_df = list_all_teams()
        team_df["label"] = team_df["season_label"] + " • " + team_df["league_name"] + " • " + team_df["team_name"]
        choice = st.selectbox("Team", team_df["label"])
        if st.button("Link this team"):
            row = team_df[team_df["label"] == choice].iloc[0]
            ok, msg = assign_team(user["username"], row["league_name"], row["season_label"], row["team_name"])
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    st.stop()

user_teams["label"] = (
    user_teams["season_label"] + " • " + user_teams["league_name"] + " • " + user_teams["team_name"]
)
selected_label = st.sidebar.selectbox("Select your team", user_teams["label"].tolist())
selected_team = user_teams[user_teams["label"] == selected_label].iloc[0]

data = build_team_dashboard(int(selected_team["team_id"]))
meta = data["meta"].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Team", meta["team_name"])
col2.metric("Current Week", data["current_week"])
col3.metric("Total Points", f"{data['total']:.1f}")

tab_team, tab_players, tab_bonus, tab_elims, tab_events = st.tabs(
    ["Team Performance", "Player Performance", "Bonus Questions", "Eliminations", "Event Details"]
)

with tab_team:
    st.subheader("Standings")
    standings = data["standings"].copy()
    standings["Rank"] = standings["total_points"].rank(ascending=False, method="min").astype(int)
    standings = standings[["Rank", "team_name", "total_points"]].rename(
        columns={"team_name": "Team", "total_points": "Points"}
    )
    st.dataframe(standings, use_container_width=True)

    weekly = data["weekly"]
    if not weekly.empty:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Cumulative Trend")
            fig = px.line(weekly, x="week_number", y="cumulative_total", markers=True)
            fig.update_layout(xaxis_title="Week", yaxis_title="Cumulative Points", height=380)
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.subheader("Weekly Team Breakdown")
            melted = weekly.melt(
                id_vars=["week_number"],
                value_vars=["player_points", "bonus_points"],
                var_name="source",
                value_name="points",
            )
            fig2 = px.bar(melted, x="week_number", y="points", color="source", barmode="group")
            fig2.update_layout(xaxis_title="Week", yaxis_title="Points", height=380)
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Raw weekly scoring data"):
            st.dataframe(weekly, use_container_width=True)
    else:
        st.info("No weekly data is available yet for this team.")

with tab_players:
    st.subheader("Player Totals")
    player_totals = data["player_totals"]
    if not player_totals.empty:
        st.dataframe(player_totals, use_container_width=True)
        fig = px.bar(player_totals, x="Player", y="Total Points", color="Player")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No individual player points are available yet.")

    st.subheader("Weekly Player Performance")
    player_weekly = data["player_weekly"]
    if not player_weekly.empty:
        fig = px.line(
            player_weekly,
            x="week_number",
            y="points",
            color="player_name",
            markers=True,
            labels={"week_number": "Week", "points": "Points", "player_name": "Player"},
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(player_weekly, use_container_width=True)
    else:
        st.info("No weekly player data available.")

with tab_bonus:
    st.subheader("Weekly Bonus Question Results")
    bonus = data["bonus_weekly"].rename(columns={"week_number": "Week", "points": "Bonus Points"})
    if not bonus.empty:
        st.dataframe(bonus, use_container_width=True)
        fig = px.bar(bonus, x="Week", y="Bonus Points")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bonus question points have been recorded yet.")

with tab_elims:
    st.subheader("Elimination-related Events")
    elim = data["eliminations"].copy()
    if not elim.empty:
        elim = elim.rename(
            columns={
                "week_number": "Week",
                "player_name": "Player",
                "event_name": "Event",
                "value": "Count",
                "points": "Point Value",
                "event_points": "Points Awarded",
            }
        )
        st.dataframe(elim, use_container_width=True)
    else:
        st.info("No elimination events have been scored yet for this roster.")

with tab_events:
    st.subheader("All Scoring Events")
    events = data["event_breakdown"].copy()
    if not events.empty:
        events = events.rename(
            columns={
                "week_number": "Week",
                "player_name": "Player",
                "event_name": "Event",
                "value": "Count",
                "points": "Point Value",
                "event_points": "Points Awarded",
            }
        )
        st.dataframe(events, use_container_width=True)
    else:
        st.info("No event-level data is available yet.")

st.markdown("---")
st.caption("Admin scoring updates can be entered through `admin_app.py` and are reflected here automatically.")
