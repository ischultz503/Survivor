# -*- coding: utf-8 -*-
"""
Created on Thu Oct  9 15:03:06 2025

@author: IsaacSchultz
"""

import pandas as pd
import streamlit as st

# File reads (cached)
@st.cache_data(show_spinner=False)
def read_excel(path, sheet_name):
    return pd.read_excel(path, sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def read_csv(path):
    return pd.read_csv(path)

# Derivations (cache any expensive table by a simple key)
@st.cache_data(show_spinner=False)
def cache_df(key: str, df: pd.DataFrame):
    return df.copy()

# Lightweight object cache (e.g., image bytes, rosters)
@st.cache_resource(show_spinner=False)
def cache_obj(key: str, obj):
    return obj
