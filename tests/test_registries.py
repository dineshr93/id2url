"""Tests for registry URL resolvers."""

import pytest

from id2url import (
    SUPPORTED_REGISTRIES,
    get_crates_download_url,
    get_dart_download_url,
    get_download_url,
    get_go_module_download_url,
    get_hex_download_url,
    get_maven_download_url,
    get_npm_download_url,
    get_nuget_download_url,
    get_rubygems_download_url,
    normalize_pypi_name,
    parse_maven_coordinate,
)


class TestNPM:
    """Tests for NPM registry."""

    def test_regular_package(self):
        name, version, url = get_npm_download_url("lodash/4.17.21")
        assert name == "lodash"
        assert version == "4.17.21"
        assert url == "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"

    def test_scoped_package(self):
        name, version, url = get_npm_download_url("@babel/core/7.22.0")
        assert name == "@babel/core"
        assert version == "7.22.0"
        assert url == "https://registry.npmjs.org/@babel/core/-/core-7.22.0.tgz"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_npm_download_url("invalid")

    def test_invalid_scoped_format(self):
        with pytest.raises(ValueError):
            get_npm_download_url("@scope/package")  # Missing version


class TestDart:
    """Tests for Dart (pub.dev) registry."""

    def test_regular_package(self):
        name, version, url = get_dart_download_url("vm_service/15.0.2")
        assert name == "vm_service"
        assert version == "15.0.2"
        assert url == "https://pub.dev/api/archives/vm_service-15.0.2.tar.gz"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_dart_download_url("invalid")


class TestPyPINormalization:
    """Tests for PyPI name normalization."""

    def test_underscore(self):
        assert normalize_pypi_name("typing_extensions") == "typing-extensions"

    def test_dot(self):
        assert normalize_pypi_name("ruamel.yaml") == "ruamel-yaml"

    def test_uppercase(self):
        assert normalize_pypi_name("Pillow") == "pillow"

    def test_mixed(self):
        assert normalize_pypi_name("My_Package.Name") == "my-package-name"


class TestMaven:
    """Tests for Maven registry."""

    def test_three_part_coordinate(self):
        name, version, url = get_maven_download_url("com.google.guava:guava:31.1-jre")
        assert name == "guava"
        assert version == "31.1-jre"
        assert "com/google/guava/guava/31.1-jre/guava-31.1-jre-sources.jar" in url

    def test_four_part_coordinate(self):
        name, version, url = get_maven_download_url("com.google.guava:guava:pom:31.1-jre")
        assert name == "guava"
        assert version == "31.1-jre"
        assert url.endswith("guava-31.1-jre.pom")

    def test_five_part_coordinate(self):
        name, version, url = get_maven_download_url("org.lwjgl:lwjgl:jar:3.3.3:natives-windows")
        assert name == "lwjgl"
        assert version == "3.3.3"
        assert "lwjgl-3.3.3-natives-windows.jar" in url

    def test_artifact_type_override(self):
        name, version, url = get_maven_download_url(
            "com.google.guava:guava:31.1-jre", artifact_type="jar"
        )
        assert url.endswith("guava-31.1-jre.jar")

    def test_parse_coordinate(self):
        coord = parse_maven_coordinate("com.google.guava:guava:31.1-jre")
        assert coord["group_id"] == "com.google.guava"
        assert coord["artifact_id"] == "guava"
        assert coord["version"] == "31.1-jre"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_maven_download_url("invalid:only")

    def test_android_package_google_maven(self):
        """Test that AndroidX packages are found on Google Maven."""
        name, version, url = get_maven_download_url("androidx.glance.wear:wear:1.0.0-alpha10")
        assert name == "wear"
        assert version == "1.0.0-alpha10"
        # AndroidX packages are on Google Maven, not Maven Central
        assert "dl.google.com/android/maven2" in url


