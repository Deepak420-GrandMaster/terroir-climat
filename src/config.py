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

# Study period. 1950 rather than 1900 because département boundaries and the
# Paris region were reorganised in 1968 and earlier records are patchier;
# ERA5 reanalysis also starts in 1940, so 1950 leaves a clean margin.
YEAR_MIN = 1950
YEAR_MAX = 2018

# Baseline for "normal". The WMO standard reference period.
NORMAL_START = 1961
NORMAL_END = 1990

# Season windows, as inclusive month ranges.
SEASONS: dict[str, tuple[int, int]] = {
    "Apr – Jul (cereals)": (4, 7),
    "Mar – Jun (early)": (3, 6),
    "Apr – Sep (full season)": (4, 9),
    "May – Aug (summer crops)": (5, 8),
    "Jan – Dec (calendar year)": (1, 12),
}
DEFAULT_SEASON = "Apr – Jul (cereals)"

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

# Fetch batching. Kept small deliberately: the free tier's limits are not
# published, so the script trades a few more requests for a lower chance of
# being throttled, and caches every chunk so a failure resumes rather than
# restarts.
COORDS_PER_CALL = 8
YEARS_PER_CALL = 10
