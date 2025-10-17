import logging
import logging.handlers
import os
import sys
from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path

import pandas
import pytest

from src.getmyapidata.aou_package import DUMMY, AouPackage

ApiRequestPackage = namedtuple("ApiRequestPackage", ["aou_package", "token"])


@pytest.fixture(name="real_aou_package")
def aou_package(fake_logger) -> AouPackage:
    # Copy a real config file.
    config_file_real: str = os.path.join(os.path.dirname(__file__), "config_real.ini")

    if not os.path.exists(config_file_real):
        pytest.fail(f"Missing real config file '{config_file_real}'")

    ap: AouPackage = AouPackage(log=fake_logger, config_file=config_file_real)
    return ap


@pytest.fixture(name="fake_dummy_value")
def dummy_value() -> str:
    return DUMMY


@pytest.fixture(name="fake_aou_package")
def fake_aou_package(fake_logger: logging.Logger, fake_config_file: Path) -> AouPackage:
    aou_package: AouPackage = AouPackage(fake_logger, config_file=str(fake_config_file))
    return aou_package


@pytest.fixture(name="fake_api_request_package")
def fake_api_request_package(
    fake_aou_package: AouPackage, fake_token: str
) -> ApiRequestPackage:
    api_package = ApiRequestPackage(fake_aou_package, fake_token)
    return api_package


@pytest.fixture(scope="function")
def fake_config_file(tmp_path) -> Path:
    """
    Create temporary config file for testing.
    """
    config_file = tmp_path / "config.ini"

    path_not_real: str = r"C:\tmp\not_there"
    config: ConfigParser = ConfigParser()
    config["AoU"] = {
        "awardee": "dummy_awardee",
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": path_not_real,
    }
    config["Logon"] = {
        "aou_service_account": "awardee-not_real@all-of-us-ops-data-api-prod.iam.gserviceaccount.com",
        "pmi_account": "nobody@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(path_not_real, "key.json"),
    }
    config["Logs"] = {"log_directory": os.path.join(path_not_real, "logs")}

    with open(config_file, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    return config_file


@pytest.fixture(scope="function")
def fake_config_file_blank_input(tmp_path) -> Path:
    """
    Create temporary config file for testing.
    """
    config_file = tmp_path / "config.ini"

    path_not_real: str = r"C:\tmp\not_there"
    config: ConfigParser = ConfigParser()
    config["AoU"] = {
        "awardee": "dummy_awardee",
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": path_not_real,
    }
    # Leave aou_service_account blank with \tab.
    config["Logon"] = {
        "aou_service_account": "    ",
        "pmi_account": "nobody@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(path_not_real, "key.json"),
    }
    config["Logs"] = {"log_directory": os.path.join(path_not_real, "logs")}

    with open(config_file, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    return config_file


@pytest.fixture(scope="function")
def fake_config_file_null_input(tmp_path) -> Path:
    """
    Create temporary config file for testing.
    """
    config_file = tmp_path / "config.ini"

    path_not_real: str = r"C:\tmp\not_there"
    config: ConfigParser = ConfigParser()
    config["AoU"] = {
        "awardee": "dummy_awardee",
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": path_not_real,
    }
    # Leave aou_service_account empty.
    config["Logon"] = {
        "aou_service_account": "",
        "pmi_account": "nobody@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(path_not_real, "key.json"),
    }
    config["Logs"] = {"log_directory": os.path.join(path_not_real, "logs")}

    with open(config_file, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    return config_file


@pytest.fixture(name="fake_token")
def fake_token() -> str:
    return "AODIUFGNAHERFUEWRUEIWIOTBWEOFINEWF"


@pytest.fixture(name="fake_logger")
def logger() -> logging.Logger:
    """
    Synthesizes a log object for testing.

    Returns
    -------
    log: logging.Logger
    """

    log_filename: str = os.path.join(os.path.dirname(__file__), "test.log")
    logger = logging.getLogger(log_filename)
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)

    logfile_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    return logger


@pytest.fixture(name="nonexistent_config_file")
def non_existent_config_file() -> Path:
    return Path("file_not_there.ini")


@pytest.fixture(name="fake_series")
def pandas_series() -> pandas.Series:
    date_list: list[str] = ["2025-12-25", "01-01-2026 08:00"]
    return pandas.Series(date_list)


@pytest.fixture(name="fake_patient_dataframe")
def patient_dataframe() -> pandas.DataFrame:
    test_csv_file: str = os.path.join(
        os.path.dirname(__file__), "TEST_participant_list.csv"
    )
    return pandas.read_csv(test_csv_file)


@pytest.fixture(name="fake_patient_status_dataframe")
def patient_status_dataframe() -> pandas.DataFrame:
    patient_status_1: str = "[{'status': 'NO', 'organization': 'CAL_PMC_UCSD'}]"
    patient_status_2: str = "[{'status': 'YES', 'organization': 'CAL_PMC_SDBB'}]"
    data_dict: dict = {"patientStatus": [patient_status_1, patient_status_2]}
    return pandas.DataFrame(data_dict)
