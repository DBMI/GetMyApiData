"""
Contains class HealthProConverter, which converts participant list into Health Pro format.
"""
import json
import logging
import os
from collections.abc import Callable

import numpy as np
import pandas

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
        return str


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


# pylint: disable=too-few-public-methods
class HealthProConverter:
    """
    Allows us to convert new InSite API format to the HealthPro format we're used to.
    """

    def __init__(
        self, log: logging.Logger, data_directory: str, status_fn: Callable = None
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

        for filename_and_ext in os.listdir(self.__directory):
            if (
                filename_and_ext.endswith(".csv")
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
        participant_match[
            "clinicPhysicalMeasurementsFinalizedTimeFormatted"
        ] = convert_date(participant_match["clinicPhysicalMeasurementsFinalizedTime"])
        participant_match[
            "consentForElectronicHealthRecordsAuthoredFormatted"
        ] = convert_date(participant_match["consentForElectronicHealthRecordsAuthored"])
        participant_match["consentForStudyEnrollmentAuthoredFormatted"] = convert_date(
            participant_match["consentForStudyEnrollmentAuthored"]
        )
        participant_match["deactivationTimeFormatted"] = convert_date(
            participant_match["deactivationTime"]
        )
        participant_match["deceasedAuthoredFormatted"] = convert_date(
            participant_match["deceasedAuthored"]
        )
        participant_match["latestEhrReceiptTimeFormatted"] = convert_date(
            participant_match["latestEhrReceiptTime"]
        )
        participant_match["withdrawalTimeFormatted"] = convert_date(
            participant_match["withdrawalTime"]
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

        # Create a new DataFrame and assign columns with new names.
        hp = pandas.DataFrame(
            {
                "Last Name": participant_match["lastName"],
                "First Name": participant_match["firstName"],
                "Middle Initial": participant_match["middleName"],
                "Date of Birth": participant_match["dateOfBirth"],
                "PMI ID": participant_match["participantId"],
                "Withdrawal Status": participant_match["withdrawalStatus"],
                "Withdrawal Date": participant_match["withdrawalTimeFormatted"],
                "Withdrawal Reason": participant_match["withdrawalReason"],
                "Deactivation Status": participant_match["deactivationStatus"],
                "Deactivation Date": participant_match["deactivationTimeFormatted"],
                "Deceased": participant_match["deceasedStatus"],
                "Date of Death": participant_match["deceasedAuthoredFormatted"],
                "Street Address": participant_match["streetAddress"],
                "Street Address2": participant_match["streetAddress2"],
                "City": participant_match["city"],
                "State": participant_match["state"],
                "Zip": participant_match["zipCode"],
                "Login Phone": participant_match["phoneNumber"],
                "Phone": participant_match["phoneNumber"],
                "Email": participant_match["email"],
                "Paired Organization": participant_match["organization"],
                "Physical Measurements Status": participant_match[
                    "clinicPhysicalMeasurementsStatus"
                ],
                "Physical Measurements Completion Date": participant_match[
                    "clinicPhysicalMeasurementsFinalizedTimeFormatted"
                ],
                "Paired Site": participant_match[
                    "clinicPhysicalMeasurementsFinalizedSite"
                ],
                "EHR Consent Status": participant_match[
                    "consentForElectronicHealthRecords"
                ],
                "EHR Consent Date": participant_match[
                    "consentForElectronicHealthRecordsAuthoredFormatted"
                ],
                "Most Recent EHR Receipt": participant_match[
                    "latestEhrReceiptTimeFormatted"
                ],
                "Patient Status: Yes": participant_match["patientStatusYes"],
                "Patient Status: No": participant_match["patientStatusNo"],
                "Patient Status: No Access": participant_match["patientStatusNoAccess"],
                "Patient Status: Unknown": participant_match["patientStatusUnknown"],
                "Primary Consent Status": participant_match[
                    "consentForStudyEnrollment"
                ],
                "Date of First Primary Consent": participant_match[
                    "consentForStudyEnrollmentAuthoredFormatted"
                ],
                "Primary Consent Date": participant_match[
                    "consentForStudyEnrollmentAuthoredFormatted"
                ],
            },
            columns=[
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
            ],
        )

        # Write the modified DataFrame back to a new CSV file, overwriting if necessary.
        if self.__status_fn is not None:
            self.__status_fn(f"Writing file {target_filename}.")

        hp.to_csv(target_filename, index=False, header=True, mode="w")


if __name__ == "__main__":
    my_log: logging.Logger = setup_logging(
        log_filename=os.path.join(os.getcwd(), "convert_to_hp_format.log")
    )
    hpc: HealthProConverter = HealthProConverter(
        data_directory=r"F:\dbmi.data\aou_submission\api_gui_test",
        log=my_log,
        status_fn=None,
    )
    hpc.convert()
