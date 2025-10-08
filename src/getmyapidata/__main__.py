"""
Main routine--creates API GUI.
"""
import argparse
import logging
import os

import wx.adv

from src.getmyapidata.api_gui import ApiGui
from src.getmyapidata.common import resource_path
from src.getmyapidata.my_logging import setup_logging
from src.getmyapidata.splash import MySplashScreen

if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="A GUI-based tool to retrieve All of Us participant data using the InSite API."
    )
    parser.add_argument(
        "--log-level", type=str, help="INFO, DEBUG, etc.", default="INFO"
    )

    log: logging.Logger = setup_logging(
        log_filename=os.path.join(os.getcwd(), "getmyapidata.log")
    )

    args = parser.parse_args()

    if args.log_level and args.log_level in [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]:
        log.setLevel(args.log_level)

    # Display splash screen.
    app: wx.App = wx.App(redirect=False)
    splash = MySplashScreen(resource_path("UCSD_school_of_medicine.png"))
    splash.Show()
    app.Yield()

    # Create the GUI.
    log.info("Instantiating ApiGui object.")
    gui: ApiGui = ApiGui(log)

    try:
        splash.Destroy()
    except RuntimeError:
        pass

    app.MainLoop()
