"""Registry modules for various package managers."""

from .npm import get_npm_download_url
from .dart import get_dart_download_url
from .pypi import get_pypi_download_url, normalize_pypi_name
from .maven import get_maven_download_url, parse_maven_coordinate, GOOGLE_MAVEN_PREFIXES
from .crates import get_crates_download_url
from .nuget import get_nuget_download_url
from .rubygems import get_rubygems_download_url
from .go import get_go_module_download_url
from .packagist import get_packagist_download_url
from .cocoapods import get_cocoapods_download_url
from .hex import get_hex_download_url

__all__ = [
    "get_npm_download_url",
    "get_dart_download_url",
    "get_pypi_download_url",
    "normalize_pypi_name",
    "get_maven_download_url",
    "parse_maven_coordinate",
    "GOOGLE_MAVEN_PREFIXES",
    "get_crates_download_url",
    "get_nuget_download_url",
    "get_rubygems_download_url",
    "get_go_module_download_url",
    "get_packagist_download_url",
    "get_cocoapods_download_url",
    "get_hex_download_url",
]
