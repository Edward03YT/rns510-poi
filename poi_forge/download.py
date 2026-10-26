"""Cached, resumable download utility with MD5 checksum verification."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import osmium
import requests


@dataclass
class DownloadResult:
    """Result of a download operation with metadata."""

    file_path: Path
    md5: str
    size_bytes: int
    extract_timestamp: str | None  # ISO 8601 string
    from_cache: bool


def compute_md5(file_path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    """Compute MD5 checksum of a local file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def fetch_remote_md5(md5_url: str, timeout: int = 15) -> str:
    """Fetch expected MD5 checksum from Geofabrik .md5 URL."""
    resp = requests.get(md5_url, timeout=timeout)
    resp.raise_for_status()
    # Content format: "<md5_hash>  <filename>\n"
    text = resp.text.strip()
    return text.split()[0].lower()


def get_pbf_extract_timestamp(pbf_path: Path | str) -> str | None:
    """Extract OSM replication timestamp from PBF header using osmium."""
    try:
        reader = osmium.io.Reader(str(pbf_path))
        header = reader.header()
        # Geofabrik stores timestamp in osmosis_replication_timestamp or timestamp
        ts_str = header.get("osmosis_replication_timestamp") or header.get("timestamp")
        reader.close()
        if ts_str:
            # Parse or ensure standard ISO format
            if ts_str.endswith("Z") or "+" in ts_str:
                return ts_str
            return f"{ts_str}Z"
    except Exception:
        pass
    return None


def download_pbf_with_cache(
    pbf_url: str,
    target_dir: Path | str,
    md5_url: str | None = None,
    progress_callback: Callable[[int, int | None], None] | None = None,
    chunk_size: int = 1024 * 512,
    timeout: int = 30,
) -> DownloadResult:
    """Download a .osm.pbf file with MD5 check, cache validation, and resume support.

    Args:
        pbf_url: Direct URL to the .osm.pbf file.
        target_dir: Directory where the download should be stored.
        md5_url: Optional URL to .md5 checksum file (defaults to pbf_url + '.md5').
        progress_callback: Optional callback receiving (bytes_read, total_bytes).
        chunk_size: Buffer size for streaming download.
        timeout: HTTP timeout in seconds.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = pbf_url.split("/")[-1]
    final_path = target_dir / filename
    part_path = target_dir / f"{filename}.part"

    if md5_url is None:
        md5_url = pbf_url + ".md5"

    # 1. Fetch remote MD5
    expected_md5 = fetch_remote_md5(md5_url, timeout=timeout)

    # 2. Check if cached complete file exists and matches MD5
    if final_path.exists():
        local_md5 = compute_md5(final_path)
        if local_md5 == expected_md5:
            # Valid cached file
            ts = get_pbf_extract_timestamp(final_path)
            return DownloadResult(
                file_path=final_path,
                md5=local_md5,
                size_bytes=final_path.stat().st_size,
                extract_timestamp=ts,
                from_cache=True,
            )

    # 3. Check for partial file for resumable download
    existing_bytes = 0
    headers: dict[str, str] = {}
    if part_path.exists():
        existing_bytes = part_path.stat().st_size
        if existing_bytes > 0:
            headers["Range"] = f"bytes={existing_bytes}-"

    # 4. Stream download
    with requests.get(pbf_url, headers=headers, stream=True, timeout=timeout) as resp:
        is_partial = resp.status_code == 206
        if resp.status_code not in (200, 206):
            resp.raise_for_status()

        # Parse total size and last-modified header as fallback timestamp
        total_size: int | None = None
        content_len = resp.headers.get("content-length")
        if content_len:
            total_size = int(content_len) + (existing_bytes if is_partial else 0)

        http_last_modified = resp.headers.get("last-modified")

        mode = "ab" if is_partial else "wb"
        bytes_read = existing_bytes if is_partial else 0

        with open(part_path, mode) as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bytes_read += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_read, total_size)

    # 5. Verify MD5 of finished file
    downloaded_md5 = compute_md5(part_path)
    if downloaded_md5 != expected_md5:
        part_path.unlink(missing_ok=True)
        raise ValueError(
            f"MD5 checksum verification failed for {filename}. "
            f"Expected: {expected_md5}, got: {downloaded_md5}"
        )

    # 6. Move .part to final file
    if final_path.exists():
        final_path.unlink()
    part_path.rename(final_path)

    # 7. Resolve extract timestamp
    ts = get_pbf_extract_timestamp(final_path)
    if not ts and http_last_modified:
        try:
            dt = parsedate_to_datetime(http_last_modified).astimezone(timezone.utc)
            ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            pass

    return DownloadResult(
        file_path=final_path,
        md5=downloaded_md5,
        size_bytes=final_path.stat().st_size,
        extract_timestamp=ts,
        from_cache=False,
    )
