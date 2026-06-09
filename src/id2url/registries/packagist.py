"""Packagist (PHP/Composer) package registry URL resolver."""

from typing import Optional, Tuple

import requests

PACKAGIST_BASE_URL = "https://packagist.org"
PACKAGIST_API_URL = "https://repo.packagist.org/p2"


def get_packagist_download_url(
    origin_id: str, timeout: int = 30
) -> Tuple[str, str, str]:
    """
    Convert Packagist origin ID to download URL by querying the API.

    Args:
        origin_id: Package coordinate (e.g., "laravel/framework/v10.35.0")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or package not found

    Note:
        Packagist packages are typically hosted on GitHub/GitLab.
        The API returns the actual download URL (usually a GitHub archive).

    Example:
        >>> get_packagist_download_url("monolog/monolog/3.5.0")
        ('monolog/monolog', '3.5.0', 'https://api.github.com/repos/Seldaek/monolog/zipball/...')
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 3 or not parts[0] or not parts[1] or not parts[2]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<vendor>/<package>/<version>', got: {origin_id}"
        )

    vendor, package, version = parts[0], parts[1], parts[2]
    package_name = f"{vendor}/{package}"

    # Fetch package metadata from Packagist API
    api_url = f"{PACKAGIST_API_URL}/{vendor}/{package}.json"
    response = requests.get(api_url, timeout=timeout)

    if response.status_code == 404:
        raise ValueError(f"Package not found: {package_name}")
    elif response.status_code != 200:
        raise Exception(f"Packagist API error: HTTP {response.status_code}")

    data = response.json()
    packages = data.get("packages", {}).get(package_name, [])

    # Find the matching version
    download_url: Optional[str] = None
    for pkg_version in packages:
        if (
            pkg_version.get("version") == version
            or pkg_version.get("version_normalized") == version
        ):
            dist = pkg_version.get("dist", {})
            download_url = dist.get("url")
            break

    if not download_url:
        raise ValueError(f"Version {version} not found for {package_name}")

    return package_name, version, download_url


def get_packagist_github_archive_url(vendor: str, repo: str, version: str) -> str:
    """
    Construct direct GitHub archive URL for Packagist packages hosted on GitHub.

    Args:
        vendor: GitHub username/org
        repo: Repository name
        version: Version tag (e.g., "v10.35.0" or "3.5.0")

    Returns:
        Direct GitHub archive download URL
    """
    return f"https://api.github.com/repos/{vendor}/{repo}/zipball/{version}"
