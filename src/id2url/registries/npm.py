"""NPM (npmjs) package registry URL resolver."""

from typing import Tuple

import requests

NPM_REGISTRY_BASE_URL = "https://registry.npmjs.org"


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_npm_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert NPM origin ID to download URL with automatic verification.

    Args:
        origin_id: Package coordinate (e.g., "lodash/4.17.21" or "@babel/core/7.22.0")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Example:
        >>> get_npm_download_url("lodash/4.17.21")
        ('lodash', '4.17.21', 'https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz')
        >>> get_npm_download_url("@babel/core/7.22.0")
        ('@babel/core', '7.22.0', 'https://registry.npmjs.org/@babel/core/-/core-7.22.0.tgz')
    """
    origin_id = origin_id.strip()

    if origin_id.startswith("@"):
        # Scoped package: @scope/package/version
        parts = origin_id.split("/")
        if len(parts) != 3:
            raise ValueError(f"Invalid scoped package format: {origin_id}")
        scope, package, version = parts[0], parts[1], parts[2]
        libname = f"{scope}/{package}"
        download_url = f"{NPM_REGISTRY_BASE_URL}/{scope}/{package}/-/{package}-{version}.tgz"
    else:
        # Regular package: package/version
        parts = origin_id.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid package format: {origin_id}")
        libname, version = parts[0], parts[1]
        download_url = f"{NPM_REGISTRY_BASE_URL}/{libname}/-/{libname}-{version}.tgz"

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Package not found in NPM registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return libname, version, download_url
