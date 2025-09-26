"""
Collection of static utility methods.
"""
import logging
import os
import re
import sys
from pathlib import Path

import pywintypes
import win32api


def ensure_path_possible(filename: str, log: logging.Logger) -> bool:
    """
    Tests to ensure the filename provided can actually be created.

    Parameters
    ----------
    filename: str           File we propose to create
    log: logging.Logger     To assist in debugging

    Returns
    -------
    bool
    """
    log.debug(f"Checking path '{filename}' exists.")
    directory_name: str = os.path.dirname(filename)
    log.debug(f"Checking directory '{directory_name}' exists.")
    directory_path = Path(directory_name)

    # Does this directory already exist?
    if os.path.exists(directory_path):
        return True

    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Directory '{directory_name}' created.")

        # OK, we CAN create it, so now delete it.
        # (Helps when we're calling this method with every new
        os.rmdir(directory_name)
        return True
    except OSError as e:
        log.error(f"Error ensuring directory '{directory_name} because: {e}")
        print(f"Error ensuring directory '{directory_name}': {e}")
        return False


def get_base_path() -> str:
    """
    Adapts to running either in development OR in executable format.

    Returns
    -------
    base_path: str      Where to find included data or image files.
    """
    base_path: str

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # pylint: disable=W0212
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return base_path


def get_exe_path() -> str:
    """
    Where to look for the .exe file information

    Returns
    -------
    exe_path: str
    """
    exe_path: str

    if getattr(sys, "frozen", False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(__file__)

    return exe_path


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
    exe_path: str = get_exe_path()
    log.debug("Found exe path: {exe_path}.")

    try:
        # Get the full path to the executable.
        log.debug(f"Getting abspath from {exe_path}.")
        full_path = os.path.abspath(exe_path)

        # Get the file version information.
        log.debug(f"Requesting version info from {full_path}.")
        info = win32api.GetFileVersionInfo(full_path, "\\")
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
    except pywintypes.error as e:  # pylint: disable=no-member
        ver_from_file: str = parse_version_file()

        if ver_from_file:
            return ver_from_file

        print(f"Error getting version for {exe_path}: {e}")
        return ""


def parse_version_file() -> str:
    """
    Parse the version file to extract the ProductVersion string.

    Returns
    -------
    version: str
    """
    file_path: str = resource_path("version_info.txt")

    with open(file_path, "r", encoding="utf-8") as version_file:
        file_content = version_file.read()
        pattern: str = r"ProductVersion',\s'(?P<version>\d+\.\d+\.\d+)"
        match = re.search(pattern, file_content)

        if match:
            return match.group("version")

        return ""


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
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle.
        base_path = sys._MEIPASS  # pylint: disable=W0212
    else:
        # Running in a normal Python environment.
        base_path = os.getcwd()
    return str(os.path.join(base_path, relative_path))
