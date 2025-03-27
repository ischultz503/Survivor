import streamlit as st
from rules_tab import rules_tab
from standings_tab import standings_tab
from weekly_tab import weekly_tab
from elimination_tab import eliminations_tab
from player_trends import trends_tab


# Sidebar
st.sidebar.header("Fantasy Survivor")
st.sidebar.markdown("""
Pick your **season** and **league** to see standings, rosters, individual player performance, answers
to weekly questions and more.
""")

season = st.sidebar.selectbox("Season", ["Season 48",'Season 47'])
league = st.sidebar.selectbox("League", ["NE Portland"])
st.session_state["season"] = season
st.session_state["league"] = league

# Create tabs for different sections
tab1, tab2 , tab3 , tab4, tab5 = st.tabs(["Scoring System",
                                    "Standings & Rosters",
                                    'Weekly Question Scores',
                                    'Individual Player Data',
                                    'Elminiations by Week'])


with tab1:
    rules_tab()
with tab2:
    standings_tab()
with tab3:
    weekly_tab()
with tab4:
    trends_tab()
with tab5:
    eliminations_tab()

