"""
Tests methods related to class InsiteAPI
"""
import csv
import os
from typing import Union
from unittest import mock

import pytest
import requests
import requests_mock
from urllib3.exceptions import ConnectTimeoutError

from src.getmyapidata.aou_package import AouPackage
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


def test_insite_api(
    logger, fake_api_request_package, fake_json_I, fake_json_II, fake_data_directory
) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress} % complete")
        elif isinstance(progress, str):
            logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url_I: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    # To test "link" extraction & processing, fake a SECOND URL...
    fake_url_II: str = (
        "https://fake.url?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    # ...wrap into the expected dict structure...
    next_url: dict = {"relation": "next", "url": fake_url_II}

    # ...and tuck this dict into the FIRST json package.
    fake_json_I["link"] = [next_url]

    # Create a mock web API service.
    with requests_mock.Mocker() as m:
        # Register a mocked service that defines TWO URLs.
        # The API Package used to instantiate the InSiteAPI object will point the object
        # to the first URL, which will return the first JSON package, containing a link to the SECOND URL,
        # which returns the second JSON package, which HAS no link & therefore stops the processing.
        m.register_uri(method="GET", url=fake_url_I, json=fake_json_I, status_code=200)
        m.register_uri(
            method="GET", url=fake_url_II, json=fake_json_II, status_code=200
        )

        api_obj.run()

    api_obj.output_data(fake_data_directory)
    assert os.path.exists(fake_data_directory)

    for file in os.listdir(fake_data_directory):
        full_file_path: str = os.path.join(fake_data_directory, file)
        data: list[dict] = []

        with open(full_file_path, "r", encoding="utf-8") as f:
            reader: csv.DictReader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        assert len(data) == 2
        this_org: dict = data[0]
        assert isinstance(this_org, dict)
        assert "organization" in this_org


def test_insite_api_malformed_json(
    logger, fake_api_request_package, fake_json, fake_data_directory
) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress} % complete")
        elif isinstance(progress, str):
            logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )
    # Remove 'resourceType' from json dict.
    del fake_json["resourceType"]

    with requests_mock.Mocker() as m:
        m.register_uri(method="GET", url=fake_url, json=fake_json, status_code=200)

        with pytest.raises(RuntimeError):
            api_obj.run()


def test_insite_api_no_report_fn(
    logger, fake_api_request_package, fake_json_no_total, fake_data_directory
) -> None:

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    with requests_mock.Mocker() as m:
        m.register_uri(
            method="GET", url=fake_url, json=fake_json_no_total, status_code=200
        )
        api_obj.run()

    api_obj.output_data(fake_data_directory)
    assert os.path.exists(fake_data_directory)

    for file in os.listdir(fake_data_directory):
        full_file_path: str = os.path.join(fake_data_directory, file)
        data: list[dict] = []

        with open(full_file_path, "r", encoding="utf-8") as f:
            reader: csv.DictReader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        assert len(data) == 1
        this_org: dict = data[0]
        assert isinstance(this_org, dict)
        assert "organization" in this_org


def test_insite_api_other_errors(
    logger, fake_api_request_package, fake_json, fake_data_directory
) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress} % complete")
        elif isinstance(progress, str):
            logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    with requests_mock.Mocker() as m:
        # Pretend we NEVER get a 200.
        m.register_uri(method="GET", url=fake_url, json=fake_json, status_code=400)

        with pytest.raises(RuntimeError):
            api_obj.run()


def test_insite_api_stop(logger, fake_api_request_package, fake_json) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress} % complete")
            logger.debug("Invoking 'stop' method.")
            api_obj.stop()
        elif isinstance(progress, str):
            logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    # Wrap the fake URL into the expected dict...
    next_url: dict = {"relation": "next", "url": fake_url}

    # ...and tuck this dict into the JSON package.
    fake_json["link"] = [next_url]

    # Create a mock web API service.
    with requests_mock.Mocker() as m:
        # Register a mocked service.
        # Theory is that the API Package used to instantiate the InSiteAPI object will point the object
        # to the fake URL, which will return the fake JSON package, containing A LINK TO THE SAME URL,
        # which will cause an infinite loop--until we invoke the stop() method as part of the on_auth_completion callback.
        m.register_uri(method="GET", url=fake_url, json=fake_json, status_code=200)

        api_obj.run()


def test_insite_api_timeouts(
    logger, fake_api_request_package, fake_json, fake_data_directory
) -> None:
    def on_auth_completion(progress: Union[bool, int, str]) -> None:
        if isinstance(progress, bool):
            logger.info("Authorization complete.")
        elif isinstance(progress, int):
            logger.info(f"progress: {progress} % complete")
        elif isinstance(progress, str):
            logger.info(progress)

    api_obj: InSiteAPI = InSiteAPI(
        api_package=fake_api_request_package,
        log=logger,
        report_fn=on_auth_completion,
    )
    assert isinstance(api_obj, InSiteAPI)

    fake_aou_package: AouPackage = fake_api_request_package.aou_package
    fake_url: str = (
        fake_aou_package.endpoint
        + "?_sort=lastModified&_includeTotal=TRUE&_count=1000&awardee="
        + fake_aou_package.awardee
    )

    # Simulate that we get a 500 error, then a 200 on retry.
    logger.debug("Simulating status code 500, then 200.")
    with requests_mock.Mocker() as m:
        m.register_uri(
            method="GET",
            url=fake_url,
            response_list=[
                {"status_code": 500},
                {"json": fake_json, "status_code": 200},
            ],
        )
        api_obj.run()

    # Simulate we NEVER get a 200--forcing a RuntimeError after multiple attempts.
    logger.debug("Simulating status code 500 forever.")
    with requests_mock.Mocker() as m:
        m.register_uri(method="GET", url=fake_url, json=fake_json, status_code=500)

        with pytest.raises(RuntimeError):
            api_obj.run()

    # Simulate receiving an exception during request.
    logger.debug("Simulating exception during request.")
    with requests_mock.Mocker() as m:
        m.register_uri(
            method="GET", url=fake_url, exc=requests.exceptions.ConnectionError
        )

        with pytest.raises(RuntimeError):
            api_obj.run()

    # Simulate receiving an exception during RETRY.
    logger.debug("Simulating exception during retry.")
    with requests_mock.Mocker() as m:
        m.register_uri(
            method="GET",
            url=fake_url,
            response_list=[
                {"status_code": 500},
                {"exc": requests.exceptions.ConnectionError},
            ]
        )

        with pytest.raises(RuntimeError):
            api_obj.run()
