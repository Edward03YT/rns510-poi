"""Release index builder for web app consumption."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from poi_forge.countries import load_countries_config
from poi_forge.formats.rns510_asc import RNS510AscConfig
from poi_forge.packaging import compute_sha256


def build_index(
    packages_dir: Path | str,
    format_config_path: Path | str | None = None,
    countries_config_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build the index.json dictionary by scanning the packages directory.

    Args:
        packages_dir: Directory containing per-country package subdirectories.
        format_config_path: Path to config/format.yml.
        countries_config_path: Path to config/countries.yml.
    """
    packages_path = Path(packages_dir)
    countries_cfg = load_countries_config(countries_config_path)

    if format_config_path and Path(format_config_path).exists():
        fmt_cfg = RNS510AscConfig.from_yaml(format_config_path)
    else:
        fmt_cfg = RNS510AscConfig()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    countries_data: list[dict[str, Any]] = []

    if packages_path.exists():
        for country_dir in sorted(packages_path.iterdir()):
            if not country_dir.is_dir():
                continue

            country_id = country_dir.name
            country_cfg = countries_cfg.get(country_id, {})
            name_dict = country_cfg.get(
                "name", {"ro": country_id.title(), "en": country_id.title()}
            )

            categories_list: list[dict[str, Any]] = []
            country_extract_date: str | None = None

            for cat_dir in sorted(country_dir.iterdir()):
                if not cat_dir.is_dir():
                    continue

                cat_id = cat_dir.name
                meta_file = cat_dir / "meta.json"

                if meta_file.exists():
                    try:
                        with open(meta_file, encoding="utf-8") as f:
                            meta = json.load(f)
                        count = meta.get("count", 0)
                        files = meta.get("files", [])
                        if not country_extract_date and "osm_extract_date" in meta:
                            country_extract_date = meta["osm_extract_date"]
                    except Exception:
                        count, files = _scan_category_files(cat_dir)
                else:
                    count, files = _scan_category_files(cat_dir)

                if files:
                    categories_list.append({
                        "id": cat_id,
                        "count": count,
                        "files": files,
                    })

            if categories_list:
                countries_data.append({
                    "id": country_id,
                    "name": name_dict,
                    "osm_extract_date": country_extract_date or now_iso,
                    "categories": categories_list,
                })

    countries_data.sort(key=lambda c: c["name"].get("en", c["id"]))

    return {
        "schema": 1,
        "generated": now_iso,
        "format": {
            "verified": fmt_cfg.verified,
            "note": fmt_cfg.verification_note,
        },
        "countries": countries_data,
    }


def _scan_category_files(cat_dir: Path) -> tuple[int, list[dict[str, Any]]]:
    """Fallback scanner if meta.json does not exist."""
    files: list[dict[str, Any]] = []
    total_count = 0
    for asc in sorted(cat_dir.glob("*.asc")):
        lines_count = 0
        try:
            with open(asc, "rb") as f:
                lines_count = sum(1 for line in f if line.strip())
        except Exception:
            pass
        total_count += lines_count
        files.append({
            "name": asc.name,
            "bytes": asc.stat().st_size,
            "sha256": compute_sha256(asc),
        })
    return total_count, files


def write_index(
    index_dict: dict[str, Any],
    output_path: Path | str,
) -> Path:
    """Write index dictionary to JSON file."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index_dict, f, indent=2, ensure_ascii=False)
    return out
