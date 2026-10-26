"""Tests for release index generation."""

from __future__ import annotations

import json
from pathlib import Path

from poi_forge.index import build_index, write_index


def test_build_index_structure(tmp_path: Path):
    """Verify build_index schema and structure matching specifications."""
    packages_dir = tmp_path / "packages"
    ro_fuel = packages_dir / "romania" / "fuel"
    ro_fuel.mkdir(parents=True)

    asc1 = ro_fuel / "romania_fuel_001.asc"
    asc1.write_bytes(b'26.1,44.4,"OMV",""\r\n')

    meta = {
        "country": "romania",
        "category": "fuel",
        "count": 4321,
        "files": [
            {
                "name": "romania_fuel_001.asc",
                "bytes": 123456,
                "sha256": "abc123sha256",
            }
        ],
        "osm_extract_date": "2026-10-25T21:21:00Z",
    }
    (ro_fuel / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    index_dict = build_index(packages_dir)

    assert index_dict["schema"] == 1
    assert "generated" in index_dict
    assert "format" in index_dict
    assert index_dict["format"]["verified"] is False

    countries = index_dict["countries"]
    assert len(countries) == 1
    ro = countries[0]
    assert ro["id"] == "romania"
    assert ro["osm_extract_date"] == "2026-10-25T21:21:00Z"
    assert len(ro["categories"]) == 1

    cat = ro["categories"][0]
    assert cat["id"] == "fuel"
    assert cat["count"] == 4321
    assert len(cat["files"]) == 1
    assert cat["files"][0]["name"] == "romania_fuel_001.asc"


def test_write_index(tmp_path: Path):
    """Verify writing index.json to disk."""
    out_file = tmp_path / "output_index.json"
    dummy = {"schema": 1, "test": True}
    written = write_index(dummy, out_file)

    assert written.exists()
    loaded = json.loads(written.read_text(encoding="utf-8"))
    assert loaded["schema"] == 1
    assert loaded["test"] is True
