"""Plotly figures. One scale per axis, no dual axes."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..config import ACCENT, ACCENT_WARM

GRID = "#e7eae7"
INK = "#4b565d"
DRY = "#c07a2e"
WET = "#4f8fc0"


def _layout(fig: go.Figure, height: int, ytitle: str) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="ui-sans-serif, system-ui", size=12, color=INK),
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title=ytitle)
    return fig


def anomaly_bars(seasonal: pd.DataFrame, code: str, name: str) -> go.Figure:
    """Water-balance departure from normal, one bar per year.

    Colour carries the sign, which the axis already shows — but the pairing is
    what makes a run of dry years legible at a glance, and the bar's direction
    keeps the meaning available without colour.
    """
    d = seasonal[seasonal["code"] == code].sort_values("year")
    colours = [DRY if v < 0 else WET for v in d["wb_anom_mm"].fillna(0)]

    fig = go.Figure(
        go.Bar(
            x=d["year"],
            y=d["wb_anom_mm"],
            marker_color=colours,
            marker_line_width=0,
            hovertemplate="%{x}<br>%{y:+.0f} mm vs normal<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_width=1, line_color=INK, opacity=0.45)
    fig.update_layout(title=f"{name} — water balance vs its own 1961–1990 normal")
    return _layout(fig, 260, "mm")


def season_lines(seasonal: pd.DataFrame, code: str, name: str) -> go.Figure:
    """Rainfall and ET0 on one millimetre axis — same unit, so one scale."""
    d = seasonal[seasonal["code"] == code].sort_values("year")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["p_mm"], name="Rainfall",
        line=dict(color=ACCENT, width=2),
        hovertemplate="%{x}<br>rain %{y:.0f} mm<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["et0_mm"], name="ET₀",
        line=dict(color=ACCENT_WARM, width=2, dash="dot"),
        hovertemplate="%{x}<br>ET₀ %{y:.0f} mm<extra></extra>"))
    fig.update_layout(
        title=f"{name} — rainfall and reference evapotranspiration",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return _layout(fig, 260, "mm per season")


def national_series(seasonal: pd.DataFrame) -> go.Figure:
    """The country-wide median anomaly, so single years have a reference."""
    d = (
        seasonal.groupby("year", as_index=False)
        .agg(median_anom=("wb_anom_mm", "median"))
        .sort_values("year")
    )
    colours = [DRY if v < 0 else WET for v in d["median_anom"].fillna(0)]
    fig = go.Figure(go.Bar(
        x=d["year"], y=d["median_anom"], marker_color=colours, marker_line_width=0,
        hovertemplate="%{x}<br>national median %{y:+.0f} mm<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=INK, opacity=0.45)
    fig.update_layout(title="National median water-balance anomaly")
    return _layout(fig, 230, "mm")
