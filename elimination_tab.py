# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 13:09:55 2025

@author: IsaacSchultz
"""

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def eliminations_tab():
    st.header("Player Eliminations")
    
    def overlay_red_x(image_url):
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    
        draw = ImageDraw.Draw(img)
    
        width, height = img.size
        line_width = int(width * 0.08)
    
        # Draw red X across the image
        draw.line((0, 0, width, height), fill=(255, 0, 0, 255), width=line_width)
        draw.line((width, 0, 0, height), fill=(255, 0, 0, 255), width=line_width)
    
        return img
    
    season = st.session_state["season"]

    # File paths per season
    if season == "Season 47":
        score_file = "data/PointsScored_Survivor_47.xlsx"
        image_file = "data/Player_images_S47_Survivor.csv"
    elif season == "Season 48":
        score_file = "data/PointsScored_Survivor_48.xlsx"
        image_file = "data/Player_images_S48_Survivor.csv"

    # Load data
    elim_table = pd.read_excel(score_file, sheet_name="Elimination_Table")
    player_images = pd.read_csv(image_file)

    # Merge to get image URLs
    merged = pd.merge(elim_table, player_images, on="Player", how="left")
    merged = merged.dropna(subset=["Image"])

    # Separate out numeric and string week values
    string_weeks = merged[~merged["Week"].apply(lambda x: str(x).isdigit())]
    numeric_weeks = merged[merged["Week"].apply(lambda x: str(x).isdigit())]
    numeric_weeks["Week"] = numeric_weeks["Week"].astype(int)
    numeric_weeks = numeric_weeks.sort_values("Week")

    # Combine sorted string and numeric weeks
    full_weeks = pd.concat([string_weeks, numeric_weeks], ignore_index=True)

    st.markdown("Players eliminated each week are shown below.")

    # Display grid by week label
    for week_label in full_weeks["Week"].unique():
        week_df = full_weeks[full_weeks["Week"] == week_label]
        st.subheader(str(week_label))
        cols = st.columns(len(week_df))

        for i, (_, row) in enumerate(week_df.iterrows()):
            with cols[i]:
                st.image(row["Image"], caption=f"❌ {row['Player']}", width=130)
