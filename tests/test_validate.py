"""Tests for ASC validation against format rules."""

from __future__ import annotations

from pathlib import Path

from poi_forge.formats.rns510_asc import RNS510AscConfig
from poi_forge.validate import validate_asc_file, validate_path


def test_validate_valid_file(tmp_path: Path):
    """A correctly formatted ASC file passes validation."""
    asc_file = tmp_path / "valid.asc"
    asc_file.write_bytes(
        b'26.100000,44.400000,"OMV Aviatorilor","Fuel 24/7"\r\n'
        b'26.110000,44.410000,"Petrom Baneasa","Non-Stop"\r\n'
    )
    count, issues = validate_asc_file(asc_file)
    assert count == 2
    # No ERROR severity issues
    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 0


def test_validate_corrupt_coordinates(tmp_path: Path):
    """Out of range and non-numeric coordinates must trigger errors."""
    asc_file = tmp_path / "bad_coords.asc"
    asc_file.write_bytes(
        b'999.000000,44.400000,"Valid Name",""\r\n'
        b'invalid_lon,44.400000,"Valid Name",""\r\n'
    )
    count, issues = validate_asc_file(asc_file)
    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 2


def test_validate_oversized_name(tmp_path: Path):
    """Names exceeding max_name_length must trigger an error."""
    cfg = RNS510AscConfig(max_name_length=20)
    asc_file = tmp_path / "long_name.asc"
    long_name = "This Name Is Extremely Long And Exceeds Twenty Characters"
    asc_file.write_bytes(f'26.100000,44.400000,"{long_name}",""\r\n'.encode("cp1250"))

    count, issues = validate_asc_file(asc_file, config=cfg)
    errors = [i for i in issues if i.severity == "ERROR"]
    assert any("Name length" in e.message for e in errors)


def test_validate_file_size_limit(tmp_path: Path):
    """Files exceeding max_file_size_bytes must trigger an error."""
    cfg = RNS510AscConfig(max_file_size_bytes=50)
    asc_file = tmp_path / "huge.asc"
    asc_file.write_bytes(b"A" * 100)

    count, issues = validate_asc_file(asc_file, config=cfg)
    errors = [i for i in issues if i.severity == "ERROR"]
    assert any("File size" in e.message for e in errors)


def test_validate_path_recursive(tmp_path: Path):
    """validate_path recursively validates all .asc files in a folder."""
    pkg_dir = tmp_path / "packages" / "romania" / "fuel"
    pkg_dir.mkdir(parents=True)

    f1 = pkg_dir / "romania_fuel_001.asc"
    f1.write_bytes(b'26.100000,44.400000,"OMV",""\r\n')

    f2 = pkg_dir / "romania_fuel_002.asc"
    f2.write_bytes(b'26.110000,44.410000,"Petrom",""\r\n')

    report = validate_path(tmp_path / "packages")
    assert report.total_files == 2
    assert report.total_records == 2
    assert report.is_valid is True
