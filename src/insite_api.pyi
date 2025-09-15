import logging
from collections.abc import Callable as Callable
from typing import Union

def join_headers(h1: list, h2: list) -> list: ...
def make_header(dict1: dict) -> list: ...

class InSiteAPI:
    def __init__(
        self, log_directory: str, progress_fn: Callable = ..., status_fn: Callable = ...
    ) -> None:
        self.__log: logging.Logger = None
        self.__official_header: list = []
        self.__progress_fn: Callable = None
        self.__status_fn: Callable = None
    def output_data(self, data: dict, data_directory: str) -> None: ...
    def request_data(
        self,
        awardee: str,
        endpoint: str,
        token: str,
        max_pages: Union[int, None] = ...,
        num_rows_per_page: Union[int, None] = ...,
    ) -> dict: ...
