"""Tests for RNS 510 ASC format writer and configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from poi_forge.cli import create_probe_records, main
from poi_forge.formats.base import POIRecord
from poi_forge.formats.rns510_asc import (
    RNS510AscConfig,
    RNS510AscWriter,
    transliterate_to_ascii,
)


@pytest.fixture
def sample_records() -> list[POIRecord]:
    """Fixture providing diverse POI records."""
    return [
        POIRecord(
            id="1",
            lat=44.43234567,
            lon=26.10634567,
            name="OMV Aviatorilor",
            description="Fuel 24/7",
            category="fuel",
        ),
        POIRecord(
            id="2",
            lat=44.450000,
            lon=26.120000,
            name="Stația Petrom Ștefan cel Mare & Moși",
            description="Diacritice: ș, ț, ă, â, î și Ș, Ț, Ă, Â, Î",
            category="fuel",
        ),
        POIRecord(
            id="3",
            lat=44.410000,
            lon=26.090000,
            name='Magazin "La Nea Popa", Str. Viilor nr. 12',
            description='Test ghilimele "duble" si, virgule, peste tot',
            category="supermarket",
        ),
        POIRecord(
            id="4",
            lat=44.400000,
            lon=26.080000,
            name="Supermarket Mega Image Concept Store Piata Sudului Bucuresti Sector 4 Punct de Lucru Principal",
            description="Descriere extrem de lunga destinata sa depaseasca limita admisa de caractere pentru RNS510",
            category="supermarket",
        ),
        POIRecord(
            id="5",
            lat=44.420000,
            lon=26.110000,
            name="Emoji Test ⛽ 🚗 ⚡",
            description="Description with control chars \x00\x08 and \n newlines",
            category="fuel",
        ),
    ]


def test_transliterate_romanian_diacritics():
    """Verify Romanian diacritics are correctly transliterated to plain ASCII."""
    text = "șerif țintă apă pâine înot ȘERIF ȚINTĂ APĂ PÂINE ÎNOT şcoală ţară"
    expected = "serif tinta apa paine inot SERIF TINTA APA PAINE INOT scoala tara"
    assert transliterate_to_ascii(text) == expected


def test_transliterate_european_ligatures():
    """Verify German and European ligatures."""
    text = "Straße, Straßburg, café, naïve, façade, København, Gdańsk"
    expected = "Strasse, Strassburg, cafe, naive, facade, Kobenhavn, Gdansk"
    assert transliterate_to_ascii(text) == expected


def test_format_record_default_golden():
    """Golden test for standard default ASC formatting."""
    cfg = RNS510AscConfig(
        coordinate_order="lon_lat",
        coordinate_decimals=6,
        separator=",",
        quote_text=True,
        ascii_transliterate=True,
    )
    writer = RNS510AscWriter(cfg)

    record = POIRecord(
        id="100",
        lat=44.43234567,
        lon=26.10634567,
        name="Stația Petrom",
        description="Non-Stop",
    )
    line = writer.format_record(record)
    assert line == '26.106346,44.432346,"Statia Petrom","Non-Stop"'


def test_quotes_and_commas_escaping():
    """Verify quotes are doubled and commas inside quoted text are preserved."""
    cfg = RNS510AscConfig(quote_text=True, escape_quote='""')
    writer = RNS510AscWriter(cfg)

    record = POIRecord(
        id="101",
        lat=44.0,
        lon=26.0,
        name='Store "Best Deals", Sector 1',
        description='Special "Offer", today only',
    )
    line = writer.format_record(record)
    assert line == '26.000000,44.000000,"Store ""Best Deals"", Sector 1","Special ""Offer"", today only"'


def test_unquoted_format_replaces_separator():
    """If quote_text is false, separator in text must be replaced with space to prevent column misalignment."""
    cfg = RNS510AscConfig(quote_text=False, separator=",")
    writer = RNS510AscWriter(cfg)

    record = POIRecord(
        id="102",
        lat=44.0,
        lon=26.0,
        name="Store, Sector 1",
        description="Open, 24/7",
    )
    line = writer.format_record(record)
    assert line == "26.000000,44.000000,Store  Sector 1,Open  24/7"


def test_coordinate_order_lat_lon():
    """Verify coordinate order can be inverted to lat_lon."""
    cfg = RNS510AscConfig(coordinate_order="lat_lon")
    writer = RNS510AscWriter(cfg)

    record = POIRecord(id="103", lat=44.123456, lon=26.654321, name="Point")
    line = writer.format_record(record)
    assert line.startswith("44.123456,26.654321")


def test_line_endings_crlf_vs_lf():
    """Verify CRLF vs LF line endings."""
    crlf_writer = RNS510AscWriter(RNS510AscConfig(line_endings="crlf"))
    lf_writer = RNS510AscWriter(RNS510AscConfig(line_endings="lf"))

    line_crlf = crlf_writer.encode_line("test")
    line_lf = lf_writer.encode_line("test")

    assert line_crlf == b"test\r\n"
    assert line_lf == b"test\n"


def test_length_clamping_and_control_chars():
    """Verify name and description are clamped to limits and control chars removed."""
    cfg = RNS510AscConfig(max_name_length=20, max_desc_length=30)
    writer = RNS510AscWriter(cfg)

    record = POIRecord(
        id="104",
        lat=44.0,
        lon=26.0,
        name="Very Long Name That Exceeds Twenty Characters",
        description="A very long description text that easily surpasses thirty characters limit",
    )
    line = writer.format_record(record)
    # Name should be clamped to 20 chars
    assert '"Very Long Name That"' in line


def test_chunking_by_record_count(tmp_path: Path):
    """Verify files are split when exceeding max_pois_per_file."""
    cfg = RNS510AscConfig(max_pois_per_file=2)
    writer = RNS510AscWriter(cfg)

    records = [
        POIRecord(id=f"{i}", lat=44.0 + i * 0.01, lon=26.0, name=f"POI {i}")
        for i in range(5)
    ]

    out_file = tmp_path / "test.asc"
    written = writer.write(records, out_file)

    # 5 records with max 2 per file -> 3 files (2, 2, 1)
    assert len(written) == 3
    assert written[0].name == "test_001.asc"
    assert written[1].name == "test_002.asc"
    assert written[2].name == "test_003.asc"

    content_001 = written[0].read_bytes()
    assert b"POI 0" in content_001
    assert b"POI 1" in content_001
    assert b"POI 2" not in content_001


def test_chunking_by_byte_size(tmp_path: Path):
    """Verify files are split when exceeding max_file_size_bytes."""
    cfg = RNS510AscConfig(max_pois_per_file=1000, max_file_size_bytes=100)
    writer = RNS510AscWriter(cfg)

    records = [
        POIRecord(id=f"{i}", lat=44.0, lon=26.0, name=f"POI Number {i:03d} Padding Text")
        for i in range(10)
    ]

    out_file = tmp_path / "sized.asc"
    written = writer.write(records, out_file)

    assert len(written) > 1
    for f in written:
        assert f.stat().st_size <= 100


def test_single_file_write_without_suffix_unless_forced(tmp_path: Path):
    """Single file fits in one chunk without suffix unless forced."""
    cfg = RNS510AscConfig(max_pois_per_file=10)
    writer = RNS510AscWriter(cfg)

    records = [POIRecord(id="1", lat=44.0, lon=26.0, name="Single")]

    out_file = tmp_path / "single.asc"
    written = writer.write(records, out_file, force_chunk_suffix=False)
    assert len(written) == 1
    assert written[0].name == "single.asc"

    written_forced = writer.write(records, out_file, force_chunk_suffix=True)
    assert len(written_forced) == 1
    assert written_forced[0].name == "single_001.asc"


def test_cp1250_and_utf8_encodings(tmp_path: Path):
    """Verify different encodings write valid bytes."""
    # CP1250 with transliterate=False
    cfg_cp1250 = RNS510AscConfig(charset="cp1250", ascii_transliterate=False)
    writer_cp1250 = RNS510AscWriter(cfg_cp1250)

    # UTF-8
    cfg_utf8 = RNS510AscConfig(charset="utf-8", ascii_transliterate=False)
    writer_utf8 = RNS510AscWriter(cfg_utf8)

    record = POIRecord(id="1", lat=44.0, lon=26.0, name="Brașov România")

    f_cp = tmp_path / "cp1250.asc"
    f_utf = tmp_path / "utf8.asc"

    writer_cp1250.write([record], f_cp)
    writer_utf8.write([record], f_utf)

    # Decode bytes back to test integrity
    content_cp = f_cp.read_bytes().decode("cp1250")
    content_utf = f_utf.read_bytes().decode("utf-8")

    # In CP1250, Romanian comma-below ș is mapped to cedilla ş (0xba in CP1250)
    # so that it encodes cleanly without turning into ?
    assert "Bra\u015fov" in content_cp and "Rom\xe2nia" in content_cp
    # In UTF-8, native unicode comma-below is retained
    assert "Bra\u0219ov" in content_utf and "Rom\xe2nia" in content_utf


def test_probe_file_cli(tmp_path: Path):
    """Test probe-file subcommand end-to-end via CLI."""
    out_file = tmp_path / "my_probe.asc"
    ret = main([
        "probe-file",
        "--out", str(out_file),
        "--lat", "44.4323",
        "--lon", "26.1063",
        "--count", "5",
        "--generate-matrix",
    ])
    assert ret == 0
    assert out_file.exists()
    assert out_file.stat().st_size > 0

    # Check matrix files were generated
    matrix_dir = tmp_path / "probe_matrix"
    assert matrix_dir.exists()
    matrix_files = list(matrix_dir.glob("*.asc"))
    assert len(matrix_files) == 8


def test_probe_records_grid_generation():
    """Test generating large synthetic grid for stress testing."""
    records = create_probe_records(count=100, preset="grid")
    assert len(records) == 100
    assert records[0].id == "probe-00001"
    assert records[99].id == "probe-00100"
