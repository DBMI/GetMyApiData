"""
Tests methods related to class InsiteAPI
"""
from typing import Union

from src.getmyapidata.insite_api import InSiteAPI, join_headers, make_header


def test_join_headers() -> None:
    h1: list[str] = ["A", "B", "C"]
    h2: list[str] = ["D", "E", "F"]
    h_joined: list[str] = join_headers(h1, h2)
    assert isinstance(h_joined, list)
    assert len(h_joined) == 6
    assert "A" in h_joined
    assert "B" in h_joined
    assert "C" in h_joined
    assert "D" in h_joined
    assert "E" in h_joined
    assert "F" in h_joined

    # Corner cases
    h_joined = join_headers(h1, [])
    assert isinstance(h_joined, list)
    assert len(h_joined) == 3

    h_joined = join_headers([], h2)
    assert isinstance(h_joined, list)
    assert len(h_joined) == 3

    h_joined = join_headers([], [])
    assert isinstance(h_joined, list)
    assert len(h_joined) == 0

def test_make_header() -> None:
    d: dict = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
    h: list[str] = make_header(d)
    assert isinstance(h, list)
    assert len(h) == 6
    assert "A" in h
    assert "B" in h
    assert "C" in h
    assert "D" in h
    assert "E" in h
    assert "F" in h


def test_insite_api_instantiation(fake_logger, fake_api_request_package) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            fake_logger.info("Authorization complete.")
        elif isinstance(progress, int):
            fake_logger.info(f"progress: {progress}")
        elif isinstance(progress, str):
            fake_logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=fake_logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)
