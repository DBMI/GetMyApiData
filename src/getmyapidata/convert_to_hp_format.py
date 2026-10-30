"""
Contains class HealthProConverter, which converts participant list into Health Pro format.
"""

import glob
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas
import yaml

from src.getmyapidata.common import (
    find_time_or_date_columns,
    get_config_path,
)
from src.getmyapidata.my_logging import setup_logging


# UTILITY CLASS
# Forces all data typing to strings
class StringConverter(dict):
    """
    Required for read_csv method.
    """

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return str

    def get(self, default=None):  # pylint: disable=unused-argument
        return str  # pragma: no cover


def convert_date(raw_date: pandas.Series) -> pandas.Series:
    """
    Convert date format.

    Parameters
    ----------
    raw_date: pandas.Series         One column

    Returns
    -------
    date_converted: pandas.Series
    """
    date_temp: pandas.Series = pandas.to_datetime(raw_date, errors="coerce")
    date_converted: pandas.Series = date_temp.dt.strftime("%Y-%m-%dT%H:%M:%S")
    return date_converted


def convert_patient_status(df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Converts patient status columns.

    Parameters
    ----------
    df: pandas.DataFrame

    Returns
    -------
    df: pandas.DataFrame
    """
    # Add new columns derived from patientStatus JSON strings.
    temp_ser: pandas.Series = df["patientStatus"].apply(lambda s: s.replace("'", '"'))
    df["patientStatusParsed"] = temp_ser.apply(json.loads)
    df["patientStatusWord"] = df["patientStatusParsed"].apply(
        lambda x: x[0]["status"] if x else None
    )
    df["patientStatusOrganization"] = df["patientStatusParsed"].apply(
        lambda x: x[0]["organization"] if x else None
    )

    # Empty columns for now.
    df["patientStatusYes"] = None
    df["patientStatusNo"] = None
    df["patientStatusNoAccess"] = None
    df["patientStatusUnknown"] = None

    # Insert the patientStatusOrganization where patientStatusWord is YES/NO/NO ACCESS/UNKNOWN.
    mask: bool = df["patientStatusWord"].values == "YES"
    df.loc[mask, "patientStatusYes"] = df.loc[mask, "patientStatusOrganization"]
    mask = df["patientStatusWord"].values == "NO"
    df.loc[mask, "patientStatusNo"] = df.loc[mask, "patientStatusOrganization"]
    mask = df["patientStatusWord"].values == "NO ACCESS"
    df.loc[mask, "patientStatusNoAccess"] = df.loc[mask, "patientStatusOrganization"]
    mask = df["patientStatusWord"].values == "UNKNOWN"
    df.loc[mask, "patientStatusUnknown"] = df.loc[mask, "patientStatusOrganization"]

    return df


def read_column_mappings(logger: logging.Logger) -> dict:
    """
    Find and read the .yaml file that defines the translation between
    InSite API column names and the names we'll export.

    Parameters
    ----------
    logger: logging.Logger object

    Returns
    -------
    columns: dict
    """
    mapping: dict = {}
    config_dir: Path = get_config_path()
    config_file: Path = config_dir / "column_mapping.yaml"

    try:
        with open(config_file) as file:
            mapping = yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"File not found at {config_file}.")

    try:
        return mapping["output_variables"]
    except KeyError:
        (logger.error(f"Unable to find 'output_variables' in {config_file}."))


def read_output_columns(logger: logging.Logger) -> list[str]:
    """
    Find and read the .yaml file that defines the additional columns we'll export.

    Parameters
    ----------
    logger: logging.Logger object

    Returns
    -------
    columns: list[str]
    """
    columns: dict
    config_dir: Path = get_config_path()
    config_file: Path = config_dir / "additional_output_columns.yaml"

    try:
        with open(config_file) as file:
            columns = yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"File not found at {config_file}.")

    try:
        return columns["additional_output_columns"]
    except KeyError:
        logger.error(f"Unable to find 'output_columns' in {config_file}.")


# pylint: disable=too-few-public-methods
class HealthProConverter:
    """
    Allows us to convert new InSite API format to the HealthPro format we're used to.
    """

    def __init__(
        self,
        log: logging.Logger,
        data_directory: str,
        status_fn: Callable[[str], None] | None = None,
    ) -> None:
        """Instantiate a HealthProConverter object

        Parameters
        ----------
        log: logging.Logger         log object
        data_directory: str         Where to store the data file
        status_fn: Callable         Method from calling object to report status.
        """
        self.__log: logging.Logger = log
        self.__directory: str = data_directory
        self.__status_fn: Callable = status_fn

    def convert(self) -> None:
        """Convert all .csv files in given directory that aren't already marked as "transformed"."""
        directory_plus_ext: str = os.path.join(self.__directory, "*.csv")

        for filename_and_ext in glob.glob(directory_plus_ext):
            if (
                os.path.isfile(filename_and_ext)
                and "transformed" not in filename_and_ext
            ):
                just_the_filename, ext = os.path.splitext(filename_and_ext)
                output_file: str = os.path.join(
                    self.__directory, just_the_filename + "_transformed" + ext
                )

                input_file: str = os.path.join(self.__directory, filename_and_ext)
                self.__convert_file(input_file, output_file)

    def __convert_file(self, source_filename: str, target_filename: str) -> None:
        """Reads a CSV, applies field conversions, and writes it out as new file."""
        if self.__status_fn is not None:
            self.__status_fn(f"Converting '{source_filename}' to '{target_filename}'.")

        self.__log.info("Converting '%s' to '%s'.", source_filename, target_filename)

        # Read CSV, forcing all data as string.
        participant_match: pandas.DataFrame = pandas.read_csv(
            source_filename,
            converters=StringConverter(),
            delimiter=",",
        )
        #
        #   SPECIAL HANDLING OF PATIENT STATUS
        #
        participant_match = convert_patient_status(participant_match)
        #
        #   CONVERT COLUMNS
        #
        # Consent status.
        consent_map: dict = {
            "yes": "1",
            "no": "0",
        }
        participant_match["consentForElectronicHealthRecords"] = participant_match[
            "consentForElectronicHealthRecords"
        ].map(consent_map)
        participant_match["consentForStudyEnrollment"] = participant_match[
            "consentForStudyEnrollment"
        ].map(consent_map)
        #
        #   FORMAT DATE COLUMNS
        #
        time_date_columns: list = find_time_or_date_columns(participant_match)

        for time_date_column in time_date_columns:
            formatted_column_name: str = time_date_column + "Formatted"
            participant_match[formatted_column_name] = convert_date(
                participant_match[time_date_column]
            )

        # Deactivation status.
        deactivation_map: dict = {
            "deactivated": "NO_CONTACT",
            "not_deactivated": "NOT_SUSPENDED",
            "unset": "UNSET",
        }
        participant_match["deactivationStatus"] = participant_match[
            "deactivationStatus"
        ].map(deactivation_map)

        # Deceased status.
        deceased_map: dict = {
            "deceased": "APPROVED",
            "unset": "UNSET",
        }
        participant_match["deceasedStatus"] = participant_match["deceasedStatus"].map(
            deceased_map
        )

        # Physical measurements.
        participant_match["clinicPhysicalMeasurementsStatus"] = participant_match[
            "clinicPhysicalMeasurementsStatus"
        ].str.upper()

        # State
        participant_match.replace("", {"state": np.nan}, inplace=True)
        participant_match.fillna({"state": "UNSET"}, inplace=True)

        # Withdrawn status.
        withdrawal_map: dict = {
            "not_withdrawn": "0",
            "withdrawn": "1",
        }
        participant_match["withdrawalStatus"] = participant_match[
            "withdrawalStatus"
        ].map(withdrawal_map)

        # Add dummy columns.
        participant_match["withdrawalReason"] = "UNSET"

        # Read mapping from input names to output names.
        mapping: dict = read_column_mappings(self.__log)
        new_data: dict = {}

        for key, value in mapping.items():
            try:
                new_data[key] = participant_match[value]
            except KeyError:
                # If this input column name isn't present in participant match, just skip it.
                pass

        # Merge columns names actually IN the data with the additional columns expected, but remove duplicates.
        additional_output_columns: list[str] = read_output_columns(self.__log)

        for additional_output_column in additional_output_columns:
            if additional_output_column not in new_data:
                new_data[additional_output_column] = None

        # Create a new DataFrame from the data dictionary.
        hp = pandas.DataFrame(data=new_data)

        # Write the modified DataFrame back to a new CSV file, overwriting if necessary.
        if self.__status_fn is not None:
            self.__status_fn(f"Writing file {target_filename}.")

        hp.to_csv(target_filename, index=False, header=True, mode="w")


if __name__ == "__main__":
    my_log: logging.Logger = setup_logging(
        log_filename=os.path.join(os.getcwd(), "convert_to_hp_format.log")
    )
    hpc: HealthProConverter = HealthProConverter(
        data_directory=r"E:\dbmi.data\aou_submission\api_gui_test",
        log=my_log,
        status_fn=None,
    )
    hpc.convert()
