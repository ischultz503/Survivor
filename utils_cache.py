# -*- coding: utf-8 -*-
"""
Created on Thu Oct  9 15:03:06 2025

@author: IsaacSchultz
"""

import os
import hashlib
import pandas as pd
import streamlit as st

def _file_fingerprint(path):
    try:
        stat = os.stat(path)
        raw = f"{stat.st_size}-{stat.st_mtime}"
        return hashlib.md5(raw.encode()).hexdigest()
    except FileNotFoundError:
        return "missing"

@st.cache_data(show_spinner=False)
def cache_df(base_key: str, df: pd.DataFrame, file_path: str):
    
    fingerprint = _file_fingerprint(file_path)
    full_key = f"{base_key}|{fingerprint}"
    return df.copy()

@st.cache_data(show_spinner=False)
def read_excel(path, sheet_name):
    return pd.read_excel(path, sheet_name=sheet_name)

@st.cache_data(show_spinner=False)
def read_csv(path):
    return pd.read_csv(path)


@st.cache_resource(show_spinner=False)
def cache_obj(key: str, obj):
    return obj
