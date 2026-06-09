"""RubyGems package registry URL resolver."""

from typing import Dict, Optional, Tuple

import requests

RUBYGEMS_BASE_URL = "https://rubygems.org"

# Known Ruby platforms
RUBY_PLATFORMS = {
    "ruby",
    "x86_64-linux",
    "x86_64-linux-musl",
    "x86_64-darwin",
    "arm64-darwin",
    "x86-mingw32",
    "x64-mingw32",
    "x64-mingw-ucrt",
    "java",
    "jruby",
    "mswin32",
    "universal-darwin",
}


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def parse_rubygems_coordinate(origin_id: str) -> Dict[str, Optional[str]]:
    """
    Parse RubyGems coordinate, handling platform-specific gems.

    Formats:
    - gem/version           -> Generic gem
    - gem/version-platform  -> Platform-specific precompiled gem

    Examples:
        nokogiri/1.15.4              -> Generic source gem
        nokogiri/1.15.4-x86_64-linux -> Precompiled for Linux x64
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<gem>/<version>', got: {origin_id}"
        )

    gem_name = parts[0]
    version_part = parts[1]

    # Check if version contains a platform suffix
    # Platform is typically after a hyphen at the end: 1.15.4-x86_64-linux
    platform: Optional[str] = None
    version = version_part

    # Try to detect platform suffix (check longer platforms first)
    for plat in sorted(RUBY_PLATFORMS, key=len, reverse=True):
        if version_part.endswith(f"-{plat}"):
            version = version_part[: -(len(plat) + 1)]  # Remove -platform
            platform = plat
            break

    return {
        "gem_name": gem_name,
        "version": version,
        "platform": platform,
        "full_version": version_part,
    }


def get_rubygems_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert RubyGems origin ID to download URL with automatic verification.

    Args:
        origin_id: Gem coordinate (e.g., "rails/7.1.2" or "nokogiri/1.15.4-x86_64-linux")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (gem_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or gem not found

    Note:
        Platform-specific gems have the platform in the filename:
        - nokogiri-1.15.4.gem           (source/generic)
        - nokogiri-1.15.4-x86_64-linux.gem  (precompiled)

    Examples:
        >>> get_rubygems_download_url("rails/7.1.2")
        ('rails', '7.1.2', 'https://rubygems.org/downloads/rails-7.1.2.gem')
        >>> get_rubygems_download_url("nokogiri/1.15.4-x86_64-linux")
        ('nokogiri', '1.15.4-x86_64-linux', 'https://rubygems.org/downloads/nokogiri-1.15.4-x86_64-linux.gem')
    """
    parsed = parse_rubygems_coordinate(origin_id)

    gem_name = parsed["gem_name"]
    full_version = parsed["full_version"]

    # Filename includes full version (with platform if present)
    download_url = f"{RUBYGEMS_BASE_URL}/downloads/{gem_name}-{full_version}.gem"

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Gem not found in RubyGems registry: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return gem_name, full_version or "", download_url


def get_rubygems_source_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Get RubyGems source gem URL (always generic, no platform) with verification.

    Use this when you specifically want the source gem, not a precompiled version.
    """
    parsed = parse_rubygems_coordinate(origin_id)

    gem_name = parsed["gem_name"]
    version = parsed["version"]  # Base version without platform

    download_url = f"{RUBYGEMS_BASE_URL}/downloads/{gem_name}-{version}.gem"

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Source gem not found in RubyGems registry: {gem_name}/{version}\n"
            f"Checked: {download_url}"
        )

    return gem_name, version or "", download_url
