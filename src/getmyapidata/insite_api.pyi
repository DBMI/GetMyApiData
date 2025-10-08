import logging
import threading
from collections import namedtuple
from collections.abc import Callable as Callable
from typing import Union

import requests

from src.getmyapidata.progress import Progress

# Fold resp, num_attempts into a named tuple.
ResponsePackage = namedtuple("ResponsePackage", ["resp", "num_attempts"])

def join_headers(h1: list, h2: list) -> list: ...
def make_header(dict1: dict) -> list: ...

class InSiteAPI(threading.Thread):
    def __init__(
        self, api_package: namedtuple, log: logging.Logger, report_fn: Callable
    ) -> None:
        self.__api_package: namedtuple = api_package
        self.__data: dict = {}
        self.__log: logging.Logger = log
        self.__official_header: list = []
        self.__report_fn: Callable = report_fn
        self.__stop_event: threading.Event = threading.Event()
        self.__progress: Progress = None
    def __build_line(self, d: dict) -> list: ...
    def __extract_organization_data(self, resource: dict) -> None: ...
    def __handle_timeouts(
        self,
        resp: requests.Response,
        num_attempts: int,
        next_url: Union[str, None],
        headers: dict,
    ) -> ResponsePackage: ...
    def output_data(self, data_directory: str) -> None: ...
    def __report_completion(self) -> None: ...
    def __report_progress(self, num_new_records: int) -> None: ...
    def __request_response(self, next_url: Union[str, None], headers: dict) -> dict: ...
    def run(self) -> None: ...
    def stop(self) -> None: ...
    def __test_for_bundle(self, ps_data: dict) -> None: ...
    def __update_url(self, ps_data: dict) -> str: ...
