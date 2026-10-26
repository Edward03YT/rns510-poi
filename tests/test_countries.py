"""Tests for Geofabrik country index resolution."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from poi_forge.countries import (
    fetch_geofabrik_index,
    get_country,
    load_countries_config,
    resolve_european_countries,
)

SAMPLE_GEOFABRIK_INDEX = {
    "features": [
        {
            "properties": {
                "id": "romania",
                "name": "Romania",
                "parent": "europe",
                "iso3166-1:alpha2": ["RO"],
                "urls": {
                    "pbf": "https://download.geofabrik.de/europe/romania-latest.osm.pbf",
                },
            }
        },
        {
            "properties": {
                "id": "luxembourg",
                "name": "Luxembourg",
                "parent": "europe",
                "iso3166-1:alpha2": ["LU"],
                "urls": {
                    "pbf": "https://download.geofabrik.de/europe/luxembourg-latest.osm.pbf",
                },
            }
        },
        {
            "properties": {
                "id": "alps",
                "name": "Alps",
                "parent": "europe",
                "urls": {
                    "pbf": "https://download.geofabrik.de/europe/alps-latest.osm.pbf",
                },
            }
        },
        {
            "properties": {
                "id": "japan",
                "name": "Japan",
                "parent": "asia",
                "urls": {
                    "pbf": "https://download.geofabrik.de/asia/japan-latest.osm.pbf",
                },
            }
        },
    ]
}


def test_load_countries_config(tmp_path: Path):
    """Verify loading countries configuration."""
    cfg_file = tmp_path / "countries.yml"
    cfg_file.write_text(
        "countries:\n"
        "  - id: romania\n"
        "    name: { ro: 'România', en: 'Romania' }\n"
        "    publish: true\n"
        "  - id: alps\n"
        "    name: { ro: 'Alpi', en: 'Alps' }\n"
        "    publish: false\n",
        encoding="utf-8",
    )

    loaded = load_countries_config(cfg_file)
    assert "romania" in loaded
    assert loaded["romania"]["publish"] is True
    assert loaded["alps"]["publish"] is False


def test_fetch_geofabrik_index_caching(tmp_path: Path):
    """Verify fetch_geofabrik_index caches response to disk."""
    cache_dir = tmp_path / "cache"

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_GEOFABRIK_INDEX
        mock_get.return_value = mock_resp

        # First call fetches via HTTP
        data1 = fetch_geofabrik_index(cache_dir=cache_dir)
        assert len(data1["features"]) == 4
        assert mock_get.call_count == 1

        # Second call should read from local cache file without HTTP call
        data2 = fetch_geofabrik_index(cache_dir=cache_dir)
        assert len(data2["features"]) == 4
        assert mock_get.call_count == 1


def test_resolve_european_countries(tmp_path: Path):
    """Verify resolving European countries and filtering out non-European."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "geofabrik_index_v1.json"
    cache_file.write_text(json.dumps(SAMPLE_GEOFABRIK_INDEX), encoding="utf-8")

    cfg_file = tmp_path / "countries.yml"
    cfg_file.write_text(
        "countries:\n"
        "  - id: romania\n"
        "    name: { ro: 'România', en: 'Romania' }\n"
        "    publish: true\n"
        "  - id: alps\n"
        "    publish: false\n",
        encoding="utf-8",
    )

    all_countries = resolve_european_countries(
        cache_dir=cache_dir,
        config_path=cfg_file,
        publish_only=False,
    )
    # Romania, Luxembourg, Alps are in Europe; Japan is in Asia
    ids = [c.id for c in all_countries]
    assert "romania" in ids
    assert "luxembourg" in ids
    assert "alps" in ids
    assert "japan" not in ids

    # Test publish_only filter
    published = resolve_european_countries(
        cache_dir=cache_dir,
        config_path=cfg_file,
        publish_only=True,
    )
    pub_ids = [c.id for c in published]
    assert "romania" in pub_ids
    assert "luxembourg" in pub_ids
    assert "alps" not in pub_ids


def test_get_country(tmp_path: Path):
    """Verify retrieving a single country by ID."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "geofabrik_index_v1.json"
    cache_file.write_text(json.dumps(SAMPLE_GEOFABRIK_INDEX), encoding="utf-8")

    ro = get_country("romania", cache_dir=cache_dir, config_path=tmp_path / "none.yml")
    assert ro.id == "romania"
    assert ro.pbf_url == "https://download.geofabrik.de/europe/romania-latest.osm.pbf"
    assert ro.md5_url == "https://download.geofabrik.de/europe/romania-latest.osm.pbf.md5"

    with pytest.raises(KeyError):
        get_country("unknown-country", cache_dir=cache_dir, config_path=tmp_path / "none.yml")
