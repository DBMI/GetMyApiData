import os
import time
from pathlib import Path
import logging
from my_logging import setup_logging
from mock_ipython import getoutput, system


class GCloudTools:
    """
    Takes care of gcloud authentication, tokens, etc.

    Attributes
    ----------
    no public attributes

    Methods
    -------

    """

    def __init__(
        self,
        pmi_account: str,
        project: str,
        aou_service_account: str,
        token_file: str,
        log_directory: str,
    ):
        """
        Create instance of GCloudTools class.

        Parameters
        ----------
        log: logging.Logger         logging object
        pmi_account : str           pmi account of user
        project : str               project name
        aou_service_account : str   pmi service account
        token_file : str            full path to token file
        log_directory : str         log directory

        Return
        ------
        none; Instantiates object
        """

        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                log_directory,
                "gcloud_tools.log",
            )
        )
        self.__pmi_account: str = pmi_account
        self.__project: str = project
        self.__service_account: str = aou_service_account
        self.__token_file: str = token_file

        # Ensure the path to the token file exists.
        file_path: Path = Path(self.__token_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Automatically prepare key file & activate account.
        self.__auth()
        time.sleep(5)
        self.__create_key_file()
        time.sleep(10)
        self.__activate()

        # Maybe we need to pause after account activation?
        time.sleep(5)

    def __activate(self) -> None:
        """
        Activates the service account.

        Returns
        -------
        none
        """

        self.__log.info("Activating the service account...")

        system(
            f"gcloud -q auth activate-service-account --key-file={self.__token_file}"
        )

    def __auth(self) -> None:
        """
        Uses GCloud to authorize

        Returns
        -------
        results: str        Result of 'gcloud auth login' command.
        """

        self.__log.info("Authorizing...")

        command: str = (
            f"gcloud -q auth application-default login --impersonate-service-account {self.__service_account}"
        )
        results_list: list = getoutput(command)

        if not results_list or len(results_list) < 6:
            self.__log.exception(f"Unable to login.")
            raise RuntimeError(f"Unable to login.")

        results: str = results_list[5]

        if not results.startswith("Credentials saved"):
            self.__log.exception(f"Unable to login: {results}")
            raise RuntimeError(f"Unable to login: {results}")

    def __create_key_file(self) -> None:
        """
        Uses GCloud to create key file.

        Returns
        -------
        results: str        Result of 'gcloud keys create' command.
        """

        self.__log.info("Creating key file...")

        command: str = (
            f"gcloud -q iam service-accounts keys create --account {self.__pmi_account} --project {self.__project} --iam-account {self.__service_account} "
            + self.__token_file
        )
        results_list: list = getoutput(command)
        results: str = results_list[0]

        if not results.startswith("created key"):
            self.__log.exception(f"Unable to create key file: {results}")
            raise RuntimeError(f"Unable to create key file: {results}")

    def get_token(self) -> str:
        """
        Retrieves just the token from the token file.

        Returns
        -------
        token: str
        """
        self.__log.info("Reading key file.")
        token: list = getoutput("gcloud -q auth print-access-token")

        if token:
            token_payload: str = token[0]

            if not token_payload.startswith("ya"):
                self.__log.exception(f"Authentication Token Error: {token_payload}")
                raise RuntimeError(f"Authentication Token Error: {token_payload}")
        else:
            self.__log.exception("Unable to retrieve token.")
            raise RuntimeError("Unable to retrieve token.")

        return token_payload
