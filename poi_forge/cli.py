"""Command Line Interface for rns510-poi-forge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from poi_forge.countries import get_country, resolve_european_countries
from poi_forge.download import download_pbf_with_cache
from poi_forge.extract import extract_pois, load_categories
from poi_forge.formats.base import POIRecord
from poi_forge.formats.rns510_asc import RNS510AscConfig, RNS510AscWriter
from poi_forge.index import build_index, write_index
from poi_forge.overpass import (
    MAX_RADIUS_KM,
    build_overpass_query,
    extract_overpass_elements,
    query_overpass,
    validate_custom_area_limits,
)
from poi_forge.packaging import (
    create_category_meta,
    create_country_zip,
    write_attribution_file,
    write_category_meta,
)
from poi_forge.validate import validate_path


def create_probe_records(
    center_lat: float = 44.4323,
    center_lon: float = 26.1063,
    count: int = 5,
    preset: str = "probe",
) -> list[POIRecord]:
    """Generate synthetic POIs for format probing and hardware testing."""
    if preset == "probe":
        records = [
            POIRecord(
                id="probe-001",
                lat=center_lat + 0.0020,
                lon=center_lon + 0.0020,
                name="OMV Aviatorilor",
                description="Fuel 24/7, MaxxMotion 100plus",
                category="fuel",
            ),
            POIRecord(
                id="probe-002",
                lat=center_lat + 0.0040,
                lon=center_lon + 0.0010,
                name="Statia Petrom Stefan cel Mare & Mosi",
                description="Diacritice test: ș, ț, ă, â, î / Ș, Ț, Ă, Â, Î",
                category="fuel",
            ),
            POIRecord(
                id="probe-003",
                lat=center_lat - 0.0020,
                lon=center_lon + 0.0030,
                name='Magazin "La Nea Popa", Str. Viilor nr. 12',
                description='Ghilimele "interioare" si virgule, test delimitator',
                category="supermarket",
            ),
            POIRecord(
                id="probe-004",
                lat=center_lat - 0.0030,
                lon=center_lon - 0.0020,
                name="Supermarket Mega Image Concept Store Piata Sudului Bucuresti Sector 4 Punct de Lucru Principal",
                description="Nume foarte lung peste 60 caractere pentru test trunchiere pe display RNS 510",
                category="supermarket",
            ),
            POIRecord(
                id="probe-005",
                lat=center_lat + 0.0010,
                lon=center_lon - 0.0040,
                name="Enel X Charging Station",
                description="Capacitate 2x50kW CCS, Type 2 22kW, Non-Stop, Tarif 2.49 RON/kWh",
                category="ev_charging",
            ),
        ]
        if count <= 5:
            return records[:count]
        extra_count = count - 5
        records.extend(_generate_grid_records(center_lat, center_lon, extra_count, offset=5))
        return records

    return _generate_grid_records(center_lat, center_lon, count, offset=1)


def _generate_grid_records(
    center_lat: float, center_lon: float, count: int, offset: int = 1
) -> list[POIRecord]:
    """Generate a grid of synthetic POIs around center coordinates."""
    import math

    records: list[POIRecord] = []
    side = int(math.ceil(math.sqrt(count)))
    step = 0.0015

    generated = 0
    for r in range(side):
        for c in range(side):
            if generated >= count:
                break
            idx = offset + generated
            lat = center_lat + (r - side / 2) * step
            lon = center_lon + (c - side / 2) * step
            records.append(
                POIRecord(
                    id=f"probe-{idx:05d}",
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    name=f"Probe POI #{idx:05d}",
                    description=f"Synthetic probe record #{idx} at {lat:.5f}, {lon:.5f}",
                    category="probe",
                )
            )
            generated += 1
    return records


def cmd_probe_file(args: argparse.Namespace) -> int:
    """Execute 'probe-file' subcommand."""
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Warning: Config file '{config_path}' not found, using default unverified settings.")
        config = RNS510AscConfig()
    else:
        config = RNS510AscConfig.from_yaml(config_path)

    out_path = Path(args.out)
    count = args.count

    print("=" * 60)
    print("RNS 510 POI FORGE - PROBE FILE GENERATOR")
    print("=" * 60)
    print(f"Config path        : {config_path}")
    print(f"Verified status    : {config.verified}")
    print(f"Field order        : {config.field_order}")
    print(f"Separator          : repr({repr(config.separator)})")
    print(f"Coordinate order   : {config.coordinate_order}")
    print(f"Encoding           : {config.charset} (transliterate={config.ascii_transliterate})")
    print(f"Line endings       : {config.line_endings}")
    print(f"Center coordinates : {args.lat:.6f}, {args.lon:.6f}")
    print(f"POI count          : {count} (preset: {args.preset})")
    print("-" * 60)

    records = create_probe_records(
        center_lat=args.lat,
        center_lon=args.lon,
        count=count,
        preset=args.preset,
    )

    writer = RNS510AscWriter(config)
    written_files = writer.write(records, out_path)

    print(f"Successfully generated {len(written_files)} probe file(s):")
    for f in written_files:
        print(f"  -> {f} ({f.stat().st_size} bytes)")

    if args.generate_matrix:
        matrix_dir = out_path.parent / "probe_matrix"
        matrix_dir.mkdir(parents=True, exist_ok=True)
        print("\nGenerating probe variant matrix in:", matrix_dir)
        _generate_variant_matrix(records, matrix_dir, config)

    print("\nNext steps:")
    print("1. Copy the probe file(s) to a FAT32-formatted SD card.")
    print("2. Insert SD card into VW RNS 510 unit.")
    print("3. Navigate to: Navigation -> My special destinations -> Import -> Import into database.")
    print("4. Read docs/FORMAT_PROBE.md for observation checklist and reporting format.")
    print("=" * 60)
    return 0


def _generate_variant_matrix(
    records: list[POIRecord], target_dir: Path, base_cfg: RNS510AscConfig
) -> None:
    """Generate a matrix of common ASC variants to quickly determine what works."""
    variants = [
        ("01_default_lon_lat_comma_quoted", {}),
        ("02_lat_lon_comma_quoted", {"coordinate_order": "lat_lon"}),
        ("03_lon_lat_tab_quoted", {"separator": "\t"}),
        ("04_lon_lat_semicolon_quoted", {"separator": ";"}),
        ("05_lon_lat_comma_unquoted", {"quote_text": False}),
        ("06_utf8_encoding", {"charset": "utf-8", "ascii_transliterate": False}),
        ("07_cp1250_with_diacritics", {"charset": "cp1250", "ascii_transliterate": False}),
        ("08_lf_line_endings", {"line_endings": "lf"}),
    ]

    for name, overrides in variants:
        cfg_dict = base_cfg.to_dict()
        for k, v in overrides.items():
            if k in cfg_dict:
                cfg_dict[k] = v
            elif k in cfg_dict["fields"]:
                cfg_dict["fields"][k] = v
            elif k in cfg_dict["encoding"]:
                cfg_dict["encoding"][k] = v

        var_cfg = RNS510AscConfig.from_dict(cfg_dict)
        var_writer = RNS510AscWriter(var_cfg)
        dest = target_dir / f"{name}.asc"
        files = var_writer.write(records, dest)
        for f in files:
            print(f"  [Matrix] {f.name} ({f.stat().st_size} bytes)")


def cmd_list_countries(args: argparse.Namespace) -> int:
    """Execute 'list-countries' subcommand."""
    print("Fetching European countries from Geofabrik index...")
    countries = resolve_european_countries(
        cache_dir=args.cache,
        config_path=args.config,
        publish_only=not args.all,
    )

    print(f"\nAvailable European Extracts ({len(countries)} total):")
    print("-" * 90)
    print(f"{'ID':<25} {'Name (EN)':<25} {'Publish':<10} {'Sub-extracts'}")
    print("-" * 90)
    for c in countries:
        sub_info = f"{len(c.sub_extract_ids)} sub-regions" if c.sub_extract_ids else "-"
        pub_str = "YES" if c.publish else "NO"
        print(f"{c.id:<25} {c.name.get('en', c.id):<25} {pub_str:<10} {sub_info}")
    print("-" * 90)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Execute 'build' subcommand."""
    country_id = args.country
    cache_dir = Path(args.cache)
    out_dir = Path(args.out)
    fmt_config_path = Path(args.format_config)
    cat_config_path = Path(args.categories_config)

    # 1. Load configs
    fmt_config = (
        RNS510AscConfig.from_yaml(fmt_config_path)
        if fmt_config_path.exists()
        else RNS510AscConfig()
    )
    all_categories = load_categories(cat_config_path)

    # 2. Selected categories
    if args.categories:
        selected_cat_ids = [c.strip() for c in args.categories.split(",") if c.strip()]
        for cid in selected_cat_ids:
            if cid not in all_categories:
                print(f"Error: Unknown category '{cid}'. Available: {list(all_categories.keys())}")
                return 1
    else:
        selected_cat_ids = list(all_categories.keys())

    # 3. Resolve country extract info
    print(f"Resolving country extract for '{country_id}'...")
    try:
        country = get_country(country_id, cache_dir=cache_dir)
    except KeyError as e:
        print(f"Error: {e}")
        return 1

    print(f"Country      : {country.name.get('en', country.id)} ({country.id})")
    print(f"PBF URL      : {country.pbf_url}")

    # 4. Download / verify cache
    print("Downloading / checking cache for PBF extract...")

    def progress_cb(current: int, total: int | None) -> None:
        if total:
            pct = (current / total) * 100
            sys.stdout.write(f"\rDownloading: {pct:.1f}% ({current / 1048576:.1f}/{total / 1048576:.1f} MB)")
            sys.stdout.flush()

    dl_result = download_pbf_with_cache(
        country.pbf_url,
        target_dir=cache_dir,
        md5_url=country.md5_url,
        progress_callback=progress_cb,
    )
    print(f"\nPBF ready at : {dl_result.file_path}")
    print(f"MD5 checksum : {dl_result.md5} ({'cached' if dl_result.from_cache else 'downloaded'})")
    print(f"Extract date : {dl_result.extract_timestamp or 'unknown'}")

    # 5. Extract POIs
    print(f"\nExtracting POIs for {len(selected_cat_ids)} category(ies)...")
    pois_by_cat = extract_pois(
        pbf_path=dl_result.file_path,
        categories_path=cat_config_path,
        category_ids=selected_cat_ids,
        lang="ro",
    )

    # 6. Write packages, metadata, and attribution
    writer = RNS510AscWriter(fmt_config)
    country_out_dir = out_dir / country_id
    total_written = 0

    print("\nWriting packages:")
    print("-" * 65)
    print(f"{'Category':<20} {'POIs Count':<12} {'Files Generated'}")
    print("-" * 65)

    for cat_id in selected_cat_ids:
        records = pois_by_cat.get(cat_id, [])
        cat_dir = country_out_dir / cat_id
        target_asc = cat_dir / f"{country_id}_{cat_id}.asc"

        written_files = writer.write(records, target_asc, force_chunk_suffix=True)
        total_written += len(records)

        # Write per-category meta.json
        meta_dict = create_category_meta(
            country_id=country_id,
            category_id=cat_id,
            asc_files=written_files,
            count=len(records),
            osm_extract_date=dl_result.extract_timestamp,
        )
        write_category_meta(cat_dir, meta_dict)

        files_str = ", ".join(f.name for f in written_files)
        print(f"{cat_id:<20} {len(records):<12} {files_str}")

    # Write country ATTRIBUTION.txt
    write_attribution_file(country_out_dir)

    print("-" * 65)
    print(f"Total POIs written: {total_written} across {len(selected_cat_ids)} categories")
    print(f"Output directory  : {country_out_dir}")

    # Optional zip creation
    if args.zip:
        zip_path = out_dir / f"{country_id}.zip"
        print(f"Creating country zip archive: {zip_path}...")
        create_country_zip(country_out_dir, zip_path)
        print(f"Zip ready ({zip_path.stat().st_size} bytes)")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute 'validate' subcommand."""
    target_path = Path(args.path)
    config_path = Path(args.config)
    config = (
        RNS510AscConfig.from_yaml(config_path)
        if config_path.exists()
        else RNS510AscConfig()
    )

    print("=" * 60)
    print(f"Validating path: {target_path}")
    print(f"Format config  : {config_path} (charset={config.charset}, max_pois={config.max_pois_per_file})")
    print("=" * 60)

    report = validate_path(target_path, config=config)

    print(f"Total files checked  : {report.total_files}")
    print(f"Total records checked: {report.total_records}")
    print(f"Errors               : {report.error_count}")
    print(f"Warnings             : {report.warning_count}")
    print("-" * 60)

    for issue in report.issues:
        loc = f"{issue.file_path.name}"
        if issue.line_number is not None:
            loc += f":L{issue.line_number}"
        tag = f"[{issue.severity}]"
        print(f"{tag:<10} {loc:<30} {issue.message}")

    if not report.is_valid:
        print("\nValidation FAILED.")
        return 1

    print("\nValidation PASSED successfully.")
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    """Execute 'index' subcommand."""
    packages_dir = Path(args.packages)
    out_file = Path(args.out)
    fmt_config = Path(args.format_config)
    countries_config = Path(args.countries_config)

    print(f"Building release index from packages in '{packages_dir}'...")
    index_dict = build_index(
        packages_dir=packages_dir,
        format_config_path=fmt_config,
        countries_config_path=countries_config,
    )

    written = write_index(index_dict, out_file)
    print(f"Index generated successfully at: {written}")
    print(f"  Countries indexed : {len(index_dict.get('countries', []))}")
    print(f"  Verified format   : {index_dict['format']['verified']}")
    return 0


def cmd_custom_area(args: argparse.Namespace) -> int:
    """Execute 'custom-area' subcommand using Overpass API with strict limits."""
    out_dir = Path(args.out)
    fmt_config_path = Path(args.format_config)
    cat_config_path = Path(args.categories_config)
    area_name = args.name

    fmt_config = (
        RNS510AscConfig.from_yaml(fmt_config_path)
        if fmt_config_path.exists()
        else RNS510AscConfig()
    )
    all_categories = load_categories(cat_config_path)

    if args.categories:
        selected_cat_ids = [c.strip() for c in args.categories.split(",") if c.strip()]
        for cid in selected_cat_ids:
            if cid not in all_categories:
                print(f"Error: Unknown category '{cid}'. Available: {list(all_categories.keys())}")
                return 1
    else:
        selected_cat_ids = list(all_categories.keys())

    bbox_tuple: tuple[float, float, float, float] | None = None
    if args.bbox:
        try:
            parts = [float(x.strip()) for x in args.bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except Exception:
            print("Error: --bbox must be formatted as 'min_lon,min_lat,max_lon,max_lat'")
            return 1

    try:
        if bbox_tuple:
            validate_custom_area_limits(bbox=bbox_tuple)
            print(f"Validating bounding box: {bbox_tuple}")
        else:
            validate_custom_area_limits(radius_km=args.radius_km)
            print(
                f"Custom area center: ({args.lat:.4f}, {args.lon:.4f}), "
                f"radius: {args.radius_km:.1f} km (max allowed: {MAX_RADIUS_KM} km)"
            )
    except ValueError as e:
        print(f"Area Limit Error: {e}")
        return 1

    print("Building Overpass query...")
    query = build_overpass_query(
        categories=all_categories,
        category_ids=selected_cat_ids,
        lat=args.lat if not bbox_tuple else None,
        lon=args.lon if not bbox_tuple else None,
        radius_km=args.radius_km if not bbox_tuple else None,
        bbox=bbox_tuple,
    )

    print("Querying Overpass API...")
    try:
        overpass_data = query_overpass(query)
    except Exception as e:
        print(f"Overpass Error: {e}")
        return 1

    elements = overpass_data.get("elements", [])
    print(f"Received {len(elements)} raw elements from Overpass.")

    pois_by_cat = extract_overpass_elements(
        overpass_data,
        categories_path=cat_config_path,
        category_ids=selected_cat_ids,
        lang=args.lang,
    )

    writer = RNS510AscWriter(fmt_config)
    area_out_dir = out_dir / area_name
    total_written = 0

    print("\nWriting packages:")
    print("-" * 65)
    print(f"{'Category':<20} {'POIs Count':<12} {'Files Generated'}")
    print("-" * 65)

    for cat_id in selected_cat_ids:
        records = pois_by_cat.get(cat_id, [])
        cat_dir = area_out_dir / cat_id
        target_asc = cat_dir / f"{area_name}_{cat_id}.asc"

        written_files = writer.write(records, target_asc, force_chunk_suffix=True)
        total_written += len(records)

        meta_dict = create_category_meta(
            country_id=area_name,
            category_id=cat_id,
            asc_files=written_files,
            count=len(records),
            osm_extract_date="live-overpass",
        )
        write_category_meta(cat_dir, meta_dict)

        files_str = ", ".join(f.name for f in written_files)
        print(f"{cat_id:<20} {len(records):<12} {files_str}")

    write_attribution_file(area_out_dir)

    print("-" * 65)
    print(f"Total POIs written: {total_written} across {len(selected_cat_ids)} categories")
    print(f"Output directory  : {area_out_dir}")

    if args.zip:
        zip_path = out_dir / f"{area_name}.zip"
        create_country_zip(area_out_dir, zip_path)
        print(f"Created zip archive: {zip_path}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="poi-forge",
        description="Personal POI builder for Volkswagen RNS 510 head units from OpenStreetMap data",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # probe-file subcommand
    probe_p = subparsers.add_parser(
        "probe-file",
        help="Generate a synthetic test POI file to probe format requirements on a physical RNS 510 unit",
    )
    probe_p.add_argument(
        "--out",
        "-o",
        default="probe.asc",
        help="Output file path (default: probe.asc)",
    )
    probe_p.add_argument(
        "--lat",
        type=float,
        default=44.4323,
        help="Center latitude for synthetic POIs (default: 44.4323)",
    )
    probe_p.add_argument(
        "--lon",
        type=float,
        default=26.1063,
        help="Center longitude for synthetic POIs (default: 26.1063)",
    )
    probe_p.add_argument(
        "--count",
        "-n",
        type=int,
        default=5,
        help="Number of POIs to generate (default: 5)",
    )
    probe_p.add_argument(
        "--preset",
        choices=["probe", "grid"],
        default="probe",
        help="Preset type: 'probe' for edge cases, 'grid' for stress testing (default: probe)",
    )
    probe_p.add_argument(
        "--config",
        "-c",
        default="config/format.yml",
        help="Path to format.yml configuration (default: config/format.yml)",
    )
    probe_p.add_argument(
        "--generate-matrix",
        action="store_true",
        help="Generate a folder with all common format variants to test on hardware",
    )
    probe_p.set_defaults(func=cmd_probe_file)

    # list-countries subcommand
    list_p = subparsers.add_parser(
        "list-countries", help="List available Geofabrik country extracts"
    )
    list_p.add_argument(
        "--cache", default="cache", help="Cache directory for index (default: cache)"
    )
    list_p.add_argument(
        "--config",
        default="config/countries.yml",
        help="Countries config (default: config/countries.yml)",
    )
    list_p.add_argument(
        "--all",
        action="store_true",
        help="Show all extracts including unlisted/composite regions",
    )
    list_p.set_defaults(func=cmd_list_countries)

    # build subcommand
    build_p = subparsers.add_parser("build", help="Build POI packages for a country")
    build_p.add_argument(
        "--country",
        required=True,
        help="Geofabrik country ID (e.g. romania, malta, luxembourg)",
    )
    build_p.add_argument(
        "--categories",
        help="Comma-separated category IDs to build (default: all)",
    )
    build_p.add_argument(
        "--out",
        default="packages",
        help="Output directory (default: packages)",
    )
    build_p.add_argument(
        "--cache",
        default="cache",
        help="Cache directory for PBF downloads (default: cache)",
    )
    build_p.add_argument(
        "--format-config",
        default="config/format.yml",
        help="Format config file (default: config/format.yml)",
    )
    build_p.add_argument(
        "--categories-config",
        default="config/categories.yml",
        help="Categories config file (default: config/categories.yml)",
    )
    build_p.add_argument(
        "--zip",
        action="store_true",
        help="Create a distributable ZIP package of the country",
    )
    build_p.set_defaults(func=cmd_build)

    # validate subcommand
    validate_p = subparsers.add_parser(
        "validate", help="Validate generated POI files against format.yml"
    )
    validate_p.add_argument("path", help="Path to .asc file or directory of packages")
    validate_p.add_argument(
        "--config",
        "-c",
        default="config/format.yml",
        help="Path to format.yml (default: config/format.yml)",
    )
    validate_p.set_defaults(func=cmd_validate)

    # index subcommand
    index_p = subparsers.add_parser(
        "index", help="Build index.json for release and web app"
    )
    index_p.add_argument(
        "--packages",
        default="packages",
        help="Path to packages directory (default: packages)",
    )
    index_p.add_argument(
        "--out",
        "-o",
        default="index.json",
        help="Output index JSON path (default: index.json)",
    )
    index_p.add_argument(
        "--format-config",
        default="config/format.yml",
        help="Path to format.yml (default: config/format.yml)",
    )
    index_p.add_argument(
        "--countries-config",
        default="config/countries.yml",
        help="Path to countries.yml (default: config/countries.yml)",
    )
    index_p.set_defaults(func=cmd_index)

    # custom-area subcommand
    custom_p = subparsers.add_parser(
        "custom-area",
        help="Extract POIs for a custom area (radius or bbox) via Overpass API with strict limits",
    )
    custom_p.add_argument(
        "--lat",
        type=float,
        default=44.4323,
        help="Center latitude for radius query (default: 44.4323)",
    )
    custom_p.add_argument(
        "--lon",
        type=float,
        default=26.1063,
        help="Center longitude for radius query (default: 26.1063)",
    )
    custom_p.add_argument(
        "--radius-km",
        type=float,
        default=10.0,
        help="Radius in kilometers (default: 10.0, max: 25.0)",
    )
    custom_p.add_argument(
        "--bbox",
        help="Bounding box 'min_lon,min_lat,max_lon,max_lat' (max area: 0.25 sq degrees)",
    )
    custom_p.add_argument(
        "--categories",
        help="Comma-separated category IDs to extract (default: all)",
    )
    custom_p.add_argument(
        "--name",
        default="custom_area",
        help="Custom area name identifier (default: custom_area)",
    )
    custom_p.add_argument(
        "--out",
        default="custom_packages",
        help="Output directory (default: custom_packages)",
    )
    custom_p.add_argument(
        "--format-config",
        default="config/format.yml",
        help="Path to format.yml (default: config/format.yml)",
    )
    custom_p.add_argument(
        "--categories-config",
        default="config/categories.yml",
        help="Path to categories.yml (default: config/categories.yml)",
    )
    custom_p.add_argument(
        "--lang",
        default="ro",
        choices=["ro", "en"],
        help="Language for fallback names (default: ro)",
    )
    custom_p.add_argument(
        "--zip",
        action="store_true",
        help="Create a distributable ZIP archive of the custom area",
    )
    custom_p.set_defaults(func=cmd_custom_area)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
