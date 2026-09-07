"""Tests on synthetic weather with known answers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.climate import add_normals, daily_to_monthly, detrend, rank_years, season_totals
from src.services.openmeteo import Point, chunks, year_chunks


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
def daily_record(code: str, year: int, p_per_day: float, et0_per_day: float) -> dict:
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    return {
        "code": code,
        "time": [d.strftime("%Y-%m-%d") for d in dates],
        "precipitation_sum": [p_per_day] * len(dates),
        "et0_fao_evapotranspiration": [et0_per_day] * len(dates),
    }


def synthetic_monthly(codes=("51", "29"), years=range(1961, 1991), seed=0):
    """A stable baseline period, so normals are predictable."""
    rng = np.random.default_rng(seed)
    rows = []
    for code in codes:
        for year in years:
            for month in range(1, 13):
                rows.append({
                    "code": code, "year": year, "month": month,
                    "p_mm": 50 + rng.normal(0, 3),
                    "et0_mm": 40 + rng.normal(0, 3),
                    "days": 30,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# daily -> monthly
# ---------------------------------------------------------------------------
def test_daily_to_monthly_sums_correctly():
    monthly = daily_to_monthly([daily_record("51", 2000, 2.0, 1.0)])
    assert len(monthly) == 12
    january = monthly[monthly["month"] == 1].iloc[0]
    assert january["p_mm"] == pytest.approx(62.0)     # 31 days x 2 mm
    assert january["et0_mm"] == pytest.approx(31.0)
    assert january["days"] == 31


def test_daily_to_monthly_handles_several_departements():
    monthly = daily_to_monthly(
        [daily_record("51", 2000, 2.0, 1.0), daily_record("29", 2000, 4.0, 1.0)]
    )
    assert set(monthly["code"]) == {"51", "29"}
    assert len(monthly) == 24


def test_daily_to_monthly_empty_input():
    assert daily_to_monthly([]).empty


# ---------------------------------------------------------------------------
# season windows
# ---------------------------------------------------------------------------
def test_season_totals_sums_the_window_only():
    monthly = daily_to_monthly([daily_record("51", 2000, 1.0, 0.5)])
    season = season_totals(monthly, (4, 7))          # Apr+May+Jun+Jul = 122 days
    assert len(season) == 1
    assert season["p_mm"].iloc[0] == pytest.approx(122.0)
    assert season["wb_mm"].iloc[0] == pytest.approx(61.0)


def test_season_totals_drops_incomplete_seasons():
    monthly = daily_to_monthly([daily_record("51", 2000, 1.0, 0.5)])
    monthly = monthly[monthly["month"] != 6]          # lose one month of the window
    assert season_totals(monthly, (4, 7)).empty


def test_season_totals_rejects_wrapped_window():
    monthly = daily_to_monthly([daily_record("51", 2000, 1.0, 0.5)])
    with pytest.raises(ValueError, match="wraps the calendar year"):
        season_totals(monthly, (10, 3))


# ---------------------------------------------------------------------------
# normals and anomalies
# ---------------------------------------------------------------------------
def test_anomaly_is_zero_on_average_across_the_baseline():
    seasonal = season_totals(synthetic_monthly(), (4, 7))
    out = add_normals(seasonal)
    baseline = out[out["year"].between(1961, 1990)]
    assert baseline["wb_anom_mm"].mean() == pytest.approx(0, abs=0.5)


def with_dry_year(year: int = 1995, p_mm: float = 5.0) -> pd.DataFrame:
    """Baseline 1961-1990 plus one extra, genuinely dry year outside it."""
    monthly = synthetic_monthly()
    dry = monthly[monthly["year"] == 1990].copy()
    dry["year"] = year
    dry["p_mm"] = p_mm
    return pd.concat([monthly, dry], ignore_index=True)


def test_dry_year_gets_a_negative_anomaly():
    out = add_normals(season_totals(with_dry_year(), (4, 7)))
    row = out[(out["year"] == 1995) & (out["code"] == "51")].iloc[0]
    assert row["wb_anom_mm"] < -100
    assert row["wb_z"] < -3


def test_short_baseline_is_blanked_not_published():
    monthly = synthetic_monthly(years=range(1961, 1966))   # only 5 baseline years
    out = add_normals(season_totals(monthly, (4, 7)))
    assert out["wb_normal"].isna().all()
    assert out["wb_anom_mm"].isna().all()


def test_normals_are_per_departement():
    monthly = synthetic_monthly(codes=("51", "29"))
    monthly.loc[monthly["code"] == "29", "p_mm"] += 100    # Finistère is much wetter
    out = add_normals(season_totals(monthly, (4, 7)))
    norms = out.groupby("code")["wb_normal"].first()
    assert norms["29"] > norms["51"] + 300
    # but both sit near zero anomaly, because each is judged against itself
    assert out.groupby("code")["wb_anom_mm"].mean().abs().max() < 1.0


# ---------------------------------------------------------------------------
# rankings and detrending
# ---------------------------------------------------------------------------
def test_rank_years_finds_the_planted_extreme():
    out = add_normals(season_totals(with_dry_year(), (4, 7)))
    ranks = rank_years(out, "51")
    assert ranks["driest"][0]["year"] == 1995
    assert ranks["n_years"] == 31          # 30 baseline years plus the dry one
    assert ranks["wettest"][0]["year"] != 1995


def test_rank_years_unknown_code_is_empty_not_an_error():
    out = add_normals(season_totals(synthetic_monthly(), (4, 7)))
    assert rank_years(out, "999") == {"driest": [], "wettest": [], "n_years": 0}


def test_detrend_removes_a_linear_trend():
    series = pd.Series(np.arange(50, dtype=float) * 3 + 10)
    assert detrend(series).abs().max() == pytest.approx(0, abs=1e-6)


def test_detrend_keeps_the_wiggle():
    x = np.arange(50, dtype=float)
    series = pd.Series(x * 3 + 10 + np.sin(x))
    residual = detrend(series)
    assert residual.abs().max() > 0.5
    assert residual.mean() == pytest.approx(0, abs=1e-6)


def test_detrend_too_short_returns_nan():
    assert detrend(pd.Series([1.0, 2.0])).isna().all()


# ---------------------------------------------------------------------------
# batching helpers
# ---------------------------------------------------------------------------
def test_chunks_covers_everything_once():
    points = [Point(str(i), 45.0, 2.0) for i in range(96)]
    batched = chunks(points, 8)
    assert len(batched) == 12
    assert sum(len(b) for b in batched) == 96


def test_year_chunks_are_contiguous_and_inclusive():
    spans = year_chunks(1950, 2018, 10)
    assert spans[0] == (1950, 1959)
    assert spans[-1][1] == 2018
    for (_, end), (start, _) in zip(spans, spans[1:]):
        assert start == end + 1


# ---------------------------------------------------------------------------
# rate-limit handling — the bug a real run found
# ---------------------------------------------------------------------------
def test_rate_limit_waits_a_full_minute_then_succeeds(monkeypatch):
    """A 429 must be waited out, not retried after three seconds."""
    import urllib.error

    from src.services import openmeteo as om

    calls = {"n": 0}
    slept: list[float] = []

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                req.full_url, 429, "Too Many Requests", {},
                __import__("io").BytesIO(b'{"error":true,"reason":"Minutely API '
                                         b'request limit exceeded."}'),
            )
        class R:
            def read(self): return b'{"daily":{"time":["2000-01-01"],' \
                                   b'"precipitation_sum":[1.0],' \
                                   b'"et0_fao_evapotranspiration":[0.5]}}'
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()

    monkeypatch.setattr(om.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(om.time, "sleep", lambda s: slept.append(s))

    out = om.fetch_daily([om.Point("51", 48.95, 4.24)], "2000-01-01", "2000-01-01")
    assert calls["n"] == 2
    assert slept and slept[0] >= 60, f"waited only {slept}, must ride out the minute"
    assert out[0]["code"] == "51"


def test_persistent_rate_limit_says_what_to_do(monkeypatch):
    import io
    import urllib.error

    from src.services import openmeteo as om

    def always_429(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(om.urllib.request, "urlopen", always_429)
    monkeypatch.setattr(om.time, "sleep", lambda s: None)

    with pytest.raises(om.OpenMeteoError, match="cached"):
        om.fetch_daily([om.Point("51", 48.95, 4.24)], "2000-01-01", "2000-01-01")


def test_server_error_uses_short_backoff_not_the_minute(monkeypatch):
    import io
    import urllib.error

    from src.services import openmeteo as om

    calls = {"n": 0}
    slept: list[float] = []

    def flaky(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                req.full_url, 503, "Service Unavailable", {}, io.BytesIO(b"{}"))
        class R:
            def read(self): return b'{"daily":{"time":["2000-01-01"],' \
                                   b'"precipitation_sum":[1.0],' \
                                   b'"et0_fao_evapotranspiration":[0.5]}}'
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()

    monkeypatch.setattr(om.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(om.time, "sleep", lambda s: slept.append(s))
    om.fetch_daily([om.Point("51", 48.95, 4.24)], "2000-01-01", "2000-01-01")
    assert slept[0] < 30, "a 503 should retry quickly, not wait out a minute"
