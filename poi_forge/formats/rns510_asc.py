"""Configurable writer for VW RNS 510 Personal POI (.asc) format.

NOTE: All defaults are marked UNVERIFIED until physical hardware testing
is completed on an RNS 510 unit. See docs/FORMAT_PROBE.md.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from poi_forge.formats.base import POIRecord, POIWriter

# Specific character transliteration mapping (Romanian and common European characters)
TRANSLITERATION_MAP = {
    # Romanian diacritics (standard comma-below and legacy cedilla)
    "ș": "s",
    "Ș": "S",
    "ş": "s",
    "Ş": "S",
    "ț": "t",
    "Ț": "T",
    "ţ": "t",
    "Ţ": "T",
    "ă": "a",
    "Ă": "A",
    "â": "a",
    "Â": "A",
    "î": "i",
    "Î": "I",
    # German and Nordic ligatures
    "ß": "ss",
    "æ": "ae",
    "Æ": "AE",
    "œ": "oe",
    "Œ": "OE",
    "ø": "o",
    "Ø": "O",
    "đ": "d",
    "Đ": "D",
    "ł": "l",
    "Ł": "L",
}

# Mapping for Romanian comma-below characters to legacy cedilla characters
# required for Windows-1250 (CP1250) compatibility when transliteration is disabled
CP1250_CEDILLA_MAP = {
    "\u0218": "\u015e",  # Ș -> Ş
    "\u0219": "\u015f",  # ș -> ş
    "\u021a": "\u0162",  # Ț -> Ţ
    "\u021b": "\u0163",  # ț -> ţ
}

CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class RNS510AscConfig:
    """Configuration parameters for the RNS 510 ASC writer."""

    verified: bool = False
    verification_note: str = "UNVERIFIED: Default ASC settings based on community convention."

    # Fields structure
    field_order: list[str] = field(
        default_factory=lambda: ["lon", "lat", "name", "description"]
    )
    separator: str = ","
    coordinate_order: str = "lon_lat"  # "lon_lat" or "lat_lon"
    coordinate_decimals: int = 6
    quote_text: bool = True
    quote_char: str = '"'
    escape_quote: str = '""'  # '""' (double), r'\"' (backslash), or 'strip'

    # Encoding
    charset: str = "cp1250"
    ascii_transliterate: bool = True
    on_encoding_error: str = "replace"

    # Line formatting
    line_endings: str = "crlf"  # "crlf" (\r\n) or "lf" (\n)

    # Practical limits
    max_name_length: int = 60
    max_desc_length: int = 120
    max_pois_per_file: int = 5000
    max_file_size_bytes: int = 2097152

    # SD Card directory
    sd_card_dir: str = "PersonalPOI"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RNS510AscConfig:
        """Create config from dictionary."""
        fields_data = data.get("fields", {})
        encoding_data = data.get("encoding", {})
        limits_data = data.get("limits", {})

        return cls(
            verified=data.get("verified", False),
            verification_note=data.get(
                "verification_note", "UNVERIFIED: Default ASC settings."
            ),
            field_order=fields_data.get(
                "order", ["lon", "lat", "name", "description"]
            ),
            separator=fields_data.get("separator", ","),
            coordinate_order=fields_data.get("coordinate_order", "lon_lat"),
            coordinate_decimals=fields_data.get("coordinate_decimals", 6),
            quote_text=fields_data.get("quote_text", True),
            quote_char=fields_data.get("quote_char", '"'),
            escape_quote=fields_data.get("escape_quote", '""'),
            charset=encoding_data.get("charset", "cp1250"),
            ascii_transliterate=encoding_data.get("ascii_transliterate", True),
            on_encoding_error=encoding_data.get("on_encoding_error", "replace"),
            line_endings=data.get("line_endings", "crlf"),
            max_name_length=limits_data.get("max_name_length", 60),
            max_desc_length=limits_data.get("max_desc_length", 120),
            max_pois_per_file=limits_data.get("max_pois_per_file", 5000),
            max_file_size_bytes=limits_data.get("max_file_size_bytes", 2097152),
            sd_card_dir=data.get("sd_card_dir", "PersonalPOI"),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> RNS510AscConfig:
        """Load configuration from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "verified": self.verified,
            "verification_note": self.verification_note,
            "fields": {
                "order": self.field_order,
                "separator": self.separator,
                "coordinate_order": self.coordinate_order,
                "coordinate_decimals": self.coordinate_decimals,
                "quote_text": self.quote_text,
                "quote_char": self.quote_char,
                "escape_quote": self.escape_quote,
            },
            "encoding": {
                "charset": self.charset,
                "ascii_transliterate": self.ascii_transliterate,
                "on_encoding_error": self.on_encoding_error,
            },
            "line_endings": self.line_endings,
            "limits": {
                "max_name_length": self.max_name_length,
                "max_desc_length": self.max_desc_length,
                "max_pois_per_file": self.max_pois_per_file,
                "max_file_size_bytes": self.max_file_size_bytes,
            },
            "sd_card_dir": self.sd_card_dir,
        }


def transliterate_to_ascii(text: str) -> str:
    """Transliterate diacritics and special characters to plain ASCII equivalents."""
    # 1. Apply explicit mappings (Romanian, ligatures)
    for char, repl in TRANSLITERATION_MAP.items():
        if char in text:
            text = text.replace(char, repl)

    # 2. Decompose unicode characters with combining marks (NFKD)
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))

    # 3. Handle remaining non-ASCII characters if any
    return stripped


