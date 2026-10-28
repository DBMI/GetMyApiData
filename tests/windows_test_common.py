"""
Test methods from common.py
"""

import logging
from pathlib import Path

from src.getmyapidata.common import (
    ensure_path_possible,
    get_exe_version,
)


def windows_test_ensure_path_possible(logger: logging.Logger) -> None:
    assert ensure_path_possible(__file__, logger)
    assert ensure_path_possible(str(Path(r"C:/") / "test" / "temp.txt"), logger)
    assert not ensure_path_possible(str(Path(r"Q:/") / "test" / "temp.txt"), logger)


def windows_test_get_exe_version(logger: logging.Logger) -> None:
    exe_version: str = get_exe_version(logger)
    assert isinstance(exe_version, str)
