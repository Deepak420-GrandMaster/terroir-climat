# Terroir & Climat

**Growing-season water balance across the 96 French départements, 1961–2018 — Streamlit + Folium + Open-Meteo.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

No API keys. No accounts. No database. No paid services.

```bash
python scripts/build_climate_table.py --check   # prove the connection works
python scripts/build_climate_table.py           # build the table (a few minutes)
streamlit run app.py
```

On macOS you can skip the terminal entirely: double-click **`start.command`**.

---

## What it shows

Pick a season window and a year. The map shades every département by its
growing-season **water balance** — rainfall minus reference evapotranspiration —
against **that département's own 1961–1990 normal**. Pick a département and you
get its full record: the anomaly year by year, rainfall and ET₀ on one
millimetre axis, and its driest and wettest seasons on record.

Set the year to **1976** and the Paris basin goes brown. That is the drought
everyone in France still refers to, and it is the first thing to check the
pipeline against: if it does not appear, something is wrong upstream.

## Why it exists

This grew out of an MSc dissertation on crop yield under climate variability.
The dataset that work relied on turned out to be unable to answer the question:
its rainfall column held one fixed value per country, repeated for every year,
so there was no within-country variation to correlate against yield at all.

This project builds the measurement that was missing — real daily weather,
resolved to 96 sub-national units, over 58 years. Crop yields join it in the
next milestone. The climate half stands on its own in the meantime.

## Data

