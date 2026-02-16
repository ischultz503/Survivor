import streamlit as st

from fantasy_backend import (
    authenticate_user,
    init_db,
    list_events_for_season,
    list_leagues,
    list_players_for_season,
    list_seasons,
    list_teams_for_league_season,
    upsert_player_event,
    upsert_weekly_bonus,
)

st.set_page_config(page_title="Fantasy Survivor Admin", page_icon="🛠️", layout="wide")
init_db(force_seed=True)

st.title("🛠️ Fantasy Survivor Admin Console")
st.caption("Use this private app to record weekly events and question bonus points.")

if "admin" not in st.session_state:
    st.session_state.admin = None

if st.session_state.admin is None:
    with st.form("admin_login"):
        username = st.text_input("Admin username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    if submit:
        user = authenticate_user(username, password)
        if user and user["is_admin"]:
            st.session_state.admin = user
            st.success("Authenticated")
            st.rerun()
        st.error("Admin credentials required.")
    st.info("Default seeded admin is `admin` / `admin123`. Change this immediately.")
    st.stop()

with st.sidebar:
    st.success(f"Signed in as {st.session_state.admin['username']}")

season = st.selectbox("Season", list_seasons())

col1, col2 = st.columns(2)
with col1:
    st.subheader("Player event scoring")
    with st.form("player_event_form"):
        player = st.selectbox("Player", list_players_for_season(season))
        week = st.number_input("Week", min_value=1, max_value=30, value=1, step=1)
        event = st.selectbox("Event", list_events_for_season(season))
        value = st.number_input("Event count/value", value=0.0, step=1.0)
        submit_event = st.form_submit_button("Save event value")

    if submit_event:
        upsert_player_event(season, int(week), player, event, float(value))
        st.success("Player event saved.")

with col2:
    st.subheader("Weekly question / bonus points")
    with st.form("weekly_bonus_form"):
        league = st.selectbox("League", list_leagues())
        team = st.selectbox("Team", list_teams_for_league_season(league, season))
        week_bonus = st.number_input("Week", min_value=1, max_value=30, value=1, step=1, key="week_bonus")
        points = st.number_input("Bonus points", value=0.0, step=1.0)
        submit_bonus = st.form_submit_button("Save weekly bonus")

    if submit_bonus:
        upsert_weekly_bonus(league, season, team, int(week_bonus), float(points))
        st.success("Weekly bonus saved.")

st.markdown("---")
st.caption("All updates are stored in `data/fantasy_survivor.db` and sync instantly with the main app.")
