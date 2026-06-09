"""Dart (pub.dev) package registry URL resolver."""

from typing import Tuple

import requests

PUB_DEV_BASE_URL = "https://pub.dev"
PUB_DEV_ARCHIVE_PATH = "/api/archives"


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_dart_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert Dart pub.dev origin ID to download URL with automatic verification.

    Args:
        origin_id: Package coordinate (e.g., "vm_service/15.0.2")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Example:
        >>> get_dart_download_url("vm_service/15.0.2")
        ('vm_service', '15.0.2', 'https://pub.dev/api/archives/vm_service-15.0.2.tar.gz')
    """
    origin_id = origin_id.strip()

    if "/" not in origin_id:
        raise ValueError(
            f"Invalid origin id format. Expected '<package>/<version>', got: {origin_id}"
        )

    parts = origin_id.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid origin id format: {origin_id}")

    libname, libversion = parts[0], parts[1]
    download_url = f"{PUB_DEV_BASE_URL}{PUB_DEV_ARCHIVE_PATH}/{libname}-{libversion}.tar.gz"

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Package not found in pub.dev registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return libname, libversion, download_url
