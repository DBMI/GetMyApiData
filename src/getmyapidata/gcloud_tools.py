import logging
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from my_logging import setup_logging


def gcloud_tools_installed() -> bool:
    installed: bool = False

    try:
        # Execute the command and display output directly to console
        subprocess.run("gcloud version", shell=True, check=True)
        installed: bool = True
    except subprocess.CalledProcessError as e:
        print("Gcloud command-line tools are not installed.")

    return installed


def getoutput(command) -> list[str]:
    """Execute a shell command and return the output as a list of strings."""
    try:
        # Execute the command, capture the output
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        # Split the output into lines and return as a list
        return output.strip().split("\n")
    except subprocess.CalledProcessError as e:
        # Return error output if command execution fails
        return e.output.strip().split("\n")


def system(command) -> None:
    """Execute a shell command, displaying the output directly to the console."""
    try:
        # Execute the command and display output directly to console
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        # Print error message if command execution fails
        print(f"Command failed with return code {e.returncode}")


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
        status_fn: Callable = None,
    ):
        """
        Create instance of GCloudTools class.

        Parameters
        ----------
        pmi_account : str           pmi account of user
        project : str               project name
        aou_service_account : str   pmi service account
        token_file : str            full path to token file
        log_directory : str         log directory
        status_fn : callable        Optional external fn to report status
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
        self.__status_fn: Callable = status_fn

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
        if self.__status_fn is not None:
            self.__status_fn("Activating the service account...")
        else:
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

        if self.__status_fn is not None:
            self.__status_fn("Authorizing via GCloud...")
        else:
            self.__log.info("Authorizing via GCloud...")

        command: str = f"gcloud -q auth application-default login --impersonate-service-account {self.__service_account}"
        results_list: list = getoutput(command)

        if not results_list or len(results_list) < 6:
            if self.__status_fn is not None:
                self.__status_fn("Unable to login...")

            self.__log.exception("Unable to login.")
            raise RuntimeError("Unable to login.")

        results: str = results_list[5]

        if not results.startswith("Credentials saved"):
            if self.__status_fn is not None:
                self.__status_fn(f"Unable to login: {results}")
            self.__log.exception(f"Unable to login: {results}")
            raise RuntimeError(f"Unable to login: {results}")

    def __create_key_file(self) -> None:
        """
        Uses GCloud to create key file.

        Returns
        -------
        results: str        Result of 'gcloud keys create' command.
        """

        if self.__status_fn is not None:
            self.__status_fn("Creating key file...")
        else:
            self.__log.info("Creating key file...")

        command: str = (
            f"gcloud -q iam service-accounts keys create --account {self.__pmi_account} --project {self.__project} --iam-account {self.__service_account} "
            + self.__token_file
        )
        results_list: list = getoutput(command)
        results: str = results_list[0]

        if not results.startswith("created key"):
            if self.__status_fn is not None:
                self.__status_fn(f"Unable to create key file: {results}")

            self.__log.exception(f"Unable to create key file: {results}")
            raise RuntimeError(f"Unable to create key file: {results}")

    def get_token(self) -> str:
        """
        Retrieves just the token from the token file.

        Returns
        -------
        token: str
        """
        if self.__status_fn is not None:
            self.__status_fn("Reading key file...")
        else:
            self.__log.info("Reading key file...")

        token: list = getoutput("gcloud -q auth print-access-token")

        if token:
            token_payload: str = token[0]

            if not token_payload.startswith("ya"):
                if self.__status_fn is not None:
                    self.__status_fn(f"Authentication Token Error: {token_payload}")

                self.__log.exception(f"Authentication Token Error: {token_payload}")
                raise RuntimeError(f"Authentication Token Error: {token_payload}")
        else:
            if self.__status_fn is not None:
                self.__status_fn("Unable to retrieve token.")

            self.__log.exception("Unable to retrieve token.")
            raise RuntimeError("Unable to retrieve token.")

        return token_payload
