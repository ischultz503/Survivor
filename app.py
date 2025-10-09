import streamlit as st
from rules_tab import rules_tab
from standings_tab import standings_tab
from weekly_questions_tab import weekly_questions_tab
from elimination_tab import eliminations_tab
from player_trends import trends_tab


# app.py (sidebar picker)

LEAGUE_SEASONS = {
    "NE Portland": ["Season 49", "Season 48", "Season 47"],
    "Bi-coastal Elites": ["Season 49"],
}

st.sidebar.header("Fantasy Survivor")
def get_paths(league, season):
    if season == "Season 49":
        scores = (
            "data/east/Survivor_49_East.xlsx"
            if league == "Bi-coastal Elites"
            else "data/PointsScored_Survivor_49.xlsx"
        )
        images = "data/Player_images_S49_Survivor.xlsx"
    elif season == "Season 48":
        scores = "data/PointsScored_Survivor_48.xlsx"
        images = "data/Player_images_S48_Survivor.xlsx"
    else:  # 47
        scores = "data/PointsScored_Survivor_47.xlsx"
        images = "data/Player_images_S47_Survivor.xlsx"

    point_values = (
        "data/east/Survivor_49_East.xlsx"
        if league == "Bi-coastal Elites" and season == "Season 49"
        else "data/PointValues_Survivor.csv"
    )

    return {"scores": scores, "images": images, "point_values": point_values}


paths = get_paths(st.session_state["league"], st.session_state["season"])
st.session_state["paths"] = paths

# set once; widgets will manage values afterwards
st.session_state.setdefault("league", "NE Portland")
st.session_state.setdefault("season", LEAGUE_SEASONS[st.session_state["league"]][0])

# 1) Pick league
league = st.sidebar.selectbox("League", list(LEAGUE_SEASONS.keys()), key="league")

# 2) Season depends on league
allowed = LEAGUE_SEASONS[league]
if st.session_state["season"] not in allowed:
    st.session_state["season"] = allowed[0]

season = st.sidebar.selectbox("Season", allowed, key="season")

# (Optional) expose for tabs
st.session_state["selected_league"] = league
st.session_state["selected_season"] = season

# Create tabs for different sections
tab1, tab2 , tab3 , tab4, tab5 = st.tabs(["Scoring System",
                                    "Standings & Rosters",
                                    'Weekly Question Scores',
                                    'Individual Player Data',
                                    'Eliminations by Week'])


with tab1:
    rules_tab()
with tab2:
    standings_tab()
with tab3:
    weekly_questions_tab()
with tab4:
    trends_tab()
with tab5:
    eliminations_tab()

