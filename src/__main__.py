import argparse
import logging
import os

import wx.adv

from src.api_gui import ApiGui
from src.common import get_args, get_config, resource_path
from src.my_logging import setup_logging
from src.splash import MySplashScreen


def get_local_args(parser: argparse.ArgumentParser) -> None:
    pass


if __name__ == "__main__":

    log: logging.Logger = setup_logging(
        log_filename=os.path.join(os.getcwd(), "getmyapidata.log")
    )

    # Display splash screen.
    app: wx.App = wx.App(redirect=False)
    splash_path: str = resource_path("UCSD_school_of_medicine.png")
    log.info(f"Splash path: {splash_path}")
    splash = MySplashScreen(splash_path)
    splash.Show()
    app.Yield()

    log.info("Getting arguments.")
    args: argparse.Namespace = get_args(get_local_args)
    log.info("Getting config.")
    myconfig = get_config(args, log)

    # Create the GUI.
    log.info("Instantiating ApiGui object.")
    gui: ApiGui = ApiGui(myconfig)

    try:
        splash.Destroy()
    except RuntimeError:
        pass

    app.MainLoop()
