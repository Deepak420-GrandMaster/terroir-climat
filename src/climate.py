"""Turning daily readings into the numbers the map shows.

The stored table is monthly, not seasonal, on purpose: any season window the
app offers is then a sum over months, so changing the window costs nothing and
needs no refetch.

The water balance here is the simple climatic one, P − ET0: how much rain fell
against how much the atmosphere could have evaporated from a well-watered
reference grass surface. It is not a soil water balance — no runoff, no
drainage, no rooting depth, no soil storage — and it is not a drought index.
It is the cheapest honest measure of whether a season was wet or dry *for that
place*, which is exactly what an anomaly against that place's own normal asks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import NORMAL_END, NORMAL_START


def daily_to_monthly(records: list[dict]) -> pd.DataFrame:
    """Collapse Open-Meteo daily blocks to one row per département-year-month."""
    frames = []
    for rec in records:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(rec["time"]),
                "p_mm": rec["precipitation_sum"],
                "et0_mm": rec["et0_fao_evapotranspiration"],
            }
        )
        df["code"] = rec["code"]
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["code", "year", "month", "p_mm", "et0_mm", "days"])

    daily = pd.concat(frames, ignore_index=True)
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month

    monthly = (
        daily.groupby(["code", "year", "month"], as_index=False)
        .agg(p_mm=("p_mm", "sum"), et0_mm=("et0_mm", "sum"), days=("date", "size"))
        .sort_values(["code", "year", "month"])
        .reset_index(drop=True)
    )
    monthly["p_mm"] = monthly["p_mm"].round(2)
    monthly["et0_mm"] = monthly["et0_mm"].round(2)
    return monthly


def season_totals(monthly: pd.DataFrame, months: tuple[int, int]) -> pd.DataFrame:
    """Sum a month window to one row per département-year.

    A window that wraps the new year (e.g. Oct–Mar) is not supported; every
    season this app offers sits inside one calendar year, and silently getting
    a wrapped window wrong would be worse than refusing it.
    """
    first, last = months
    if first > last:
        raise ValueError(
            f"season window {months} wraps the calendar year, which is not supported"
        )
    sel = monthly[monthly["month"].between(first, last)]
    out = (
        sel.groupby(["code", "year"], as_index=False)
        .agg(p_mm=("p_mm", "sum"), et0_mm=("et0_mm", "sum"), months=("month", "nunique"))
    )
    # Drop part-seasons: a year missing months would look artificially dry.
    expected = last - first + 1
    out = out[out["months"] == expected].drop(columns="months")
    out["wb_mm"] = (out["p_mm"] - out["et0_mm"]).round(2)
    return out.reset_index(drop=True)


def add_normals(
    seasonal: pd.DataFrame,
    start: int = NORMAL_START,
    end: int = NORMAL_END,
    min_years: int = 20,
) -> pd.DataFrame:
    """Attach each département's own baseline, and the anomaly against it.

    ``wb_anom_mm`` is the millimetre departure from that département's normal.
    ``wb_z`` standardises it by the baseline's own spread, which is what makes
    a dry year in Finistère comparable to a dry year in Marne.
    """
    base = seasonal[seasonal["year"].between(start, end)]
    norms = base.groupby("code").agg(
        wb_normal=("wb_mm", "mean"),
        wb_sd=("wb_mm", "std"),
        p_normal=("p_mm", "mean"),
        et0_normal=("et0_mm", "mean"),
        baseline_years=("year", "nunique"),
    )
    # A baseline built on a handful of years is not a normal; blank it instead
    # of quietly publishing an anomaly nobody should trust.
    norms.loc[norms["baseline_years"] < min_years, ["wb_normal", "wb_sd"]] = np.nan

    out = seasonal.merge(norms, on="code", how="left")
    out["wb_anom_mm"] = (out["wb_mm"] - out["wb_normal"]).round(2)
    sd = out["wb_sd"].replace(0, np.nan)
    out["wb_z"] = (out["wb_anom_mm"] / sd).round(3)
    return out


def drop_partial_years(
    seasonal: pd.DataFrame, min_share: float = 0.9
) -> tuple[pd.DataFrame, list[int]]:
    """Remove years that only some départements have.

    A partial download leaves years covering a handful of départements — the
    first batch fetched before the API cut the run off. Those years are not
    wrong, but a map of them is: it shows a quarter of France coloured and the
    rest blank, which reads as "no data there" rather than "not downloaded
    yet". Better to hide the year than to publish a map that misleads.

    Returns the filtered frame and the years removed, so the app can say how
    many are still pending rather than quietly showing fewer.
    """
    if seasonal.empty:
        return seasonal, []
    full = seasonal["code"].nunique()
    per_year = seasonal.groupby("year")["code"].nunique()
    keep = per_year[per_year >= full * min_share].index
    dropped = sorted(set(per_year.index) - set(keep))
    return seasonal[seasonal["year"].isin(keep)].reset_index(drop=True), dropped


def rank_years(seasonal: pd.DataFrame, code: str, n: int = 5) -> dict:
    """The driest and wettest seasons on record for one département."""
    d = seasonal[seasonal["code"] == code].dropna(subset=["wb_mm"])
    if d.empty:
        return {"driest": [], "wettest": [], "n_years": 0}
    ordered = d.sort_values("wb_mm")
    keep = ["year", "wb_mm", "wb_anom_mm"]
    return {
        "driest": ordered.head(n)[keep].to_dict("records"),
        "wettest": ordered.tail(n)[keep].iloc[::-1].to_dict("records"),
        "n_years": int(d["year"].nunique()),
    }


def detrend(series: pd.Series) -> pd.Series:
    """Residuals from a linear fit — used when comparing against yield later.

    Kept here because it is the honest way to correlate anything with yield:
    French yields roughly quadrupled over the century for reasons that have
    nothing to do with rainfall, so a raw correlation mostly measures the
    passage of time.
    """
    y = series.to_numpy(dtype=float)
    ok = ~np.isnan(y)
    if ok.sum() < 3:
        return pd.Series(np.full(len(y), np.nan), index=series.index)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x[ok], y[ok], 1)
    return pd.Series(y - (slope * x + intercept), index=series.index)
