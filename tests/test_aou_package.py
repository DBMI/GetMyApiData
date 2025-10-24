"""
Tests methods related to class AouPackage
"""
import logging
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Union

from src.getmyapidata.aou_package import (AouPackage, get_config,
                                          get_default_ini_path)


def remove_config_file(config_file: Union[str, Path, None] = None) -> None:
    # Remove any leftover config file.
    if not config_file:
        config_file: str = get_default_ini_path()

    if os.path.exists(str(config_file)):
        os.remove(config_file)


def test_aou_package_no_config(logger: logging.Logger) -> None:
    # Remove any leftover config file.
    remove_config_file()

    config_file: str = get_default_ini_path()

    if os.path.exists(config_file):
        os.remove(config_file)

    aou_package: AouPackage = AouPackage(logger)
    assert isinstance(aou_package, AouPackage)
    assert (
        aou_package.aou_service_account
        == "awardee-<YourNameHere>@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )
    assert aou_package.data_directory == os.getcwd()
    assert not aou_package.inputs_complete()


def test_aou_package_with_config(
    logger: logging.Logger, fake_config_file: Path
) -> None:
    aou_package: AouPackage = AouPackage(logger, config_file=str(fake_config_file))
    assert isinstance(aou_package, AouPackage)
    assert aou_package.inputs_complete()


def test_bad_inputs(
    logger: logging.Logger,
    fake_config_file_blank_input: Path,
    fake_config_file_null_input: Path,
) -> None:
    aou_package: AouPackage = AouPackage(
        logger, config_file=str(fake_config_file_blank_input)
    )
    assert isinstance(aou_package, AouPackage)
    assert not aou_package.inputs_complete()

    aou_package = AouPackage(logger, config_file=str(fake_config_file_null_input))
    assert isinstance(aou_package, AouPackage)
    assert not aou_package.inputs_complete()


# Test reading mocked-up file using get_config().
def test_get_config(logger: logging.Logger, fake_config_file: Path) -> None:
    cp: ConfigParser = get_config(logger, str(fake_config_file))
    assert isinstance(cp, ConfigParser)
    assert isinstance(cp["AoU"]["Awardee"], str)
    assert cp["AoU"]["awardee"] == "dummy_awardee"
    assert isinstance(cp["AoU"]["endpoint"], str)
    assert cp["AoU"]["endpoint"] == r"https://test.com"
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
def test_make_config(logger: logging.Logger, fake_dummy_value: str) -> None:
    # Remove any leftover config file.
    remove_config_file()

    cp: ConfigParser = get_config(logger)
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


def test_no_config(logger: logging.Logger, nonexistent_config_file: Path) -> None:
    remove_config_file(nonexistent_config_file)

    cp: ConfigParser = get_config(logger, str(nonexistent_config_file))
    assert isinstance(cp, ConfigParser)
    assert os.path.exists(nonexistent_config_file)


def test_restore(logger: logging.Logger, fake_config_file: Path) -> None:
    aou_package: AouPackage = AouPackage(logger, config_file=str(fake_config_file))
    assert isinstance(aou_package, AouPackage)
    assert aou_package.inputs_complete()

    # AoU service account
    assert (
        aou_package.aou_service_account
        == "awardee-not_real@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )
    aou_package.aou_service_account = "not_really"
    assert aou_package.aou_service_account == "not_really"
    aou_package.restore_aou_service_account()
    assert (
        aou_package.aou_service_account
        == "awardee-not_real@all-of-us-ops-data-api-prod.iam.gserviceaccount.com"
    )

    # Awardee
    assert aou_package.awardee == "dummy_awardee"
    aou_package.awardee = "not_really"
    assert aou_package.awardee == "not_really"
    aou_package.restore_awardee()
    assert aou_package.awardee == "dummy_awardee"

    # Endpoint
    assert aou_package.endpoint == r"https://test.com"
    aou_package.endpoint = "not_really"
    assert aou_package.endpoint == "not_really"
    aou_package.restore_endpoint()
    assert aou_package.endpoint == r"https://test.com"

    # PMI account
    assert aou_package.pmi_account == "nobody@pmi-ops.org"
    aou_package.pmi_account = "not_really"
    assert aou_package.pmi_account == "not_really"
    aou_package.restore_pmi_account()
    assert aou_package.pmi_account == "nobody@pmi-ops.org"

    # Project
    assert aou_package.project == "all-of-us-ops-data-api-prod"
    aou_package.project = "not_really"
    assert aou_package.project == "not_really"
    aou_package.restore_project()
    assert aou_package.project == "all-of-us-ops-data-api-prod"

    # Token file
    token_file: str = aou_package.token_file
    aou_package.token_file = "not_really"
    assert aou_package.token_file == "not_really"
    aou_package.restore_token_file()
    assert aou_package.token_file == token_file

    aou_package.update_config()
