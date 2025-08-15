import ast
import json
import logging
import os
from collections.abc import Callable
from typing import Union

import numpy as np
import pandas
import pandas as pd

from my_logging import setup_logging


# UTILITY CLASS
# Forces all data typing to strings
class StringConverter(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return str

    def get(self, default=None):
        return str


class HealthProConverter(object):
    """
    Allows us to convert new InSite API format to the HealthPro format we're used to.
    """

    def __init__(
        self, log_directory: str, data_directory: str, status_fn: Callable = None
    ):
        """Instantiate a HealthProConverter object

        Parameters
        ----------
        log_directory: str
        data_directory: str
        """
        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                log_directory,
                "convert_to_hp.log",
            )
        )

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
        """Reads a CSV, applies field conversions, and writes it back."""
        if self.__status_fn is not None:
            self.__status_fn(f"Converting '{source_filename}' to '{target_filename}'.")

        self.__log.info(f"Converting '{source_filename}' to '{target_filename}'.")

        # Read CSV, forcing all data as string.
        participant_match: pandas.DataFrame = pd.read_csv(
            source_filename,
            converters=StringConverter(),
            delimiter=",",
        )
        #
        #   SPECIAL HANDLING OF PATIENT STATUS
        #
        # Add new columns derived from patientStatus JSON strings.
        temp_ser: pandas.Series = participant_match["patientStatus"].apply(
            lambda s: s.replace("'", '"')
        )
        participant_match["patientStatusParsed"] = temp_ser.apply(json.loads)
        participant_match["patientStatusWord"] = participant_match[
            "patientStatusParsed"
        ].apply(lambda x: x[0]["status"] if x else None)
        participant_match["patientStatusOrganization"] = participant_match[
            "patientStatusParsed"
        ].apply(lambda x: x[0]["organization"] if x else None)

        # Empty columns for now.
        participant_match["patientStatusYes"] = None
        participant_match["patientStatusNo"] = None
        participant_match["patientStatusNoAccess"] = None
        participant_match["patientStatusUnknown"] = None

        # Insert the patientStatusOrganization where patientStatusWord is YES/NO/NO ACCESS/UNKNOWN.
        mask: bool = participant_match["patientStatusWord"].values == "YES"
        participant_match.loc[mask, "patientStatusYes"] = participant_match.loc[
            mask, "patientStatusOrganization"
        ]
        mask = participant_match["patientStatusWord"].values == "NO"
        participant_match.loc[mask, "patientStatusNo"] = participant_match.loc[
            mask, "patientStatusOrganization"
        ]
        mask = participant_match["patientStatusWord"].values == "NO ACCESS"
        participant_match.loc[mask, "patientStatusNoAccess"] = participant_match.loc[
            mask, "patientStatusOrganization"
        ]
        mask = participant_match["patientStatusWord"].values == "UNKNOWN"
        participant_match.loc[mask, "patientStatusUnknown"] = participant_match.loc[
            mask, "patientStatusOrganization"
        ]
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
        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["clinicPhysicalMeasurementsFinalizedTime"],
            errors="coerce",
        )
        participant_match["clinicPhysicalMeasurementsFinalizedTimeFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["consentForElectronicHealthRecordsAuthored"],
            errors="coerce",
        )
        participant_match["consentForElectronicHealthRecordsAuthoredFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["consentForStudyEnrollmentAuthored"], errors="coerce"
        )
        participant_match["consentForStudyEnrollmentAuthoredFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["deactivationTime"], errors="coerce"
        )
        participant_match["deactivationTimeFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["deceasedAuthored"], errors="coerce"
        )
        participant_match["deceasedAuthoredFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["latestEhrReceiptTime"], errors="coerce"
        )
        participant_match["latestEhrReceiptTimeFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        participant_match["dateTemp"] = pd.to_datetime(
            participant_match["withdrawalTime"], errors="coerce"
        )
        participant_match["withdrawalTimeFormatted"] = (
            participant_match["dateTemp"]
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

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
        hp = pd.DataFrame(
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

    def __convert_cabor_consent_status(self, original: Union[int, str]) -> int:
        """Converts int or text to int status.

        Parameters
        ----------
        original : either str or int

        Returns
        -------
        status : int
        """
        zero = ["UNSET", "SUBMITTED_NO_CONSENT", "SUBMITTED_INVALID"]
        one = ["SUBMITTED"]
        two = ["SUBMITTED_NOT_SURE"]

        if len(original) == 0 or original.upper() in zero:
            return 0
        elif original.upper() in one:
            return 1
        elif original.upper() in two:
            return 2

        self.__log.exception(f"Unhandled EHR Consent Status: {original}")
        raise Exception(f"Unhandled EHR Consent Status: {original}")

    def __convert_campus(self, original: str, response: str) -> str:
        quote_fix: str = original.replace("'", '"')

        try:
            # For when it looks like [{'status': 'YES', 'organization', 'CAL_PMC_UCSD'}]
            j = json.loads(quote_fix)
            results = []

            for entry in j:
                status = entry["status"].upper()
                organization = entry["organization"]

                if status == response.upper():
                    results.append(organization)

            return "; ".join(results)
        except json.decoder.JSONDecodeError:
            # For when it looks like 'CAL_PMC_UCSD'
            return quote_fix

    def __convert_date(self, original: str) -> str:
        try:
            # Convert to datetime, automatically handling multiple formats
            date_obj = pd.to_datetime(original, errors="coerce")

            # If conversion failed (NaT), return original
            if pd.isna(date_obj):
                return original

            # Format as MM/DD/YYYY
            # return date_obj.strftime("%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%dT%H:%M:%S")

        except Exception as e:
            self.__log.exception(f"Unhandled Date: {original}")
            raise Exception(f"Unhandled Date: {original}")

    def __convert_deceased(self, original: Union[int, str]) -> int:
        zero = ["UNSET"]
        one = ["PENDING"]
        two = ["APPROVED", "DECEASED"]

        if len(original) == 0 or original.upper() in zero:
            return 0
        elif original.upper() in one:
            return 1
        elif original.upper() in two:
            return 2

        self.__log.exception(f"Unhandled EHR Consent Status: {original}")
        raise Exception(f"Unhandled EHR Consent Status: {original}")

    def __convert_ehr_consent_status(self, original: Union[int, str]) -> int:
        zero = [
            "UNSET",
            "SUBMITTED_NO_CONSENT",
            "SUBMITTED_NOT_VALIDATED",
            "SUBMITTED_INVALID",
            "NO",
        ]
        one = ["SUBMITTED", "YES"]
        two = ["SUBMITTED_NOT_SURE"]

        if len(original) == 0 or original.upper() in zero:
            return 0
        elif original.upper() in one:
            return 1
        elif original.upper() in two:
            return 2
        self.__log.exception(f"Unhandled EHR Consent Status: {original}")
        raise Exception(f"Unhandled EHR Consent Status: {original}")

    def __convert_field(self, value: str, datatype: str) -> Union[int, str]:
        """Calls the appropriate conversion function based on field type."""
        if datatype == "Date":
            return self.__convert_date(value)
        if datatype == "State":
            return self.__convert_state(value)
        if datatype == "Sex":
            return self.__convert_sex(value)
        if datatype == "Gender":
            return self.__convert_gender(value)
        if datatype == "Race":
            return self.__convert_race(value)
        if datatype == "Withdrawal":
            return self.__convert_withdrawal_status(value)
        if datatype == "Primary Consent":
            return self.__convert_primary_consent_status(value)
        if datatype == "EHR Consent":
            return self.__convert_ehr_consent_status(value)
        if datatype == "CampusYes":
            return self.__convert_campus(value, "yes")
        if datatype == "CampusNo":
            return self.__convert_campus(value, "no")
        if datatype == "CampusUnknown":
            return self.__convert_campus(value, "unknown")
        if datatype == "CampusNoAccess":
            return self.__convert_campus(value, "noaccess")
        if datatype == "Deceased":
            return self.__convert_deceased(value)
        return value  # Return value unchanged if type is not found

    def __convert_gender(self, original: str) -> str:
        sexes = [
            "Man",
            "Woman",
            "NonBinary",
            "Transgender",
            "Skip",  # NOT IN DATA DICTIONARY
        ]
        convert = {
            "MoreThanOne": "More Than One Gender Identity",
            "AdditionalOptions": "Other",
        }

        tokens = original.split("_")

        if original.upper() == "UNSET":
            return original
        if original.upper() == "PMI_SKIP":
            return "Skip"
        if original.upper() == "PMI_PREFERNOTTOANSWER":
            return "Prefer Not to Answer"
        elif tokens[1] in convert:
            return convert[tokens[1]]
        elif len(tokens) != 2:
            return "GENDER_ERROR"
        elif tokens[1] not in sexes:
            return f"{original} GENDER_ERROR"
        return tokens[1]

    def __convert_primary_consent_status(self, original: str) -> int:
        zero = ["UNSET", "SUBMITTED_NO_CONSENT", "SUBMITTED_INVALID", "NO"]
        one = ["SUBMITTED", "YES"]
        two = ["SUBMITTED_NOT_SURE"]

        if len(original) == 0 or original.upper() in zero:
            return 0
        elif original.upper() in one:
            return 1
        elif original.upper() in two:
            return 2
        self.__log.exception(f"Unhandled Primary Consent Status: {original}")
        raise Exception(f"Unhandled Primary Consent Status: {original}")

    def __convert_race(self, original: str) -> str:
        conversion_map = {
            "AMERICAN_INDIAN_OR_ALASKA_NATIVE": "American Indian /Alaska Native",
            "BLACK_OR_AFRICAN_AMERICAN": "Black or African American",
            "ASIAN": "Asian",
            "NATIVE_HAWAIIAN_OR_OTHER_PACIFIC_ISLANDER": "Native Hawaiian or Other Pacific Islander",
            "WHITE": "White",
            "HISPANIC_LATINO_OR_SPANISH": "Hispanic, Latino, or Spanish",
            "MIDDLE_EASTERN_OR_NORTH_AFRICAN": "Middle Eastern or North African",
            "HLS_AND_WHITE": r"H/L/S and White",
            "HLS_AND_BLACK": r"H/L/S and Black",
            "HLS_AND_ONE_OTHER_RACE": r"H/L/S and one other race",
            "HLS_AND_MORE_THAN_ONE_OTHER_RACE": r"H/L/S and more than one race",
            "UNSET": "Other",
            "UNMAPPED": "Other",
            "MORE_THAN_ONE_RACE": "Other",
            "OTHER_RACE": "Other",
            "PREFER_NOT_TO_SAY": "Other",
            "Skip": "Skip",
        }
        tokens = original.split("_")

        if original.upper() in conversion_map:
            return conversion_map[original.upper()]
        elif tokens[1] in conversion_map:
            return conversion_map[tokens[1]]
        elif len(tokens) != 2:
            return "RACE_ERROR"
        elif tokens[1] not in conversion_map:
            return f"{original} RACE_ERROR"
        self.__log.exception(f"Unhandled Race: {original}")
        raise Exception(f"Unhandled Race: {original}")

    def __convert_sex(self, original: str) -> str:
        sexes = [
            "Male",
            "Female",
            "Intersex",
            "Skip",  # NOT IN DATA DICTIONARY
        ]
        convert = {
            "SexAtBirth_None".upper(): "Other",
            "SexAtBirth_SexAtBirthNoneOfThese".upper(): "Other",
        }
        tokens = original.split("_")

        if original.upper() == "UNSET":
            return original
        elif original.upper() == "PMI_SKIP":
            return "Skip"
        elif original.upper() == "PMI_PREFERNOTTOANSWER":
            return "Prefer Not to Answer"
        elif original.upper() in convert:
            return convert[original.upper()]
        elif len(tokens) != 2:
            return "SEX_ERROR"
        elif tokens[1] not in sexes:
            return f"{original} SEX_ERROR"
        return tokens[1]

    def __convert_state(self, original: str) -> str:
        if len(original) == 0:
            return "UNSET"

        if "_" in original:
            return self.__convert_state_two_part(original)

        return self.__convert_state_full_name(original)

    def __convert_state_full_name(self, original: str) -> str:
        conversion_map = {
            "ALASKA": "AK",
            "ALABAMA": "AL",
            "ARKANSAS": "AR",
            "ARIZONA": "AZ",
            "CALIFORNIA": "CA",
            "COLORADO": "CO",
            "CONNECTICUT": "CT",
            "DELAWARE": "DE",
            "FLORIDA": "FL",
            "GEORGIA": "GA",
            "HAWAII": "HI",
            "IOWA": "IA",
            "IDAHO": "ID",
            "ILLINOIS": "IL",
            "INDIANA": "IN",
            "KANSAS": "KS",
            "KENTUCKY": "KY",
            "LOUISIANA": "LA",
            "MASSACHUSETTS": "MA",
            "MARYLAND": "MD",
            "MAINE": "ME",
            "MICHIGAN": "MI",
            "MINNESOTA": "MN",
            "MISSOURI": "MO",
            "MISSISSIPPI": "MS",
            "MONTANA": "MT",
            "NORTH CAROLINA": "NC",
            "NORTH DAKOTA": "ND",
            "NEBRASKA": "NE",
            "NEW HAMPSHIRE": "NH",
            "NEW JERSEY": "NJ",
            "NEW MEXICO": "NM",
            "NEVADA": "NV",
            "NEW YORK": "NY",
            "OHIO": "OH",
            "OKLAHOMA": "OK",
            "OREGON": "OR",
            "PENNSYLVANIA": "PA",
            "RHODE ISLAND": "RI",
            "SOUTH CAROLINA": "SC",
            "SOUTH DAKOTA": "SD",
            "TENNESSEE": "TN",
            "TEXAS": "TX",
            "UTAH": "UT",
            "VIRGINIA": "VA",
            "VERMONT": "VT",
            "WASHINGTON": "WA",
            "WISCONSIN": "WI",
            "WEST VIRGINIA": "WV",
            "WYOMING": "WY",
            # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Federal_district.
            "DISTRICT OF COLUMBIA": "DC",
            # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Inhabited_territories.
            "AMERICAN SAMOA": "AS",
            # https://pe.usps.com/text/pub28/pub28apb.htm
            "FEDERATED STATES OF MICRONESIA": "FM",
            "GUAM": "GU",
            "MARSHALL ISLANDS": "MH",
            "NORTHERN MARIANA ISLANDS": "MP",
            "PALAU": "PW",
            "PUERTO RICO": "PR",
            "VIRGIN ISLANDS": "VI",
            "US VIRGIN ISLANDS": "VI",
            "U.S. VIRGIN ISLANDS": "VI",
        }

        if original.upper() in conversion_map:
            return conversion_map[original.upper()]

        self.__log.exception(f"Unhandled Race: {original}")
        raise Exception(f"Unhandled Race: {original}")

    # Converts "PIIState_CA" to "CA"
    def __convert_state_two_part(self, original: str) -> str:
        """

        Parameters
        ----------
        original : str

        Returns
        -------
        abbreviation : str

        """
        state_abbreviations = [
            "AL",
            "AK",
            "AZ",
            "AR",
            "CA",
            "CO",
            "CT",
            "DE",
            "FL",
            "GA",
            "HI",
            "ID",
            "IL",
            "IN",
            "IA",
            "KS",
            "KY",
            "LA",
            "ME",
            "MD",
            "MA",
            "MI",
            "MN",
            "MS",
            "MO",
            "MT",
            "NE",
            "NV",
            "NH",
            "NJ",
            "NM",
            "NY",
            "NC",
            "ND",
            "OH",
            "OK",
            "OR",
            "PA",
            "RI",
            "SC",
            "SD",
            "TN",
            "TX",
            "UT",
            "VT",
            "VA",
            "WA",
            "WV",
            "WI",
            "WY",
            "PR",  # Puerto Rico?
            "DC",  # Washington DC?
            "GU",  # Guam?
            "FM",  # Federated States of Micronesia?
            "AS",  # American Samoa?
            "VI",  # U.S. Virgin Islands?
        ]

        tokens: list = original.split("_")

        if original.upper() == "UNSET":
            return original
        elif len(tokens) != 2:
            self.__log.exception(f"State parsing error: {original}")
            return "STATE_ERROR"
        elif tokens[1] not in state_abbreviations:
            self.__log.exception(f"State parsing error: {original}")
            return f"{original} STATE_ERROR"
        return tokens[1]

    def __convert_withdrawal_status(self, original: Union[int, str]) -> int:
        if original == 0 or original.upper() == "NOT_WITHDRAWN":
            return 0
        elif original == 1 or original.upper() in ["NO_USE", "WITHDRAWN"]:
            return 1

        self.__log.exception(f"Unhandled Withdrawal Status: {original}")
        raise Exception(f"Unhandled Withdrawal Status: {original}")


if __name__ == "__main__":
    hpc = HealthProConverter(
        log_directory=r"F:\dbmi.data\aou_submission\api_test",
        data_directory=r"F:\dbmi.data\aou_submission\api_test",
    )
    hpc.convert()
