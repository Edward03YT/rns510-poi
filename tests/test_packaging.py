"""Tests for packaging, attribution generation, and ZIP creation."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from poi_forge.packaging import (
    compute_sha256,
    create_category_meta,
    create_country_zip,
    write_attribution_file,
    write_category_meta,
)


def test_write_attribution_file(tmp_path: Path):
    """Verify ODbL attribution file creation."""
    target_dir = tmp_path / "romania"
    attr_file = write_attribution_file(target_dir)

    assert attr_file.exists()
    content = attr_file.read_text(encoding="utf-8")
    assert "OpenStreetMap" in content
    assert "ODbL" in content
    assert "© OpenStreetMap contributors" in content


def test_compute_sha256(tmp_path: Path):
    """Verify SHA256 computation."""
    f = tmp_path / "test.asc"
    data = b"26.100000,44.400000,\"OMV\",\"\""
    f.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest().lower()
    assert compute_sha256(f) == expected


def test_create_and_write_category_meta(tmp_path: Path):
    """Verify creation and writing of category meta.json."""
    cat_dir = tmp_path / "romania" / "fuel"
    cat_dir.mkdir(parents=True)

    asc_file = cat_dir / "romania_fuel_001.asc"
    asc_file.write_bytes(b"sample asc content")

    meta = create_category_meta(
        country_id="romania",
        category_id="fuel",
        asc_files=[asc_file],
        count=15,
        osm_extract_date="2026-10-25T21:00:00Z",
    )

    assert meta["country"] == "romania"
    assert meta["category"] == "fuel"
    assert meta["count"] == 15
    assert len(meta["files"]) == 1
    assert meta["files"][0]["name"] == "romania_fuel_001.asc"

    meta_file = write_category_meta(cat_dir, meta)
    assert meta_file.exists()

    with open(meta_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["count"] == 15


def test_create_country_zip(tmp_path: Path):
    """Verify country ZIP archive bundles all files and ATTRIBUTION.txt."""
    country_dir = tmp_path / "romania"
    fuel_dir = country_dir / "fuel"
    fuel_dir.mkdir(parents=True)

    asc_file = fuel_dir / "romania_fuel_001.asc"
    asc_file.write_bytes(b"dummy asc")

    meta_file = fuel_dir / "meta.json"
    meta_file.write_text("{}", encoding="utf-8")

    out_zip = tmp_path / "romania.zip"
    create_country_zip(country_dir, out_zip)

    assert out_zip.exists()
    with zipfile.ZipFile(out_zip, "r") as zf:
        namelist = zf.namelist()
        assert "ATTRIBUTION.txt" in namelist
        assert "fuel/romania_fuel_001.asc" in namelist or "fuel\\romania_fuel_001.asc" in namelist
