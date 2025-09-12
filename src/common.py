import argparse
import configparser
import os
import re
import sys
from collections.abc import Callable

import win32api
from win32api import GetFileVersionInfo


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

    if getattr(sys, "frozen", True) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return base_path


def get_config(args: argparse.Namespace) -> configparser.ConfigParser:
    config_file: str = get_default_ini_path()

    if not os.path.isfile(config_file):
        make_config(config_file)

    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    config.read(config_file)
    return config


def get_default_ini_path() -> str:
    return os.path.join(os.getcwd(), "src", "config.ini")


def get_exe_path() -> str:
    exe_path: str

    if getattr(sys, "frozen", True) and hasattr(sys, "_MEIPASS"):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(__file__)

    return exe_path


def get_exe_version() -> str:
    exe_path: str = get_exe_path()

    try:
        # Get the full path to the executable
        full_path = os.path.abspath(exe_path)

        # Get the file version information
        info = win32api.GetFileVersionInfo(full_path, "\\")

        # Extract the major, minor, build, and private parts of the version
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


def make_config(config_file: str) -> None:
    cwd: str = os.getcwd()
    config: configparser.ConfigParser = configparser.ConfigParser()
    config["AoU"] = {
        "awardee": "CAL_PMC",
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": cwd,
    }
    config["Logon"] = {
        "aou_service_account": r"awardee-california@all-of-us-ops-data-api-prod.iam.gservice"
        r"account.com",
        "pmi_account": "my.name@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(cwd, "key.json"),
    }
    config["Logs"] = {"log_directory": cwd}

    with open(config_file, "w") as configfile:
        config.write(configfile)


def parse_version_file() -> str:
    file_path: str = os.path.join(os.getcwd(), 'src', 'version_info.txt')

    with open(file_path, 'r', encoding="utf-8") as version_file:
        file_content = version_file.read()
        pattern: str = "ProductVersion',\s'(?P<version>\d+\.\d+)"
        match = re.search(pattern, file_content)

        if match:
            return match.group("version")

        return ""

def update_config(config: configparser.ConfigParser) -> None:
    with open(get_default_ini_path(), "w") as configfile:
        config.write(configfile)
