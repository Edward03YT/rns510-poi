"""OpenStreetMap PBF extraction using pyosmium."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import osmium
import yaml

from poi_forge.formats.base import POIRecord
from poi_forge.normalize import deduplicate_records, normalize_record


def load_categories(categories_path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Load config/categories.yml."""
    if categories_path is None:
        categories_path = Path("config/categories.yml")
    else:
        categories_path = Path(categories_path)

    with open(categories_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cat_list = data.get("categories", [])
    return {c["id"]: c for c in cat_list if "id" in c}


def matches_category(tags: Mapping[str, str], cat_def: dict[str, Any]) -> bool:
    """Check if OSM tags match a category definition."""
    cat_id = cat_def.get("id")
    filters = cat_def.get("filters", {})

    # Check custom rule for parking_large
    if cat_id == "parking_large":
        if tags.get("amenity") != "parking":
            return False
        has_name = bool(tags.get("name"))
        has_pr = "park_ride" in tags
        cap_val = 0
        try:
            cap_val = int(tags.get("capacity", 0))
        except (ValueError, TypeError):
            cap_val = 0
        return has_name or has_pr or cap_val >= 100

    # General 'all' condition
    all_filters = filters.get("all")
    if all_filters:
        for k, v in all_filters.items():
            if tags.get(k) != v:
                return False

    # General 'any' condition
    any_filters = filters.get("any")
    if any_filters:
        for k, v_list in any_filters.items():
            if tags.get(k) not in v_list:
                return False

    return True


class POIExtractionHandler(osmium.SimpleHandler):
    """Pyosmium handler that filters nodes and ways into POIRecords."""

    def __init__(
        self,
        categories: dict[str, dict[str, Any]],
        filter_category_ids: set[str] | None = None,
        lang: str = "ro",
    ) -> None:
        super().__init__()
        self.categories = categories
        self.filter_category_ids = filter_category_ids
        self.lang = lang
        self.records_by_category: dict[str, list[POIRecord]] = {
            cid: [] for cid in categories if not filter_category_ids or cid in filter_category_ids
        }

    def _process_element(
        self,
        osm_id: str,
        lat: float,
        lon: float,
        tags: Mapping[str, str],
    ) -> None:
        """Evaluate tags and create POIRecords for matching categories."""
        if not tags:
            return

        for cat_id, cat_def in self.categories.items():
            if self.filter_category_ids and cat_id not in self.filter_category_ids:
                continue

            if matches_category(tags, cat_def):
                record = normalize_record(
                    osm_id=osm_id,
                    lat=lat,
                    lon=lon,
                    category_id=cat_id,
                    tags=tags,
                    category_def=cat_def,
                    lang=self.lang,
                )
                if record is not None:
                    self.records_by_category[cat_id].append(record)

    def node(self, n: osmium.osm.Node) -> None:
        """Handle OSM node elements."""
        if not n.location.valid():
            return
        tags = {tag.k: tag.v for tag in n.tags}
        self._process_element(
            osm_id=f"n{n.id}",
            lat=n.location.lat,
            lon=n.location.lon,
            tags=tags,
        )

    def way(self, w: osmium.osm.Way) -> None:
        """Handle OSM way elements by calculating centroid from valid nodes."""
        if not w.nodes:
            return

        # Fast check: does way have any relevant tag before computing centroid?
        tags = {tag.k: tag.v for tag in w.tags}
        if not tags:
            return

        has_potential_match = False
        for cat_id, cat_def in self.categories.items():
            if self.filter_category_ids and cat_id not in self.filter_category_ids:
                continue
            if matches_category(tags, cat_def):
                has_potential_match = True
                break

        if not has_potential_match:
            return

        valid_coords: list[tuple[float, float]] = []
        for node in w.nodes:
            try:
                valid_coords.append((node.lat, node.lon))
            except (osmium.InvalidLocationError, AttributeError):
                pass

        if not valid_coords:
            return

        # Compute centroid (average coordinates of way nodes)
        centroid_lat = sum(lat for lat, _ in valid_coords) / len(valid_coords)
        centroid_lon = sum(lon for _, lon in valid_coords) / len(valid_coords)

        self._process_element(
            osm_id=f"w{w.id}",
            lat=centroid_lat,
            lon=centroid_lon,
            tags=tags,
        )


def extract_pois(
    pbf_path: Path | str,
    categories_path: Path | str | None = None,
    category_ids: list[str] | None = None,
    lang: str = "ro",
) -> dict[str, list[POIRecord]]:
    """Extract POIs from an OSM PBF file and return deduplicated records by category.

    Args:
        pbf_path: Path to the .osm.pbf file.
        categories_path: Path to config/categories.yml.
        category_ids: Optional list of category IDs to extract (extracts all if None).
        lang: Language for fallback names ("ro" or "en").

    Returns:
        Dictionary mapping category ID to list of deduplicated, sorted POIRecords.
    """
    categories = load_categories(categories_path)
    filter_set = set(category_ids) if category_ids else None

    handler = POIExtractionHandler(
        categories=categories,
        filter_category_ids=filter_set,
        lang=lang,
    )

    # Apply file with location cache enabled for way centroid calculation
    handler.apply_file(str(pbf_path), locations=True)

    # Deduplicate each category
    result: dict[str, list[POIRecord]] = {}
    for cat_id, records in handler.records_by_category.items():
        result[cat_id] = deduplicate_records(records)

    return result
