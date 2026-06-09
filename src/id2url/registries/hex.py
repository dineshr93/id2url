"""Hex.pm (Erlang/Elixir) package registry URL resolver."""

from typing import Dict, Optional, Tuple

import requests

HEX_PM_BASE_URL = "https://repo.hex.pm"


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def parse_hex_coordinate(origin_id: str) -> Dict[str, Optional[str]]:
    """
    Parse Hex.pm coordinate, handling organization-scoped packages.

    Formats:
    - package/version           -> Public package
    - @org/package/version      -> Organization private package

    Note: Organization packages require authentication and use a different repo URL.
    """
    origin_id = origin_id.strip()

    if origin_id.startswith("@"):
        # Organization package: @org/package/version
        parts = origin_id[1:].split("/")  # Remove @ and split
        if len(parts) != 3 or not parts[0] or not parts[1] or not parts[2]:
            raise ValueError(
                f"Invalid org package format. Expected '@org/package/version', got: {origin_id}"
            )
        return {
            "organization": parts[0],
            "package_name": parts[1],
            "version": parts[2],
            "is_org_package": True,
        }
    else:
        # Public package: package/version
        parts = origin_id.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid origin_id format. Expected '<package>/<version>', got: {origin_id}"
            )
        return {
            "organization": None,
            "package_name": parts[0],
            "version": parts[1],
            "is_org_package": False,
        }


def get_hex_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert Hex.pm origin ID to download URL with automatic verification.

    Args:
        origin_id: Package coordinate (e.g., "phoenix/1.7.10" or "@myorg/private_pkg/1.0.0")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Note:
        - Public packages: https://repo.hex.pm/tarballs/{package}-{version}.tar
        - Org packages: https://repo.hex.pm/repos/{org}/tarballs/{package}-{version}.tar
        - Organization packages require authentication (API key)

    Example:
        >>> get_hex_download_url("phoenix/1.7.10")
        ('phoenix', '1.7.10', 'https://repo.hex.pm/tarballs/phoenix-1.7.10.tar')
        >>> get_hex_download_url("@myorg/private_lib/2.0.0")
        ('private_lib', '2.0.0', 'https://repo.hex.pm/repos/myorg/tarballs/private_lib-2.0.0.tar')
    """
    parsed = parse_hex_coordinate(origin_id)

    package_name = parsed["package_name"]
    version = parsed["version"]

    if parsed["is_org_package"]:
        org = parsed["organization"]
        download_url = f"{HEX_PM_BASE_URL}/repos/{org}/tarballs/{package_name}-{version}.tar"
    else:
        download_url = f"{HEX_PM_BASE_URL}/tarballs/{package_name}-{version}.tar"

    # Verify URL exists (skip for org packages as they require auth)
    if not parsed["is_org_package"] and not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Package not found in Hex.pm registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return package_name, version or "", download_url


def get_hex_docs_url(origin_id: str) -> str:
    """
    Get Hex.pm documentation tarball URL.

    Args:
        origin_id: Package coordinate

    Returns:
        URL to the documentation tarball
    """
    parsed = parse_hex_coordinate(origin_id)
    package_name = parsed["package_name"]
    version = parsed["version"]

    if parsed["is_org_package"]:
        org = parsed["organization"]
        return f"{HEX_PM_BASE_URL}/repos/{org}/docs/{package_name}-{version}.tar.gz"
    else:
        return f"{HEX_PM_BASE_URL}/docs/{package_name}-{version}.tar.gz"


def get_hex_api_url(package_name: str, organization: Optional[str] = None) -> str:
    """
    Get Hex.pm API URL for package metadata.

    Args:
        package_name: Package name
        organization: Optional organization name

    Returns:
        API URL for package metadata
    """
    if organization:
        return f"https://hex.pm/api/repos/{organization}/packages/{package_name}"
    return f"https://hex.pm/api/packages/{package_name}"
