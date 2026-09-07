"""Terroir & Climat — French growing-season water balance, by département.

    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from src.climate import national_rank, rank_years, year_rank_in_departement
from src.config import DEFAULT_SEASON, NORMAL_END, NORMAL_START, SEASONS
from src.data_loading import (
    describe_state,
    load_departements,
    load_geojson,
    load_seasonal,
)
from src.i18n import DEFAULT_LANG, LANGUAGES, num, season_label, t
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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');
:root{
  --ink:#131a1d; --ink-2:#4a565c; --ink-3:#7c878c;
  --rule:#e3e8e4; --rule-soft:#eef2ee; --surface:#fff; --paper:#f6f9f6;
  --accent:#1f6fb2; --dry:#c07a2e; --wet:#4f8fc0;
  --sans:"IBM Plex Sans Condensed",ui-sans-serif,system-ui,sans-serif;
  --serif:"Source Serif 4",Georgia,serif;
}
.block-container{padding-top:1.8rem;padding-bottom:4rem;max-width:1560px}

/* ---- type: bigger and calmer than Streamlit's default ---- */
html,body,[class*="css"],p,li,label{font-family:var(--serif)}
h1{font-family:var(--sans)!important;font-size:2.35rem!important;font-weight:700!important;
   letter-spacing:-.022em;line-height:1.03;margin:0 0 .25rem!important;color:var(--ink)}
.lede{color:var(--ink-2);font-size:1.08rem;line-height:1.55;margin:0 0 1.5rem;
      max-width:62rem;border-bottom:1px solid var(--rule);padding-bottom:1.2rem}
.sec{font-family:var(--sans);font-size:.76rem;font-weight:600;letter-spacing:.13em;
     text-transform:uppercase;color:var(--ink-3);margin:2.1rem 0 .7rem;
     display:flex;align-items:center;gap:.7rem}
.sec::after{content:"";flex:1;height:1px;background:var(--rule)}

/* ---- verdict banner ---- */
[data-testid="stAlert"]{border-radius:8px;border:1px solid #cfe0ef;
  background:#f2f8fd;padding:.85rem 1.1rem}
[data-testid="stAlert"] p{font-size:1.02rem!important;line-height:1.5;color:var(--ink)!important}

/* ---- metric cards ---- */
[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--rule);
  border-radius:10px;padding:.95rem 1.1rem 1.05rem;height:100%;
  transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease}
[data-testid="stMetric"]:hover{border-color:#c3cec7;transform:translateY(-3px);
  box-shadow:0 10px 26px -14px rgba(19,26,29,.35)}
[data-testid="stMetricLabel"]{font-family:var(--sans)!important;font-size:.76rem!important;
  font-weight:600!important;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3)!important}
[data-testid="stMetricValue"]{font-family:var(--sans)!important;font-size:1.9rem!important;
  font-weight:700!important;letter-spacing:-.025em;font-variant-numeric:tabular-nums;
  line-height:1.15}
[data-testid="stMetricDelta"]{font-size:.82rem!important}

/* ---- sidebar ---- */
[data-testid="stSidebar"]{background:var(--paper);border-right:1px solid var(--rule)}
[data-testid="stSidebar"] .block-container{padding-top:1.4rem}
[data-testid="stSidebar"] h3{font-family:var(--sans)!important;font-size:.76rem!important;
  font-weight:600!important;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-3)!important;margin:1.1rem 0 .35rem!important}
[data-testid="stSidebar"] label{font-size:.88rem!important;color:var(--ink-2)!important}
.caveat{color:var(--ink-3);font-size:.82rem;line-height:1.6}

/* ---- panels ---- */
iframe{border-radius:10px;border:1px solid var(--rule)}
[data-testid="stPlotlyChart"]{background:var(--surface);border:1px solid var(--rule);
  border-radius:10px;padding:.4rem .6rem .15rem;
  transition:border-color .2s ease,box-shadow .2s ease}
[data-testid="stPlotlyChart"]:hover{border-color:#c3cec7;
  box-shadow:0 8px 22px -16px rgba(19,26,29,.3)}
[data-testid="stDataFrame"]{border-radius:8px;overflow:hidden;border:1px solid var(--rule)}
[data-testid="stExpander"]{border:1px solid var(--rule)!important;border-radius:10px!important;
  background:var(--surface)}
[data-testid="stExpander"] p,[data-testid="stExpander"] li{font-size:.95rem;line-height:1.65}

/* ---- motion: one cascade in, then quiet ---- */
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes sweep{from{opacity:0;transform:translateY(6px) scale(.995)}
                 to{opacity:1;transform:none}}
h1{animation:fade .45s ease both}
.lede{animation:rise .5s cubic-bezier(.22,.8,.3,1) both;animation-delay:.05s}
[data-testid="stAlert"]{animation:sweep .55s cubic-bezier(.22,.8,.3,1) both;animation-delay:.10s}
[data-testid="stMetric"],[data-testid="stPlotlyChart"],iframe,
[data-testid="stDataFrame"],.sec{
  animation:rise .55s cubic-bezier(.22,.8,.3,1) both}
[data-testid="column"]:nth-child(1) [data-testid="stMetric"]{animation-delay:.16s}
[data-testid="column"]:nth-child(2) [data-testid="stMetric"]{animation-delay:.22s}
[data-testid="column"]:nth-child(3) [data-testid="stMetric"]{animation-delay:.28s}
[data-testid="column"]:nth-child(4) [data-testid="stMetric"]{animation-delay:.34s}
iframe{animation-delay:.30s}
[data-testid="stPlotlyChart"]{animation-delay:.38s}
[data-testid="stDataFrame"]{animation-delay:.44s}

/* controls feel responsive rather than instant-swap */
[data-testid="stSidebar"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-baseweb="input"]>div{transition:border-color .16s ease}
[data-testid="stSidebar"] [data-baseweb="select"]>div:hover{border-color:var(--accent)}

@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
  [data-testid="stMetric"]:hover,[data-testid="stPlotlyChart"]:hover{transform:none;box-shadow:none}
}
</style>""",
    unsafe_allow_html=True,
)


