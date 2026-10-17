"""Cached climate lookups shared by the pages."""
from dataclasses import asdict

import streamlit as st

from engine import fallback_climate, fetch_climate


@st.cache_data(ttl=24 * 3600, show_spinner="Fetching sunshine data from NASA POWER…")
def climate_for(lat: float, lon: float, country: str, live: bool = True) -> dict:
    if live:
        return asdict(fetch_climate(lat, lon, country))
    return asdict(fallback_climate(lat, lon, "Built-in values chosen.", country))
