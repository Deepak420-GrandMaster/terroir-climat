"""Terroir & Climat — French growing-season water balance, by département.

    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from src.climate import rank_years
from src.config import DEFAULT_SEASON, NORMAL_END, NORMAL_START, SEASONS
from src.data_loading import (
    describe_state,
    load_departements,
    load_geojson,
    load_seasonal,
)
from src.utils.charts import anomaly_bars, national_series, season_lines
from src.utils.maps import choropleth

st.set_page_config(
    page_title="Terroir & Climat",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    .block-container{padding-top:2.2rem;padding-bottom:3rem;max-width:1500px}
    h1{font-size:1.9rem!important;letter-spacing:-.01em;margin-bottom:.15rem}
    .lede{color:#6b767c;font-size:.97rem;margin-bottom:1.4rem}
    [data-testid="stMetricValue"]{font-size:1.6rem}
    .caveat{color:#7b868c;font-size:.83rem;line-height:1.5}
    </style>""",
    unsafe_allow_html=True,
)


def setup_screen(state) -> None:
    """Shown when the climate table has not been built. Says exactly what to do."""
    st.title("Terroir & Climat")
    st.markdown(
        '<p class="lede">Growing-season water balance across the 96 French '
        "départements, 1950–2018.</p>",
        unsafe_allow_html=True,
    )
    st.warning(f"**Not ready yet.** {state.message}")
    st.markdown(
        """
### One step to go

The app needs a climate table built from the Open-Meteo ERA5 archive. It is
free and needs no account, but it does need an internet connection, and the
download takes a few minutes. In a terminal, from this folder:

```bash
python scripts/build_climate_table.py --check   # proves the connection works
python scripts/build_climate_table.py           # builds the table
```

The first command makes one small request and stops. Run it first — if it
fails you will know immediately, and the message will say why.

Every chunk is cached as it arrives, so if the download is interrupted you can
rerun the same command and it picks up where it stopped.
"""
    )
    if state.has_geometry:
        st.success(f"Boundaries are already in place: {state.n_departements} départements.")


def main() -> None:
    state = describe_state()
    if not state.ready:
        setup_screen(state)
        return

    deps = load_departements()
    geojson = load_geojson()

    # ---------------- sidebar ----------------
    st.sidebar.markdown("### Season")
    season_label = st.sidebar.selectbox(
        "Months summed", list(SEASONS), index=list(SEASONS).index(DEFAULT_SEASON)
    )
    months = SEASONS[season_label]

    seasonal = load_seasonal(months)
    if seasonal.empty:
        st.error("The climate table has no complete seasons for that window.")
        return

    years = sorted(seasonal["year"].unique())
    st.sidebar.markdown("### Year")
    year = st.sidebar.select_slider(
        "Season shown", options=years, value=1976 if 1976 in years else years[-1]
    )

    st.sidebar.markdown("### Département")
    names = deps["nom"].tolist()
    default_name = "Marne" if "Marne" in names else names[0]
    dep_name = st.sidebar.selectbox(
        "Detail below the map", names, index=names.index(default_name)
    )
    dep_code = deps.loc[deps["nom"] == dep_name, "code"].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<p class="caveat">Normals are each département\'s own '
        f"{NORMAL_START}–{NORMAL_END} mean for the same months. "
        "Water balance is rainfall minus reference evapotranspiration (ET₀) — "
        "a climatic measure, not a soil water budget.</p>",
        unsafe_allow_html=True,
    )

    # ---------------- header ----------------
    st.title("Terroir & Climat")
    st.markdown(
        f'<p class="lede">Growing-season water balance across {state.n_departements} '
        f"French départements, {state.year_min}–{state.year_max}. "
        f"Showing <b>{season_label}</b> in <b>{year}</b>.</p>",
        unsafe_allow_html=True,
    )

    this_year = seasonal[seasonal["year"] == year].copy()
    this_year["detail"] = this_year.apply(
        lambda r: f"{r.p_mm:,.0f} mm rain − {r.et0_mm:,.0f} mm ET₀", axis=1
    )

    national_median = this_year["wb_anom_mm"].median()
    driest = this_year.nsmallest(1, "wb_anom_mm")
    driest_name = "—"
    if not driest.empty:
        code = driest["code"].iloc[0]
        match = deps.loc[deps["code"] == code, "nom"]
        driest_name = match.iloc[0] if len(match) else code

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("National median anomaly", f"{national_median:+,.0f} mm")
    c2.metric("Départements below normal",
              f"{int((this_year['wb_anom_mm'] < 0).sum())} of {len(this_year)}")
    c3.metric("Driest département", driest_name,
              f"{driest['wb_anom_mm'].iloc[0]:+,.0f} mm" if not driest.empty else None)
    sel = this_year[this_year["code"] == dep_code]
    c4.metric(f"{dep_name}",
              f"{sel['wb_mm'].iloc[0]:+,.0f} mm" if not sel.empty else "no data",
              f"{sel['wb_anom_mm'].iloc[0]:+,.0f} mm vs normal" if not sel.empty else None)

    # ---------------- map ----------------
    vmax = seasonal["wb_anom_mm"].abs().quantile(0.98)
    left, right = st.columns([3, 2], gap="large")

    with left:
        fmap = choropleth(geojson, this_year, "wb_anom_mm", "detail", vmax)
        st_folium(fmap, height=560, use_container_width=True,
                  returned_objects=[], key=f"map-{year}-{season_label}")

    with right:
        st.plotly_chart(anomaly_bars(seasonal, dep_code, dep_name), width="stretch")
        st.plotly_chart(season_lines(seasonal, dep_code, dep_name), width="stretch")

    st.plotly_chart(national_series(seasonal), width="stretch")

    # ---------------- rankings ----------------
    ranks = rank_years(seasonal, dep_code)
    a, b = st.columns(2)
    with a:
        st.markdown(f"**{dep_name} — driest seasons on record**")
        st.dataframe(
            [{"Year": r["year"], "P − ET₀ (mm)": round(r["wb_mm"]),
              "vs normal (mm)": round(r["wb_anom_mm"])} for r in ranks["driest"]],
            hide_index=True, width="stretch")
    with b:
        st.markdown(f"**{dep_name} — wettest seasons on record**")
        st.dataframe(
            [{"Year": r["year"], "P − ET₀ (mm)": round(r["wb_mm"]),
              "vs normal (mm)": round(r["wb_anom_mm"])} for r in ranks["wettest"]],
            hide_index=True, width="stretch")

    with st.expander("What this does and does not show"):
        st.markdown(
            f"""
**Water balance** here is rainfall minus FAO reference evapotranspiration,
summed over {season_label.split(" (")[0]}. It says whether a season delivered
more or less water than the atmosphere could take from a well-watered reference
grass surface — nothing about soil type, rooting depth, drainage, irrigation or
runoff. It is not a drought index and not a soil water budget.

**Anomalies** are against each département's own {NORMAL_START}–{NORMAL_END}
mean, so a dry year in Finistère is measured against Finistère, not against
France. Départements whose baseline has fewer than 20 usable years are left
blank rather than shown against a shaky normal.

**Source** is the ERA5 reanalysis via Open-Meteo, on roughly a 10 km grid,
sampled at each département's area-weighted centroid. One point per département
is a real simplification: it will misrepresent the large or mountainous ones,
where conditions vary more within the département than between neighbours.

**Crop yields are not in this version.** The département-level yield data
(1900–2018, ten crops) is the next milestone; this release is the climate half,
which is the part the dissertation was missing.
"""
        )


if __name__ == "__main__":
    main()
