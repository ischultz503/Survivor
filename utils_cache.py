# utils_cache.py

import os
import hashlib
from typing import Any, Optional

import pandas as pd
import streamlit as st


# ---------- File fingerprint helper (optional, if you want it later) ----------

def file_fingerprint(path: str) -> str:
    """
    Return a simple fingerprint string for a file based on size + mtime.
    Safe to call even if the file does not exist.
    """
    try:
        stat = os.stat(path)
        raw = f"{stat.st_size}-{stat.st_mtime}"
        return hashlib.md5(raw.encode()).hexdigest()
    except FileNotFoundError:
        return "missing"


# ---------- Cached readers ----------

@st.cache_data(show_spinner=False)
def read_excel(path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Thin wrapper around pandas.read_excel with Streamlit caching.
    """
    return pd.read_excel(path, sheet_name=sheet_name)


@st.cache_data(show_spinner=False)
def read_csv(path: str) -> pd.DataFrame:
    """
    Thin wrapper around pandas.read_csv with Streamlit caching.
    """
    return pd.read_csv(path)


# ---------- DataFrame cache helper ----------

@st.cache_data(show_spinner=False)
def _cache_df_internal(full_key: str, df: pd.DataFrame) -> pd.DataFrame:
    # Streamlit will cache on (full_key, df) arguments automatically.
    # We just return a copy so callers can't mutate the cached version.
    return df.copy()


def cache_df(
    full_key: str,
    df: pd.DataFrame,
    file_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Cache a DataFrame under a given key.

    full_key  – logical cache key (you already build things like f"{league}|{season}|…")
    df        – DataFrame to store
    file_path – optional; only included so existing calls like
                cache_df(key, df, file_path=scores_file_path) keep working.
                It isn't used directly here but will participate in Streamlit's
                argument-based caching if you need that later.
    """
    # We *could* build a combined key with file_path/fingerprint here,
    # but it's not strictly necessary.
    return _cache_df_internal(full_key, df)


# ---------- Generic object cache (for images, etc.) ----------

@st.cache_resource(show_spinner=False)
def _obj_store() -> dict:
    """
    A single cached dictionary we can use to store arbitrary Python objects.
    """
    return {}


def cache_obj(key: str, value: Optional[Any]) -> Optional[Any]:
    """
    Simple get/set wrapper around a cached object store.

    - If value is None  -> return any previously cached object for `key`
    - If value is not None -> store it under `key` and return it
    """
    store = _obj_store()
    if value is None:
        return store.get(key)
    store[key] = value
    return value
