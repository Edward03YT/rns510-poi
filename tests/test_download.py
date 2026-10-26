"""Tests for cached, resumable downloader."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from poi_forge.download import (
    compute_md5,
    download_pbf_with_cache,
    fetch_remote_md5,
)


def test_compute_md5(tmp_path: Path):
    """Verify local MD5 hash computation."""
    f = tmp_path / "sample.bin"
    content = b"OpenStreetMap POI Data for RNS 510"
    f.write_bytes(content)
    expected = hashlib.md5(content).hexdigest().lower()
    assert compute_md5(f) == expected


def test_fetch_remote_md5():
    """Verify parsing remote MD5 format."""
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = "246ec72103aafdd01201f4be316382b5  romania-latest.osm.pbf\n"
        mock_get.return_value = mock_resp

        md5 = fetch_remote_md5("https://example.com/romania-latest.osm.pbf.md5")
        assert md5 == "246ec72103aafdd01201f4be316382b5"


def test_download_cache_hit(tmp_path: Path):
    """Verify that existing file with matching MD5 skips download."""
    target_dir = tmp_path / "downloads"
    target_dir.mkdir(parents=True)
    f = target_dir / "sample.osm.pbf"
    content = b"cached pbf bytes"
    f.write_bytes(content)
    content_md5 = hashlib.md5(content).hexdigest().lower()

    with patch("poi_forge.download.fetch_remote_md5", return_value=content_md5):
        with patch("requests.get") as mock_get:
            res = download_pbf_with_cache(
                pbf_url="https://example.com/sample.osm.pbf",
                target_dir=target_dir,
            )
            assert res.from_cache is True
            assert res.md5 == content_md5
            assert res.size_bytes == len(content)
            # No network call to download file
            assert mock_get.call_count == 0


def test_download_stream_and_verify(tmp_path: Path):
    """Verify streaming download and MD5 verification."""
    target_dir = tmp_path / "downloads"
    content = b"downloaded osm pbf stream chunk1 chunk2"
    content_md5 = hashlib.md5(content).hexdigest().lower()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "content-length": str(len(content)),
        "last-modified": "Mon, 26 Oct 2026 00:00:00 GMT",
    }
    mock_resp.iter_content.return_value = [b"downloaded osm pbf ", b"stream chunk1 chunk2"]
    mock_resp.__enter__.return_value = mock_resp

    with patch("poi_forge.download.fetch_remote_md5", return_value=content_md5):
        with patch("requests.get", return_value=mock_resp):
            res = download_pbf_with_cache(
                pbf_url="https://example.com/test.osm.pbf",
                target_dir=target_dir,
            )
            assert res.from_cache is False
            assert res.md5 == content_md5
            assert res.file_path.exists()
            assert res.file_path.read_bytes() == content
            assert res.extract_timestamp == "2026-10-26T00:00:00Z"


def test_download_md5_mismatch_raises_error(tmp_path: Path):
    """Verify that an MD5 mismatch raises an exception and cleans up partial file."""
    target_dir = tmp_path / "downloads"
    content = b"corrupted data"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": str(len(content))}
    mock_resp.iter_content.return_value = [content]

    with patch("poi_forge.download.fetch_remote_md5", return_value="expected_different_md5"):
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(ValueError, match="MD5 checksum verification failed"):
                download_pbf_with_cache(
                    pbf_url="https://example.com/corrupt.osm.pbf",
                    target_dir=target_dir,
                )

    # Temporary .part file should be deleted
    assert not (target_dir / "corrupt.osm.pbf.part").exists()
    assert not (target_dir / "corrupt.osm.pbf").exists()