class TestCrates:
    """Tests for Crates.io registry."""

    def test_regular_crate(self):
        name, version, url = get_crates_download_url("serde/1.0.188")
        assert name == "serde"
        assert version == "1.0.188"
        assert url == "https://static.crates.io/crates/serde/serde-1.0.188.crate"

    def test_hyphenated_crate(self):
        name, version, url = get_crates_download_url("windows-targets/0.52.6")
        assert name == "windows-targets"
        assert version == "0.52.6"
        assert url == "https://static.crates.io/crates/windows-targets/windows-targets-0.52.6.crate"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_crates_download_url("invalid")


class TestNuGet:
    """Tests for NuGet registry."""

    def test_regular_package(self):
        name, version, url = get_nuget_download_url("Newtonsoft.Json/13.0.3")
        assert name == "Newtonsoft.Json"
        assert version == "13.0.3"
        assert "newtonsoft.json" in url.lower()
        assert url.endswith(".nupkg")

    def test_case_insensitivity(self):
        _, _, url = get_nuget_download_url("Newtonsoft.Json/13.0.3")
        assert "newtonsoft.json" in url  # URL should be lowercase

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_nuget_download_url("invalid")


class TestRubyGems:
    """Tests for RubyGems registry."""

    def test_regular_gem(self):
        name, version, url = get_rubygems_download_url("rails/7.1.2")
        assert name == "rails"
        assert version == "7.1.2"
        assert url == "https://rubygems.org/downloads/rails-7.1.2.gem"

    def test_platform_specific_gem(self):
        name, version, url = get_rubygems_download_url("nokogiri/1.15.4-x86_64-linux")
        assert name == "nokogiri"
        assert version == "1.15.4-x86_64-linux"
        assert url == "https://rubygems.org/downloads/nokogiri-1.15.4-x86_64-linux.gem"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_rubygems_download_url("invalid")


class TestGoModules:
    """Tests for Go Modules registry."""

    def test_github_module(self):
        name, version, url = get_go_module_download_url("github.com/gin-gonic/gin/v1.9.1")
        assert name == "github.com/gin-gonic/gin"
        assert version == "v1.9.1"
        assert url == "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.zip"

    def test_golang_x_module(self):
        name, version, url = get_go_module_download_url("golang.org/x/text/v0.14.0")
        assert name == "golang.org/x/text"
        assert version == "v0.14.0"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_go_module_download_url("github.com/user/repo")  # No version


class TestHex:
    """Tests for Hex.pm registry."""

    def test_public_package(self):
        name, version, url = get_hex_download_url("phoenix/1.7.10")
        assert name == "phoenix"
        assert version == "1.7.10"
        assert url == "https://repo.hex.pm/tarballs/phoenix-1.7.10.tar"

    def test_org_package(self):
        name, version, url = get_hex_download_url("@myorg/private_lib/2.0.0")
        assert name == "private_lib"
        assert version == "2.0.0"
        assert url == "https://repo.hex.pm/repos/myorg/tarballs/private_lib-2.0.0.tar"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_hex_download_url("invalid")


class TestUnifiedAPI:
    """Tests for the unified get_download_url API."""

    def test_npm(self):
        name, version, url = get_download_url("npm", "lodash/4.17.21")
        assert name == "lodash"
        assert "registry.npmjs.org" in url

    def test_registry_alias(self):
        # "npmjs" should work as alias for "npm"
        name, version, url = get_download_url("npmjs", "lodash/4.17.21")
        assert name == "lodash"

    def test_case_insensitivity(self):
        name, version, url = get_download_url("NPM", "lodash/4.17.21")
        assert name == "lodash"

    def test_unsupported_registry(self):
        with pytest.raises(ValueError) as exc_info:
            get_download_url("unsupported", "package/1.0.0")
        assert "Unsupported registry" in str(exc_info.value)

    def test_all_supported_registries_listed(self):
        expected = {
            "npm", "dart", "pypi", "maven", "crates",
            "nuget", "rubygems", "go", "packagist", "cocoapods", "hex"
        }
        assert set(SUPPORTED_REGISTRIES) == expected
