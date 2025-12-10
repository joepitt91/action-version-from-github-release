# SPDX-FileCopyrightText: 2025 Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

"""Get latest version information from PIP module on PyPI."""

from requests import get

from . import __version__


def get_current_module_version(module: str) -> str:
    """Get the current version of the specified PIP module.

    Args:
        package (str): The module to check.

    Raises:
        HTTPError: If communication with PyPI fails

    Returns:
        str: The current version of the module.
    """

    response = get(
        f"https://pypi.org/pypi/{module}/json",
        headers={
            "Accept": "application/json",
            "User-Agent": f"Python get_latest_version/v{__version__}",
        },
        timeout=30,
    )
    response.raise_for_status()

    return response.json()["info"]["version"]
