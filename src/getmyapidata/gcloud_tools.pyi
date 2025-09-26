import logging
from collections.abc import Callable as Callable
from typing import Union

from src.getmyapidata.aou_package import AouPackage

def gcloud_tools_installed() -> bool: ...
def getoutput(command: str) -> list[str]: ...
def system(command: str) -> None: ...

class GCloudTools:
    def __init__(
        self,
        aou_package: AouPackage,
        log_level: Union[int, str] = "INFO",
        status_fn: Callable = ...,
    ) -> None:
        self.__log: logging.Logger = None
        self.__aou_package: AouPackage = None
        self.__status_fn: Callable = None
    def __activate(self) -> None: ...
    def __auth(self) -> None: ...
    def __create_key_file(self) -> None: ...
    def get_token(self) -> str: ...
