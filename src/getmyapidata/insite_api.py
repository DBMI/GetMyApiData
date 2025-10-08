"""
Contains InSiteAPI class.
"""
import csv
import logging
import os
import threading
import time
from collections import namedtuple
from collections.abc import Callable
from pathlib import Path
from typing import Union

import requests

from src.getmyapidata.aou_package import AouPackage
from src.getmyapidata.progress import Progress

# Fold resp, num_attempts into a named tuple.
ResponsePackage = namedtuple("ResponsePackage", ["resp", "num_attempts"])


def join_headers(h1: list, h2: list) -> list:
    """
    Joins two lists into one list.

    Parameters
    ----------
    h1: list
    h2: list

    Returns
    -------
    combined: list
    """
    if h1 is None:
        if h2 is None:
            return []
        return h2
    if h2 is None:
        return h1

    set1: set = set(h1)
    set2: set = set(h2)
    combined: set = set1 | set2
    return list(combined)


def make_header(dict1: dict) -> list:
    """
    Turns a dictionary keys into a header list.

    Parameters
    ----------
    dict1: dict

    Returns
    -------
    list
    """
    ret = []

    for key in dict1.keys():
        ret.append(key)

    return ret


class InSiteAPI(threading.Thread):
    """
    An interface with the AwardeeInSite API

    Parameters
    ----------
    self.__api_package
    self.data
    self.__log
    self.__official_header
    self.__report_fn
    self.__stop_event

    Methods
    ---------
    output_data()
    run()
    """

    def __init__(
        self, api_package: namedtuple, log: logging.Logger, report_fn: Callable
    ):
        """Instantiate an InSiteAPI object.

        Parameters
        ----------
        api_package: namedtuple     Contains the token file name, awardee & endpoint info
        log: logging.Logger
        report_fn: Callable         Tell something to calling function
        """
        # Set up ability of calling function to stop data request.
        threading.Thread.__init__(self)
        self.__stop_event: threading.Event = threading.Event()

        # Everything we'll need to make request.
        self.__api_package: namedtuple = api_package

        # Property used to record results.
        self.__data: dict = {}

        # Logger
        self.__log: logging.Logger = log

        # Variables developed in request_list() to be used in output_data().
        self.__official_header: list = []

        # We can use these to report to calling function how & what we're doing.
        self.__report_fn: Callable = report_fn

        # Status
        self.__progress: Progress = Progress()

    def __build_line(self, d: dict) -> list:
        """
        Handles putting together output package from dictionary.

        Parameters
        ----------
        d: dict         One organization's data

        Returns
        -------
        line: list      To be written out
        """

        line: list = []

        for h in self.__official_header:
            try:
                if d[h] != "UNSET":
                    line.append(d[h])
                else:
                    line.append("")
            except KeyError:
                line.append("")

        return line

    def __extract_organization_data(self, resource: dict) -> None:
        """
        Updates the self.__data dictionary given one entry.

        Parameters
        ----------
        resource: dict

        """

        if "organization" in resource:
            organization: str = resource["organization"]

            if organization is None or organization.strip() == "":
                organization = "Unpaired"

            if organization not in self.__data:
                self.__data[organization] = []

            self.__data[organization].append(resource)

    def __handle_timeouts(
        self,
        resp: requests.Response,
        num_attempts: int,
        next_url: Union[str, None],
        headers: dict,
    ) -> ResponsePackage:
        """
            Handles the details of timeouts & other errors.

        Parameters
        ----------
        resp: requests.Response
        num_attempts: int           So far
        next_url: str               Exact ping address
        headers: dict               How we want data reported

        Returns
        -------
        response_package: ResponsePackage w/ updated values of resp, num_attempts
        """
        status_code: str = str(resp.status_code) if resp else "Unknown status"

        if not resp or resp.status_code == 500:
            # Server error. Pause & try again.
            num_attempts += 1
            self.__log.error(
                "Server error: %s. Have made %d attempts.",
                status_code,
                num_attempts,
            )

            if num_attempts < 2:
                self.__log.debug("Pausing for another try.")
                time.sleep(30)
                resp = requests.get(next_url, headers=headers, timeout=60)
            else:
                self.__log.error("Exiting.")
                raise RuntimeError(
                    (
                        f"Server error: {status_code}. "
                        f"Have made {num_attempts} attempts. Exiting."
                    )
                )
        else:
            resp_text: str = resp.text if resp else "Unknown error"
            self.__log.error("Error: api request failed.\n\n%s.", resp_text)
            self.__log.error(status_code)
            raise RuntimeError(f"Server error: {status_code}. Exiting.")

        return ResponsePackage(resp, num_attempts)

    def output_data(self, data_directory: str) -> None:
        """
        Produces .csv files from extracted data.

        Parameters
        ----------
        data_directory: str                             Where do you want the files to be created?

        Returns
        -------
        None
        """

        self.__official_header.sort()

        # Ensure the path to the data directory exists.
        data_directory_path: Path = Path(data_directory)
        data_directory_path.mkdir(parents=True, exist_ok=True)

        for key, value in self.__data.items():
            csv_filepath = os.path.join(data_directory, key + "_participant_list.csv")

            if self.__report_fn is not None:
                self.__report_fn(f"Writing to {csv_filepath}")
            else:
                self.__log.info("Writing to %s", csv_filepath)

            with open(csv_filepath, "w", newline="", encoding="utf-8") as file:
                writer: csv.writer = csv.writer(file)
                writer.writerow(self.__official_header)

                for d in value:
                    line: list = self.__build_line(d)
                    writer.writerow(line)

    def __report_completion(self) -> None:
        """
        Handles call to external function.
        """
        # Let calling function know we're done.
        if self.__report_fn is not None:
            self.__report_fn(True)

    def __report_progress(
        self,
        num_new_records: int,
    ) -> None:
        """
        Takes care of logging & external status functions.

        Parameters
        ----------
        num_new_records: int
        """
        self.__progress.increment(num_new_records)
        comment: str = "Success: retrieved %d records. Total records: %d"
        self.__log.info(comment, num_new_records, self.__progress.num_complete())

        if self.__report_fn is not None:
            self.__log.debug("Calling external progress function.")
            self.__report_fn(self.__progress.percent_complete())

    def __request_response(self, next_url: Union[str, None], headers: dict) -> dict:
        """
        Handles the http request, retries, etc.

        Parameters
        ----------
        next_url: URL of request
        headers: list

        Returns
        -------
        ps_data: dict of retrieved data
        """
        num_attempts: int = 0
        ps_data: dict = {}

        resp: requests.Response = requests.get(next_url, headers=headers, timeout=30)

        while True:
            if resp and resp.status_code == 200:
                ps_data = resp.json()
                self.__test_for_bundle(ps_data)
                break

            response_package: ResponsePackage = self.__handle_timeouts(
                resp=resp, num_attempts=num_attempts, next_url=next_url, headers=headers
            )
            resp = response_package.resp
            num_attempts = response_package.num_attempts

        if "total" in ps_data and not self.__progress.is_set():
            self.__progress.set(ps_data["total"])

        return ps_data

    def run(self) -> None:
        """
        Request data from AwardeeInSite API.

        Saves result in internal variable:
        self.data: dict by organization
        """
        # Constants
        num_rows_per_page: int = 1000

        headers: dict = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.__api_package.token}",
        }

        aou_package: AouPackage = self.__api_package.aou_package
        next_url: Union[str, None] = (
            f"{aou_package.endpoint}?_sort=lastModified&_includeTotal=TRUE"
            f"&_count={num_rows_per_page}&awardee={aou_package.awardee}"
        )

        self.__log.debug("next_url: %s", next_url)

        self.__data = {}

        while next_url and not self.__stop_event.is_set():
            ps_data: dict = self.__request_response(next_url, headers)
            self.__report_progress(len(ps_data["entry"]))

            for entry in ps_data["entry"]:
                resource = entry["resource"]
                h = make_header(resource)
                self.__official_header = join_headers(self.__official_header, h)
                self.__extract_organization_data(resource)

            next_url = self.__update_url(ps_data)

        # Let calling function know we're done.
        self.__report_completion()

    def stop(self) -> None:
        """
        Lets calling function tell us to stop.
        """
        self.__log.info("Stop requested")
        self.__stop_event.set()

    def __test_for_bundle(self, ps_data: dict) -> None:
        """
            Tests to ensure dictionary is as expected.

        Parameters
        ----------
        ps_data: dict
        """

        if (
            "resourceType" not in ps_data
            or ps_data["resourceType"] != "Bundle"
            or "entry" not in ps_data
        ):
            self.__log.error("No bundle")

    def __update_url(self, ps_data: dict) -> str:
        """
        Get url of next page from the returned data.

        Parameters
        ----------
        ps_data: dict

        Returns
        -------
        next_url: str
        """
        next_url: Union[str, None] = None

        try:
            next_url_info: dict = ps_data["link"][0]

            if next_url_info["relation"] == "next":
                next_url = next_url_info["url"]

            self.__log.debug("------------------")
            self.__log.debug(next_url)
        except KeyError:
            self.__log.error("Key error")

        return next_url
