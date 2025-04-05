import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from stats_data import fetch_player_stats_by_name, extract_player_data


# Constants
APP_TITLE = "Player Comparison Dashboard"
DEFAULT_YEAR = 2023


# Functions
def fetch_player_data(player_name, year):
    player_data = fetch_player_stats_by_name(player_name, year)
    return extract_player_data(player_data)


def create_comparison_df(player1, player2):
    return pd.DataFrame({
        "Player": [player1.get("name", "Unknown"), player2.get("name", "Unknown")],
        "Age": [player1.get("age", 0), player2.get("age", 0)],
        "Height": [player1.get("height", 0), player2.get("height", 0)],
        "Weight": [player1.get("weight", 0), player2.get("weight", 0)]
    })


def create_league_stats_df(player1, player2):
    league_stats = []
    if player1 and "leagues" in player1:
        for league in player1["leagues"]:
            league_stats.append({
                "Player": player1["name"],
                "League": league["league_name"],
                "Team": league["team_name"],
                "Appearances": league["appearences"],
                "Goals": league["goals"],
                "Assists": league["assists"]
            })
    if player2 and "leagues" in player2:
        for league in player2["leagues"]:
            league_stats.append({
                "Player": player2["name"],
                "League": league["league_name"],
                "Team": league["team_name"],
                "Appearances": league["appearences"],
                "Goals": league["goals"],
                "Assists": league["assists"]
            })
    return pd.DataFrame(league_stats)


def main():
    st.title(APP_TITLE)

    # Player selection
    with st.form("comparison_form"):
        player1_name = st.text_input("Player 1")
        player2_name = st.text_input("Player 2")
        year = st.selectbox("Year", range(2024, 2012, -1), index=12)
        submit_button = st.form_submit_button("Compare")

    # Fetch player data
    if submit_button:
        player1 = fetch_player_data(player1_name, year)
        player2 = fetch_player_data(player2_name, year)

        # Comparison stats
        comparison_df = create_comparison_df(player1, player2)
        st.subheader("Comparison Stats")
        st.dataframe(comparison_df, height=300)

        # League stats
        league_stats_df = create_league_stats_df(player1, player2)
        st.subheader("League Stats")
        st.dataframe(league_stats_df, height=500)

        # Visual comparisons
        st.subheader("Visual Comparisons")
        goals_df = league_stats_df[["Player", "Goals"]]
        goals_fig = px.bar(goals_df, x="Player", y="Goals", title="Goals Comparison")
        st.plotly_chart(goals_fig, use_container_width=True)

        assists_df = league_stats_df[["Player", "Assists"]]
        assists_fig = px.bar(asserts_df, x="Player", y="Assists", title="Assists Comparison")
        st.plotly_chart(assists_fig, use_container_width=True)


if __name__ == "__main__":
    main()