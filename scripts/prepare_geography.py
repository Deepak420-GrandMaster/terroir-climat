"""Download département boundaries and derive their centroids.

    python scripts/prepare_geography.py

Writes ``data/raw/departements.geojson`` and ``departements_centroids.csv``.
Both are small and committed to the repo, so this only needs running if you
want to refresh them — the app works without ever calling it.

Centroids are area-weighted across a département's polygons, so an island
commune does not drag the point off the mainland. No GeoPandas: the shoelace
formula is a dozen lines and this keeps the dependency list short enough that
the app installs in seconds.
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CENTROIDS, GEOJSON, RAW  # noqa: E402

SOURCE = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements-version-simplifiee.geojson"
)


def ring_centroid(ring: list) -> tuple[float, float, float] | None:
    """Centroid and absolute area of one closed ring, by the shoelace formula."""
    area = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[i + 1][0], ring[i + 1][1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if area == 0:
        return None
    area *= 0.5
    return cx / (6 * area), cy / (6 * area), abs(area)


def feature_centroid(geometry: dict) -> tuple[float, float] | None:
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    elif geometry["type"] == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        return None

    sx = sy = total = 0.0
    for polygon in polygons:
        result = ring_centroid(polygon[0])   # outer ring only
        if result is None:
            continue
        x, y, area = result
        sx += x * area
        sy += y * area
        total += area
    if total == 0:
        return None
    return sx / total, sy / total


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)

    if not GEOJSON.exists():
        print(f"downloading {SOURCE}")
        req = urllib.request.Request(SOURCE, headers={"User-Agent": "terroir-climat/0.1"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            GEOJSON.write_bytes(resp.read())
    geo = json.loads(GEOJSON.read_text())
    print(f"{len(geo['features'])} départements in {GEOJSON.name}")

    rows = []
    for feature in geo["features"]:
        props = feature["properties"]
        point = feature_centroid(feature["geometry"])
        if point is None:
            print(f"  skipped {props.get('code')}: no usable geometry")
            continue
        lon, lat = point
        rows.append({"code": props["code"], "nom": props["nom"],
                     "lat": round(lat, 4), "lon": round(lon, 4)})

    rows.sort(key=lambda r: r["code"])
    with CENTROIDS.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["code", "nom", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)

    lats = [r["lat"] for r in rows]
    lons = [r["lon"] for r in rows]
    print(f"wrote {CENTROIDS} — {len(rows)} centroids")
    print(f"  lat {min(lats):.2f}..{max(lats):.2f}   lon {min(lons):.2f}..{max(lons):.2f}")
    if not (41 < min(lats) and max(lats) < 52 and -6 < min(lons) and max(lons) < 10):
        print("  WARNING: centroids fall outside metropolitan France")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
