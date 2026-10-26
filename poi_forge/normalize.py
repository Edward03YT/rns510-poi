"""POI normalization, deduplication, and name templating."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from poi_forge.formats.base import POIRecord

WHITESPACE_RE = re.compile(r"\s+")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Keys that must never be added to descriptions to preserve privacy and space
FORBIDDEN_DESCRIPTION_KEYS = {
    "phone",
    "mobile",
    "fax",
    "email",
    "contact:phone",
    "contact:mobile",
    "contact:email",
    "contact:fax",
    "contact:website",
    "website",
    "url",
    "image",
    "source",
}


def build_poi_name(
    tags: Mapping[str, str],
    fallback_name: str = "",
) -> str:
    """Build POI name according to template: '<brand/operator> - <name>'.

    When both exist and differ, formats as '<brand or operator> - <name>',
    else whichever exists, else localized fallback.
    """
    raw_name = tags.get("name", "").strip()
    brand = (tags.get("brand") or tags.get("operator") or "").strip()

    name = WHITESPACE_RE.sub(" ", raw_name).strip()
    brand = WHITESPACE_RE.sub(" ", brand).strip()

    if brand and name and brand.lower() != name.lower():
        # Check if brand is already a prefix or suffix of name to avoid "Petrom - Petrom Aviatorilor"
        if name.lower().startswith(brand.lower()):
            final_name = name
        else:
            final_name = f"{brand} - {name}"
    elif brand:
        final_name = brand
    elif name:
        final_name = name
    else:
        final_name = fallback_name

    return final_name


# EV charging socket standard display names
SOCKET_DISPLAY = {
    "type2": "Type 2",
    "type2_combo": "CCS (Combo 2)",
    "type3": "Type 3",
    "chademo": "CHAdeMO",
    "tesla_supercharger": "Tesla Supercharger",
    "schuko": "Schuko",
    "type1": "Type 1",
    "type1_combo": "CCS (Combo 1)",
}


def build_poi_description(
    tags: Mapping[str, str],
    allowed_tags: list[str] | None = None,
) -> str:
    """Build concise, privacy-safe description from allowed OSM tags."""
    parts: list[str] = []

    # Opening hours
    hours = tags.get("opening_hours")
    if hours and len(hours) <= 40:
        parts.append(f"Hours: {hours}")

    # Capacity
    cap = tags.get("capacity")
    if cap:
        parts.append(f"Cap: {cap}")

    # EV specific sockets
    ev_sockets: list[str] = []
    for k, v in tags.items():
        if k.startswith("socket:") and v not in ("no", "0"):
            raw_key = k[len("socket:") :]
            socket_type = SOCKET_DISPLAY.get(
                raw_key, raw_key.replace("_", " ").title()
            )
            if v in ("yes", "1"):
                ev_sockets.append(socket_type)
            else:
                ev_sockets.append(f"{socket_type} x{v}")

    if ev_sockets:
        parts.append(", ".join(ev_sockets[:3]))

    # Max power for charging
    power = tags.get("maxpower")
    if power:
        parts.append(f"{power}kW")

    # Extra allowed tags if specified
    if allowed_tags:
        for tag in allowed_tags:
            if tag in FORBIDDEN_DESCRIPTION_KEYS or tag.startswith("contact:"):
                continue
            if tag in tags and tag not in ("opening_hours", "capacity", "maxpower"):
                val = tags[tag].strip()
                if val and val != "yes" and len(val) <= 30:
                    parts.append(f"{tag.replace('_', ' ').title()}: {val}")

    return ", ".join(parts)


def deduplicate_records(
    records: list[POIRecord],
    coordinate_decimals: int = 4,  # ~11 meters resolution
) -> list[POIRecord]:
    """Deduplicate records by (~10m coordinates, normalized lowercase name, category).

    When duplicate records are encountered, keeps the one with the longest description.
    """
    seen: dict[tuple[float, float, str, str], POIRecord] = {}

    for record in records:
        key = (
            round(record.lat, coordinate_decimals),
            round(record.lon, coordinate_decimals),
            record.name.lower().strip(),
            record.category,
        )

        existing = seen.get(key)
        if existing is None:
            seen[key] = record
        else:
            # Keep richer record
            if len(record.description) > len(existing.description):
                seen[key] = record

    # Deterministic sort
    deduped = list(seen.values())
    deduped.sort(key=lambda r: (r.category, r.name, r.lat, r.lon, r.id))
    return deduped


def normalize_record(
    osm_id: str,
    lat: float,
    lon: float,
    category_id: str,
    tags: Mapping[str, str],
    category_def: dict[str, Any],
    lang: str = "ro",
) -> POIRecord | None:
    """Normalize raw OSM element into POIRecord."""
    fallback_dict = category_def.get("fallback_name", {})
    fallback_name = fallback_dict.get(lang, fallback_dict.get("en", ""))

    name = build_poi_name(tags, fallback_name=fallback_name)
    if not name:
        # Drop POI if no name and no fallback available
        return None

    allowed_desc_tags = category_def.get("description_tags", [])
    desc = build_poi_description(tags, allowed_tags=allowed_desc_tags)

    return POIRecord(
        id=osm_id,
        lat=lat,
        lon=lon,
        name=name,
        description=desc,
        category=category_id,
        extra=dict(tags),
    )
