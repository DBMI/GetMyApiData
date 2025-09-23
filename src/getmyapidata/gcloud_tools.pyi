import logging
from collections.abc import Callable as Callable
from typing import Any, Union

def gcloud_tools_installed() -> bool: ...
def getoutput(command: Any) -> list[str]: ...
def system(command: Any) -> None: ...

class GCloudTools:
    def __init__(
        self,
        pmi_account: str,
        project: str,
        aou_service_account: str,
        token_file: str,
        log_directory: str,
        log_level: Union[int, str] = "INFO",
        status_fn: Callable = ...,
    ) -> None:
        self.__log: logging.Logger = None
        self.__pmi_account: str = None
        self.__project: str = None
        self.__service_account: str = None
        self.__token_file: str = None
        self.__status_fn: Callable = None
    def __activate(self) -> None: ...
    def __auth(self) -> None: ...
    def __create_key_file(self) -> None: ...
    def get_token(self) -> str: ...
