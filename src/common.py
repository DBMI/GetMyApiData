import argparse
import configparser
import os
import sys
from collections.abc import Callable
from typing import Union


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


def get_config(args: argparse.Namespace) -> tuple[str, configparser.ConfigParser]:
    config_file: str = get_default_ini_path()

    if not os.path.isfile(config_file):
        make_config(config_file)

    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    config.read(config_file)
    return config_file, config


def get_default_ini_path() -> str:
    return os.path.join(os.getcwd(), "config.ini")


def make_config(config_file: str) -> None:
    config = configparser.ConfigParser()
    config["AoU"] = {
        "awardee": "CAL_PMC",
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": r"C:\data",
    }
    config["Logon"] = {
        "aou_service_account": r"awardee-california@all-of-us-ops-data-api-prod.iam.gservice"
        r"account.com",
        "pmi_account": "my.name@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": r"C:\data\aou_submission\key.json",
    }
    config["Logs"] = {"log_directory": os.getcwd()}

    with open(config_file, "w") as configfile:
        config.write(configfile)


def update_config(config: configparser.ConfigParser) -> None:
    with open(get_default_ini_path(), "w") as configfile:
        config.write(configfile)
