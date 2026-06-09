"""Maven package registry URL resolver with multi-repository support."""

from typing import Dict, List, Optional, Tuple

import requests

MAVEN_CENTRAL_BASE_URL = "https://repo1.maven.org/maven2"
GOOGLE_MAVEN_BASE_URL = "https://dl.google.com/android/maven2"

# Group ID prefixes that are typically hosted on Google's Maven repository
GOOGLE_MAVEN_PREFIXES = (
    "androidx.",
    "com.google.android.",
    "com.google.firebase.",
    "com.google.gms.",
    "com.google.mlkit.",
    "com.google.ar.",
    "com.google.ads.",
    "com.google.maps.",
    "com.android.",
    "android.arch.",
)


def _check_url_exists(url: str, timeout: int = 10) -> bool:
    """Check if a URL exists using HEAD request."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _get_repositories_for_group(group_id: str) -> List[Tuple[str, str]]:
    """
    Get ordered list of repositories to try for a given group ID.
    
    Google/Android packages try Google Maven first, others try Maven Central first.
    """
    if group_id.startswith(GOOGLE_MAVEN_PREFIXES):
        return [
            ("Google Maven", GOOGLE_MAVEN_BASE_URL),
            ("Maven Central", MAVEN_CENTRAL_BASE_URL),
        ]
    else:
        return [
            ("Maven Central", MAVEN_CENTRAL_BASE_URL),
            ("Google Maven", GOOGLE_MAVEN_BASE_URL),
        ]


def _build_maven_url(
    group_id: str,
    artifact_id: str,
    version: str,
    filename: str,
    repo_base_url: str,
) -> str:
    """Build a Maven download URL for a specific repository."""
    group_path = group_id.replace(".", "/")
    return f"{repo_base_url.rstrip('/')}/{group_path}/{artifact_id}/{version}/{filename}"


def parse_maven_coordinate(origin_id: str) -> Dict[str, Optional[str]]:
    """
    Parse Maven coordinate handling all formats:
    - 3 parts: groupId:artifactId:version
    - 4 parts: groupId:artifactId:packaging:version
    - 5 parts: groupId:artifactId:packaging:version:classifier

    Returns dict with: group_id, artifact_id, version, packaging, classifier
    """
    origin_id = origin_id.strip()
    parts = origin_id.split(":")

    if len(parts) < 3:
        raise ValueError(
            f"Invalid Maven coordinate. Expected at least 'groupId:artifactId:version', "
            f"got: {origin_id}"
        )

    result: Dict[str, Optional[str]] = {
        "group_id": parts[0],
        "artifact_id": parts[1],
        "packaging": "jar",  # default
        "version": None,
        "classifier": None,
    }

    if len(parts) == 3:
        # groupId:artifactId:version
        result["version"] = parts[2]
    elif len(parts) == 4:
        # groupId:artifactId:packaging:version
        result["packaging"] = parts[2]
        result["version"] = parts[3]
    elif len(parts) >= 5:
        # groupId:artifactId:packaging:version:classifier
        result["packaging"] = parts[2]
        result["version"] = parts[3]
        result["classifier"] = parts[4]

    return result


def get_maven_download_url(
    origin_id: str,
    artifact_type: Optional[str] = None,
    timeout: int = 10,
) -> Tuple[str, str, str]:
    """
    Convert Maven origin ID to download URL with automatic verification.
    
    Automatically checks multiple repositories (Maven Central, Google Maven)
    and returns the first valid URL. For Android/Google packages, checks
    Google Maven first.

    Handles multiple coordinate formats:
    - 3 parts: groupId:artifactId:version (default to sources jar)
    - 4 parts: groupId:artifactId:packaging:version
    - 5 parts: groupId:artifactId:packaging:version:classifier

    Args:
        origin_id: Maven coordinate (e.g., "com.google.guava:guava:31.1-jre")
        artifact_type: Override artifact type. Options:
                       - None (auto-detect from coordinate)
                       - "sources" -> {artifact}-{version}-sources.jar
                       - "jar" -> {artifact}-{version}.jar
                       - "pom" -> {artifact}-{version}.pom
        timeout: HTTP request timeout in seconds

    Returns:
        Tuple of (artifact_id, version, download_url)
    
    Raises:
        ValueError: If artifact not found in any repository

    Examples:
        >>> get_maven_download_url("com.google.guava:guava:31.1-jre")
        ('guava', '31.1-jre', 'https://repo1.maven.org/maven2/.../guava-31.1-jre-sources.jar')

        >>> get_maven_download_url("androidx.glance.wear:wear:1.0.0-alpha10")
        ('wear', '1.0.0-alpha10', 'https://dl.google.com/android/maven2/.../wear-1.0.0-alpha10-sources.jar')
    """
    coord = parse_maven_coordinate(origin_id)

    group_id = coord["group_id"]
    artifact_id = coord["artifact_id"]
    version = coord["version"]
    packaging = coord["packaging"]
    classifier = coord["classifier"]

    if not group_id or not artifact_id or not version:
        raise ValueError(f"Invalid Maven coordinate: {origin_id}")

    # Determine file extension from packaging
    extension_map = {
        "jar": "jar",
        "pom": "pom",
        "war": "war",
        "ear": "ear",
        "aar": "aar",  # Android
        "bundle": "jar",  # OSGi bundle
    }
    extension = extension_map.get(packaging or "jar", packaging or "jar")

    # Build filename
    if artifact_type:
        if artifact_type == "sources":
            filename = f"{artifact_id}-{version}-sources.jar"
        elif artifact_type == "javadoc":
            filename = f"{artifact_id}-{version}-javadoc.jar"
        elif artifact_type == "pom":
            filename = f"{artifact_id}-{version}.pom"
        elif artifact_type == "jar":
            filename = f"{artifact_id}-{version}.jar"
        else:
            filename = f"{artifact_id}-{version}.{artifact_type}"
    elif classifier:
        filename = f"{artifact_id}-{version}-{classifier}.{extension}"
    elif packaging == "pom":
        filename = f"{artifact_id}-{version}.pom"
    else:
        # Default to sources for compliance review
        filename = f"{artifact_id}-{version}-sources.jar"

    # Get repositories in priority order for this group
    repos = _get_repositories_for_group(group_id)
    checked_repos = []

    for repo_name, repo_url in repos:
        download_url = _build_maven_url(group_id, artifact_id, version, filename, repo_url)
        checked_repos.append((repo_name, download_url))

        if _check_url_exists(download_url, timeout):
            return artifact_id, version, download_url

    # Artifact not found in any repository
    repo_details = "\n".join(f"  - {name}: {url}" for name, url in checked_repos)
    raise ValueError(
        f"Artifact not found in any Maven repository for {origin_id}\n"
        f"Checked:\n{repo_details}"
    )
