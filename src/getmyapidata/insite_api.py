import csv
import logging
import math
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import List, Union

import requests

from my_logging import setup_logging


def join_headers(h1: list, h2: list) -> list:
    if h1 is None:
        if h2 is None:
            return []
        else:
            return h2
    if h2 is None:
        return h1

    set1 = set(h1)
    set2 = set(h2)
    combined = set1 | set2
    return list(combined)


def make_header(dict1: dict) -> list:
    ret = []

    for key in dict1.keys():
        ret.append(key)

    return ret


class InSiteAPI(object):
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

        # Variables developed in request_list() to be used in output_data().
        self.__official_header: list = []

        # We can use these to report to calling function how & what we're doing.
        self.__progress_fn: Callable = progress_fn
        self.__status_fn: Callable = status_fn

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
            self.__log.info(f"Writing to {csv_filepath}")

            if self.__status_fn is not None:
                self.__status_fn(f"Writing to {csv_filepath}")

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

    def request_data(
        self,
        awardee: str,
        endpoint: str,
        token: str,
        max_pages: Union[int, None] = None,
        num_rows_per_page: Union[int, None] = 1000,
    ) -> list:
        """
        Request list from AwardeeInSite API.

        Parameters
        ----------
        awardee: str
        endpoint: str
        token: str
        num_rows_per_page: int      Optional (default: 1000)
        max_pages: int              Optional (default: None)

        Returns
        -------
        data: dict by organization
        """
        headers: dict = {
            "content-type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        }

        data: dict = {}

        next_url: Union[
            str, None
        ] = f"{endpoint}?_sort=lastModified&_includeTotal=TRUE&_count={num_rows_per_page}&awardee={awardee}"
        total_records: int = 0
        total_available_records: int = 65000

        while next_url:
            if max_pages is not None:
                max_pages -= 1

            if max_pages is not None and max_pages < 0:
                break

            num_attempts: int = 0
            resp: requests.Response = requests.get(next_url, headers=headers)

            while True:
                status_code: str = str(resp.status_code) if resp else "Unknown status"

                if resp and resp.status_code == 200:
                    break
                elif not resp or resp.status_code == 500:
                    # Server error. Pause & try again.
                    num_attempts += 1
                    self.__log.error(
                        f"Server error: {status_code}. Have made {num_attempts} attempts."
                    )

                    if num_attempts < 2:
                        self.__log.error(f"Pausing for another try.")
                        time.sleep(30)
                        resp: requests.Response = requests.get(
                            next_url, headers=headers
                        )
                    else:
                        self.__log.error(f"Exiting.")
                        raise RuntimeError(
                            f"Server error: {status_code}. Have made {num_attempts} attempts. Exiting."
                        )
                else:
                    self.__log.error(
                        "Error: api request failed.\n\n{0}.".format(
                            resp.text if resp else "Unknown error"
                        )
                    )
                    self.__log.error(status_code)
                    raise RuntimeError(f"Server error: {status_code}. Exiting.")

            ps_data: dict = resp.json()

            if (
                "resourceType" not in ps_data
                or ps_data["resourceType"] != "Bundle"
                or "entry" not in ps_data
            ):
                self.__log.error("No bundle")

            if "total" in ps_data:
                total_available_records = ps_data["total"]

            num_new_records: int = len(ps_data["entry"])
            total_records += num_new_records
            self.__log.info(
                f"Success: retrieved {num_new_records} records.  Total records: {total_records}"
            )

            if self.__progress_fn is not None:
                self.__progress_fn(
                    math.trunc(100 * total_records / total_available_records)
                )

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

                self.__log.info("------------------")
                self.__log.info(next_url)
            except KeyError:
                self.__log.error("Key error")
                pass

        return data
