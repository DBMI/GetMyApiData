"""
Contains the AouPackage class,
    which packages up all the variables needed to request participant data.
"""
import logging
import os
from configparser import ConfigParser, ExtendedInterpolation

from src.getmyapidata.common import \
    ensure_path_possible  # pylint: disable=import-error

# String we insert into config file & GUI entries.
DUMMY: str = "<YourNameHere>"


def get_config(log: logging.Logger, config_file: str = None) -> ConfigParser:
    """
    Reads config file.

    Parameters
    ----------
    log: logging.Logger object
    config_file: str                    Optional

    Returns
    -------
    config parser object
    """

    if not config_file:
        config_file = get_default_ini_path()

    log.info(f"Reading config from {config_file}.")

    if not (os.path.exists(config_file) and os.path.isfile(config_file)):
        log.info(f"Config file {config_file} not found.")
        make_config(config_file, log)

    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_file)
    return config


def get_default_ini_path() -> str:
    """
    Where to look for config file.

    Returns
    -------
    default_path: str
    """
    return str(os.path.join(os.getcwd(), "config.ini"))


def make_config(config_file: str, log: logging.Logger) -> None:
    """
    Initializes config file with default values.

    Parameters
    ----------
    config_file: str        Full path to config.ini file
    log

    Returns
    -------
    None
    """
    cwd: str = os.getcwd()
    config: ConfigParser = ConfigParser()
    config["AoU"] = {
        "awardee": DUMMY,
        "endpoint": r"https://rdr-api.pmi-ops.org/rdr/v1/AwardeeInSite",
    }
    config["InSite API"] = {
        "data_directory": cwd,
    }
    config["Logon"] = {
        "aou_service_account": r"awardee-"
        + DUMMY
        + r"@all-of-us-ops-data-api-prod.iam.gservice"
        r"account.com",
        "pmi_account": DUMMY + "@pmi-ops.org",
        "project": "all-of-us-ops-data-api-prod",
        "token_file": os.path.join(cwd, "key.json"),
    }
    config["Logs"] = {"log_directory": cwd}

    with open(config_file, "w", encoding="utf-8") as configfile:
        log.info(f"Writing config to file {config_file}.")
        config.write(configfile)


# pylint: disable=too-many-instance-attributes
class AouPackage:
    """
    Contains variables needed to request participant data.
    """

    def __init__(self, log: logging.Logger, config_file: str = "") -> None:
        """
        Initializes the AouPackage class.

        Parameters
        ----------
        log: logging.Logger
        config_file: str        Optional
        """

        self.__log: logging.Logger = log
        self.__log.info("Instantiating AoU Package object.")

        # Either read or create a config file.
        self.__config: ConfigParser = get_config(self.__log, config_file)

        # Variables we need for data request.
        self.aou_service_account: str = self.__config["Logon"]["aou_service_account"]
        self.awardee: str = self.__config["AoU"]["awardee"]
        self.data_directory: str = self.__config["InSite API"]["data_directory"]
        self.endpoint: str = self.__config["AoU"]["endpoint"]
        self.pmi_account: str = self.__config["Logon"]["pmi_account"]
        self.project: str = self.__config["Logon"]["project"]
        self.token_file: str = self.__config["Logon"]["token_file"]

    def inputs_complete(self) -> bool:
        """
        Checks to see if all inputs are complete.

        Returns
        -------
        bool
        """
        return (
            self.__input_ok(self.aou_service_account)
            and self.__input_ok(self.pmi_account)
            and self.__input_ok(self.project)
            and self.__input_ok(self.token_file)
            and ensure_path_possible(self.token_file, self.__log)
        )

    def __input_ok(self, input_value: str) -> bool:
        """
        Performs basic checks:
            - is the input_value null
            - is it just whitespace?
            = does it contain the dummy value <YourNameHere>?

        Parameters
        ----------
        input_value: str

        Returns
        -------
        ok: bool
        """
        if input_value:
            self.__log.debug("Input not null: %s", input_value)
        else:
            self.__log.debug("Input is null.")

        if DUMMY in input_value:
            self.__log.debug("Input has dummy value: %s", input_value)
        else:
            self.__log.debug("Input does not contain dummy: %s", input_value)

        return input_value and not DUMMY in input_value

    def restore_aou_service_account(self) -> str:
        """
        Lets external class pull the config file value of AoU service account property.

        Returns
        -------
        str
        """
        self.aou_service_account = self.__config["Logon"]["aou_service_account"]
        return self.aou_service_account

    def restore_awardee(self) -> str:
        """
        Lets external class pull the config file value of AoU awardee property.

        Returns
        -------
        str
        """
        self.awardee = self.__config["AoU"]["awardee"]
        return self.awardee

    def restore_endpoint(self) -> str:
        """
        Lets external class pull the config file value of endpoint property.

        Returns
        -------
        str
        """
        self.endpoint = self.__config["AoU"]["endpoint"]
        return self.endpoint

    def restore_pmi_account(self) -> str:
        """
        Lets external class pull the config file value of PMI account name property.

        Returns
        -------
        str
        """
        self.pmi_account = self.__config["Logon"]["pmi_account"]
        return self.pmi_account

    def restore_project(self) -> str:
        """
        Lets external class pull the config file value of project name property.

        Returns
        -------
        str
        """
        self.project = self.__config["Logon"]["project"]
        return self.project

    def restore_token_file(self) -> str:
        """
        Lets external class pull the config file value of token file property.

        Returns
        -------
        str
        """
        self.token_file = self.__config["Logon"]["token_file"]
        return self.token_file

    def update_config(self) -> None:
        """
        Writes current property values to the config file.

        Returns
        -------
        None
        """

        # Update config file.
        self.__config["Logon"]["aou_service_account"] = self.aou_service_account
        self.__config["AoU"]["awardee"] = self.awardee
        self.__config["InSite API"]["data_directory"] = self.data_directory
        self.__config["Logon"]["pmi_account"] = self.pmi_account
        self.__config["Logon"]["project"] = self.project
        self.__config["Logon"]["token_file"] = self.token_file

        with open(get_default_ini_path(), "w", encoding="utf-8") as configfile:
            self.__config.write(configfile)