def pick_language() -> str:
    """Language sits at the top of the sidebar, above everything it affects."""
    codes = list(LANGUAGES)
    chosen = st.sidebar.radio(
        "Language / Langue",
        codes,
        index=codes.index(DEFAULT_LANG),
        format_func=lambda c: LANGUAGES[c],
        horizontal=True,
        key="lang",
    )
    st.sidebar.markdown("---")
    return chosen


def _ordinal(n: int, lang: str) -> str:
    """1st / 2nd / 3rd in English; 1re / 2e in French."""
    if lang == "fr":
        return "1re" if n == 1 else f"{n}e"
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def setup_screen(state, lang: str) -> None:
    """Shown when the climate table has not been built. Says exactly what to do."""
    st.title(t(lang, "title"))
    st.markdown(
        f'<p class="lede">{t(lang, "lede_setup", y0=1961, y1=2018)}</p>',
        unsafe_allow_html=True,
    )
    key = "setup_msg_geometry" if not state.has_geometry else "setup_msg_climate"
    st.warning(t(lang, "setup_warning", msg=t(lang, key)))
    st.markdown(t(lang, "setup_body"))
    if state.has_geometry:
        st.success(t(lang, "setup_geometry_ok", n=state.n_departements))


def main() -> None:
    lang = pick_language()
    state = describe_state()
    if not state.ready:
        setup_screen(state, lang)
        return

    deps = load_departements()
    geojson = load_geojson()

    # ---------------- sidebar ----------------
    st.sidebar.markdown(f"### {t(lang, 'sidebar_season')}")
    season_key = st.sidebar.selectbox(
        t(lang, "sidebar_season_help"),
        list(SEASONS),
        index=list(SEASONS).index(DEFAULT_SEASON),
        format_func=lambda k: season_label(lang, k),
    )
    months = SEASONS[season_key]
    season_name = season_label(lang, season_key)

    seasonal, pending_years = load_seasonal(months)
    if seasonal.empty:
        st.error(t(lang, "error_no_seasons"))
        return

    years = sorted(seasonal["year"].unique())
    st.sidebar.markdown(f"### {t(lang, 'sidebar_year')}")
    year = st.sidebar.select_slider(
        t(lang, "sidebar_year_help"),
        options=years,
        value=1976 if 1976 in years else years[-1],
    )

    st.sidebar.markdown(f"### {t(lang, 'sidebar_dep')}")
    names = deps["nom"].tolist()
    default_name = "Marne" if "Marne" in names else names[0]
    dep_name = st.sidebar.selectbox(
        t(lang, "sidebar_dep_help"), names, index=names.index(default_name)
    )
    dep_code = deps.loc[deps["nom"] == dep_name, "code"].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<p class="caveat">{t(lang, "sidebar_note", n0=NORMAL_START, n1=NORMAL_END)}</p>',
        unsafe_allow_html=True,
    )

    # ---------------- header ----------------
    st.title(t(lang, "title"))
    st.markdown(
        f'<p class="lede">{t(lang, "lede", n=state.n_departements, y0=state.year_min, y1=state.year_max, season=season_name, year=year)}</p>',
        unsafe_allow_html=True,
    )

    this_year = seasonal[seasonal["year"] == year].copy()
    this_year["detail"] = this_year.apply(
        lambda r: t(lang, "map_detail",
                    p=num(r.p_mm, lang), e=num(r.et0_mm, lang)), axis=1
    )

    national_median = this_year["wb_anom_mm"].median()
    driest = this_year.nsmallest(1, "wb_anom_mm")
    driest_name = "—"
    if not driest.empty:
        code = driest["code"].iloc[0]
        match = deps.loc[deps["code"] == code, "nom"]
        driest_name = match.iloc[0] if len(match) else code

    # A sentence saying whether this season is remarkable, before the numbers.
    rank = national_rank(seasonal, year)
    if rank:
        below = int((this_year["wb_anom_mm"] < 0).sum())
        common = dict(year=year, k=below, n=len(this_year),
                      total=rank["n_years"], v=num(rank["value"], lang, signed=True))
        if rank["driest_rank"] == 1:
            st.info(t(lang, "verdict_driest", **common))
        elif rank["wettest_rank"] == 1:
            st.info(t(lang, "verdict_wettest", **common))
        elif rank["driest_rank"] <= 5:
            st.info(t(lang, "verdict_dry", r=rank["driest_rank"], **common))
        elif rank["wettest_rank"] <= 5:
            st.info(t(lang, "verdict_wet", r=rank["wettest_rank"], **common))
        else:
            st.caption(t(lang, "verdict_normal", r=rank["driest_rank"], **common))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t(lang, "metric_national"), f"{num(national_median, lang, signed=True)} mm")
    c2.metric(
        t(lang, "metric_below"),
        t(lang, "metric_below_value",
          k=int((this_year["wb_anom_mm"] < 0).sum()), n=len(this_year)),
    )
    c3.metric(
        t(lang, "metric_driest"), driest_name,
        f"{num(driest['wb_anom_mm'].iloc[0], lang, signed=True)} mm"
        if not driest.empty else None,
    )
    sel = this_year[this_year["code"] == dep_code]
    c4.metric(
        dep_name,
        f"{num(sel['wb_mm'].iloc[0], lang, signed=True)} mm"
        if not sel.empty else t(lang, "metric_no_data"),
        t(lang, "metric_vs_normal",
          v=num(sel["wb_anom_mm"].iloc[0], lang, signed=True)) if not sel.empty else None,
    )

    # ---------------- map ----------------
    st.markdown(f'<p class="sec">{t(lang, "sec_map", year=year)}</p>',
                unsafe_allow_html=True)
    vmax = seasonal["wb_anom_mm"].abs().quantile(0.98)
    left, right = st.columns([3, 2], gap="large")

    with left:
        fmap = choropleth(geojson, this_year, "wb_anom_mm", "detail", vmax,
                          lang=lang, highlight=dep_code)
        st_folium(fmap, height=560, use_container_width=True,
                  returned_objects=[], key=f"map-{year}-{season_key}-{lang}-{dep_code}")

    with right:
        st.plotly_chart(anomaly_bars(seasonal, dep_code, dep_name, lang), width="stretch")
        st.plotly_chart(season_lines(seasonal, dep_code, dep_name, lang), width="stretch")

    st.markdown(f'<p class="sec">{t(lang, "sec_record")}</p>', unsafe_allow_html=True)
    st.plotly_chart(national_series(seasonal, lang), width="stretch")

    # ---------------- rankings ----------------
    st.markdown(f'<p class="sec">{t(lang, "sec_dep", dep=dep_name)}</p>',
                unsafe_allow_html=True)
    ranks = rank_years(seasonal, dep_code)
    cols = {"year": t(lang, "col_year"), "wb": t(lang, "col_wb"),
            "anom": t(lang, "col_anom")}

    def table(rows):
        return [
            {cols["year"]: r["year"],
             cols["wb"]: round(r["wb_mm"]),
             cols["anom"]: round(r["wb_anom_mm"])}
            for r in rows
        ]

    dep_rank = year_rank_in_departement(seasonal, dep_code, year)
    span = dict(y0=dep_rank.get("first_year", ""), y1=dep_rank.get("last_year", ""))

    a, b = st.columns(2)
    with a:
        st.markdown(t(lang, "table_driest", dep=dep_name, **span))
        st.dataframe(table(ranks["driest"]), hide_index=True, width="stretch")
    with b:
        st.markdown(t(lang, "table_wettest", dep=dep_name, **span))
        st.dataframe(table(ranks["wettest"]), hide_index=True, width="stretch")

    # Says out loud where the slider's year falls, so the all-time tables stop
    # looking like they ignored the slider.
    if dep_rank:
        st.caption(t(lang, "table_note", year=year, dep=dep_name,
                     r=_ordinal(dep_rank["driest_rank"], lang),
                     n=dep_rank["n_years"]))

    if pending_years:
        st.caption(
            t(lang, "pending_years", k=len(pending_years),
              y0=min(pending_years), y1=max(pending_years))
        )

    with st.expander(t(lang, "origin_header")):
        st.markdown(t(lang, "origin_body"))

    with st.expander(t(lang, "notes_header")):
        st.markdown(
            t(lang, "notes_body",
              season=season_name.split(" (")[0], n0=NORMAL_START, n1=NORMAL_END)
        )


if __name__ == "__main__":
    main()
