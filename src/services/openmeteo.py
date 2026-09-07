"""Open-Meteo client. No Streamlit import, so scripts and tests can use it.

Two endpoints are used:

* the ERA5 archive, for the 1950-2018 history — reanalysis, stable, cacheable;
* the forecast endpoint with ``past_days``, for the season currently underway.

Nothing here needs an API key. The free tier's rate limits are not published,
so every call goes through :func:`fetch_daily` which batches coordinates,
retries on 429 with a backoff, and leaves caching to the caller.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from ..config import ARCHIVE_URL, DAILY_VARS, TIMEZONE

USER_AGENT = "terroir-climat/0.1 (+https://github.com/Deepak420-GrandMaster)"


class OpenMeteoError(RuntimeError):
    """Raised when the API cannot be reached or returns an error payload."""


@dataclass(frozen=True)
class Point:
    code: str
    lat: float
    lon: float


# Open-Meteo's free tier meters by data volume, not request count, and a
# refusal says "try again in one minute". A doubling backoff that starts at a
# few seconds never waits long enough, so a 429 is handled on its own terms:
# wait out the minute, then carry on. Server errors keep the doubling backoff.
RATE_LIMIT_WAIT = 62.0


def _get(
    url: str,
    params: dict,
    timeout: int = 120,
    retries: int = 8,
    on_wait=None,
) -> dict:
    query = urllib.parse.urlencode(params, safe=",")
    full = f"{url}?{query}"
    delay = 4.0
    last: Exception | None = None

    for attempt in range(retries):
        req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = exc.read()[:400].decode("utf-8", "replace")
            if exc.code == 429 and attempt < retries - 1:
                if on_wait:
                    on_wait(RATE_LIMIT_WAIT, attempt + 1, retries)
                time.sleep(RATE_LIMIT_WAIT)
                last = exc
                continue
            if exc.code in (500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                last = exc
                continue
            if exc.code == 429:
                raise OpenMeteoError(
                    "Open-Meteo is still rate-limiting after "
                    f"{retries} attempts. Wait a few minutes and rerun — "
                    "everything already downloaded is cached."
                ) from exc
            raise OpenMeteoError(
                f"Open-Meteo returned HTTP {exc.code}. {body}"
            ) from exc
        except urllib.error.URLError as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise OpenMeteoError(
                "Could not reach archive-api.open-meteo.com. This usually means no "
                "internet connection, or a network that blocks it. The app needs it "
                f"once, to build the climate table. Underlying error: {exc}"
            ) from exc

    raise OpenMeteoError(f"Open-Meteo failed after {retries} attempts: {last}")


def _as_list(payload: dict | list) -> list[dict]:
    """The API returns a bare object for one coordinate, a list for several."""
    return payload if isinstance(payload, list) else [payload]


def fetch_daily(
    points: list[Point],
    start: str,
    end: str,
    url: str = ARCHIVE_URL,
    on_wait=None,
) -> list[dict]:
    """Daily precipitation and ET0 for several points over one date range.

    Returns one record per point, in the order given, each shaped::

        {"code": "51", "time": [...], "precipitation_sum": [...],
         "et0_fao_evapotranspiration": [...]}
    """
    if not points:
        return []

    payload = _get(
        url,
        {
            "latitude": ",".join(f"{p.lat:.4f}" for p in points),
            "longitude": ",".join(f"{p.lon:.4f}" for p in points),
            "start_date": start,
            "end_date": end,
            "daily": ",".join(DAILY_VARS),
            "timezone": TIMEZONE,
        },
        on_wait=on_wait,
    )
    blocks = _as_list(payload)

    if len(blocks) != len(points):
        raise OpenMeteoError(
            f"asked for {len(points)} locations, got {len(blocks)} back — "
            "the batch size may exceed what the API accepts; lower "
            "COORDS_PER_CALL in src/config.py"
        )

    out = []
    for point, block in zip(points, blocks):
        if "error" in block:
            raise OpenMeteoError(f"{point.code}: {block.get('reason', block['error'])}")
        daily = block.get("daily")
        if not daily or "time" not in daily:
            raise OpenMeteoError(f"{point.code}: response had no daily block")
        record = {"code": point.code, "time": daily["time"]}
        for var in DAILY_VARS:
            if var not in daily:
                raise OpenMeteoError(
                    f"{point.code}: '{var}' missing from the response — the API's "
                    "variable names may have changed"
                )
            record[var] = daily[var]
        out.append(record)
    return out


def chunks(seq: list, size: int) -> list[list]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def year_chunks(first: int, last: int, span: int) -> list[tuple[int, int]]:
    out = []
    y = first
    while y <= last:
        out.append((y, min(y + span - 1, last)))
        y += span
    return out
