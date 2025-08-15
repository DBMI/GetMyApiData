import argparse
import logging
import os
from typing import List

import wx

import common
from api_gui import ApiGui
from gcloud_tools import GCloudTools
from insite_api import InSiteAPI
from my_logging import setup_logging
from paired_organizations import PairedOrganization


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

    unpaired_empty_marker = (
        "UNSET"  # We're generally interested in Unpaired organizations
    )
    # These normally show up as blanks for the 'organization' field.

    paired_organizations: List[PairedOrganization] = [
        PairedOrganization(organization="UCSD", marker="CAL_PMC_UCSD"),
        PairedOrganization(organization="SDBB", marker="CAL_PMC_SDBB"),
        PairedOrganization(organization="UCSF", marker="CAL_PMC_UCSF"),
        PairedOrganization(organization="UCD", marker="CAL_PMC_UCD"),
        PairedOrganization(organization="Unpaired", marker=unpaired_empty_marker),
    ]

    app: wx.App = wx.App(redirect=False)

    with ApiGui(config) as gui:
        if gui.ShowModal() == wx.ID_OK:
            log.info("GUI returned setup data.")
            log.debug(f"AoU Service Account: {gui.aou_service_account}")
            log.debug(f"PMI Account: {gui.pmi_account}")
            log.debug(f"Project: {gui.project}")
            log.debug(f"Token: {gui.token_file}")

            gcloud_mgr: GCloudTools = GCloudTools(
                project=gui.project,
                pmi_account=gui.pmi_account,
                aou_service_account=gui.service_account,
                token_file=gui.token_file,
                log_directory=config["Logs"]["log_directory"],
            )
            token: str = gcloud_mgr.get_token()

            # Get data from InSiteAPI.
            api_mgr: InSiteAPI = InSiteAPI(
                log_directory=config["Build"]["log_directory"]
            )
            data_combined: dict = api_mgr.request_data(
                awardee=config["AoU"]["awardee"],
                endpoint=config["AoU"]["endpoint"],
                token=token,
            )

            # Create .csv output files.
            api_mgr.output_data(
                data_combined=data_combined,
                data_directory=config["InSite API"]["data_directory"],
                paired_organizations=paired_organizations,
            )

        else:
            log.info("User cancelled.")
