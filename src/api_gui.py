import argparse
import logging
import os
import sys
from configparser import ConfigParser
from tkinter import filedialog
from typing import List

import wx
import wx.adv

from src.common import (get_args, get_base_path, get_config, get_exe_version,
                        update_config)
from src.convert_to_hp_format import HealthProConverter
from src.gcloud_tools import GCloudTools, gcloud_tools_installed
from src.insite_api import InSiteAPI
from src.my_logging import setup_logging
from src.paired_organizations import PairedOrganization, PairedOrganizations
from src.splash import MySplashScreen


class ApiGui(wx.Dialog):
    def __init__(self, config: ConfigParser) -> None:
        self.__config: ConfigParser = config

        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                self.__config["Logs"]["log_directory"],
                "api_gui.log",
            )
        )

        self.__log.info("Instantiating Api Gui.")
        wx.Dialog.__init__(
            self,
            parent=None,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            title="Get Awardee InSite API data",
        )

        # Variables we need for data request.
        self.__aou_service_account: str = config["Logon"]["aou_service_account"]
        self.__pmi_account: str = config["Logon"]["pmi_account"]
        self.__project: str = config["Logon"]["project"]
        self.__token_file: str = config["Logon"]["token_file"]

        sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Set up this panel.
        my_panel: wx.Panel = wx.Panel(self)

        # Create sizer.
        grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        # Title
        title_font: wx.Font = wx.Font(
            18,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_NORMAL,
            weight=wx.FONTWEIGHT_BOLD,
        )
        title_text: wx.StaticText = wx.StaticText(
            my_panel,
            id=wx.ID_ANY,
            label="Get Awardee InSite API data: " + config["AoU"]["organization"],
        )
        title_text.SetFont(title_font)
        grid.Add(
            title_text,
            pos=(0, 0),
            span=(1, 2),
            flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        grid.AddGrowableCol(idx=1, proportion=1)

        # PROJECT NAME
        project_label: wx.StaticText = wx.StaticText(
            my_panel, id=wx.ID_ANY, label="Project"
        )
        grid.Add(project_label, pos=(1, 0), flag=wx.ALIGN_RIGHT, border=5)
        self.__project_text: wx.TextCtrl = wx.TextCtrl(
            my_panel, id=wx.ID_ANY, value=self.__project
        )
        self.__project_text.Bind(wx.EVT_TEXT, self.__on_project_text_changed)
        grid.Add(
            self.__project_text, pos=(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT, border=5
        )
        self.__restore_project_button: wx.Button = wx.Button(
            my_panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        self.__restore_project_button.Disable()
        grid.Add(self.__restore_project_button, pos=(1, 2), flag=wx.ALL, border=5)
        self.__restore_project_button.Bind(
            wx.EVT_BUTTON, self.__on_restore_project_button_clicked
        )

        # PMI OPS ACCOUNT
        pmi_account_label: wx.StaticText = wx.StaticText(
            my_panel, id=wx.ID_ANY, label="PMI Account"
        )
        grid.Add(pmi_account_label, pos=(2, 0), flag=wx.ALIGN_RIGHT, border=5)
        self.__pmi_account_text: wx.TextCtrl = wx.TextCtrl(
            my_panel, id=wx.ID_ANY, value=self.__pmi_account
        )
        self.__pmi_account_text.Bind(wx.EVT_TEXT, self.__on_pmi_account_text_changed)
        grid.Add(self.__pmi_account_text, pos=(2, 1), flag=wx.EXPAND | wx.ALL, border=5)
        self.__restore_pmi_account_button: wx.Button = wx.Button(
            my_panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        self.__restore_pmi_account_button.Disable()
        grid.Add(self.__restore_pmi_account_button, pos=(2, 2), flag=wx.ALL, border=5)
        self.__restore_pmi_account_button.Bind(
            wx.EVT_BUTTON, self.__on_restore_pmi_account_button_clicked
        )

        # AOU SERVICE ACCOUNT
        aou_service_account_label: wx.StaticText = wx.StaticText(
            my_panel, id=wx.ID_ANY, label="AoU Service Account"
        )
        grid.Add(aou_service_account_label, pos=(3, 0), flag=wx.ALIGN_RIGHT, border=5)
        self.__aou_service_account_text: wx.TextCtrl = wx.TextCtrl(
            my_panel, id=wx.ID_ANY, value=self.__aou_service_account
        )
        self.__aou_service_account_text.Bind(
            wx.EVT_TEXT, self.__on_aou_service_account_text_changed
        )
        grid.Add(
            self.__aou_service_account_text,
            pos=(3, 1),
            flag=wx.EXPAND | wx.ALL,
            border=5,
        )
        self.__restore_aou_service_account_button: wx.Button = wx.Button(
            my_panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        self.__restore_aou_service_account_button.Disable()
        grid.Add(
            self.__restore_aou_service_account_button, pos=(3, 2), flag=wx.ALL, border=5
        )
        self.__restore_aou_service_account_button.Bind(
            wx.EVT_BUTTON, self.__on_restore_aou_service_account_button_clicked
        )

        # LOCATION OF TOKEN FILE
        token_file_label: wx.StaticText = wx.StaticText(
            my_panel, id=wx.ID_ANY, label="Token File"
        )
        grid.Add(token_file_label, pos=(4, 0), flag=wx.ALIGN_RIGHT, border=5)
        self.__token_file_text: wx.TextCtrl = wx.TextCtrl(
            my_panel, id=wx.ID_ANY, value=self.__token_file
        )
        self.__token_file_text.Bind(wx.EVT_TEXT, self.__on_token_file_text_changed)
        grid.Add(self.__token_file_text, pos=(4, 1), flag=wx.EXPAND | wx.ALL, border=5)
        self.__restore_token_file_button: wx.Button = wx.Button(
            my_panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        self.__restore_token_file_button.Disable()
        grid.Add(self.__restore_token_file_button, pos=(4, 2), flag=wx.ALL, border=5)
        self.__restore_token_file_button.Bind(
            wx.EVT_BUTTON, self.__on_restore_token_file_button_clicked
        )

        # CHECK THAT GCLOUD TOOLS ARE INSTALLED.
        if gcloud_tools_installed():

            # PROGRESS BAR
            self.__gauge = wx.Gauge(my_panel, range=100, size=wx.Size(350, 25))
            grid.Add(
                self.__gauge,
                pos=(5, 0),
                span=(1, 2),
                flag=wx.ALIGN_CENTER | wx.TOP,
                border=5,
            )

            # STATUS BOX
            self.__status_text: wx.StaticText = wx.StaticText(
                my_panel, id=wx.ID_ANY, label="Ready"
            )
            grid.Add(
                self.__status_text,
                pos=(6, 0),
                span=(1, 2),
                flag=wx.EXPAND | wx.ALL,
                border=5,
            )

            # OK BUTTON
            self.__ok_button: wx.Button = wx.Button(
                my_panel, id=wx.ID_ANY, label="Request Data", style=wx.BORDER_SUNKEN
            )
            grid.Add(self.__ok_button, pos=(7, 0), flag=wx.ALL, border=5)
            self.__ok_button.Bind(wx.EVT_BUTTON, self.__on_ok_clicked)
        else:
            link_label = "Must first install GCloud tools"
            link_url = "https://cloud.google.com/sdk/docs/install"
            hyperlink = wx.adv.HyperlinkCtrl(my_panel, -1, link_label, link_url)

            grid.Add(
                hyperlink, pos=(6, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5
            )

        # CANCEL BUTTON
        cancel_button: wx.Button = wx.Button(
            my_panel, id=wx.ID_ANY, label="Cancel", style=wx.BORDER_SUNKEN
        )
        grid.Add(cancel_button, pos=(7, 1), flag=wx.ALL, border=5)
        cancel_button.Bind(wx.EVT_BUTTON, self.__on_cancel_clicked)

        # VERSION INFO
        footnote_font: wx.Font = wx.Font(
            10,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_ITALIC,
            weight=wx.FONTWEIGHT_NORMAL,
        )
        version_text: wx.StaticText = wx.StaticText(
            my_panel, id=wx.ID_ANY, label="Version: " + get_exe_version()
        )
        version_text.SetFont(footnote_font)
        grid.Add(version_text, pos=(7, 2), flag=wx.ALIGN_LEFT, border=5)

        # Connect grid sizer to panel.
        my_panel.SetSizerAndFit(grid)

        # Finish at Frame level.
        sizer.Add(my_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        self.ShowModal()

    def __enable_if_inputs_complete(self) -> None:
        if (
            self.__aou_service_account
            and self.__pmi_account
            and self.__project
            and self.__token_file
        ):
            self.__ok_button.Enable()
        else:
            self.__ok_button.Disable()

    def __get_data(self) -> None:
        self.__set_status("Calling GCloudTools...")
        gcloud_mgr: GCloudTools = GCloudTools(
            project=self.__project,
            pmi_account=self.__pmi_account,
            aou_service_account=self.__aou_service_account,
            token_file=self.__token_file,
            log_directory=self.__config["Logs"]["log_directory"],
            status_fn=self.__set_status,
        )
        self.__set_status("Requesting token...")
        token: str = gcloud_mgr.get_token()

        # Get data from InSiteAPI.
        self.__set_status("Instantiating InSiteAPI object...")
        api_mgr: InSiteAPI = InSiteAPI(
            log_directory=self.__config["Logs"]["log_directory"],
            progress_fn=self.__set_progress,
            status_fn=self.__set_status,
        )
        self.__set_status("Requesting InSiteAPI data...")

        data_combined: dict = api_mgr.request_data(
            awardee=self.__config["AoU"]["awardee"],
            endpoint=self.__config["AoU"]["endpoint"],
            token=token,
        )

        data_directory: str = self.__get_destination_directory()

        # Create .csv output files.
        self.__set_status(f"Saving data to {data_directory}...")
        api_mgr.output_data(
            data_combined=data_combined,
            data_directory=data_directory,
            paired_organizations=self.__get_paired_organizations(),
        )
        self.__set_status(f"Download complete. Results in {data_directory}.")
        self.__set_progress(0)

        # Convert to HealthPro format.
        hp_converter: HealthProConverter = HealthProConverter(
            log_directory=self.__config["Logs"]["log_directory"],
            data_directory=data_directory,
            status_fn=self.__set_status,
        )
        hp_converter.convert()
        self.__set_status("Complete.")

    def __get_destination_directory(self) -> str:
        initial_dir: str

        try:
            initial_dir = self.__config["InSite API"]["data_directory"]
        except KeyError:
            initial_dir = "/"

        # Open the directory selection dialog
        directory_path: str = filedialog.askdirectory(
            title="Select Directory to Save File",
            initialdir=initial_dir,  # Optional: Set an initial directory
        )

        if directory_path:
            self.__config["InSite API"]["data_directory"] = directory_path
            update_config(config=self.__config)

        return directory_path

    def __get_paired_organizations(self) -> PairedOrganizations:
        paired_organizations: List[PairedOrganization] = []
        all_allowed: bool = False

        if self.__config["AoU"]["organization"].upper() == "ALL":
            all_allowed = True
            unpaired_empty_marker: str = (
                "UNSET"  # We're generally interested in Unpaired organizations
            )
            paired_organizations = [
                PairedOrganization(organization="UCSD", marker="CAL_PMC_UCSD"),
                PairedOrganization(organization="SDBB", marker="CAL_PMC_SDBB"),
                PairedOrganization(organization="UCSF", marker="CAL_PMC_UCSF"),
                PairedOrganization(organization="UCD", marker="CAL_PMC_UCD"),
                PairedOrganization(
                    organization="Unpaired", marker=unpaired_empty_marker
                ),
            ]
        else:
            organization: str = self.__config["AoU"]["organization"].upper()
            marker: str = self.__config["AoU"]["awardee"] + "_" + organization
            paired_organizations.append(
                PairedOrganization(organization=organization, marker=marker)
            )

        return PairedOrganizations(all=all_allowed, list=paired_organizations)

    def __on_aou_service_account_text_changed(self, event):
        self.__aou_service_account = self.__aou_service_account_text.GetValue()
        self.__restore_aou_service_account_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_cancel_clicked(self, event) -> None:
        # self.EndModal(wx.ID_CANCEL)
        self.Destroy()
        event.Skip()

    def __on_ok_clicked(self, event) -> None:
        self.__ok_button.Disable()

        # Update config file.
        self.__config["Logon"]["aou_service_account"] = self.__aou_service_account
        self.__config["Logon"]["pmi_account"] = self.__pmi_account
        self.__config["Logon"]["project"] = self.__project
        self.__config["Logon"]["token_file"] = self.__token_file
        update_config(config=self.__config)

        self.__get_data()
        self.__ok_button.Enable()

    def __on_pmi_account_text_changed(self, event) -> None:
        self.__pmi_account = self.__pmi_account_text.GetValue()
        self.__restore_pmi_account_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_project_text_changed(self, event) -> None:
        self.__project = self.__project_text.GetValue()
        self.__restore_project_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_restore_aou_service_account_button_clicked(self, event: wx.Event) -> None:
        self.__aou_service_account_text.SetValue(
            self.__config["Logon"]["aou_service_account"]
        )
        self.__restore_aou_service_account_button.Disable()

    def __on_restore_pmi_account_button_clicked(self, event: wx.Event) -> None:
        self.__pmi_account_text.SetValue(self.__config["Logon"]["pmi_account"])
        self.__restore_pmi_account_button.Disable()

    def __on_restore_project_button_clicked(self, event: wx.Event) -> None:
        self.__project_text.SetValue(self.__config["Logon"]["project"])
        self.__restore_project_button.Disable()

    def __on_restore_token_file_button_clicked(self, event: wx.Event) -> None:
        self.__token_file_text.SetValue(self.__config["Logon"]["token_file"])
        self.__restore_token_file_button.Disable()

    def __on_token_file_text_changed(self, event) -> None:
        self.__token_file = self.__token_file_text.GetValue()
        self.__restore_token_file_button.Enable()
        self.__enable_if_inputs_complete()

    def __set_progress(self, pct: int) -> None:
        self.__gauge.SetValue(pct)
        wx.Yield()

    def __set_status(self, status: str) -> None:
        self.__log.info(status)
        self.__status_text.SetLabel(status)
        wx.Yield()


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
        log_filename=os.path.join(os.getcwd(), "api_gui.log")
    )

    log.info("Getting arguments.")
    args: argparse.Namespace = get_args(get_local_args)
    log.info("Getting config.")
    myconfig = get_config(args)

    # What campus is this?
    org_filename: str = os.path.join(get_base_path(), "organization.txt")

    if os.path.isfile(org_filename):
        with open(org_filename, "r") as f:
            myconfig["AoU"]["organization"] = f.read()
    else:
        myconfig["AoU"]["organization"] = "NOT READ"

    # Create the GUI.
    log.info("Instantiating ApiGui object.")
    gui: ApiGui = ApiGui(myconfig)

    try:
        splash.Destroy()
    except RuntimeError:
        pass

    app.MainLoop()
