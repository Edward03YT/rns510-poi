"""Command Line Interface for rns510-poi-forge."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from poi_forge.formats.base import POIRecord
from poi_forge.formats.rns510_asc import RNS510AscConfig, RNS510AscWriter


def create_probe_records(
    center_lat: float = 44.4323,
    center_lon: float = 26.1063,
    count: int = 5,
    preset: str = "probe",
) -> list[POIRecord]:
    """Generate synthetic POIs for format probing and hardware testing.

    Args:
        center_lat: Center latitude.
        center_lon: Center longitude.
        count: Number of records to generate.
        preset: 'probe' for curated edge cases, or 'grid' for bulk stress testing.
    """
    if preset == "probe":
        # Hand-crafted edge cases to test RNS 510 parser limits
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
        # If user asked for more than 5 in probe preset, add grid records to reach count
        extra_count = count - 5
        records.extend(_generate_grid_records(center_lat, center_lon, extra_count, offset=5))
        return records

    # Generic grid/stress testing
    return _generate_grid_records(center_lat, center_lon, count, offset=1)


def _generate_grid_records(
    center_lat: float, center_lon: float, count: int, offset: int = 1
) -> list[POIRecord]:
    """Generate a grid of synthetic POIs around center coordinates."""
    import math

    records: list[POIRecord] = []
    side = int(math.ceil(math.sqrt(count)))
    step = 0.0015  # ~150 meters apart

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
        size_bytes = f.stat().st_size
        print(f"  -> {f} ({size_bytes} bytes)")

    if args.generate_matrix:
        matrix_dir = out_path.parent / "probe_matrix"
        matrix_dir.mkdir(parents=True, exist_ok=True)
        print("\nGenerating probe variant matrix in:", matrix_dir)
        _generate_variant_matrix(records, matrix_dir, config)

    print("\nNext steps:")
    print("1. Copy the probe file(s) to a FAT32-formatted SD card.")
    print("   Test both the root folder and /PersonalPOI/ directory.")
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

    # Placeholders for future phases
    list_p = subparsers.add_parser(
        "list-countries", help="List available Geofabrik country extracts (Phase 1)"
    )
    list_p.set_defaults(
        func=lambda args: print("list-countries will be implemented in Phase 1.") or 0
    )

    build_p = subparsers.add_parser("build", help="Build POI packages (Phase 2)")
    build_p.set_defaults(
        func=lambda args: print("build will be implemented in Phase 2.") or 0
    )

    validate_p = subparsers.add_parser(
        "validate", help="Validate generated POI files against format.yml (Phase 3)"
    )
    validate_p.set_defaults(
        func=lambda args: print("validate will be implemented in Phase 3.") or 0
    )

    index_p = subparsers.add_parser(
        "index", help="Build index.json for release and web app (Phase 3)"
    )
    index_p.set_defaults(
        func=lambda args: print("index will be implemented in Phase 3.") or 0
    )

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
