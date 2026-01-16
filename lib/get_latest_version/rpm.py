# SPDX-FileCopyrightText: 2023-2025 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

"""Get latest version information from RPM packages."""

from gzip import open as gzip_open
from io import BytesIO
from typing import Dict, List, Optional

from defusedxml import ElementTree
from requests import get, RequestException
from semver import Version

from . import __version__
from .functions import clean_version, find_latest


def get_latest_from_rpm_repo(
    mirror_list_url: str,
    package_name: str,
    *,
    package_arch: str = "x86_64",
    greater_equal_version: Optional[Version] = None,
    less_than_version: Optional[Version] = None,
) -> str:
    """Get the latest available version of an RPM from a dnf/yum repository.

    Args:
        mirror_list_url (str): The URL to download the mirror list from.
        package_name (str): The name of the package to check.
        package_arch (str, optional): The package architecture to check. Defaults to "x86_64".
        greater_equal_version (Version, optional): The minimum version to accept. Defaults to None.
        less_than_version (Version, optional): The version to accept versions less than.
            Defaults to None.

    Returns:
        str: The latest rpm available in the repository.
    """

    versions: Dict[str, Version] = {}
    mirror_urls: List[str] = (
        get(
            mirror_list_url,
            headers={"User-Agent": f"Python get_latest_version/v{__version__}"},
            timeout=30,
        )
        .content.decode("utf-8")
        .split("\n")
    )
    for mirror in mirror_urls:  # pylint: disable=too-many-nested-blocks
        try:
            for metadata in ElementTree.fromstring(
                get(
                    f"{mirror}repodata/repomd.xml",
                    headers={"User-Agent": f"Python get_latest_version/v{__version__}"},
                    timeout=30,
                ).content.decode("utf-8")
            ):
                if (
                    "type" not in metadata.attrib
                    or metadata.attrib["type"] != "primary"
                ):
                    continue
                for option in metadata:
                    if "href" not in option.attrib:
                        continue
                    for package_metadata in ElementTree.parse(
                        gzip_open(
                            BytesIO(
                                get(
                                    f"{mirror}{option.attrib['href']}",
                                    headers={
                                        "User-Agent": f"Python get_latest_version/v{__version__}"
                                    },
                                    timeout=30,
                                ).content
                            )
                        )
                    ).getroot():
                        if (
                            "type" not in package_metadata.attrib
                            or package_metadata.attrib["type"] != "rpm"
                            or package_metadata.findtext(
                                ".//ns0:name",
                                namespaces={
                                    "ns0": "http://linux.duke.edu/metadata/common"
                                },
                            )
                            != package_name
                            or package_metadata.findtext(
                                ".//ns0:arch",
                                namespaces={
                                    "ns0": "http://linux.duke.edu/metadata/common"
                                },
                            )
                            != package_arch
                        ):
                            continue
                        version_name = package_metadata.find(
                            ".//ns0:version",
                            namespaces={"ns0": "http://linux.duke.edu/metadata/common"},
                        ).get("ver")
                        version = clean_version(version_name).split(".")
                        version = Version(
                            int(version[0]), int(version[1]), int(version[2])
                        )
                        if (
                            greater_equal_version is None
                            or version >= greater_equal_version
                        ) and (
                            less_than_version is None or version < less_than_version
                        ):
                            versions[version_name] = version
            break
        except RequestException:
            pass

    return find_latest(versions)
