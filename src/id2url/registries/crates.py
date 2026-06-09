"""Crates.io (Rust) package registry URL resolver."""

from typing import Tuple

import requests

CRATES_IO_STATIC_URL = "https://static.crates.io/crates"
CRATES_IO_API_URL = "https://crates.io/api/v1/crates"


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        headers = {"User-Agent": "id2url/1.0"}  # Required by crates.io
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_crates_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert crates.io origin ID to download URL with automatic verification.

    Args:
        origin_id: Crate coordinate (e.g., "serde/1.0.188")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (crate_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or crate not found

    Note:
        The .crate file is a gzipped tarball.

    Example:
        >>> get_crates_download_url("serde/1.0.188")
        ('serde', '1.0.188', 'https://static.crates.io/crates/serde/serde-1.0.188.crate')
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<crate>/<version>', got: {origin_id}"
        )

    crate_name, version = parts[0], parts[1]

    # Static URL pattern
    download_url = f"{CRATES_IO_STATIC_URL}/{crate_name}/{crate_name}-{version}.crate"

    # Verify the crate exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Crate not found in crates.io registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return crate_name, version, download_url


def get_crates_api_url(origin_id: str) -> Tuple[str, str, str]:
    """
    Get crates.io API redirect URL (alternative method).

    This URL redirects to the static URL. Useful if you want the API
    to handle version resolution or want to follow redirects.

    Args:
        origin_id: Crate coordinate (e.g., "serde/1.0.188")

    Returns:
        Tuple of (crate_name, version, api_redirect_url)
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2:
        raise ValueError(f"Invalid origin_id format: {origin_id}")

    crate_name, version = parts[0], parts[1]

    # API redirect URL (302 redirects to static URL)
    download_url = f"{CRATES_IO_API_URL}/{crate_name}/{version}/download"

    return crate_name, version, download_url
