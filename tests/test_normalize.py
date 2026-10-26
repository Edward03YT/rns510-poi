"""Tests for POI normalization, templating, privacy rules, and deduplication."""

from __future__ import annotations

from poi_forge.formats.base import POIRecord
from poi_forge.normalize import (
    build_poi_description,
    build_poi_name,
    deduplicate_records,
    normalize_record,
)


def test_build_poi_name_both_differ():
    """When brand and name both exist and differ, format as '<brand> - <name>'."""
    tags = {"brand": "OMV", "name": "Băneasa Nord"}
    assert build_poi_name(tags, "Benzinărie") == "OMV - Băneasa Nord"


def test_build_poi_name_brand_prefix_avoids_repetition():
    """When name already starts with brand, do not repeat brand."""
    tags = {"brand": "Petrom", "name": "Petrom Aviatorilor"}
    assert build_poi_name(tags, "Benzinărie") == "Petrom Aviatorilor"


def test_build_poi_name_only_brand_or_name():
    """When only one exists, use that one."""
    assert build_poi_name({"brand": "MOL"}, "Benzinărie") == "MOL"
    assert build_poi_name({"name": "Parcare Centru"}, "Parcare") == "Parcare Centru"


def test_build_poi_name_fallback():
    """When neither brand nor name exists, use localized fallback."""
    assert build_poi_name({}, fallback_name="Farmacie") == "Farmacie"


def test_build_poi_description_privacy_stripping():
    """Ensure personal data like phone, mobile, email, contact:* are never included."""
    tags = {
        "brand": "Shell",
        "phone": "+40722123456",
        "contact:phone": "+40722123456",
        "email": "manager@shell.ro",
        "contact:email": "private@example.com",
        "opening_hours": "24/7",
    }
    desc = build_poi_description(tags, allowed_tags=["opening_hours", "phone", "email"])
    assert "Hours: 24/7" in desc
    assert "+40722123456" not in desc
    assert "manager@shell.ro" not in desc
    assert "private@example.com" not in desc


def test_build_poi_description_ev_charging():
    """Verify EV charging socket formatting."""
    tags = {
        "amenity": "charging_station",
        "socket:type2": "2",
        "socket:type2_combo": "2",
        "maxpower": "150",
        "capacity": "4",
        "opening_hours": "24/7",
    }
    desc = build_poi_description(tags)
    assert "Type 2 x2" in desc
    assert "CCS (Combo 2) x2" in desc
    assert "150kW" in desc
    assert "Cap: 4" in desc
    assert "Hours: 24/7" in desc


def test_deduplicate_records():
    """Verify deduplication by ~10m coordinates, name, and category, keeping richer description."""
    r1 = POIRecord(
        id="n1",
        lat=44.43231,
        lon=26.10631,
        name="Petrom",
        description="Hours: 24/7",
        category="fuel",
    )
    # r2 is ~3 meters away from r1, same name and category, but with richer description
    r2 = POIRecord(
        id="w2",
        lat=44.43234,
        lon=26.10633,
        name="petrom",
        description="Hours: 24/7, Cap: 8, LPG",
        category="fuel",
    )
    # r3 is different category
    r3 = POIRecord(
        id="n3",
        lat=44.43232,
        lon=26.10632,
        name="Petrom",
        description="ATM",
        category="atm",
    )
    # r4 is far away
    r4 = POIRecord(
        id="n4",
        lat=44.50000,
        lon=26.20000,
        name="Petrom",
        description="Hours: 24/7",
        category="fuel",
    )

    records = [r1, r2, r3, r4]
    deduped = deduplicate_records(records, coordinate_decimals=4)

    # r1 and r2 merged into 1 fuel record (keeping richer r2)
    # r3 kept (different category)
    # r4 kept (different location)
    assert len(deduped) == 3

    fuel_at_site = [r for r in deduped if r.category == "fuel" and r.lat < 44.45]
    assert len(fuel_at_site) == 1
    assert "Cap: 8" in fuel_at_site[0].description


def test_normalize_record():
    """Verify end-to-end normalization of raw OSM element."""
    cat_def = {
        "id": "fuel",
        "fallback_name": {"ro": "Benzinărie", "en": "Fuel Station"},
        "description_tags": ["opening_hours", "brand"],
    }
    tags = {"amenity": "fuel", "brand": "Rompetrol", "opening_hours": "24/7"}
    record = normalize_record(
        osm_id="n123",
        lat=44.4,
        lon=26.1,
        category_id="fuel",
        tags=tags,
        category_def=cat_def,
        lang="ro",
    )
    assert record is not None
    assert record.name == "Rompetrol"
    assert "Hours: 24/7" in record.description
    assert record.category == "fuel"
