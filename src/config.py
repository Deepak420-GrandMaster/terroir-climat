"""Project-wide constants. No Streamlit import here, so scripts can use it too."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"

GEOJSON = RAW / "departements.geojson"
CENTROIDS = RAW / "departements_centroids.csv"
MONTHLY = PROCESSED / "monthly_climate.parquet"
CACHE = RAW / "openmeteo_cache"

# Study period. 1961 is the start of the WMO baseline, so nothing earlier is
# used by any figure the app shows. Fetching 1950-1960 cost 16% of the download
# and bought nothing.
YEAR_MIN = 1961
YEAR_MAX = 2018

# Only these months are fetched. The app is about the growing season, so
# October to February was never read by anything — and Open-Meteo's free tier
# meters by data volume, which made that waste the difference between a
# download that finishes and one that hits the ceiling. Every season window
# below sits inside this range; widening one means widening this first and
# refetching.
FETCH_MONTHS = (3, 9)

# Baseline for "normal". The WMO standard reference period.
NORMAL_START = 1961
NORMAL_END = 1990

# Season windows, as inclusive month ranges.
# Keyed by a stable id, not by a display label: the labels are translated in
# src/i18n.py, and a season must not change identity when the language does.
SEASONS: dict[str, tuple[int, int]] = {
    "apr_jul": (4, 7),
    "mar_jun": (3, 6),
    "apr_sep": (4, 9),
    "may_aug": (5, 8),
    "mar_sep": (3, 9),
}
DEFAULT_SEASON = "apr_jul"

# Diverging ramp for water-balance anomaly: dry (warm) -> neutral -> wet (blue).
# A grey midpoint, so "normal" reads as normal rather than as a third colour.
RAMP_DRY_TO_WET = [
    "#8a4407", "#a85f16", "#c07a2e", "#d7a468", "#e0c49a",
    "#c9ccc9",
    "#9dc0dc", "#6ea5cc", "#4f8fc0", "#2a6d9f", "#14507f",
]
ACCENT = "#1f6fb2"
ACCENT_WARM = "#cc6a06"

# Open-Meteo
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARS = ["precipitation_sum", "et0_fao_evapotranspiration"]
TIMEZONE = "Europe/Paris"

# Fetch batching: one call per (batch of départements, single year). The free
# tier meters by data volume rather than request count, so more départements
# per call is free — it is the same bytes in fewer round trips. One year per
# call keeps each cached chunk small, so an interrupted run loses seconds of
# work rather than minutes.
COORDS_PER_CALL = 24
