import logging
import logging.handlers
import os
import sys
from collections import namedtuple
from configparser import ConfigParser
from pathlib import Path

import pandas
import pytest
import wx.adv

from src.getmyapidata.aou_package import DUMMY, AouPackage
from src.getmyapidata.api_gui import ApiGui

ApiRequestPackage = namedtuple("ApiRequestPackage", ["aou_package", "token"])


@pytest.fixture(name="real_aou_package")
def aou_package(logger) -> AouPackage:
    # Copy a real config file.
    config_file_real: str = os.path.join(os.path.dirname(__file__), "config_real.ini")

    if not os.path.exists(config_file_real):
        pytest.fail(f"Missing real config file '{config_file_real}'")

    ap: AouPackage = AouPackage(log=logger, config_file=config_file_real)
    return ap


@pytest.fixture(name="fake_dummy_value")
def dummy_value() -> str:
    return DUMMY


@pytest.fixture(name="fake_aou_package")
def fake_aou_package(logger: logging.Logger, fake_config_file: Path) -> AouPackage:
    aou_package: AouPackage = AouPackage(logger, config_file=str(fake_config_file))
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
        "endpoint": r"https://test.com",
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


@pytest.fixture(name="fake_data_directory")
def fake_data_directory(tmp_path) -> str:
    return tmp_path / "test_data"


@pytest.fixture(name="fake_json")
def fake_json() -> dict:
    d: dict = {
        "resourceType": "Bundle",
        "total": 4,
        "entry": [
            {
                "resource": {
                    "organization": "FakeUniversity",
                    "patientName": "Ima Patient",
                    "city": "San Diego",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "organization": "FakeUniversity",
                    "patientName": "Youda Patient",
                    "city": "Silver City",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "organization": "",
                    "patientName": "Ahma Patient",
                    "city": "UNSET",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "organization": "",
                    "patientName": "Alma Patient",
                    "city": "Salmon City",
                    "state": "CA",
                }
            },
        ],
    }
    return d


# This pair (fake_json_I, fake_json_II) is
# intended to test handling a multi-page response.
@pytest.fixture(name="fake_json_I")
def fake_json_I() -> dict:
    d: dict = {
        "resourceType": "Bundle",
        "total": 2,
        "entry": [
            {
                "resource": {
                    "organization": "FakeUniversity",
                    "patientName": "Ima Patient",
                    "city": "San Diego",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "organization": "FakeUniversity",
                    "patientName": "Youda Patient",
                    "city": "Silver City",
                    "state": "CA",
                }
            },
        ],
    }
    return d


@pytest.fixture(name="fake_json_II")
def fake_json_II() -> dict:
    d: dict = {
        "resourceType": "Bundle",
        "total": 2,
        "entry": [
            {
                "resource": {
                    "organization": "",
                    "patientName": "Ahma Patient",
                    "city": "UNSET",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "organization": "",
                    "patientName": "Alma Patient",
                    "city": "Salmon City",
                    "state": "CA",
                }
            },
        ],
    }
    return d


@pytest.fixture(name="fake_json_no_total")
def fake_json_no_total() -> dict:
    d: dict = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "organization": "FakeUniversity",
                    "patientName": "Ima Patient",
                    "city": "San Diego",
                    "state": "CA",
                }
            },
            {
                "resource": {
                    "patientName": "Whooda Patient",
                    "city": "Silverado",
                    "state": "CA",
                }
            },
        ],
    }
    return d


@pytest.fixture(name="fake_token")
def fake_token() -> str:
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@pytest.fixture(name="hp_columns")
def hp_columns() -> list[str]:
    columns: list = [
        "Last Name",
        "First Name",
        "Middle Initial",
        "Date of Birth",
        "PMI ID",
        "Participant Status",
        "Core Participant Date",
        "Withdrawal Status",
        "Withdrawal Date",
        "Withdrawal Reason",
        "Deactivation Status",
        "Deactivation Date",
        "Deceased",
        "Date of Death",
        "Date of Death Approval",
        "Participant Origination",
        "Consent Cohort",
        "Date of First Primary Consent",
        "Primary Consent Status",
        "Primary Consent Date",
        "Program Update",
        "Date of Program Update",
        "EHR Consent Status",
        "EHR Consent Date",
        "gRoR Consent Status",
        "gRoR Consent Date",
        "Language of Primary Consent",
        "CABoR Consent Status",
        "CABoR Consent Date",
        "Retention Eligible",
        "Date of Retention Eligibility",
        "Retention Status",
        "EHR Data Transfer",
        "Most Recent EHR Receipt",
        "Patient Status: Yes",
        "Patient Status: No",
        "Patient Status: No Access",
        "Patient Status: Unknown",
        "Street Address",
        "Street Address2",
        "City",
        "State",
        "Zip",
        "Email",
        "Login Phone",
        "Phone",
        "Required PPI Surveys Complete",
        "Completed Surveys",
        "Paired Site",
        "Paired Organization",
        "Physical Measurements Status",
        "Physical Measurements Completion Date",
        "Samples to Isolate DNA",
        "Baseline Samples",
        "Sex",
        "Gender Identity",
        "Race/Ethnicity",
        "Education",
        "Core Participant Minus PM Date",
        "Enrollment Site",
    ]
    return columns


@pytest.fixture(name="logger")
def logger() -> logging.Logger:
    """
    Synthesizes a log object for testing.

    Returns
    -------
    log: logging.Logger
    """

    right_here: str = os.path.dirname(__file__)

    if not "tests" in right_here:
        right_here = os.path.join(right_here, "tests")

    log_filename: str = os.path.join(right_here, "testing.log")

    logger = logging.getLogger(log_filename)

    # Logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        "%(module)s - %(levelname)s - %(funcName)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Logging to a file
    logfile_format = logging.Formatter(
        fmt="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logfile_handler = logging.FileHandler(log_filename)
    logfile_handler.setFormatter(logfile_format)
    logger.addHandler(logfile_handler)

    logger.setLevel(logging.DEBUG)
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
