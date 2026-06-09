"""NuGet (.NET) package registry URL resolver."""

from typing import Tuple

import requests

NUGET_BASE_URL = "https://api.nuget.org/v3-flatcontainer"


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_nuget_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert NuGet origin ID to download URL with automatic verification.

    Args:
        origin_id: Package coordinate (e.g., "Newtonsoft.Json/13.0.3")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Note:
        NuGet package IDs are case-insensitive, but URLs use lowercase.
        The .nupkg file is a ZIP archive containing the assembly and metadata.

    Example:
        >>> get_nuget_download_url("Newtonsoft.Json/13.0.3")
        ('Newtonsoft.Json', '13.0.3', 'https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg')
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<package>/<version>', got: {origin_id}"
        )

    package_name, version = parts[0], parts[1]

    # NuGet URLs use lowercase package names
    package_lower = package_name.lower()
    version_lower = version.lower()

    download_url = (
        f"{NUGET_BASE_URL}/{package_lower}/{version_lower}/"
        f"{package_lower}.{version_lower}.nupkg"
    )

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Package not found in NuGet registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return package_name, version, download_url


def get_nuget_snupkg_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Get NuGet symbols package (.snupkg) download URL with verification.

    Args:
        origin_id: Package coordinate (e.g., "Newtonsoft.Json/13.0.3")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2:
        raise ValueError(f"Invalid origin_id format: {origin_id}")

    package_name, version = parts[0], parts[1]
    package_lower = package_name.lower()
    version_lower = version.lower()

    download_url = (
        f"{NUGET_BASE_URL}/{package_lower}/{version_lower}/"
        f"{package_lower}.{version_lower}.snupkg"
    )

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Symbols package not found in NuGet registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return package_name, version, download_url
