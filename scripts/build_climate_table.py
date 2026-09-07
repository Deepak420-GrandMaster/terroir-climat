"""Build the monthly climate table for every French département.

    python scripts/build_climate_table.py                     # 1961-2018
    python scripts/build_climate_table.py --years 2000 2018   # a quick slice
    python scripts/build_climate_table.py --check             # one call, then stop

Only the growing-season months are fetched (see FETCH_MONTHS in src/config.py).
That is not a shortcut: the app never reads October to February, and Open-Meteo's
free tier meters by data volume, so fetching them was the difference between a
download that finishes and one that hits the daily ceiling.

Needs an internet connection. Every chunk is cached under
``data/raw/openmeteo_cache/``, so an interrupted run resumes where it stopped
and a second run costs nothing. If the free tier cuts you off, wait an hour (or
a day) and rerun — it picks up exactly where it stopped.
"""

from __future__ import annotations

import argparse
import calendar
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.climate import daily_to_monthly  # noqa: E402
from src.config import (  # noqa: E402
    CACHE,
    CENTROIDS,
    COORDS_PER_CALL,
    FETCH_MONTHS,
    MONTHLY,
    PROCESSED,
    YEAR_MAX,
    YEAR_MIN,
)
from src.services.openmeteo import (  # noqa: E402
    OpenMeteoError,
    Point,
    chunks,
    fetch_daily,
)


def load_points() -> list[Point]:
    if not CENTROIDS.exists():
        raise SystemExit(
            f"missing {CENTROIDS}\nRun scripts/prepare_geography.py first."
        )
    df = pd.read_csv(CENTROIDS, dtype={"code": str})
    return [Point(r.code, float(r.lat), float(r.lon)) for r in df.itertuples()]


def cache_path(batch: int, year: int) -> Path:
    """Named by the months too, so chunks from a different fetch window
    (an earlier, wider one) are ignored rather than silently mixed in."""
    m0, m1 = FETCH_MONTHS
    return CACHE / f"b{batch:02d}_{year}_m{m0}{m1}.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs=2, type=int, metavar=("FIRST", "LAST"),
                    default=[YEAR_MIN, YEAR_MAX])
    ap.add_argument("--coords-per-call", type=int, default=COORDS_PER_CALL)
    ap.add_argument("--pause", type=float, default=10.0,
                    help="starting seconds between calls; adapts as it runs (default 10)")
    ap.add_argument("--check", action="store_true",
                    help="make a single small call to prove connectivity, then exit")
    args = ap.parse_args(argv)

    CACHE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    points = load_points()
    print(f"{len(points)} départements loaded")

    if args.check:
        print("connectivity check: one département, one month …")
        try:
            rec = fetch_daily(points[:1], "1976-06-01", "1976-06-30")
        except OpenMeteoError as exc:
            print(f"\nFAILED\n{exc}")
            return 1
        days = len(rec[0]["time"])
        p = sum(v for v in rec[0]["precipitation_sum"] if v is not None)
        print(f"OK — {days} days returned, {p:.1f} mm of rain in June 1976")
        return 0

    first, last = args.years
    m0, m1 = FETCH_MONTHS
    batches = chunks(points, args.coords_per_call)
    years = list(range(first, last + 1))
    total = len(batches) * len(years)
    days = sum(calendar.monthrange(2001, m)[1] for m in range(m0, m1 + 1))
    volume = len(points) * len(years) * days * 2
    print(f"{total} calls: {len(batches)} coordinate batches × {len(years)} years")
    print(f"months {m0}-{m1} only — about {volume/1e6:.1f}M values in total")
    print(f"cache: {CACHE}\n")

    # Open-Meteo's free tier meters by data volume per minute, so the pace is
    # self-tuning: every rate-limit refusal slows the loop down for good, and a
    # clean run gradually speeds it back up. Left alone it settles just under
    # whatever the limit happens to be that day.
    pause = args.pause
    fetched = waits = 0
    done = 0
    started = time.time()

    def on_wait(seconds, attempt, of):
        nonlocal pause, waits
        waits += 1
        pause = min(pause + 5.0, 45.0)
        print(f"        rate limit reached — waiting {seconds:.0f}s "
              f"(attempt {attempt}/{of}, pacing now {pause:.0f}s)", flush=True)

    for bi, batch in enumerate(batches):
        for yr in years:
            done += 1
            path = cache_path(bi, yr)
            tag = f"[{done}/{total}] batch {bi:02d} {yr}"
            if path.exists():
                print(f"{tag}  cached", flush=True)
                continue
            try:
                last_day = calendar.monthrange(yr, m1)[1]
                recs = fetch_daily(
                    batch,
                    f"{yr}-{m0:02d}-01",
                    f"{yr}-{m1:02d}-{last_day}",
                    on_wait=on_wait,
                )
            except OpenMeteoError as exc:
                print(f"\n{tag}  FAILED\n{exc}\n")
                print("Nothing is lost — rerun this script and it resumes from here.")
                return 1

            path.write_text(json.dumps(recs))
            fetched += 1
            n = sum(len(r["time"]) for r in recs)
            remaining = total - done
            eta = (time.time() - started) / max(fetched, 1) * remaining
            print(f"{tag}  {n:,} daily rows   ~{eta/60:.0f} min left", flush=True)

            if remaining:
                time.sleep(pause)
                if fetched % 6 == 0 and pause > args.pause:
                    pause = max(pause - 2.0, args.pause)   # ease back off

    if waits:
        print(f"\n(rate limit hit {waits}× — normal on the free tier, all recovered)")

    print("\nassembling monthly table …")
    frames = []
    for path in sorted(CACHE.glob(f"b*_m{FETCH_MONTHS[0]}{FETCH_MONTHS[1]}.json")):
        frames.append(daily_to_monthly(json.loads(path.read_text())))
    monthly = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["code", "year", "month"], keep="last")
        .sort_values(["code", "year", "month"])
        .reset_index(drop=True)
    )
    monthly.to_parquet(MONTHLY, index=False)

    print(f"wrote {MONTHLY}")
    print(f"  {len(monthly):,} rows — {monthly.code.nunique()} départements, "
          f"{monthly.year.min()}–{monthly.year.max()}")
    short = monthly[monthly["days"] < 28]
    if len(short):
        print(f"  note: {len(short)} part-months present (kept, filtered at season level)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
