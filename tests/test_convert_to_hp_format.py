"""
Tests methods of convert_to_hp_format.py
"""
import math
import os
import sys
from unittest.mock import MagicMock

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


def test_hp_converter(fake_patient_dataframe, logger, hp_columns) -> None:
    right_here: str = os.path.dirname(__file__)

    # If we run this test individually, right_here will be full path to tests.
    # But if run from project directory, we'll need to append.
    if "tests" not in right_here:
        right_here = os.path.join(right_here, "tests")

    transformed_file: str = os.path.join(
        right_here, "TEST_participant_list_transformed.csv"
    )

    if os.path.exists(str(transformed_file)):
        os.remove(transformed_file)

    mock_status_bar: MagicMock = MagicMock()
    hp: HealthProConverter = HealthProConverter(
        log=logger, data_directory=right_here, status_fn=mock_status_bar
    )
    assert isinstance(hp, HealthProConverter)
    hp.convert()
    assert os.path.exists(transformed_file)
    transformed_dataframe: pandas.DataFrame = pandas.read_csv(transformed_file)
    assert isinstance(transformed_dataframe, pandas.DataFrame)
    assert transformed_dataframe.columns.isin(hp_columns).all()


def test_hp_converter_no_status_fn(fake_patient_dataframe, logger, hp_columns) -> None:
    right_here: str = os.path.dirname(__file__)

    # If we run this test individually, right_here will be full path to tests.
    # But if run from project directory, we'll need to append.
    if "tests" not in right_here:
        right_here = os.path.join(right_here, "tests")

    transformed_file: str = os.path.join(
        right_here, "TEST_participant_list_transformed.csv"
    )

    if os.path.exists(str(transformed_file)):
        os.remove(transformed_file)

    hp: HealthProConverter = HealthProConverter(log=logger, data_directory=right_here)
    assert isinstance(hp, HealthProConverter)
    hp.convert()
    assert os.path.exists(transformed_file)
    transformed_dataframe: pandas.DataFrame = pandas.read_csv(transformed_file)
    assert isinstance(transformed_dataframe, pandas.DataFrame)
    assert transformed_dataframe.columns.isin(hp_columns).all()
