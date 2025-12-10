# SPDX-FileCopyrightText: 2025 Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

"""Get latest version information from GitHub packages and repositories."""

from typing import Any, Dict, List, Literal, Optional

from semver import Version
from requests import get

from . import __version__
from .functions import clean_version, find_latest


def get_latest_version_from_package(  # pylint: disable=too-many-arguments
    token: str,
    owner: str,
    package_name: str,
    package_type: Literal[
        "npm", "maven", "rubygems", "docker", "nuget", "container"
    ] = "container",
    *,
    greater_equal_version: Optional[Version] = None,
    less_than_version: Optional[Version] = None,
) -> str:
    """Get the latest version from a GitHub package.

    Args:
        token (str): The token to authenticate to GitHub with.
        owner (str): The owner of the package.
        package_name (str): The name of the package to query.
        package_type (Literal[npm, maven, rubygems, docker, nuget, container ], optional):
            The type of package to query. Defaults to "container".
        greater_equal_version (Version, optional): The minimum version to accept. Defaults to None.
        less_than_version (Version, optional): The version to accept versions less than.
            Defaults to None.

    Raises:
        HTTPError: If communication with GitHub fails.
        ValueError: If no semantic versions could be found.

    Returns:
        str: The latest version of the package.
    """

    semantic_versions: Dict[str, Version] = {}

    page = 1
    while True:  # pylint: disable=too-many-nested-blocks
        response = get(
            f"https://api.github.com/users/{owner}/packages/{package_type}/{package_name}/versions"
            f"?per_page=100&page={page}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": f"Python get_latest_version/v{__version__}",
            },
            timeout=30,
        )
        response.raise_for_status()
        versions: List[Dict[str, Any]] = response.json()

        if len(versions) == 0:
            break
        page = page + 1

        for version in versions:
            if package_type == "container":
                for tag in version["metadata"]["container"]["tags"]:
                    try:
                        semantic_version = Version.parse(clean_version(tag))
                        if (
                            greater_equal_version is None
                            or semantic_version >= greater_equal_version
                        ) and (
                            less_than_version is None
                            or semantic_version < less_than_version
                        ):
                            semantic_versions[tag] = semantic_version
                    except (TypeError, ValueError):
                        continue
            else:
                try:
                    semantic_version = Version.parse(clean_version(version["name"]))
                    if (
                        greater_equal_version is None
                        or semantic_version >= greater_equal_version
                    ) and (
                        less_than_version is None
                        or semantic_version < less_than_version
                    ):
                        semantic_versions[version["name"]] = semantic_version
                except (TypeError, ValueError):
                    continue
    return find_latest(semantic_versions)


def get_latest_version_from_releases(
    token: str,
    owner: str,
    repository: str,
    *,
    greater_equal_version: Optional[Version] = None,
    less_than_version: Optional[Version] = None,
) -> str:
    """Get the latest version from the releases in a GitHub repository.

    Args:
        token (str): The token to authenticate to GitHub API with.
        owner (str): The owner of the source repository.
        repository (str): The name of the source repository.
        greater_equal_version (Version, optional): The minimum version to accept. Defaults to None.
        less_than_version (Version, optional): The version to accept versions less than.
            Defaults to None.

    Raises:
        HTTPError: if communication with GitHub fails.
        ValueError: If no semantic versions can be found.

    Returns:
        str: The name of the release of the latest version.
    """

    semantic_versions: Dict[str, Version] = {}

    page = 1
    while True:
        response = get(
            f"https://api.github.com/repos/{owner}/{repository}/releases?per_page=100&page={page}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": f"Python get_latest_version/v{__version__}",
            },
            timeout=30,
        )
        response.raise_for_status()
        releases: List[Dict[str, Any]] = response.json()

        if len(releases) == 0:
            break
        page = page + 1

        for release in releases:
            if release["draft"]:
                continue
            try:
                semantic_version = Version.parse(clean_version(release["name"]))
            except (TypeError, ValueError):
                try:
                    semantic_version = Version.parse(clean_version(release["tag_name"]))
                except (TypeError, ValueError):
                    continue
            if (
                greater_equal_version is None
                or semantic_version >= greater_equal_version
            ) and (less_than_version is None or semantic_version < less_than_version):
                semantic_versions[release["tag_name"]] = semantic_version

    return find_latest(semantic_versions)


def get_latest_version_from_tags(
    token: str,
    owner: str,
    repository: str,
    *,
    greater_equal_version: Optional[Version] = None,
    less_than_version: Optional[Version] = None,
) -> str:
    """Get the latest version from the tags in a GitHub repository.

    Args:
        token (str): The token to authenticate to GitHub API with.
        owner (str): The owner of the source repository.
        repository (str): The name of the source repository.
        greater_equal_version (Version, optional): The minimum version to accept. Defaults to None.
        less_than_version (Version, optional): The version to accept versions less than.
            Defaults to None.

    Raises:
        HTTPError: if communication with GitHub fails.
        ValueError: If no semantic versions can be found.

    Returns:
        str: The tag of the latest version.
    """

    semantic_versions: Dict[str, Version] = {}

    page = 1
    while True:
        response = get(
            f"https://api.github.com/repos/{owner}/{repository}/tags?per_page=100&page={page}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": f"Python get_latest_version/v{__version__}",
            },
            timeout=30,
        )
        response.raise_for_status()
        tags: List[Dict[str, Any]] = response.json()

        if len(tags) == 0:
            break
        page = page + 1

        for tag in tags:
            try:
                semantic_version = Version.parse(clean_version(tag["name"]))
                if (
                    greater_equal_version is None
                    or semantic_version >= greater_equal_version
                ) and (
                    less_than_version is None
                    or semantic_version < less_than_version
                ):
                    semantic_versions[tag["name"]] = semantic_version
            except (TypeError, ValueError):
                pass

    return find_latest(semantic_versions)
