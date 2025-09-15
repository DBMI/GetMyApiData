from typing import List

class PairedOrganization:
    def __init__(self, organization: str, marker: str) -> None:
        self.__organization: str = None
        self.__marker: str = None
    def marker(self) -> str: ...
    def organization(self) -> str: ...

class PairedOrganizations:
    def __init__(self, my_all: bool, my_list: List[PairedOrganization]) -> None:
        self.__all: bool = None
        self.__list: List[PairedOrganization] = []
    def all_allowed(self) -> bool: ...
    def organizations_list(self) -> List[PairedOrganization]: ...
