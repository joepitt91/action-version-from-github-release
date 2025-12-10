# SPDX-FileCopyrightText: 2025 Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

"""Shared supporting functions."""

from typing import Dict

from semver import Version


def clean_version(version: str) -> str:
    """Tidy up a version number for parsing."""

    return (
        version.replace("v", "")
        .replace("V", "")
        .replace(".01", ".1")
        .replace(".02", ".2")
        .replace(".03", ".3")
        .replace(".04", ".4")
        .replace(".05", ".5")
        .replace(".06", ".6")
        .replace(".07", ".7")
        .replace(".08", ".8")
        .replace(".09", ".9")
    )


def find_latest(semantic_versions: Dict[str, Version]) -> str:
    """Find the latest version in the provided list of versions.

    Args:
        semantic_versions (Dict[str, Version]): The available versions.

    Raises:
        ValueError: If no sematic version is found.

    Returns:
        str: The identifier associated with the latest version.
    """

    semantic_versions = dict(
        sorted(semantic_versions.items(), key=lambda item: item[1], reverse=True)
    )
    if len(semantic_versions) > 0:
        return list(semantic_versions.keys())[0]
    raise ValueError("No semantic versions found")
