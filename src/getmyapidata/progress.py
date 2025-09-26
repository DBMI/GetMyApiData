"""
Contains Progress class, which keeps track of the # of things to do and # completed.
"""
import math


class Progress:
    """
    Keeps track of the # of things to do and # completed.

    Attributes:
    ----------
    no public attributes

    Methods
    -------
    increment(num_performed: int) -> None
    percent_complete() -> int
    """

    def __init__(self):
        """
        Initializes the Progress class.
        """
        self.__num_to_do: int = 0
        self.__num_complete: int = 0
        self.__set: bool = False

    def increment(self, num_performed: int) -> None:
        """
        Increment the progress counter.

        Parameters
        ----------
        num_performed: int

        Returns
        -------
        None
        """
        self.__num_complete += num_performed

    def is_set(self) -> bool:
        """
        Checks if the progress counter has been initialized.

        Returns
        -------
        bool
        """
        return self.__set

    def num_complete(self) -> int:
        """
        Returns the number of things completed so far.

        Returns
        -------
        int
        """
        return self.__num_complete

    def percent_complete(self) -> int:
        """
        Computes the percent complete status.

        Returns
        -------
        pct: int
        """
        pct: int = math.trunc(100 * self.__num_complete / self.__num_to_do)
        return pct

    def set(self, num_to_do: int) -> None:
        """
        Initializes the progress counter.

        Parameters
        ----------
        num_to_do: int

        Returns
        -------
        None
        """
        self.__num_to_do = num_to_do
        self.__set = True
