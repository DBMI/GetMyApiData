"""
Test methods from common.py
"""

import logging
import os

from src.getmyapidata.common import (
    get_base_path,
    get_exe_path,
    get_exe_version,
)


def test_get_base_path() -> None:
    base_path: str = get_base_path()
    assert isinstance(base_path, str)
    assert os.path.isdir(base_path)


def test_get_exe_path(logger: logging.Logger) -> None:
    exe_path: str = get_exe_path()
    assert isinstance(exe_path, str)
    assert os.path.isfile(exe_path)


def test_get_exe_version(logger: logging.Logger) -> None:
    exe_version: str = get_exe_version(logger)
    assert isinstance(exe_version, str)
