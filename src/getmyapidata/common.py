import argparse
import configparser
import logging
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

import win32api

DUMMY: str = "<YourNameHere>"


def ensure_path_exists(filename: str, log: logging.Logger) -> bool:
    log.debug(f"Checking path '{filename}' exists.")
    directory_name: str = os.path.dirname(filename)
    log.debug(f"Checking directory '{directory_name}' exists.")
    directory_path = Path(directory_name)

    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        log.debug(f"Directory '{directory_name}' created.")
    except OSError as e:
        log.error(f"Error ensuring directory '{directory_name} because: {e}")
        print(f"Error ensuring directory '{directory_name}': {e}")

    return os.path.exists(directory_name)


def get_args(local_args: Callable) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="read config from this file",
        default=get_default_ini_path(),
    )
    local_args(parser)
    args: argparse.Namespace = parser.parse_args()
    return args


def get_base_path() -> str:
    base_path: str

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return base_path


def get_config(
    args: argparse.Namespace, log: logging.Logger
) -> configparser.ConfigParser:
    config_file: str = get_default_ini_path()
    log.info(f"Reading config from {config_file}.")

    if not os.path.isfile(config_file):
        log.info(f"Config file {config_file} not found.")
        make_config(config_file, log)

    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    config.read(config_file)
    return config


def get_default_ini_path() -> str:
    return str(os.path.join(os.getcwd(), "config.ini"))


def get_exe_path() -> str:
    exe_path: str

    if getattr(sys, "frozen", False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(__file__)

    return exe_path


def get_exe_version(log: logging.Logger) -> str:
    exe_path: str = get_exe_path()
    log.info("Found exe path: {exe_path}.")

    try:
        # Get the full path to the executable.
        log.info(f"Getting abspath from {exe_path}.")
        full_path = os.path.abspath(exe_path)

        # Get the file version information.
        log.info(f"Requesting version info from {full_path}.")
        info = win32api.GetFileVersionInfo(full_path, "\\")
        log.info(f"Version info: {info}.")

        # Extract the major, minor, build, and private parts of the version.
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]

        version = "%d.%d.%d.%d" % (
            win32api.HIWORD(ms),
            win32api.LOWORD(ms),
            win32api.HIWORD(ls),
            win32api.LOWORD(ls),
        )
        return version
    except Exception as e:
        ver_from_file: str = parse_version_file()

        if ver_from_file:
            return ver_from_file

        print(f"Error getting version for {exe_path}: {e}")
        return ""


def make_config(config_file: str, log: logging.Logger) -> None:
    cwd: str = os.getcwd()
    config: configparser.ConfigParser = configparser.ConfigParser()
    config["AoU"] = {
        "awardee": DUMMY,
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": cwd,
    }
    config["Logon"] = {
        "aou_service_account": r"awardee-"
        + DUMMY
        + r"@all-of-us-ops-data-api-prod.iam.gservice"
        r"account.com",
        "pmi_account": DUMMY + "@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(cwd, "key.json"),
    }
    config["Logs"] = {"log_directory": cwd}

    with open(config_file, "w") as configfile:
        log.info(f"Writing config to file {config_file}.")
        config.write(configfile)


def parse_version_file() -> str:
    file_path: str = resource_path("version_info.txt")

    with open(file_path, "r", encoding="utf-8") as version_file:
        file_content = version_file.read()
        pattern: str = "ProductVersion',\s'(?P<version>\d+\.\d+)"
        match = re.search(pattern, file_content)

        if match:
            return match.group("version")

        return ""


# https://stackoverflow.com/a/13790741/20241849
def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle.
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment.
        base_path = os.getcwd()
    return str(os.path.join(base_path, relative_path))


def update_config(config: configparser.ConfigParser) -> None:
    with open(get_default_ini_path(), "w") as configfile:
        config.write(configfile)
