"""
Contains InSiteAPI class.
"""
import csv
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Union

import requests

from src.getmyapidata.aou_package import AouPackage
from src.getmyapidata.my_logging import \
    setup_logging  # pylint: disable=import-error
from src.getmyapidata.progress import Progress


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


class InSiteAPI:
    """
    An interface with the AwardeeInSite API

    Parameters
    ----------
    self.__log
    self.__official_header
    self.__progress_fn
    self.__status_fn

    Methods
    ---------
    output_data()
    request_data()
    """

    def __init__(
        self,
        log_directory: str,
        progress_fn: Callable = None,
        status_fn: Callable = None,
        log_level: Union[int, str] = "INFO",
    ):
        """Instantiate an InSiteAPI object.

        Parameters
        ----------
        log_directory: str
        progress_fn: Callable
        status_fn: Callable
        """
        # Logger
        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                log_directory,
                "insite_api.log",
            )
        )
        self.__log.setLevel(log_level)

        # Variables developed in request_list() to be used in output_data().
        self.__official_header: list = []

        # We can use these to report to calling function how & what we're doing.
        self.__progress_fn: Callable = progress_fn
        self.__status_fn: Callable = status_fn

        # Status
        self.__progress: Progress = Progress()

    def output_data(self, data: dict, data_directory: str) -> None:
        """
        Produces .csv files from extracted data.

        Parameters
        ----------
        data: dict
        data_directory: str                             Where do you want the files to be created?

        Returns
        -------
        None
        """

        self.__official_header.sort()

        # Ensure the path to the data directory exists.
        data_directory_path: Path = Path(data_directory)
        data_directory_path.mkdir(parents=True, exist_ok=True)

        for organization in data.keys():
            csv_filepath = os.path.join(
                data_directory, organization + "_participant_list.csv"
            )

            if self.__status_fn is not None:
                self.__status_fn(f"Writing to {csv_filepath}")
            else:
                self.__log.info("Writing to %s", csv_filepath)

            with open(csv_filepath, "w", newline="", encoding="utf-8") as file:
                writer: csv.writer = csv.writer(file)
                writer.writerow(self.__official_header)

                for d in data[organization]:
                    line = []

                    for h in self.__official_header:
                        try:
                            if d[h] != "UNSET":
                                line.append(d[h])
                            else:
                                line.append("")
                        except KeyError:
                            line.append("")

                    writer.writerow(line)

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
        self.__log.info(
            (
                "Success: retrieved %d records. Total records: %d",
                num_new_records,
                self.__progress.num_complete(),
            )
        )

        if self.__progress_fn is not None:
            self.__progress_fn(self.__progress.percent_complete())

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
            status_code: str = str(resp.status_code) if resp else "Unknown status"

            if resp and resp.status_code == 200:
                ps_data = resp.json()

                if (
                    "resourceType" not in ps_data
                    or ps_data["resourceType"] != "Bundle"
                    or "entry" not in ps_data
                ):
                    self.__log.error("No bundle")

                break

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
                    resp: requests.Response = requests.get(
                        next_url, headers=headers, timeout=60
                    )
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

        return ps_data

    def request_data(
        self,
        aou_package: AouPackage,
        token: str,
        max_pages: Union[int, None] = None,
        num_rows_per_page: Union[int, None] = 1000,
    ) -> list:
        """
        Request list from AwardeeInSite API.

        Parameters
        ----------
        aou_package: AouPackage     Contains the token file name, awardee & endpoint info
        token: str
        num_rows_per_page: int      Optional (default: 1000)
        max_pages: int              Optional (default: None)

        Returns
        -------
        data: dict by organization
        """
        headers: dict = {
            "content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        data: dict = {}

        next_url: Union[str, None] = (
            f"{aou_package.endpoint}?_sort=lastModified&_includeTotal=TRUE"
            f"&_count={num_rows_per_page}&awardee={aou_package.awardee}"
        )
        self.__log.debug("next_url: %s", next_url)

        while next_url:
            if max_pages is not None:
                self.__log.debug("Max pages set = -1")
                max_pages -= 1

            if max_pages is not None and max_pages < 0:
                self.__log.debug("Max pages set to %d.", max_pages)
                break

            ps_data: dict = self.__request_response(next_url, headers)

            if "total" in ps_data and not self.__progress.is_set():
                self.__progress.set(ps_data["total"])

            self.__report_progress(len(ps_data["entry"]))
            next_url = None

            for entry in ps_data["entry"]:
                resource = entry["resource"]
                h = make_header(resource)
                self.__official_header = join_headers(self.__official_header, h)

                if "organization" in resource:
                    organization: str = resource["organization"]

                    if organization is None or organization.strip() == "":
                        organization = "Unpaired"

                    if organization not in data:
                        data[organization] = []
                    else:
                        data[organization].append(resource)

            try:
                next_url_info: dict = ps_data["link"][0]

                if next_url_info["relation"] == "next":
                    next_url = next_url_info["url"]

                self.__log.debug("------------------")
                self.__log.debug(next_url)
            except KeyError:
                self.__log.error("Key error")

        return data
