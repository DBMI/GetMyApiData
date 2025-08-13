from api_gui import ApiGui
import argparse
import logging
import os
import common
from my_logging import setup_logging
import wx


def get_local_args(parser: argparse.ArgumentParser) -> None:
    pass


if __name__ == "__main__":
    args: argparse.Namespace = common.get_args(get_local_args)
    config_file, config = common.get_config(args)
    log: logging.Logger = setup_logging(
        log_filename=os.path.join(
            config["Logs"]["log_directory"],
            "get_api_data.log",
        )
    )

    app: wx.App = wx.App(redirect=False)

    with ApiGui(config) as gui:
        if gui.ShowModal() == wx.ID_OK:
            print(f"AoU Service Account: {gui.aou_service_account}")
            print(f"PMI Account: {gui.pmi_account}")
            print(f"Project: {gui.project}")
            print(f"Token: {gui.token_file}")
