"""
Test methods from common.py
"""

import logging
import os
from pathlib import Path

from src.getmyapidata.common import (
    find_time_or_date_columns,
    get_executable_path,
    resolve_path,
)


def test_config_path() -> None:
    cp: str = resolve_path("column_mapping.yaml")
    assert isinstance(cp, str)


def test_find_time_date_columns(fake_patient_dataframe) -> None:
    time_date_columns: list = find_time_or_date_columns(fake_patient_dataframe)
    assert isinstance(time_date_columns, list)
    assert len(time_date_columns) == 16


def test_get_exe_path(logger: logging.Logger) -> None:
    exe_path: Path = get_executable_path()
    assert isinstance(exe_path, Path)
    assert os.path.isfile(str(exe_path))
