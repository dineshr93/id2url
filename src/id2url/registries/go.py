"""Go Modules package registry URL resolver."""

from typing import Tuple

import requests

GO_PROXY_BASE_URL = "https://proxy.golang.org"


def _encode_module_path(path: str) -> str:
    """
    Encode Go module path for proxy URL.

    Go proxy URL encoding: uppercase letters become !lowercase
    e.g., "GitHub" -> "!git!hub"
    """
    return "".join(f"!{c.lower()}" if c.isupper() else c for c in path)


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_go_module_download_url(origin_id: str, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Convert Go module origin ID to download URL with automatic verification.

    Args:
        origin_id: Module coordinate (e.g., "github.com/gin-gonic/gin/v1.9.1")
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (module_path, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or module not found

    Note:
        Go module versions must start with 'v' (e.g., v1.9.1).
        The proxy returns a .zip file containing the module source.

    Example:
        >>> get_go_module_download_url("github.com/gin-gonic/gin/v1.9.1")
        ('github.com/gin-gonic/gin', 'v1.9.1', 'https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.zip')
    """
    origin_id = origin_id.strip()

    # Find the version (starts with 'v')
    parts = origin_id.split("/")

    version = None
    module_parts = []

    for i, part in enumerate(parts):
        if part.startswith("v") and any(c.isdigit() for c in part):
            version = part
            module_parts = parts[:i]
            break

    if not version or not module_parts:
        raise ValueError(
            f"Invalid Go module format. Expected '<module>/v<version>', got: {origin_id}"
        )

    module_path = "/".join(module_parts)
    encoded_path = _encode_module_path(module_path)
    download_url = f"{GO_PROXY_BASE_URL}/{encoded_path}/@v/{version}.zip"

    # Verify URL exists
    if not _check_url_exists(download_url, timeout):
        raise ValueError(
            f"Module not found in Go proxy: {origin_id}\n"
            f"Checked: {download_url}"
        )

    return module_path, version, download_url


def get_go_module_info_url(module_path: str, version: str) -> str:
    """
    Get Go proxy URL for module version info (.info file).

    Args:
        module_path: Module path (e.g., "github.com/gin-gonic/gin")
        version: Version tag (e.g., "v1.9.1")

    Returns:
        URL to the .info file containing version metadata JSON
    """
    encoded_path = _encode_module_path(module_path)
    return f"{GO_PROXY_BASE_URL}/{encoded_path}/@v/{version}.info"


def get_go_module_mod_url(module_path: str, version: str) -> str:
    """
    Get Go proxy URL for go.mod file.

    Args:
        module_path: Module path (e.g., "github.com/gin-gonic/gin")
        version: Version tag (e.g., "v1.9.1")

    Returns:
        URL to the go.mod file
    """
    encoded_path = _encode_module_path(module_path)
    return f"{GO_PROXY_BASE_URL}/{encoded_path}/@v/{version}.mod"
