"""Shared URL existence check with an offline verified-URL cache.

Every registry verifies that the artifact it points at actually exists. That check
is the same HEAD request in all of them, so it lives here once.

Verified URLs are appended to a cache file so a repeat lookup of the same
coordinate needs no network. The cache is append-only text (``<epoch>\\t<url>``),
which makes it safe under concurrent writers: a torn last line is ignored rather
than trusted, and re-running a conversion never corrupts prior state.
"""

import os
import time
from typing import Callable, Optional, Set

import requests

# Where verified URLs are remembered. Override with ID2URL_CACHE.
DEFAULT_CACHE_PATH = os.path.expanduser("~/.cache/id2url/verified.txt")

# How long a cached verification stays trustworthy, in seconds (30 days).
DEFAULT_TTL = 30 * 24 * 3600

# User-Agent some registries (crates.io) insist on.
USER_AGENT = "id2url/1.0"

# Verified URLs per cache file, keyed by path so a changed ID2URL_CACHE is
# never served from the previous file's set.
_verified_cache: dict = {}


def _cache_path() -> str:
    return os.environ.get("ID2URL_CACHE", DEFAULT_CACHE_PATH)


def _load_verified(path: str, ttl: int) -> Set[str]:
    """Read verified URLs whose timestamp is still inside ``ttl``.

    Malformed or torn lines are skipped, never fatal.
    """
    verified: Set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stamp, _, url = line.strip().partition("\t")
                if not url:
                    continue
                try:
                    age = time.time() - float(stamp)
                except ValueError:
                    continue
                if 0 <= age <= ttl:
                    verified.add(url)
    except OSError:
        pass
    return verified


def _remember(path: str, url: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{time.time():.3f}\t{url}\n")
    except OSError:
        pass  # a read-only cache dir must not break resolution


def check_url_exists(
    url: str,
    timeout: int = 10,
    cache_ttl: int = DEFAULT_TTL,
    session_request: Optional[Callable] = None,
) -> bool:
    """Return True if ``url`` exists, using the cache when it can.

    Args:
        url: Artifact URL to probe.
        timeout: HTTP timeout in seconds.
        cache_ttl: Trust window in seconds. 0 bypasses the cache entirely.
        session_request: override for the HTTP call, for tests.

    A network error counts as "not verified" rather than raising, matching what
    every registry caller already expects.
    """
    if cache_ttl <= 0:
        return _probe(url, timeout, session_request)

    path = _cache_path()
    verified = _verified_cache.get(path)
    if verified is None:
        verified = _verified_cache[path] = _load_verified(path, cache_ttl)

    if url in verified:
        return True

    if _probe(url, timeout, session_request):
        verified.add(url)
        _remember(path, url)
        return True
    return False


def _probe(url: str, timeout: int, session_request: Optional[Callable] = None) -> bool:
    request = session_request or requests.request
    try:
        response = request(
            "HEAD",
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False
