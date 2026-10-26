"""Tests for pyosmium OSM PBF extraction using a synthetic PBF fixture."""

from __future__ import annotations

from pathlib import Path

import osmium
import pytest

from poi_forge.extract import extract_pois, matches_category


@pytest.fixture
def synthetic_pbf(tmp_path: Path) -> Path:
    """Generate a tiny valid .osm.pbf file using osmium.SimpleWriter."""
    pbf_file = tmp_path / "fixture.osm.pbf"
    writer = osmium.SimpleWriter(str(pbf_file))

    # Node 1: Fuel Station (OMV - Aviatorilor)
    n1 = osmium.osm.mutable.Node(
        id=1,
        location=(26.10, 44.40),
        tags={"amenity": "fuel", "brand": "OMV", "name": "Aviatorilor", "opening_hours": "24/7"},
    )
    writer.add_node(n1)

    # Node 2: EV Charging Station
    n2 = osmium.osm.mutable.Node(
        id=2,
        location=(26.11, 44.41),
        tags={"amenity": "charging_station", "operator": "Enel X", "socket:type2": "2", "maxpower": "50"},
    )
    writer.add_node(n2)

    # Node 3: ATM without name (tests fallback name)
    n3 = osmium.osm.mutable.Node(
        id=3,
        location=(26.12, 44.42),
        tags={"amenity": "atm", "operator": "Banca Transilvania"},
    )
    writer.add_node(n3)

    # Node 4: Irrelevant node (tree)
    n4 = osmium.osm.mutable.Node(
        id=4,
        location=(26.13, 44.43),
        tags={"natural": "tree"},
    )
    writer.add_node(n4)

    # Nodes for Way 10 (Closed building polygon for Supermarket)
    nw1 = osmium.osm.mutable.Node(id=101, location=(26.20, 44.50))
    nw2 = osmium.osm.mutable.Node(id=102, location=(26.22, 44.50))
    nw3 = osmium.osm.mutable.Node(id=103, location=(26.22, 44.52))
    nw4 = osmium.osm.mutable.Node(id=104, location=(26.20, 44.52))
    nw5 = osmium.osm.mutable.Node(id=105, location=(26.20, 44.50))
    for n in (nw1, nw2, nw3, nw4, nw5):
        writer.add_node(n)

    w10 = osmium.osm.mutable.Way(
        id=10,
        nodes=[101, 102, 103, 104, 105],
        tags={"shop": "supermarket", "name": "Kaufland"},
    )
    writer.add_way(w10)

    writer.close()
    return pbf_file


def test_matches_category():
    """Verify matches_category logic with all/any and custom rules."""
    cat_fuel = {"id": "fuel", "filters": {"all": {"amenity": "fuel"}}}
    cat_lpg = {"id": "lpg", "filters": {"all": {"amenity": "fuel", "fuel:lpg": "yes"}}}
    cat_parking = {"id": "parking_large"}

    # Fuel
    assert matches_category({"amenity": "fuel"}, cat_fuel) is True
    assert matches_category({"amenity": "restaurant"}, cat_fuel) is False

    # LPG
    assert matches_category({"amenity": "fuel", "fuel:lpg": "yes"}, cat_lpg) is True
    assert matches_category({"amenity": "fuel"}, cat_lpg) is False

    # Large parking
    assert matches_category({"amenity": "parking", "name": "Central"}, cat_parking) is True
    assert matches_category({"amenity": "parking", "capacity": "150"}, cat_parking) is True
    assert matches_category({"amenity": "parking"}, cat_parking) is False


def test_extract_pois_from_synthetic_pbf(synthetic_pbf: Path):
    """Verify full extraction from synthetic OSM PBF."""
    results = extract_pois(synthetic_pbf, lang="ro")

    # Check fuel extracted
    assert "fuel" in results
    assert len(results["fuel"]) == 1
    fuel_poi = results["fuel"][0]
    assert fuel_poi.id == "n1"
    assert fuel_poi.name == "OMV - Aviatorilor"
    assert "Hours: 24/7" in fuel_poi.description

    # Check EV charging extracted
    assert "ev_charging" in results
    assert len(results["ev_charging"]) == 1
    ev_poi = results["ev_charging"][0]
    assert ev_poi.id == "n2"
    assert "Enel X" in ev_poi.name
    assert "50kW" in ev_poi.description

    # Check ATM extracted with fallback name
    assert "atm" in results
    assert len(results["atm"]) == 1
    atm_poi = results["atm"][0]
    assert atm_poi.name == "Banca Transilvania"

    # Check Supermarket closed way extracted with centroid coordinates
    assert "supermarket" in results
    assert len(results["supermarket"]) == 1
    sm_poi = results["supermarket"][0]
    assert sm_poi.id == "w10"
    assert sm_poi.name == "Kaufland"
    # Centroid should be approximately lat 44.51, lon 26.21
    assert 44.50 < sm_poi.lat < 44.52
    assert 26.20 < sm_poi.lon < 26.22


def test_extract_pois_with_category_filter(synthetic_pbf: Path):
    """Verify that passing category_ids extracts only requested categories."""
    results = extract_pois(synthetic_pbf, category_ids=["fuel"])
    assert "fuel" in results
    assert len(results["fuel"]) == 1
    assert "ev_charging" not in results
    assert "supermarket" not in results