| Source | What it provides | Access |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) ERA5-Land archive | Daily precipitation and FAO reference evapotranspiration, ~10 km grid, 1940–present | Free, no key |
| [france-geojson](https://github.com/gregoiredavid/france-geojson) | Département boundaries (simplified build) | Open |

Boundaries and centroids are committed to the repo (~570 KB), so the only thing
you need to download is the weather.

**Centroids** are area-weighted across each département's polygons, computed
with the shoelace formula in `scripts/prepare_geography.py` — no GeoPandas, which
keeps the install to seven packages and a few seconds.

## How the numbers are built

**Water balance** is `P − ET₀` summed over the chosen months. It is a *climatic*
measure: how much rain fell against how much the atmosphere could have
evaporated from a well-watered reference grass surface. It is deliberately not a
soil water budget — no runoff, drainage, rooting depth or soil storage — and it
is not a drought index.

**The stored table is monthly, not seasonal.** Any season window inside the
fetched months is then a sum over months, so changing the window is instant and
needs no refetch. 96 départements × 58 years × 7 months is 38,976 rows and a file
well under a megabyte.

**Anomalies are per-département.** Each is measured against its own 1961–1990
mean for the same months, which is what makes a dry year in Finistère comparable
to a dry year in Marne. A département whose baseline has fewer than 20 usable
years is left blank rather than shown against a normal that cannot carry it.

**Part-seasons are dropped.** A year missing one month of the window would look
artificially dry, so `season_totals` keeps only years with every month present.

**The colour scale is symmetric and fixed at zero.** If it ran from a single
year's minimum to its maximum, a wet year would paint the country blue and a dry
one brown, and no two years could be compared.

## Limitations

- **One point per département.** Weather is sampled at each département's
  centroid. That misrepresents the large and mountainous ones, where conditions
  vary more inside the département than between neighbours.
- **ERA5 is a reanalysis, not observations.** It is a model reconstruction
  constrained by observations — excellent for consistency across a century, not
  a substitute for a station record at a specific farm.
- **P − ET₀ is not water stress as a plant experiences it.** Soil, slope,
  drainage and irrigation all matter and none are here.
- **No crop yields yet.** That is milestone 2.
- **Not an agronomic advisory tool.** It is a historical atlas.

## Layout

```
terroir-climat/
├── app.py                        # Streamlit entry point
├── start.command                 # double-click launcher (macOS)
├── src/
│   ├── config.py                 # constants, seasons, palette
│   ├── climate.py                # monthly -> seasonal -> anomalies (no Streamlit)
│   ├── data_loading.py           # the only module that imports Streamlit
│   ├── services/openmeteo.py     # API client with retry/backoff
│   └── utils/{maps,charts}.py    # Folium and Plotly
├── scripts/
│   ├── prepare_geography.py      # boundaries -> centroids
│   └── build_climate_table.py    # the weather fetch, cached and resumable
├── data/raw/                     # committed: geojson + centroids
├── data/processed/               # built locally, gitignored
└── tests/
```

`src/climate.py` and `src/services/` import no Streamlit, so the analysis is
testable and reusable without a browser.

## The fetch

`build_climate_table.py` makes one request per (24 départements, one year) and
caches every chunk under `data/raw/openmeteo_cache/`. More départements per call
is free — the tier meters bytes, not requests — while one year per call keeps
each cached chunk small, so an interruption loses seconds rather than minutes.
Cache filenames encode the month window, so chunks from a wider earlier fetch
are ignored rather than silently mixed in.

**Only the growing season is fetched — March to September.** The app never
reads October to February, and Open-Meteo's free tier meters by *data volume*,
not by request count. Fetching the whole calendar year from 1950 meant 4.8
million values and the download simply could not finish; March–September from
1961 is 2.4 million, and 1961 is where the WMO baseline starts anyway. Widening
either means editing `FETCH_MONTHS` / `YEAR_MIN` and refetching — a test fails
if a season window falls outside what is fetched.

**Expect 30–60 minutes, once, and possibly two sittings.** The script paces
itself: every refusal waits out the full minute the API asks for and permanently
slows the loop, and a clean run gradually speeds back up. `rate limit reached —
waiting 62s` is normal. If it gives up with *"still rate-limiting after 8
attempts"*, the daily budget is spent — wait an hour or a day and rerun; every
chunk already fetched is cached.

**Do not run this on a shared runner.** Open-Meteo limits per IP address, and
GitHub Actions runners share IPs with thousands of other jobs, so they arrive
with most of that quota already spent by strangers. A real attempt managed 13 of
84 calls before being cut off for good. Run it from your own machine.

Run `--check` first. It makes one small request and stops, so a network problem
surfaces in seconds rather than halfway through.

## Bilingual

Every string is in `src/i18n.py`, English and French, with a radio at the top of
the sidebar. Nothing else in the app holds display text.

Seasons are keyed by a stable id (`apr_jul`), not by their label, so switching
language never changes which season is selected. Numbers follow each language's
conventions — `1,234.5` in English, `1 234,5` in French, with a no-break
thousands space.

Three tests keep it honest: both dictionaries must carry exactly the same keys,
every season must have a label in every language, and the `{placeholders}` in a
string must match across languages — a mismatch there would raise at runtime, in
front of a reader, rather than in CI.

## Tests

```bash
pip install pytest ruff && pytest -q && ruff check src tests scripts app.py
```

30 tests on synthetic weather with known answers: a planted drought year has to
come out as the driest on record, anomalies have to average zero across the
baseline, a short baseline has to be blanked rather than published, and a
wrapped season window has to raise rather than quietly compute the wrong thing.

## Deploy

Push to GitHub, then point [Streamlit Community Cloud](https://share.streamlit.io)
at `app.py`. Free tier, no keys.

One caveat: `data/processed/` is gitignored, so a cloud deployment has no climate
table. Either commit the built parquet (it is under a megabyte) or let the app
show its setup screen. Committing it is the sane choice for a public demo.

## Notes

The basemap is OpenStreetMap rather than CartoDB Positron: as of 2026 the Carto
basemaps require an API key, which would break the no-keys promise this project
is built on.

## Licence

MIT. Weather data © Open-Meteo (CC BY 4.0), derived from ECMWF ERA5.
Boundaries from france-geojson, derived from IGN open data.
