"""Folium map construction, kept away from the page layout."""

from __future__ import annotations

import branca.colormap as cm
import folium
import pandas as pd

from ..config import NORMAL_END, NORMAL_START, RAMP_DRY_TO_WET
from ..i18n import t

FRANCE_CENTER = (46.6, 2.4)
FRANCE_ZOOM = 6


def anomaly_scale(vmax: float, lang: str = "en") -> cm.LinearColormap:
    """A symmetric dry-to-wet scale centred on zero.

    Symmetry matters: if the scale ran from the minimum to the maximum of a
    single year, a wet year would paint the whole country blue and a dry one
    the whole country brown, and no two years could be compared. Fixing the
    midpoint at zero and mirroring the ends keeps the colours meaning the same
    thing whichever year is selected.
    """
    vmax = max(float(vmax), 1.0)
    scale = cm.LinearColormap(RAMP_DRY_TO_WET, vmin=-vmax, vmax=vmax)
    scale.caption = t(lang, "map_legend", n0=NORMAL_START, n1=NORMAL_END)
    return scale


def choropleth(
    geojson: dict,
    values: pd.DataFrame,
    value_col: str,
    label_col: str,
    vmax: float,
    unit: str = "mm",
    lang: str = "en",
) -> folium.Map:
    """One département per polygon, shaded by ``value_col``."""
    lookup = values.set_index("code")
    scale = anomaly_scale(vmax, lang)

    # OpenStreetMap, not CartoDB Positron: as of 2026 the Carto basemaps
    # require an API key, and a key would break the "no accounts, no keys"
    # promise the whole project is built on. OSM's default style is busier,
    # so opacity is kept high enough that the choropleth stays dominant.
    fmap = folium.Map(
        location=FRANCE_CENTER,
        zoom_start=FRANCE_ZOOM,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    def style(feature):
        code = feature["properties"]["code"]
        if code not in lookup.index:
            return {"fillColor": "#d9ddda", "color": "#ffffff",
                    "weight": 0.7, "fillOpacity": 0.55}
        value = lookup.at[code, value_col]
        if pd.isna(value):
            return {"fillColor": "#d9ddda", "color": "#ffffff",
                    "weight": 0.7, "fillOpacity": 0.55}
        return {"fillColor": scale(float(value)), "color": "#ffffff",
                "weight": 0.7, "fillOpacity": 0.88}

    def highlight(_feature):
        return {"weight": 2.2, "color": "#141a1e"}

    enriched = {"type": "FeatureCollection", "features": []}
    for feature in geojson["features"]:
        code = feature["properties"]["code"]
        props = dict(feature["properties"])
        if code in lookup.index:
            value = lookup.at[code, value_col]
            props["value"] = (t(lang, "map_no_data") if pd.isna(value)
                              else f"{value:,.0f} {unit}")
            props["detail"] = str(lookup.at[code, label_col])
        else:
            props["value"] = t(lang, "map_no_data")
            props["detail"] = "—"
        enriched["features"].append(
            {"type": "Feature", "geometry": feature["geometry"], "properties": props}
        )

    folium.GeoJson(
        enriched,
        style_function=style,
        highlight_function=highlight,
        tooltip=folium.GeoJsonTooltip(
            fields=["nom", "value", "detail"],
            aliases=["", "", ""],
            sticky=True,
            style=(
                "background:#fff;border:1px solid #d9ddda;border-radius:4px;"
                "padding:6px 8px;font-family:ui-monospace,Menlo,monospace;font-size:11px;"
            ),
        ),
        name="départements",
    ).add_to(fmap)

    scale.add_to(fmap)
    return fmap
