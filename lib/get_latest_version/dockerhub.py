# SPDX-FileCopyrightText: 2025 Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

"""Get latest version information from images on Docker Hub."""

from typing import Dict, Literal, Optional

from requests import get, post
from requests.auth import HTTPBasicAuth
from semver import Version

from . import __version__
from .functions import clean_version, find_latest


def _get_docker_token(
    username: str,
    token: str,
    namespace: str,
    repository: str,
    scope: Literal["hub", "registry"],
) -> str:
    """Get a Docker Hub token to pull manifests.

    Args:
        username (str): The account username.
        token (str): An account Personal Access Token to authenticate with.
        namespace (str): The namespace requiring access.
        repository (str): The repository requiring access.
        scope (Literal["hub", "registry"]): The Docker Hub system to get a token for.

    Raises:
        HTTPError: If the access token cannot be granted.
        ValueError: If an invalid scope is requested.

    Returns:
        str: The token to use to communicate with the scope.
    """

    if scope == "registry":
        response = get(
            f"https://auth.docker.io/token?service=registry.docker.io&"
            f"scope=repository:{namespace}/{repository}:pull",
            auth=HTTPBasicAuth(username, token),
            headers={
                "Accept": "application/json",
                "User-Agent": f"Python get_latest_version/v{__version__}",
            },
            timeout=30,
        )
    elif scope == "hub":
        response = post(
            "https://hub.docker.com/v2/auth/token",
            json={"identifier": username, "secret": token},
            timeout=30,
        )
    else:
        raise ValueError(f"Unknown scope {scope}")
    response.raise_for_status()
    return response.json()["access_token"]


def get_current_image_digest(  # pylint: disable=too-many-arguments
    username: str,
    token: str,
    repository: str,
    namespace: str = "library",
    tag: str = "latest",
    *,
    os: str = "linux",
    arch: str = "amd64",
) -> str:
    """Get the current digest of the given image tag on DockerHub.

    Args:
        username (str): The user to authenticate to the Docker Hub API as.
        token (str): The token to authenticate to the Docker Hub API with.
        repository (str): The repository to look in.
        namespace (str, optional): The namespace the repository is in. Defaults to "library".
        tag (str, optional): The tag to look for. Defaults to "latest".
        os (str, optional): The OS platform to look for. Defaults to "linux".
        arch (str, optional): The architecture platform to look for. Defaults to "amd64".

    Raises:
        HTTPError: If communication with DockerHub fails.
        ValueError: If the requested digest cannot be found.

    Returns:
        str: The digest of the current image matching the search.
    """

    access_token = _get_docker_token(username, token, namespace, repository, "registry")
    response = get(
        f"https://registry-1.docker.io/v2/{namespace}/{repository}/manifests/{tag}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": f"Python get_latest_version/v{__version__}",
        },
        timeout=30,
    )
    response.raise_for_status()

    for digest in response.json()["manifests"]:
        if (
            digest["platform"]["os"] == os
            and digest["platform"]["architecture"] == arch
        ):
            return digest["digest"]
    raise ValueError("No Matching manifest found")


def get_latest_image_version(  # pylint: disable=too-many-arguments
    username: str,
    token: str,
    repository: str,
    namespace: str = "library",
    *,
    greater_equal_version: Optional[Version] = None,
    less_than_version: Optional[Version] = None,
) -> str:
    """Get the latest semantic version number from a Docker Hub repository's tagged images.

    Args:
        username (str): The user to authenticate to the Docker Hub API as.
        token (str): The token to authenticate to the Docker Hub API with.
        repository (str): The repository to search tags for.
        namespace (str, optional): The namespace the repository is in. Defaults to "library".
        greater_equal_version (Version, optional): The minimum version to accept. Defaults to None.
        less_than_version (Version, optional): The version to accept versions less than.
            Defaults to None.

    Raises:
        HTTPError: If communication with Docker Hub fails.
        ValueError: If a semantic version cannot be determined.

    Returns:
        str: The image tag for the latest version.
    """

    access_token = _get_docker_token(username, token, namespace, repository, "hub")
    semantic_versions: Dict[str, Version] = {}
    next_url = (
        f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repository}/tags?"
        "page_size=100"
    )
    while True:
        response = get(
            next_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": f"Python get_latest_version/v{__version__}",
            },
            timeout=30,
        )
        response.raise_for_status()

        versions = response.json()
        for version in versions["results"]:
            try:
                semantic_version = Version.parse(clean_version(version["name"]))
                if (
                    semantic_version.prerelease is None
                    and (
                        greater_equal_version is None
                        or semantic_version >= greater_equal_version
                    )
                    and (
                        less_than_version is None
                        or semantic_version < less_than_version
                    )
                ):
                    semantic_versions[version["name"]] = semantic_version
            except (TypeError, ValueError):
                continue
        if versions["next"] is not None:
            next_url = versions["next"]
        else:
            break

    return find_latest(semantic_versions)
