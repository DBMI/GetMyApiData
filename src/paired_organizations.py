from typing import List


class PairedOrganization:
    """
    Links an organization's name (like "UCSD") with its marker ("CAL_PMC_UCSD").
    """

    def __init__(self, organization: str, marker: str):
        """
        Links an organization's name with its marker.
        """

        self.__organization = organization
        self.__marker = marker

    def marker(self) -> str:
        return self.__marker

    def organization(self) -> str:
        return self.__organization


class PairedOrganizations:
    """
    Wrapper for a list of PairedOrganization objects.
    """

    def __init__(self, my_all: bool, my_list: List[PairedOrganization]) -> None:
        self.__all: bool = my_all
        self.__list: List[PairedOrganization] = my_list

    def all_allowed(self) -> bool:
        return self.__all

    def organizations_list(self) -> List[PairedOrganization]:
        return self.__list
