"""
id2url - Convert package registry coordinates (origin IDs) to source download URLs.

All registries automatically verify that packages exist before returning URLs.

Supported package managers:
- NPM (JavaScript/Node.js)
- Dart (pub.dev)
- PyPI (Python)
- Maven (Java/JVM) - supports Maven Central & Google Maven
- Crates.io (Rust)
- NuGet (.NET/C#)
- RubyGems (Ruby)
- Go Modules (Go)
- Packagist (PHP/Composer)
- CocoaPods (iOS/macOS)
- Hex (Erlang/Elixir)
"""

from typing import Tuple

from .registries import (
    GOOGLE_MAVEN_PREFIXES,
    get_cocoapods_download_url,
    get_crates_download_url,
    get_dart_download_url,
    get_go_module_download_url,
    get_hex_download_url,
    get_maven_download_url,
    get_npm_download_url,
    get_nuget_download_url,
    get_packagist_download_url,
    get_pypi_download_url,
    get_rubygems_download_url,
    normalize_pypi_name,
    parse_maven_coordinate,
)

__version__ = "0.1.0"

# Registry name to function mapping
REGISTRY_HANDLERS = {
    "npm": get_npm_download_url,
    "dart": get_dart_download_url,
    "pypi": get_pypi_download_url,
    "maven": get_maven_download_url,
    "crates": get_crates_download_url,
    "nuget": get_nuget_download_url,
    "rubygems": get_rubygems_download_url,
    "go": get_go_module_download_url,
    "packagist": get_packagist_download_url,
    "cocoapods": get_cocoapods_download_url,
    "hex": get_hex_download_url,
}

# Aliases for registry names
REGISTRY_ALIASES = {
    "npmjs": "npm",
    "pub.dev": "dart",
    "pub": "dart",
    "python": "pypi",
    "pip": "pypi",
    "java": "maven",
    "mvn": "maven",
    "rust": "crates",
    "cargo": "crates",
    "crates.io": "crates",
    "dotnet": "nuget",
    ".net": "nuget",
    "ruby": "rubygems",
    "gems": "rubygems",
    "golang": "go",
    "gomod": "go",
    "composer": "packagist",
    "php": "packagist",
    "ios": "cocoapods",
    "pods": "cocoapods",
    "swift": "cocoapods",
    "elixir": "hex",
    "erlang": "hex",
    "hex.pm": "hex",
}

SUPPORTED_REGISTRIES = list(REGISTRY_HANDLERS.keys())


def get_download_url(registry: str, origin_id: str) -> Tuple[str, str, str]:
    """
    Convert a package coordinate to a download URL for the specified registry.
    
    Automatically verifies that the package exists in the registry.
    For Maven, checks both Maven Central and Google Maven repositories.

    Args:
        registry: Package registry name (e.g., "npm", "pypi", "maven")
        origin_id: Package coordinate in registry-specific format

    Returns:
        Tuple of (package_name, version, download_url)

    Raises:
        ValueError: If registry is not supported, origin_id is invalid, or package not found

    Examples:
        >>> get_download_url("npm", "lodash/4.17.21")
        ('lodash', '4.17.21', 'https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz')

        >>> get_download_url("maven", "com.google.guava:guava:31.1-jre")
        ('guava', '31.1-jre', 'https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre-sources.jar')
        
        >>> get_download_url("maven", "androidx.glance.wear:wear:1.0.0-alpha10")
        ('wear', '1.0.0-alpha10', 'https://dl.google.com/android/maven2/androidx/glance/wear/wear/1.0.0-alpha10/wear-1.0.0-alpha10-sources.jar')
    """
    # Normalize registry name
    registry_lower = registry.lower()
    registry_name = REGISTRY_ALIASES.get(registry_lower, registry_lower)

    if registry_name not in REGISTRY_HANDLERS:
        raise ValueError(
            f"Unsupported registry: {registry}. "
            f"Supported registries: {', '.join(SUPPORTED_REGISTRIES)}"
        )

    handler = REGISTRY_HANDLERS[registry_name]
    return handler(origin_id)


__all__ = [
    "__version__",
    "SUPPORTED_REGISTRIES",
    "REGISTRY_ALIASES",
    "GOOGLE_MAVEN_PREFIXES",
    "get_download_url",
    # Individual registry functions
    "get_npm_download_url",
    "get_dart_download_url",
    "get_pypi_download_url",
    "get_maven_download_url",
    "get_crates_download_url",
    "get_nuget_download_url",
    "get_rubygems_download_url",
    "get_go_module_download_url",
    "get_packagist_download_url",
    "get_cocoapods_download_url",
    "get_hex_download_url",
    # Utilities
    "normalize_pypi_name",
    "parse_maven_coordinate",
]
