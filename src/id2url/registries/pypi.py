"""PyPI package registry URL resolver."""

import re
from typing import Optional, Tuple

import requests

PYPI_BASE_URL = "https://pypi.org"
PYPI_API_PATH = "/pypi"


def normalize_pypi_name(name: str) -> str:
    """
    Normalize PyPI package name according to PEP 503.

    PyPI normalizes names: lowercase, and replace runs of [-_.] with single hyphen.

    Examples:
        My_Package → my-package
        some.package → some-package
        typing_extensions → typing-extensions
    """
    return re.sub(r"[-_.]+", "-", name.lower())


def get_pypi_download_url(
    origin_id: str, timeout: int = 30, prefer_wheel: bool = False
) -> Tuple[str, str, str]:
    """
    Convert PyPI origin ID to download URL by querying the PyPI JSON API.

    Args:
        origin_id: Package coordinate (e.g., "alembic/1.12.1" or "typing_extensions/4.8.0")
        timeout: Request timeout in seconds
        prefer_wheel: If True, prefer .whl files over .tar.gz

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Note:
        - PyPI requires an API call because download URLs contain content hashes.
        - Package names are normalized (My_Package → my-package)
        - Prefers .tar.gz source distributions by default; falls back to first available file.

    Example:
        >>> get_pypi_download_url("requests/2.31.0")
        ('requests', '2.31.0', 'https://files.pythonhosted.org/packages/.../requests-2.31.0.tar.gz')
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<package>/<version>', got: {origin_id}"
        )

    libname, libversion = parts[0], parts[1]

    # Normalize package name for API lookup (PEP 503)
    normalized_name = normalize_pypi_name(libname)

    # Query PyPI JSON API (uses normalized name)
    api_url = f"{PYPI_BASE_URL}{PYPI_API_PATH}/{normalized_name}/{libversion}/json"
    response = requests.get(api_url, timeout=timeout)

    if response.status_code == 404:
        raise ValueError(f"Package not found: {origin_id}")
    elif response.status_code != 200:
        raise Exception(f"PyPI API error for {origin_id}: HTTP {response.status_code}")

    data = response.json()
    urls = data.get("urls", [])

    if not urls:
        raise ValueError(f"No download URLs found for {origin_id}")

    # Select download URL based on preference
    download_url: Optional[str] = None
    if prefer_wheel:
        for file_info in urls:
            if file_info.get("filename", "").endswith(".whl"):
                download_url = file_info["url"]
                break
    else:
        for file_info in urls:
            if file_info.get("filename", "").endswith(".tar.gz"):
                download_url = file_info["url"]
                break

    # Fallback to first available URL
    if not download_url:
        download_url = urls[0]["url"]

    return libname, libversion, download_url
