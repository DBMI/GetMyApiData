import argparse
import logging
import os

import wx.adv

from src.api_gui import ApiGui
from src.common import get_args, get_base_path, get_config
from src.my_logging import setup_logging
from src.splash import MySplashScreen


def get_local_args(parser: argparse.ArgumentParser) -> None:
    pass


if __name__ == "__main__":
    # Display splash screen.
    app: wx.App = wx.App(redirect=False)
    splash = MySplashScreen(
        os.path.join(get_base_path(), "UCSD_school_of_medicine.png")
    )
    splash.Show()
    app.Yield()

    log: logging.Logger = setup_logging(
        log_filename=os.path.join(os.getcwd(), "getmyapidata.log")
    )

    log.info("Getting arguments.")
    args: argparse.Namespace = get_args(get_local_args)
    log.info("Getting config.")
    myconfig = get_config(args)

    # Create the GUI.
    log.info("Instantiating ApiGui object.")
    gui: ApiGui = ApiGui(myconfig)

    try:
        splash.Destroy()
    except RuntimeError:
        pass

    app.MainLoop()
