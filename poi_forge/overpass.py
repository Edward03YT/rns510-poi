"""Custom area POI extraction using OpenStreetMap Overpass API with strict limits."""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import requests

from poi_forge.extract import load_categories, matches_category
from poi_forge.formats.base import POIRecord
from poi_forge.normalize import deduplicate_records, normalize_record

OVERPASS_DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"

# Strict limits to protect public Overpass API from abuse
MAX_RADIUS_KM = 25.0
MAX_BBOX_AREA_SQ_DEG = 0.25  # ~2,500 km²
DEFAULT_TIMEOUT_SEC = 25

# Rate limit tracker
_last_request_time: float = 0.0
MIN_REQUEST_INTERVAL_SEC = 2.0


def validate_custom_area_limits(
    radius_km: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> None:
    """Validate that custom area query is within allowed safety limits.

    Raises:
        ValueError: If radius or bounding box area exceeds allowed thresholds.
    """
    if radius_km is not None:
        if radius_km <= 0:
            raise ValueError("Radius must be greater than 0 km.")
        if radius_km > MAX_RADIUS_KM:
            raise ValueError(
                f"Radius {radius_km:.1f} km exceeds the maximum allowed limit of {MAX_RADIUS_KM} km "
                "to prevent overloading the public Overpass API."
            )

    if bbox is not None:
        min_lon, min_lat, max_lon, max_lat = bbox
        if min_lat >= max_lat or min_lon >= max_lon:
            raise ValueError("Invalid bounding box coordinates (min values must be less than max values).")
        width = max_lon - min_lon
        height = max_lat - min_lat
        area = width * height
        if area > MAX_BBOX_AREA_SQ_DEG:
            raise ValueError(
                f"Bounding box area ({area:.3f} sq deg) exceeds the maximum allowed limit of "
                f"{MAX_BBOX_AREA_SQ_DEG} sq deg (~2,500 km²)."
            )


def calculate_bbox_from_radius(
    lat: float, lon: float, radius_km: float
) -> tuple[float, float, float, float]:
    """Calculate approximate (min_lon, min_lat, max_lon, max_lat) from center and radius."""
    lat_deg_per_km = 1.0 / 110.574
    lon_deg_per_km = 1.0 / (111.320 * math.cos(math.radians(lat)))

    delta_lat = radius_km * lat_deg_per_km
    delta_lon = radius_km * lon_deg_per_km

    return (
        round(lon - delta_lon, 6),
        round(lat - delta_lat, 6),
        round(lon + delta_lon, 6),
        round(lat + delta_lat, 6),
    )


def build_overpass_query(
    categories: dict[str, dict[str, Any]],
    category_ids: list[str],
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> str:
    """Build Overpass QL query string with spatial filtering."""
    if radius_km is not None and lat is not None and lon is not None:
        validate_custom_area_limits(radius_km=radius_km)
        radius_m = int(radius_km * 1000)
        spatial_filter = f"(around:{radius_m},{lat:.6f},{lon:.6f})"
    elif bbox is not None:
        validate_custom_area_limits(bbox=bbox)
        min_lon, min_lat, max_lon, max_lat = bbox
        spatial_filter = f"({min_lat:.6f},{min_lon:.6f},{max_lat:.6f},{max_lon:.6f})"
    else:
        raise ValueError("Either (lat, lon, radius_km) or bbox must be specified.")

    query_parts = [f"[out:json][timeout:{DEFAULT_TIMEOUT_SEC}];", "("]

    for cat_id in category_ids:
        cat_def = categories.get(cat_id)
        if not cat_def:
            continue
        filters = cat_def.get("filters", {})
        all_f = filters.get("all", {})
        any_f = filters.get("any", {})

        # Construct tags selector
        tag_selectors = []
        for k, v in all_f.items():
            tag_selectors.append(f'["{k}"="{v}"]')

        for k, v_list in any_f.items():
            regex_val = "^(" + "|".join(v_list) + ")$"
            tag_selectors.append(f'["{k}"~"{regex_val}"]')

        if tag_selectors:
            sel_str = "".join(tag_selectors)
            query_parts.append(f"  node{sel_str}{spatial_filter};")
            query_parts.append(f"  way{sel_str}{spatial_filter};")

    query_parts.append(");")
    query_parts.append("out center tags;")
    return "\n".join(query_parts)


def query_overpass(
    query_str: str,
    endpoint: str = OVERPASS_DEFAULT_ENDPOINT,
    timeout: int = 35,
) -> dict[str, Any]:
    """Execute Overpass QL query with polite rate limiting and error handling."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL_SEC:
        time.sleep(MIN_REQUEST_INTERVAL_SEC - elapsed)

    try:
        resp = requests.post(
            endpoint,
            data={"data": query_str},
            headers={"User-Agent": "rns510-poi-forge/0.1.0"},
            timeout=timeout,
        )
        _last_request_time = time.time()

        if resp.status_code == 429:
            raise RuntimeError(
                "Overpass API rate limit reached (HTTP 429). "
                "Please wait 10-20 seconds before submitting another custom area query."
            )
        if resp.status_code == 504:
            raise RuntimeError(
                "Overpass API request timed out (HTTP 504). "
                "Please reduce the area radius or select fewer categories."
            )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            "Overpass API network connection timed out. Please try a smaller area."
        ) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Overpass API request failed: {e}") from e


def extract_overpass_elements(
    overpass_data: dict[str, Any],
    categories_path: Path | str | None = None,
    category_ids: list[str] | None = None,
    lang: str = "ro",
) -> dict[str, list[POIRecord]]:
    """Parse Overpass elements into normalized POIRecords by category."""
    categories = load_categories(categories_path)
    filter_set = set(category_ids) if category_ids else set(categories.keys())

    records_by_cat: dict[str, list[POIRecord]] = {cid: [] for cid in filter_set}

    elements = overpass_data.get("elements", [])
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        el_type = el.get("type")
        osm_id = f"{el_type[0]}{el.get('id')}"

        if el_type == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        elif el_type == "way":
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        else:
            continue

        if lat is None or lon is None:
            continue

        for cat_id in filter_set:
            cat_def = categories.get(cat_id)
            if not cat_def:
                continue

            if matches_category(tags, cat_def):
                rec = normalize_record(
                    osm_id=osm_id,
                    lat=lat,
                    lon=lon,
                    category_id=cat_id,
                    tags=tags,
                    category_def=cat_def,
                    lang=lang,
                )
                if rec is not None:
                    records_by_cat[cat_id].append(rec)

    # Deduplicate
    results: dict[str, list[POIRecord]] = {}
    for cat_id, records in records_by_cat.items():
        results[cat_id] = deduplicate_records(records)

    return results
