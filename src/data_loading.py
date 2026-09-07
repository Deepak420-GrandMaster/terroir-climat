"""Cached loaders. The only module that imports Streamlit."""

from __future__ import annotations

import json
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .climate import add_normals, drop_partial_years, season_totals
from .config import CENTROIDS, GEOJSON, MONTHLY


@dataclass(frozen=True)
class DataState:
    """What the app has to work with, so the UI can be honest about gaps."""

    has_geometry: bool
    has_climate: bool
    n_departements: int = 0
    year_min: int | None = None
    year_max: int | None = None
    message: str = ""

    @property
    def ready(self) -> bool:
        return self.has_geometry and self.has_climate


@st.cache_data(show_spinner=False)
def load_geojson() -> dict | None:
    if not GEOJSON.exists():
        return None
    return json.loads(GEOJSON.read_text())


@st.cache_data(show_spinner=False)
def load_departements() -> pd.DataFrame:
    if not CENTROIDS.exists():
        return pd.DataFrame(columns=["code", "nom", "lat", "lon"])
    return pd.read_csv(CENTROIDS, dtype={"code": str}).sort_values("nom")


@st.cache_data(show_spinner="Reading the climate table…")
def load_monthly() -> pd.DataFrame | None:
    if not MONTHLY.exists():
        return None
    return pd.read_parquet(MONTHLY)


@st.cache_data(show_spinner=False)
def load_seasonal(months: tuple[int, int]) -> tuple[pd.DataFrame, list[int]]:
    """Seasonal water balance with each département's own normal attached.

    Years that only part of the country covers are withheld — see
    :func:`drop_partial_years` — and returned separately so the app can say so.
    """
    monthly = load_monthly()
    if monthly is None or monthly.empty:
        return pd.DataFrame(), []
    seasonal, pending = drop_partial_years(add_normals(season_totals(monthly, months)))
    return seasonal, pending


def describe_state() -> DataState:
    geo = load_geojson()
    deps = load_departements()
    monthly = load_monthly()

    if geo is None or deps.empty:
        return DataState(
            has_geometry=False,
            has_climate=False,
            message="Boundary files are missing. Run `python scripts/prepare_geography.py`.",
        )
    if monthly is None or monthly.empty:
        return DataState(
            has_geometry=True,
            has_climate=False,
            n_departements=len(deps),
            message="The climate table has not been built yet.",
        )
    return DataState(
        has_geometry=True,
        has_climate=True,
        n_departements=int(monthly["code"].nunique()),
        year_min=int(monthly["year"].min()),
        year_max=int(monthly["year"].max()),
    )
