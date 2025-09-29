"""
Tests methods of convert_to_hp_format.py
"""
import math
import os

import pandas

from src.getmyapidata.convert_to_hp_format import (HealthProConverter,
                                                   convert_date,
                                                   convert_patient_status)


def test_convert_date(fake_series) -> None:
    series: pandas.Series = convert_date(fake_series)
    assert isinstance(series, pandas.Series)
    assert series.size == fake_series.size
    assert isinstance(series[0], str)
    assert series[0] == "2025-12-25T00:00:00"
    assert isinstance(series[1], float)
    assert math.isnan(series[1])


def test_convert_patient_status(fake_patient_status_dataframe) -> None:
    df: pandas.DataFrame = convert_patient_status(fake_patient_status_dataframe)
    assert isinstance(df, pandas.DataFrame)
    assert df.size == fake_patient_status_dataframe.size
    assert "patientStatusOrganization" in df.columns
    assert "patientStatusYes" in df.columns
    assert "patientStatusNo" in df.columns
    assert "patientStatusNoAccess" in df.columns
    assert "patientStatusUnknown" in df.columns
    assert df["patientStatusOrganization"][0] == "CAL_PMC_UCSD"
    assert df["patientStatusOrganization"][1] == "CAL_PMC_SDBB"
    assert not df["patientStatusYes"][0]
    assert df["patientStatusYes"][1] == "CAL_PMC_SDBB"
    assert df["patientStatusNo"][0] == "CAL_PMC_UCSD"
    assert not df["patientStatusNo"][1]
    assert not df["patientStatusNoAccess"][0]
    assert not df["patientStatusNoAccess"][1]
    assert not df["patientStatusUnknown"][0]
    assert not df["patientStatusUnknown"][1]


def test_hp_converter(fake_patient_dataframe, fake_logger) -> None:
    right_here: str = os.getcwd()
    hp: HealthProConverter = HealthProConverter(
        log=fake_logger, data_directory=right_here
    )
    assert isinstance(hp, HealthProConverter)
    hp.convert()
    transformed_file: str = os.path.join(
        right_here, "TEST_participant_list_transformed.csv"
    )
    assert os.path.exists(transformed_file)
    transformed_dataframe: pandas.DataFrame = pandas.read_csv(transformed_file)
    assert isinstance(transformed_dataframe, pandas.DataFrame)
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
    assert transformed_dataframe.columns.isin(columns).all()
