import logging
from collections.abc import Callable
from typing import Any, Optional

class StringConverter(dict):
    def __contains__(self, item: Any): ...
    def __getitem__(self, item: Any): ...
    def get(self, default: Optional[Any] = ...): ...

class HealthProConverter:
    def __init__(
        self, log_directory: str, data_directory: str, status_fn: Callable
    ) -> None:
        self.__log: logging.Logger = None
        self.__directory: str = None
        self.__status_fn: Callable = None
    def convert(self) -> None: ...
    def __convert_file(self, source_filename: str, target_filename: str) -> None: ...
