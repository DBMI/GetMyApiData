import logging
import logging.handlers
import os
import shutil
import sys
from configparser import ConfigParser
from pathlib import Path

import pandas
import pytest

from src.getmyapidata.aou_package import DUMMY, AouPackage


@pytest.fixture(name="fake_aou_package")
def aou_package(fake_logger) -> AouPackage:
    # Copy a real config file.
    config_file_real: str = os.path.join(os.path.dirname(__file__), "config_real.ini")
    config_file_temp: str = os.path.join(os.path.dirname(__file__), "config.ini")
    shutil.copy(config_file_real, config_file_temp)
    ap: AouPackage = AouPackage(fake_logger)

    if os.path.exists(config_file_temp):
        os.remove(config_file_temp)

    return ap


@pytest.fixture(name="fake_dummy_value")
def dummy_value() -> str:
    return DUMMY


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


@pytest.fixture(name="fake_logger")
def logger() -> logging.Logger:
    """
    Synthesizes a log object for testing.

    Returns
    -------
    log: logging.Logger
    """
    log_filename: str = r"./tests/test.log"
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
