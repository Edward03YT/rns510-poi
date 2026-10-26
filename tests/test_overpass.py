"""Tests for Overpass API custom area mode and strict limits."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from poi_forge.overpass import (
    MAX_RADIUS_KM,
    build_overpass_query,
    calculate_bbox_from_radius,
    extract_overpass_elements,
    query_overpass,
    validate_custom_area_limits,
)


def test_validate_custom_area_radius_limits():
    """Verify radius limit checks."""
    # Valid radius
    validate_custom_area_limits(radius_km=10.0)
    validate_custom_area_limits(radius_km=MAX_RADIUS_KM)

    # Exceeding radius
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit of 25.0 km"):
        validate_custom_area_limits(radius_km=30.0)

    # Negative or zero radius
    with pytest.raises(ValueError, match="must be greater than 0 km"):
        validate_custom_area_limits(radius_km=0.0)


def test_validate_custom_area_bbox_limits():
    """Verify bounding box area limit checks."""
    # Small bbox (~0.04 sq deg)
    validate_custom_area_limits(bbox=(26.0, 44.0, 26.2, 44.2))

    # Huge bbox (>0.25 sq deg, e.g. 1.0 * 1.0 = 1.0)
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit"):
        validate_custom_area_limits(bbox=(26.0, 44.0, 27.0, 45.0))


def test_calculate_bbox_from_radius():
    """Verify approximate bbox calculation from center point and radius."""
    min_lon, min_lat, max_lon, max_lat = calculate_bbox_from_radius(
        lat=44.4323, lon=26.1063, radius_km=10.0
    )
    assert min_lon < 26.1063 < max_lon
    assert min_lat < 44.4323 < max_lat


def test_build_overpass_query():
    """Verify Overpass QL generation."""
    categories = {
        "fuel": {"filters": {"all": {"amenity": "fuel"}}},
        "pharmacy": {"filters": {"all": {"amenity": "pharmacy"}}},
    }
    query = build_overpass_query(
        categories=categories,
        category_ids=["fuel", "pharmacy"],
        lat=44.4323,
        lon=26.1063,
        radius_km=5.0,
    )
    assert "[out:json][timeout:25];" in query
    assert "node[\"amenity\"=\"fuel\"](around:5000,44.432300,26.106300);" in query
    assert "way[\"amenity\"=\"fuel\"](around:5000,44.432300,26.106300);" in query
    assert "out center tags;" in query


def test_extract_overpass_elements():
    """Verify parsing raw Overpass JSON elements into POIRecords."""
    sample_data = {
        "elements": [
            {
                "type": "node",
                "id": 1001,
                "lat": 44.4323,
                "lon": 26.1063,
                "tags": {
                    "amenity": "fuel",
                    "brand": "MOL",
                    "name": "MOL Piata Victoriei",
                    "opening_hours": "24/7",
                },
            },
            {
                "type": "way",
                "id": 2001,
                "center": {"lat": 44.4350, "lon": 26.1090},
                "tags": {
                    "shop": "supermarket",
                    "name": "Mega Image",
                },
            },
        ]
    }
    pois = extract_overpass_elements(sample_data, lang="ro")
    assert "fuel" in pois
    assert len(pois["fuel"]) == 1
    assert pois["fuel"][0].name == "MOL Piata Victoriei"

    assert "supermarket" in pois
    assert len(pois["supermarket"]) == 1
    assert pois["supermarket"][0].name == "Mega Image"


def test_query_overpass_rate_limit_error():
    """Verify rate limit (HTTP 429) generates clear user message."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="rate limit reached"):
            query_overpass("[out:json];")


def test_query_overpass_timeout_error():
    """Verify timeout (HTTP 504) generates clear user message."""
    mock_resp = MagicMock()
    mock_resp.status_code = 504
    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="timed out"):
            query_overpass("[out:json];")
