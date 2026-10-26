"""Geofabrik country index and extract URL resolution."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml

GEOFABRIK_INDEX_URL = "https://download.geofabrik.de/index-v1.json"


@dataclass
class CountryMetadata:
    """Metadata for a country extract from Geofabrik index and config."""

    id: str
    name: dict[str, str]  # {"ro": "...", "en": "..."}
    publish: bool
    pbf_url: str
    md5_url: str
    parent: str = "europe"
    iso_codes: list[str] = field(default_factory=list)
    sub_extract_ids: list[str] = field(default_factory=list)


def load_countries_config(config_path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load config/countries.yml if present."""
    if config_path is None:
        config_path = Path("config/countries.yml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return {}

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    countries_list = data.get("countries", [])
    return {c["id"]: c for c in countries_list if "id" in c}


def fetch_geofabrik_index(
    cache_dir: Path | str | None = None,
    max_age_seconds: int = 86400,  # 24 hours
    timeout: int = 20,
) -> dict[str, Any]:
    """Fetch index-v1.json from Geofabrik with local caching.

    Args:
        cache_dir: Directory where the cached index JSON is stored.
        max_age_seconds: Maximum age of cached index before re-fetching.
        timeout: HTTP request timeout in seconds.
    """
    cache_path: Path | None = None
    if cache_dir is not None:
        cache_p = Path(cache_dir)
        cache_p.mkdir(parents=True, exist_ok=True)
        cache_path = cache_p / "geofabrik_index_v1.json"

        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < max_age_seconds:
                try:
                    with open(cache_path, encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    # Corrupted cache, will re-download
                    pass

    # Download from remote
    try:
        resp = requests.get(GEOFABRIK_INDEX_URL, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if cache_path is not None:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        return data
    except Exception as e:
        # Fallback to expired cache if available
        if cache_path is not None and cache_path.exists():
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        raise RuntimeError(f"Failed to fetch Geofabrik index: {e}") from e


def resolve_european_countries(
    cache_dir: Path | str | None = None,
    config_path: Path | str | None = None,
    publish_only: bool = False,
) -> list[CountryMetadata]:
    """Resolve European countries by combining Geofabrik index with local config.

    Args:
        cache_dir: Cache directory for Geofabrik index.
        config_path: Path to config/countries.yml.
        publish_only: If True, returns only countries with publish: true.
    """
    index_data = fetch_geofabrik_index(cache_dir=cache_dir)
    features = index_data.get("features", [])
    config_map = load_countries_config(config_path=config_path)

    # Map children for each parent
    children_map: dict[str, list[str]] = {}
    for feat in features:
        props = feat.get("properties", {})
        parent = props.get("parent")
        cid = props.get("id")
        if parent and cid:
            children_map.setdefault(parent, []).append(cid)

    results: list[CountryMetadata] = []

    for feat in features:
        props = feat.get("properties", {})
        parent = props.get("parent")
        cid = props.get("id")
        urls = props.get("urls", {})
        pbf_url = urls.get("pbf")

        # We care about direct Europe entities or configured entities
        if not cid or not pbf_url:
            continue

        is_direct_europe = parent == "europe"
        in_config = cid in config_map

        if not (is_direct_europe or in_config):
            continue

        cfg_item = config_map.get(cid, {})
        default_name = props.get("name", cid)
        names = cfg_item.get("name", {"ro": default_name, "en": default_name})
        publish = cfg_item.get("publish", is_direct_europe)

        if publish_only and not publish:
            continue

        md5_url = pbf_url + ".md5"
        iso_codes = props.get("iso3166-1:alpha2", [])

        results.append(
            CountryMetadata(
                id=cid,
                name=names,
                publish=publish,
                pbf_url=pbf_url,
                md5_url=md5_url,
                parent=parent or "europe",
                iso_codes=iso_codes,
                sub_extract_ids=children_map.get(cid, []),
            )
        )

    # Sort alphabetically by English name
    results.sort(key=lambda c: c.name.get("en", c.id))
    return results


def get_country(
    country_id: str,
    cache_dir: Path | str | None = None,
    config_path: Path | str | None = None,
) -> CountryMetadata:
    """Find a specific country by Geofabrik ID.

    Raises:
        KeyError: If country is not found in European extracts.
    """
    countries = resolve_european_countries(
        cache_dir=cache_dir,
        config_path=config_path,
        publish_only=False,
    )
    for c in countries:
        if c.id == country_id:
            return c
    raise KeyError(f"Country with Geofabrik ID '{country_id}' not found in European index.")
