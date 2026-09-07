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
    .block-container{padding-top:2.2rem;padding-bottom:3rem;max-width:1500px}
    h1{font-size:1.9rem!important;letter-spacing:-.01em;margin-bottom:.15rem}
    .lede{color:#6b767c;font-size:.97rem;margin-bottom:1.4rem}
    [data-testid="stMetricValue"]{font-size:1.6rem}
    .caveat{color:#7b868c;font-size:.83rem;line-height:1.5}
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
    vmax = seasonal["wb_anom_mm"].abs().quantile(0.98)
    left, right = st.columns([3, 2], gap="large")

    with left:
        fmap = choropleth(geojson, this_year, "wb_anom_mm", "detail", vmax, lang=lang)
        st_folium(fmap, height=560, use_container_width=True,
                  returned_objects=[], key=f"map-{year}-{season_key}-{lang}")

    with right:
        st.plotly_chart(anomaly_bars(seasonal, dep_code, dep_name, lang), width="stretch")
        st.plotly_chart(season_lines(seasonal, dep_code, dep_name, lang), width="stretch")

    st.plotly_chart(national_series(seasonal, lang), width="stretch")

    # ---------------- rankings ----------------
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

    a, b = st.columns(2)
    with a:
        st.markdown(t(lang, "table_driest", dep=dep_name))
        st.dataframe(table(ranks["driest"]), hide_index=True, width="stretch")
    with b:
        st.markdown(t(lang, "table_wettest", dep=dep_name))
        st.dataframe(table(ranks["wettest"]), hide_index=True, width="stretch")

    if pending_years:
        st.caption(
            t(lang, "pending_years", k=len(pending_years),
              y0=min(pending_years), y1=max(pending_years))
        )

    with st.expander(t(lang, "notes_header")):
        st.markdown(
            t(lang, "notes_body",
              season=season_name.split(" (")[0], n0=NORMAL_START, n1=NORMAL_END)
        )


if __name__ == "__main__":
    main()
