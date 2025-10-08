"""
Contains class GCLoudTools & associated static methods for GCloud authentication.
"""
import logging
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path

from src.getmyapidata.aou_package import AouPackage


def gcloud_tools_installed() -> bool:
    """
    Tests to see if we can make the simplest gcloud call.

    Returns
    -------
    installed: bool         Is gcloud toolkit installed?
    """
    installed: bool = False

    try:
        # Execute the command and display output directly to console
        subprocess.run("gcloud version", shell=True, check=True)
        installed: bool = True
    except subprocess.CalledProcessError:
        print("Gcloud command-line tools are not installed.")

    return installed


def getoutput(cmd: str) -> list[str]:
    """
    Execute a shell command and return the output as a list of strings.

    Parameters
    ----------
    cmd: str

    Returns
    -------
    output: str
    """

    try:
        # Execute the command, capture the output
        output = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT, text=True
        )
        # Split the output into lines and return as a list
        return output.strip().split("\n")
    except subprocess.CalledProcessError as e:
        # Return error output if command execution fails
        return e.output.strip().split("\n")


def system(cmd: str) -> None:
    """
    Execute a shell command, displaying the output directly to the console.

    Parameters
    ----------
    cmd: str

    Returns
    -------
    None
    """

    try:
        # Execute the command and display output directly to console.
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        # Print error message if command execution fails
        print(f"Command failed with return code {e.returncode}")


# pylint: disable=too-few-public-methods)
class GCloudTools(threading.Thread):
    """
    Takes care of gcloud authentication, tokens, etc.

    Attributes
    ----------
    no public attributes

    Methods
    -------
    get_token() -> str
    """

    def __init__(
        self,
        aou_package: AouPackage,
        log: logging.Logger,
        status_fn: Callable = None,
    ):
        """
        Create instance of GCloudTools class.

        Parameters
        ----------
        aou_package : AouPackage
        log: logging.Logger object
        status_fn : callable        Optional external fn to report status

        Return
        ------
        none; Instantiates object
        """

        threading.Thread.__init__(self)
        self.__aou_package: AouPackage = aou_package
        self.__log: logging.Logger = log
        self.__status_fn: Callable = status_fn

        # Ensure the path to the token file exists.
        file_path: Path = Path(self.__aou_package.token_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

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
            f"gcloud -q auth activate-service-account --key-file={self.__aou_package.token_file}"
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

        cmd: str = (
            f"gcloud -q auth application-default login "
            f"--impersonate-service-account {self.__aou_package.aou_service_account}"
        )
        results_list: list[str] = getoutput(cmd)

        if not results_list or len(results_list) < 6:
            if self.__status_fn is not None:
                self.__status_fn("Unable to login...")

            self.__log.exception("Unable to login.")
            raise RuntimeError("Unable to login.")

        results: str = results_list[5]

        if not results.startswith("Credentials saved"):
            if self.__status_fn is not None:
                self.__status_fn(f"Unable to login: {results[0]}")
            self.__log.exception("Unable to login: %s", results[0])
            raise RuntimeError(f"Unable to login: {results[0]}")

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
            f"gcloud -q iam service-accounts keys create "
            f"--account {self.__aou_package.pmi_account} "
            f"--project {self.__aou_package.project} "
            f"--iam-account {self.__aou_package.aou_service_account} "
            f"{self.__aou_package.token_file}"
        )
        results_list: list[str] = getoutput(command)
        results: str = results_list[0]

        if not results.startswith("created key"):
            if self.__status_fn is not None:
                self.__status_fn(f"Unable to create key file: {results}")

            self.__log.exception("Unable to create key file: %s", results)
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

        token: list[str] = getoutput("gcloud -q auth print-access-token")

        if token:
            token_payload: str = token[0]

            if not token_payload.startswith("ya"):
                self.__report_error(f"Authentication Token Error: {token_payload}")
                raise RuntimeError(f"Authentication Token Error: {token_payload}")
        else:
            self.__report_error("Unable to retrieve token from the key file")
            raise RuntimeError("Unable to retrieve token from the key file")

        return token_payload

    def __report_error(self, status: str) -> None:
        """ "
        Wraps the status_fn provided by calling function.

        Parameters
        status: str
        """
        if self.__status_fn is not None:
            self.__status_fn(status)

        self.__log.exception(status)

    def run(self) -> None:
        """
        Handles authentication, activate and key generation in a separate thread.
        """

        # Authenticate, prepare key file & activate account.
        self.__auth()
        time.sleep(5)
        self.__create_key_file()
        time.sleep(10)
        self.__activate()

        # Maybe we need to pause after account activation?
        time.sleep(5)

        # Let calling function know we're done.
        if self.__status_fn is not None:
            self.__status_fn(True)
