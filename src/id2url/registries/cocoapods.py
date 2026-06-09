"""CocoaPods (iOS/macOS) package registry URL resolver."""

import hashlib
from typing import Optional, Tuple

import requests

COCOAPODS_CDN_URL = "https://cdn.cocoapods.org"


def get_cocoapods_download_url(
    origin_id: str, timeout: int = 30
) -> Tuple[str, str, str]:
    """
    Convert CocoaPods origin ID to download URL.

    Args:
        origin_id: Pod coordinate (e.g., "Alamofire/5.8.1")
        timeout: Request timeout in seconds

    Returns:
        Tuple of (pod_name, version, download_url)

    Raises:
        ValueError: If origin_id format is invalid or pod not found

    Note:
        CocoaPods specs point to source repositories (usually GitHub).
        This function fetches the podspec to get the actual source URL.

    Example:
        >>> get_cocoapods_download_url("Alamofire/5.8.1")
        ('Alamofire', '5.8.1', 'https://github.com/Alamofire/Alamofire/archive/5.8.1.tar.gz')
    """
    origin_id = origin_id.strip()
    parts = origin_id.split("/")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid origin_id format. Expected '<pod>/<version>', got: {origin_id}"
        )

    pod_name, version = parts[0], parts[1]

    # CocoaPods uses sharded directory structure based on pod name MD5 hash
    md5_hash = hashlib.md5(pod_name.encode()).hexdigest()
    shard_path = f"{md5_hash[0]}/{md5_hash[1]}/{md5_hash[2]}"

    spec_url = (
        f"{COCOAPODS_CDN_URL}/Specs/{shard_path}/{pod_name}/{version}/{pod_name}.podspec.json"
    )

    response = requests.get(spec_url, timeout=timeout)

    if response.status_code == 404:
        raise ValueError(f"Pod not found: {origin_id}")
    elif response.status_code != 200:
        raise Exception(f"CocoaPods CDN error: HTTP {response.status_code}")

    data = response.json()
    source = data.get("source", {})

    # Extract download URL from source specification
    download_url: Optional[str] = None

    if "http" in source:
        download_url = source["http"]
    elif "git" in source:
        git_url = source["git"]
        tag = source.get("tag", version)
        # Convert git URL to archive URL
        if "github.com" in git_url:
            repo_url = git_url.replace(".git", "").rstrip("/")
            download_url = f"{repo_url}/archive/{tag}.tar.gz"

    if not download_url:
        raise ValueError(f"Could not determine download URL for {origin_id}")

    return pod_name, version, download_url


def get_cocoapods_github_archive_url(owner: str, repo: str, version: str) -> str:
    """
    Construct direct GitHub archive URL for CocoaPods hosted on GitHub.

    Most popular CocoaPods are hosted on GitHub with matching repository names.

    Args:
        owner: GitHub username/org
        repo: Repository name
        version: Version tag

    Returns:
        Direct GitHub archive download URL
    """
    return f"https://github.com/{owner}/{repo}/archive/{version}.tar.gz"
