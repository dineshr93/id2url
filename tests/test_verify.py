"""Tests for the shared existence check and the verify command."""

import contextlib

import requests

from id2url.cli import main
from id2url.registries import check_url_exists
from id2url.registries.crates import get_crates_download_url
from id2url.registries.npm import get_npm_download_url

REAL = "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"


@contextlib.contextmanager
def no_network():
    """Fail loudly if the code under test tries to reach the network."""
    def boom(*a, **kw):  # pragma: no cover - only reached on a test failure
        raise AssertionError("unexpected network call")

    original = requests.request
    requests.request = boom
    try:
        yield
    finally:
        requests.request = original


class TestCheckUrlExists:
    def test_real_url_is_reachable(self):
        assert check_url_exists(REAL) is True

    def test_dead_url_is_not_reachable(self):
        assert check_url_exists("https://registry.npmjs.org/lodash/-/lodash-9.9.9.tgz") is False

    def test_network_error_is_not_reachable(self):
        def boom(*a, **kw):
            raise requests.ConnectionError("down")

        fresh = str(REAL) + "?nocache"  # miss the cache, force the probe
        assert check_url_exists(fresh, session_request=boom) is False


class TestOfflineCache:
    """A url verified once must not need the network again."""

    def test_resolver_hit_is_offline(self):
        get_npm_download_url("lodash/4.17.21")  # warm the cache
        with no_network():
            name, version, url = get_npm_download_url("lodash/4.17.21")
        assert (name, version, url) == ("lodash", "4.17.21", REAL)

    def test_second_registry_hit_is_offline(self):
        get_crates_download_url("serde/1.0.188")
        with no_network():
            get_crates_download_url("serde/1.0.188")

    def test_cache_file_written(self, tmp_path, monkeypatch):
        cache = tmp_path / "verified.txt"
        monkeypatch.setenv("ID2URL_CACHE", str(cache))
        check_url_exists(REAL)
        assert REAL in cache.read_text()

    def test_corrupt_cache_line_ignored(self, tmp_path, monkeypatch):
        cache = tmp_path / "verified.txt"
        cache.write_text("not-a-timestamp\t" + REAL + "\n")
        monkeypatch.setenv("ID2URL_CACHE", str(cache))
        # Stale line is ignored, so the URL must be probed again (and passes).
        assert check_url_exists(REAL) is True

    def test_ttl_zero_forces_probe(self, tmp_path, monkeypatch):
        cache = tmp_path / "verified.txt"
        monkeypatch.setenv("ID2URL_CACHE", str(cache))
        check_url_exists(REAL)  # now cached

        calls = []

        def counting(method, url, **kw):
            calls.append(url)
            return requests.request(method, url, **kw)

        # cache_ttl=0 must ignore the cache and hit the network.
        assert check_url_exists(REAL, cache_ttl=0, session_request=counting) is True
        assert calls == [REAL]


class TestVerifyCommand:
    def test_verified_coordinate_exits_zero(self, runner, tmp_path, monkeypatch):
        monkeypatch.setenv("ID2URL_CACHE", str(tmp_path / "verified.txt"))
        result = runner.invoke(main, ["verify", "npm", "lodash/4.17.21"])
        assert result.exit_code == 0
        assert "verified:" in result.output

    def test_missing_coordinate_exits_one(self, runner, tmp_path, monkeypatch):
        monkeypatch.setenv("ID2URL_CACHE", str(tmp_path / "verified.txt"))
        result = runner.invoke(main, ["verify", "npm", "lodash/9.9.9"])
        assert result.exit_code == 1
        assert "not verified" in result.output

    def test_second_verify_is_offline(self, runner, tmp_path, monkeypatch):
        monkeypatch.setenv("ID2URL_CACHE", str(tmp_path / "verified.txt"))
        assert runner.invoke(main, ["verify", "crates", "serde/1.0.188"]).exit_code == 0
        with no_network():
            result = runner.invoke(main, ["verify", "crates", "serde/1.0.188"])
        assert result.exit_code == 0
