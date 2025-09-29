import logging
from collections.abc import Callable as Callable
from typing import Union

from aou_package import AouPackage

from src.getmyapidata.progress import Progress

def join_headers(h1: list, h2: list) -> list: ...
def make_header(dict1: dict) -> list: ...

class InSiteAPI:
    def __init__(
        self,
        log: logging.Logger = ...,
        progress_fn: Callable = ...,
        status_fn: Callable = ...,
    ) -> None:
        self.__log: logging.Logger = None
        self.__official_header: list = []
        self.__progress_fn: Callable = None
        self.__status_fn: Callable = None
        self.__progress: Progress = None
    def output_data(self, data: dict, data_directory: str) -> None: ...
    def __report_progress(self, num_new_records: int) -> None: ...
    def __request_response(self, next_url: Union[str, None], headers: dict) -> dict: ...
    def request_data(
        self,
        aou_package: AouPackage,
        token: str,
        max_pages: Union[int, None] = ...,
        num_rows_per_page: Union[int, None] = ...,
    ) -> dict: ...