class RNS510AscWriter(POIWriter):
    """Writes POI records in RNS 510 .asc format according to configuration."""

    def __init__(self, config: RNS510AscConfig | None = None) -> None:
        self.config = config or RNS510AscConfig()

    def sanitize_text(self, text: str, max_length: int) -> str:
        """Sanitize, optionally transliterate, and clamp text field."""
        if not text:
            return ""

        # Remove control characters and normalize whitespaces
        cleaned = CONTROL_CHAR_RE.sub(" ", text)
        cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()

        # Transliterate if configured
        if self.config.ascii_transliterate:
            cleaned = transliterate_to_ascii(cleaned)
        elif self.config.charset.lower() in ("cp1250", "windows-1250"):
            for c_below, cedilla in CP1250_CEDILLA_MAP.items():
                if c_below in cleaned:
                    cleaned = cleaned.replace(c_below, cedilla)

        # Truncate to max_length on character boundary
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rstrip()

        return cleaned

    def format_text_field(self, text: str) -> str:
        """Format and quote a text field based on configuration."""
        q = self.config.quote_char

        if self.config.quote_text:
            if self.config.escape_quote == '""':
                escaped = text.replace(q, q + q)
            elif self.config.escape_quote in (r'\"', '\\"'):
                escaped = text.replace(q, "\\" + q)
            elif self.config.escape_quote == "strip":
                escaped = text.replace(q, "")
            else:
                escaped = text.replace(q, q + q)
            return f"{q}{escaped}{q}"
        else:
            # If not quoted, ensure field separator is stripped or replaced
            sep = self.config.separator
            return text.replace(sep, " ")

    def format_record(self, record: POIRecord) -> str:
        """Format a single POI record into an ASC line."""
        # Sanitize text fields
        name = self.sanitize_text(record.name, self.config.max_name_length)
        desc = self.sanitize_text(record.description, self.config.max_desc_length)

        # Coordinate rounding
        decimals = self.config.coordinate_decimals
        lon_str = f"{record.lon:.{decimals}f}"
        lat_str = f"{record.lat:.{decimals}f}"

        # Resolve field values
        field_values: dict[str, str] = {
            "lon": lon_str,
            "lat": lat_str,
            "name": self.format_text_field(name),
            "description": self.format_text_field(desc),
        }

        # Handle coordinate order override if order is generic
        order = list(self.config.field_order)
        if self.config.coordinate_order == "lat_lon":
            # If order has lon before lat, swap them
            if "lon" in order and "lat" in order:
                lon_idx = order.index("lon")
                lat_idx = order.index("lat")
                if lon_idx < lat_idx:
                    order[lon_idx], order[lat_idx] = "lat", "lon"
        elif self.config.coordinate_order == "lon_lat":
            if "lon" in order and "lat" in order:
                lon_idx = order.index("lon")
                lat_idx = order.index("lat")
                if lat_idx < lon_idx:
                    order[lon_idx], order[lat_idx] = "lon", "lat"

        formatted_fields = [field_values.get(f, "") for f in order]
        return self.config.separator.join(formatted_fields)

    def encode_line(self, line: str) -> bytes:
        """Encode line with configured line ending and charset."""
        ending = "\r\n" if self.config.line_endings.lower() == "crlf" else "\n"
        full_line = line + ending
        return full_line.encode(
            self.config.charset,
            errors=self.config.on_encoding_error,
        )

    def write(
        self,
        records: Sequence[POIRecord],
        destination: Path,
        force_chunk_suffix: bool = False,
    ) -> list[Path]:
        """Write POI records to destination, splitting into chunks if necessary.

        Args:
            records: Records to write.
            destination: Output file path.
            force_chunk_suffix: Always add _001, _002 suffix even if only 1 chunk.

        Returns:
            List of generated file paths.
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if not records:
            # Write empty file
            target = destination
            if force_chunk_suffix:
                target = destination.parent / f"{destination.stem}_001{destination.suffix}"
            target.write_bytes(b"")
            return [target]

        # Partition records into chunks based on max_pois_per_file and max_file_size_bytes
        chunks: list[list[bytes]] = []
        current_chunk: list[bytes] = []
        current_chunk_bytes = 0

        for record in records:
            line_bytes = self.encode_line(self.format_record(record))
            line_len = len(line_bytes)

            exceeds_count = len(current_chunk) >= self.config.max_pois_per_file
            exceeds_size = (
                current_chunk_bytes + line_len > self.config.max_file_size_bytes
                and len(current_chunk) > 0
            )

            if exceeds_count or exceeds_size:
                chunks.append(current_chunk)
                current_chunk = [line_bytes]
                current_chunk_bytes = line_len
            else:
                current_chunk.append(line_bytes)
                current_chunk_bytes += line_len

        if current_chunk:
            chunks.append(current_chunk)

        # Write chunks to disk
        written_files: list[Path] = []
        needs_suffix = force_chunk_suffix or len(chunks) > 1

        stem = destination.stem
        suffix = destination.suffix or ".asc"

        for idx, chunk in enumerate(chunks, start=1):
            if needs_suffix:
                chunk_filename = f"{stem}_{idx:03d}{suffix}"
            else:
                chunk_filename = f"{stem}{suffix}"

            chunk_path = destination.parent / chunk_filename
            with open(chunk_path, "wb") as f:
                for line in chunk:
                    f.write(line)

            written_files.append(chunk_path)

        return written_files
