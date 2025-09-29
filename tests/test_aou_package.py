"""
Tests methods related to class AouPackage
"""
import logging
import os
from configparser import ConfigParser
from pathlib import Path

from src.getmyapidata.aou_package import AouPackage, get_config


def test_aou_package(fake_logger) -> None:
    aou_package: AouPackage = AouPackage(fake_logger)
    assert isinstance(aou_package, AouPackage)
    assert (
        aou_package.aou_service_account
        == "awardee-<YourNameHere>@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )
    assert aou_package.data_directory == os.getcwd()


# Test reading test file using get_config().
def test_get_config(fake_logger: logging.Logger, fake_config_file: Path) -> None:
    cp: ConfigParser = get_config(fake_logger, str(fake_config_file))
    assert isinstance(cp, ConfigParser)
    assert isinstance(cp["AoU"]["Awardee"], str)
    assert cp["AoU"]["awardee"] == "dummy_awardee"
    assert isinstance(cp["AoU"]["endpoint"], str)
    assert cp["AoU"]["endpoint"] == r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite"
    assert isinstance(cp["InSite API"]["data_directory"], str)
    assert cp["InSite API"]["data_directory"] == r"C:\tmp\not_there"
    assert isinstance(cp["Logon"]["aou_service_account"], str)
    assert (
        cp["Logon"]["aou_service_account"]
        == "awardee-not_real@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )
    assert isinstance(cp["Logon"]["pmi_account"], str)
    assert cp["Logon"]["pmi_account"] == "nobody@pmi-ops.org"
    assert isinstance(cp["Logon"]["project"], str)
    assert cp["Logon"]["project"] == "all-of-us-ops-data-api-prod"
    assert isinstance(cp["Logon"]["token_file"], str)
    assert cp["Logon"]["token_file"] == r"C:\tmp\not_there\key.json"
    assert isinstance(cp["Logs"]["log_directory"], str)
    assert cp["Logs"]["log_directory"] == r"C:\tmp\not_there\logs"


# Test dummy values created in make_config().
def test_make_config(fake_logger: logging.Logger, fake_dummy_value: str) -> None:
    cp: ConfigParser = get_config(fake_logger)
    assert isinstance(cp, ConfigParser)
    assert isinstance(cp["AoU"]["Awardee"], str)
    assert cp["AoU"]["awardee"] == "<YourNameHere>"
    assert isinstance(cp["AoU"]["endpoint"], str)
    assert cp["AoU"]["endpoint"] == r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite"
    assert isinstance(cp["InSite API"]["data_directory"], str)
    assert isinstance(cp["Logon"]["aou_service_account"], str)
    assert (
        cp["Logon"]["aou_service_account"]
        == "awardee-<YourNameHere>@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )
    assert isinstance(cp["Logon"]["pmi_account"], str)
    assert cp["Logon"]["pmi_account"] == fake_dummy_value + "@pmi-ops.org"
    assert isinstance(cp["Logon"]["project"], str)
    assert cp["Logon"]["project"] == "all-of-us-ops-data-api-prod"
    assert isinstance(cp["Logon"]["token_file"], str)
    assert cp["Logon"]["token_file"] == os.path.join(os.getcwd(), "key.json")
    assert isinstance(cp["Logs"]["log_directory"], str)
    assert cp["Logs"]["log_directory"] == os.getcwd()
