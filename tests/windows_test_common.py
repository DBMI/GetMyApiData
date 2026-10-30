"""
Test methods from common.py
"""

import logging
import os
import sys
from pathlib import Path

from src.getmyapidata.common import (
    ensure_path_possible,
    get_exe_version,
)


def windows_test_get_exe_version(logger: logging.Logger) -> None:
    exe_version: str = get_exe_version(logger)
    print(f"Exe version is {exe_version}.")
    assert isinstance(exe_version, str)


def windows_test_ensure_path_possible(logger: logging.Logger) -> None:
    assert ensure_path_possible(__file__, logger)
    assert ensure_path_possible(str(Path(r"C:/") / "test" / "temp.txt"), logger)
    assert not ensure_path_possible(str(Path(r"Q:/") / "test" / "temp.txt"), logger)


if __name__ == "__main__":
    # Set up logger for use with test methods.
    right_here: str = os.path.dirname(__file__)

    if not "tests" in right_here:
        right_here = str(Path(right_here) / "tests")

    log_filename: str = str(Path(right_here) / "testing.log")

    logger = logging.getLogger(log_filename)

    # Logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        "%(module)s - %(levelname)s - %(funcName)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Logging to a file
    logfile_format = logging.Formatter(
        fmt="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logfile_handler = logging.FileHandler(log_filename)
    logfile_handler.setFormatter(logfile_format)
    logger.addHandler(logfile_handler)

    logger.setLevel(logging.DEBUG)

    windows_test_get_exe_version(logger)
    windows_test_ensure_path_possible(logger)
