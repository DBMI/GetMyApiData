import csv
import logging
import os
import time
from pathlib import Path
from typing import List, Union

import requests

from header_tools import join_headers, make_header
from my_logging import setup_logging
from paired_organizations import PairedOrganization


class InSiteAPI(object):
    """
    An interface with the AwardeeInSite API

    Parameters
    ----------
    self.__log
    self.__official_header


    Methods
    ---------
    output_data()
    request_data()
    """

    def __init__(self, log_directory: str):
        # Logger
        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                log_directory,
                "insite_api.log",
            )
        )

        # Variables developed in request_list() to be used in output_data().
        self.__official_header: list = []

    def output_data(
        self,
        data_combined: dict,
        data_directory: str,
        paired_organizations: List[PairedOrganization],
    ) -> None:
        """
        Produces .csv files from extracted data.

        Parameters
        ----------
        data_combined: dict                             Dict of dicts:
                                                        'by organization'   Organized by organization name
                                                        'all'               Everything
        data_directory: str                             Where do you want the files to be created?
        paired_organizations: List[PairedOrganization]

        Returns
        -------
        None
        """

        # Separate the two dicts in 'data':
        if "by organization" not in data_combined:
            self.__log.error(
                "Not finding 'by organization' in the 'data_combined' dict."
            )
            raise RuntimeError(
                "Not finding 'by organization' in the 'data_combined' dict."
            )

        data: dict = data_combined["by organization"]

        if "all" not in data_combined:
            self.__log.error("Not finding 'all' in the 'data_combined' dict.")
            raise RuntimeError("Not finding 'all' in the 'data_combined' dict.")

        everything: dict = data_combined["all"]

        self.__official_header.sort()

        # Ensure the path to the data directory exists.
        data_directory_path: Path = Path(data_directory)
        data_directory_path.mkdir(parents=True, exist_ok=True)

        csv_export_headers = map_api_to_csv_export_headers(self.__official_header)

        for po in paired_organizations:
            csv_filepath = os.path.join(
                data_directory, r"workqueue_" + po.organization + ".csv"
            )
            self.__log.info(f"Writing to {csv_filepath}")

            with open(csv_filepath, "w", newline="", encoding="utf-8") as file:
                writer: csv.writer = csv.writer(file)
                writer.writerow(self.__official_header)
                writer.writerow(csv_export_headers)

                if po.marker not in data:
                    self.__log.info("No data for " + po.marker)
                    continue

                for d in data[po.marker]:
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

        csv_filepath = os.path.join(data_directory, "everything.csv")
        self.__log.info(f"Writing to {csv_filepath}")

        with open(csv_filepath, "w", newline="", encoding="utf-8") as file:
            writer: csv.writer = csv.writer(file)
            writer.writerow(self.__official_header)
            writer.writerow(csv_export_headers)

            for d in everything:
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
    ) -> dict:
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
        data: dict                  Organized by organization name
        """
        headers = {
            "content-type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        }

        data: dict = dict()
        everything: list = []

        next_url: Union[
            str, None
        ] = f"{endpoint}?_sort=lastModified&_count={num_rows_per_page}&awardee={awardee}"
        total_records: int = 0

        while next_url:
            if max_pages is not None:
                max_pages -= 1

            if max_pages is not None and max_pages < 0:
                break

            num_attempts: int = 0
            resp: requests.Response = requests.get(next_url, headers=headers)

            while True:
                if resp and resp.status_code == 200:
                    break
                elif resp and resp.status_code == 500:
                    # Server error. Pause & try again.
                    num_attempts += 1
                    self.__log.error(
                        f"Server error: {resp.status_code}. Have made {num_attempts} attempts."
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
                            f"Server error: {resp.status_code}. Have made {num_attempts} attempts. Exiting."
                        )
                else:
                    self.__log.error(
                        "Error: api request failed.\n\n{0}.".format(
                            resp.text if resp else "Unknown error"
                        )
                    )
                    self.__log.error(resp.status_code)
                    raise RuntimeError(f"Server error: {resp.status_code}. Exiting.")

            ps_data: dict = resp.json()

            if (
                "resourceType" not in ps_data
                or ps_data["resourceType"] != "Bundle"
                or "entry" not in ps_data
            ):
                self.__log.error("No bundle")

            num_new_records: int = len(ps_data["entry"])
            total_records += num_new_records
            self.__log.info(
                f"Success: retrieved {num_new_records} records.  Total records: {total_records}"
            )

            next_url = None

            for entry in ps_data["entry"]:
                resource = entry["resource"]
                h = make_header(resource)
                self.__official_header = join_headers(self.__official_header, h)
                organization = resource["organization"]

                if organization is None or organization.strip() == "":
                    organization = "Unpaired"

                if organization not in data:
                    data[organization] = []

                data[organization].append(resource)
                everything.append(resource)

            try:
                next_url_info: dict = ps_data["link"][0]

                if next_url_info["relation"] == "next":
                    next_url = next_url_info["url"]

                self.__log.info("------------------")
                self.__log.info(next_url)
            except KeyError:
                self.__log.error("Key error")
                pass

        return {"by organization": data, "all": everything}
