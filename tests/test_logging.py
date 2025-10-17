"""
Tests methods related to logging setup
"""
import logging
import os

from src.getmyapidata.my_logging import setup_logging


def test_setup_logging(tmp_path) -> None:
    # Without log filename
    logger: logging.Logger = setup_logging()
    assert isinstance(logger, logging.Logger)

    # Using log filename
    test_log: os.path.Path = tmp_path / "test.log"
    logger = setup_logging(test_log)
    assert isinstance(logger, logging.Logger)
