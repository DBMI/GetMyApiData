"""
Test methods from common.py
"""
import logging
import os

from src.getmyapidata.common import (ensure_path_possible, get_base_path,
                                     get_exe_path, get_exe_version)


def test_ensure_path_possible(fake_logger: logging.Logger) -> None:
    assert ensure_path_possible(__file__, fake_logger)
    assert ensure_path_possible(r"C:\test\temp.txt", fake_logger)
    assert not ensure_path_possible(r"Q:\test\temp.txt", fake_logger)


def test_get_base_path() -> None:
    base_path: str = get_base_path()
    assert isinstance(base_path, str)
    assert os.path.isdir(base_path)


def test_get_exe_path() -> None:
    exe_path: str = get_exe_path()
    assert isinstance(exe_path, str)
    assert os.path.isfile(exe_path)


def test_get_exe_version(fake_logger: logging.Logger) -> None:
    exe_version: str = get_exe_version(fake_logger)
    assert isinstance(exe_version, str)
