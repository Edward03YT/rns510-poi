"""Validation utility for generated RNS 510 ASC files against format rules."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from poi_forge.formats.rns510_asc import RNS510AscConfig

# General bounding box for Europe: West, South, East, North
EUROPE_BBOX = (-32.0, 34.0, 45.0, 72.0)


@dataclass
class ValidationIssue:
    """An issue detected during validation."""

    file_path: Path
    line_number: int | None
    severity: str  # "ERROR" or "WARNING"
    message: str


@dataclass
class ValidationReport:
    """Summary of validation results across files."""

    total_files: int = 0
    total_records: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no ERROR severity issues exist."""
        return not any(i.severity == "ERROR" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")


def validate_asc_file(
    file_path: Path | str,
    config: RNS510AscConfig | None = None,
    bbox: tuple[float, float, float, float] = EUROPE_BBOX,
) -> tuple[int, list[ValidationIssue]]:
    """Validate a single .asc file against format rules.

    Returns:
        tuple: (record_count, list of ValidationIssue)
    """
    path = Path(file_path)
    config = config or RNS510AscConfig()
    issues: list[ValidationIssue] = []

    # 1. File size limit
    file_size = path.stat().st_size
    if file_size > config.max_file_size_bytes:
        issues.append(
            ValidationIssue(
                file_path=path,
                line_number=None,
                severity="ERROR",
                message=(
                    f"File size {file_size} bytes exceeds maximum allowed "
                    f"{config.max_file_size_bytes} bytes"
                ),
            )
        )

    # 2. Encoding check
    raw_bytes = path.read_bytes()
    try:
        decoded_text = raw_bytes.decode(config.charset)
    except UnicodeDecodeError as e:
        issues.append(
            ValidationIssue(
                file_path=path,
                line_number=None,
                severity="ERROR",
                message=f"File contains invalid bytes for charset '{config.charset}': {e}",
            )
        )
        return 0, issues

    # 3. Line endings check
    if config.line_endings.lower() == "crlf" and b"\r\n" not in raw_bytes and b"\n" in raw_bytes:
        issues.append(
            ValidationIssue(
                file_path=path,
                line_number=None,
                severity="WARNING",
                message="Expected CRLF line endings, but file uses LF",
            )
        )

    # 4. Parse records
    reader = csv.reader(
        io.StringIO(decoded_text),
        delimiter=config.separator,
        quotechar=config.quote_char,
    )

    seen_coords: set[tuple[float, float]] = set()
    record_count = 0

    order = list(config.field_order)
    if config.coordinate_order == "lat_lon":
        if "lon" in order and "lat" in order:
            lon_idx = order.index("lon")
            lat_idx = order.index("lat")
            if lon_idx < lat_idx:
                order[lon_idx], order[lat_idx] = "lat", "lon"
    elif config.coordinate_order == "lon_lat":
        if "lon" in order and "lat" in order:
            lon_idx = order.index("lon")
            lat_idx = order.index("lat")
            if lat_idx < lon_idx:
                order[lon_idx], order[lat_idx] = "lon", "lat"

    for line_idx, row in enumerate(reader, start=1):
        if not row:
            continue
        record_count += 1

        if len(row) < len(order):
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="ERROR",
                    message=f"Expected at least {len(order)} fields, found {len(row)}: {row}",
                )
            )
            continue

        field_map = dict(zip(order, row))

        # Check coordinates
        try:
            lon = float(field_map.get("lon", 0))
            lat = float(field_map.get("lat", 0))
        except ValueError:
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="ERROR",
                    message=f"Non-numeric coordinates: lon='{field_map.get('lon')}', lat='{field_map.get('lat')}'",
                )
            )
            continue

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="ERROR",
                    message=f"Coordinates out of WGS84 range: ({lat}, {lon})",
                )
            )

        # Bounding box check
        min_lon, min_lat, max_lon, max_lat = bbox
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="WARNING",
                    message=f"Coordinates ({lat}, {lon}) are outside Europe bounding box",
                )
            )

        # Check string lengths
        name = field_map.get("name", "")
        if len(name) > config.max_name_length:
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="ERROR",
                    message=(
                        f"Name length ({len(name)}) exceeds max allowed "
                        f"({config.max_name_length}): '{name[:20]}...'"
                    ),
                )
            )

        desc = field_map.get("description", "")
        if len(desc) > config.max_desc_length:
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="ERROR",
                    message=(
                        f"Description length ({len(desc)}) exceeds max allowed "
                        f"({config.max_desc_length}): '{desc[:20]}...'"
                    ),
                )
            )

        # Duplicate coordinate check
        coord_pair = (round(lat, 5), round(lon, 5))
        if coord_pair in seen_coords:
            issues.append(
                ValidationIssue(
                    file_path=path,
                    line_number=line_idx,
                    severity="WARNING",
                    message=f"Duplicate coordinate ({lat:.5f}, {lon:.5f}) in same file",
                )
            )
        else:
            seen_coords.add(coord_pair)

    # Check max POIs per file
    if record_count > config.max_pois_per_file:
        issues.append(
            ValidationIssue(
                file_path=path,
                line_number=None,
                severity="ERROR",
                message=(
                    f"Record count {record_count} exceeds maximum allowed "
                    f"({config.max_pois_per_file}) per file"
                ),
            )
        )

    return record_count, issues


def validate_path(
    target_path: Path | str,
    config: RNS510AscConfig | None = None,
) -> ValidationReport:
    """Validate a single .asc file or a directory of files recursively."""
    path = Path(target_path)
    config = config or RNS510AscConfig()
    report = ValidationReport()

    if path.is_file():
        files_to_check = [path]
    elif path.is_dir():
        files_to_check = sorted(path.rglob("*.asc"))
    else:
        report.issues.append(
            ValidationIssue(
                file_path=path,
                line_number=None,
                severity="ERROR",
                message=f"Target path does not exist: {path}",
            )
        )
        return report

    report.total_files = len(files_to_check)

    for f in files_to_check:
        count, file_issues = validate_asc_file(f, config=config)
        report.total_records += count
        report.issues.extend(file_issues)

    return report
