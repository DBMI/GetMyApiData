"""
Collection of static utility methods.
"""

import logging
import os
import re
import sys
from importlib import resources
from pathlib import Path

import pandas

if sys.platform == "win32":
    import pywintypes

    PyWinError = pywintypes.error
else:
    # Create a dummy exception class for Linux environments
    class PyWinError(Exception):
        pass


if sys.platform == "win32":
    import win32api
else:
    # Fallback or Mock object for Linux test environments
    win32api = None


def find_time_or_date_columns(df: pandas.DataFrame) -> list[str]:
    """
    Identify columns ending in "Authored" or "Time"

    Parameters
    ----------
    df: DataFrame

    Returns
    -------
    matching_cols: list[str]

    """
    # Find columns ending with "Authored" or "Time"
    authored_cols = df.columns[df.columns.str.contains(r"Authored$")].tolist()
    time_cols = df.columns[df.columns.str.contains(r"Time$")].tolist()
    return authored_cols + time_cols


def resolve_path(file_name: str) -> str:
    """
    Returns the Path to a config file.

    Parameters
    ----------
    file_name: str

    Returns
    -------
    config_path: Path
    """

    """Get the absolute path to a resource, compatible with PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, "config", file_name)

    # Standard development path
    config_file: str = str(resources.files("getmyapidata.config").joinpath(file_name))
    return config_file


def get_executable_path() -> Path:
    """Returns the directory where the .exe or the script is located."""
    if getattr(sys, "frozen", False):
        # Running as a compiled PyInstaller .exe
        # sys.executable is the path to the actual .exe file
        return Path(sys.executable).resolve()
    else:
        # Running as a standard python script during development
        return Path(__file__).resolve()


def get_exe_version(log: logging.Logger) -> str:
    """
    Get the version of the executable, either from the .exe OR the version.txt files.

    Parameters
    ----------
    log

    Returns
    -------
    version: str
    """
    exe_path: Path = get_executable_path()
    log.debug(f"Found exe path: {exe_path!s}.")

    try:  # pragma: no cover
        # Get the full path to the executable.
        log.debug(f"Getting abspath from {exe_path!s}.")

        # Get the file version information.
        info = win32api.GetFileVersionInfo(str(exe_path), "\\")
        log.debug(f"Version info: {info}.")

        # Extract the major, minor, build, and private parts of the version.
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]

        version = (
            f"{win32api.HIWORD(ms)}."
            f"{win32api.LOWORD(ms)}."
            f"{win32api.HIWORD(ls)}."
            f"{win32api.LOWORD(ls)}"
        )
        return version
    except PyWinError as e:  # pylint: disable=no-member
        ver_from_file: str = parse_version_file()

        if ver_from_file:
            return ver_from_file

        print(f"Error getting version for {exe_path!s}: {e}")  # pragma: no cover
        return ""  # pragma: no cover


def parse_version_file() -> str:
    """
    Parse the version file to extract the ProductVersion string.

    Returns
    -------
    version: str
    """
    file_path: str = resource_path("version_info.txt")

    with open(file_path, encoding="utf-8") as version_file:
        file_content = version_file.read()
        pattern: str = r"ProductVersion',\s'(?P<version>\d+\.\d+\.\d+)"
        match = re.search(pattern, file_content)

        if match:
            return match.group("version")

        return ""  # pragma: no cover


# https://stackoverflow.com/a/13790741/20241849
def resource_path(relative_path: str) -> str:
    """
    Given name of resource, builds absolute path to resource, works for dev and PyInstaller.

    Parameters
    ----------
    relative_path: str

    Returns
    -------
    base_path: str
    """
    if getattr(sys, "frozen", False):  # pragma: no cover
        # Running in a PyInstaller bundle.
        base_path = sys._MEIPASS  # pylint: disable=W0212
    else:
        # Running in a normal Python environment.
        base_path = os.getcwd()

    return str(os.path.join(base_path, relative_path))
