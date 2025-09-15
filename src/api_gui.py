import argparse
import logging
import os
from collections.abc import Callable
from configparser import ConfigParser
from tkinter import filedialog

import wx
import wx.adv

from src.common import (get_args, get_base_path, get_config, get_exe_version,
                        update_config)
from src.convert_to_hp_format import HealthProConverter
from src.gcloud_tools import GCloudTools, gcloud_tools_installed
from src.insite_api import InSiteAPI
from src.my_logging import setup_logging
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
            title="Get InSite API data",
        )

        # Dictionaries of controls linking text controls with their restore buttons.
        self.__buttons_and_text_boxes: dict = {}
        self.__text_boxes_and_buttons: dict = {}

        # Variables we need for data request.
        self.__aou_service_account: str = config["Logon"]["aou_service_account"]
        self.__awardee: str = config["AoU"]["awardee"]
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
            label="Get InSite API data",
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

        # AWARDEE
        self.__add_controls(
            1,
            my_panel,
            grid,
            "Awardee",
            self.__awardee,
            self.__on_awardee_text_changed,
            self.__on_restore_awardee_button_clicked,
        )

        # PROJECT NAME
        self.__add_controls(
            2,
            my_panel,
            grid,
            "Project",
            self.__project,
            self.__on_project_text_changed,
            self.__on_restore_project_button_clicked,
        )

        # PMI OPS ACCOUNT
        self.__add_controls(
            3,
            my_panel,
            grid,
            "PMI Account",
            self.__pmi_account,
            self.__on_pmi_account_text_changed,
            self.__on_restore_pmi_account_button_clicked,
        )

        # AOU SERVICE ACCOUNT
        self.__add_controls(
            4,
            my_panel,
            grid,
            "AoU Service Account",
            self.__aou_service_account,
            self.__on_aou_service_account_text_changed,
            self.__on_restore_aou_service_account_button_clicked,
        )

        # LOCATION OF TOKEN FILE
        self.__add_controls(
            5,
            my_panel,
            grid,
            "Token File",
            self.__token_file,
            self.__on_token_file_text_changed,
            self.__on_restore_token_file_button_clicked,
        )

        # CHECK THAT GCLOUD TOOLS ARE INSTALLED.
        if gcloud_tools_installed():

            # PROGRESS BAR
            self.__gauge = wx.Gauge(my_panel, range=100, size=wx.Size(350, 25))
            grid.Add(
                self.__gauge,
                pos=(6, 1),
                flag=wx.EXPAND | wx.ALL,
                border=5,
            )

            # STATUS BOX
            self.__status_text: wx.StaticText = wx.StaticText(
                my_panel, id=wx.ID_ANY, label="Ready"
            )
            grid.Add(
                self.__status_text,
                pos=(7, 1),
                span=(1, 2),
                flag=wx.EXPAND | wx.ALL,
                border=5,
            )

            # OK BUTTON
            self.__ok_button: wx.Button = wx.Button(
                my_panel, id=wx.ID_ANY, label="Request Data", style=wx.BORDER_SUNKEN
            )
            grid.Add(self.__ok_button, pos=(8, 0), flag=wx.ALL, border=5)
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
        grid.Add(cancel_button, pos=(8, 1), flag=wx.ALL, border=5)
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
        grid.Add(version_text, pos=(8, 2), flag=wx.ALIGN_LEFT, border=5)

        # Connect grid sizer to panel.
        my_panel.SetSizerAndFit(grid)

        # Finish at Frame level.
        sizer.Add(my_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        self.ShowModal()

    def __add_controls(
        self,
        row: int,
        panel: wx.Panel,
        grid: wx.GridBagSizer,
        label: str,
        default: str,
        text_changed_fn: Callable,
        restore_fn: Callable,
    ) -> None:
        control_label: wx.StaticText = wx.StaticText(panel, id=wx.ID_ANY, label=label)
        grid.Add(control_label, pos=(row, 0), flag=wx.ALIGN_RIGHT, border=5)
        text_control: wx.TextCtrl = wx.TextCtrl(panel, id=wx.ID_ANY, value=default)
        text_control.Bind(wx.EVT_TEXT, text_changed_fn)
        grid.Add(text_control, pos=(row, 1), flag=wx.EXPAND | wx.ALL, border=5)
        restore_button: wx.Button = wx.Button(
            panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        restore_button.Disable()
        grid.Add(restore_button, pos=(row, 2), flag=wx.ALL, border=5)
        restore_button.Bind(wx.EVT_BUTTON, restore_fn)
        self.__text_boxes_and_buttons[text_control] = restore_button
        self.__buttons_and_text_boxes[restore_button] = text_control

    def __enable_if_inputs_complete(self) -> None:
        if (
            self.__aou_service_account
            and self.__pmi_account
            and self.__project
            and self.__token_file
            and os.path.isfile(self.__token_file)
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

        data: dict = api_mgr.request_data(
            awardee=self.__config["AoU"]["awardee"],
            endpoint=self.__config["AoU"]["endpoint"],
            token=token,
        )

        data_directory: str = self.__get_destination_directory()

        # Create .csv output files.
        self.__set_status(f"Saving data to {data_directory}...")
        api_mgr.output_data(
            data=data,
            data_directory=data_directory,
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
            title="Select Directory to Save AoU Participants File",
            initialdir=initial_dir,  # Optional: Set an initial directory
        )

        if directory_path:
            self.__config["InSite API"]["data_directory"] = directory_path
            update_config(config=self.__config)

        return directory_path

    def __on_aou_service_account_text_changed(self, event: wx.EVT_TEXT):
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_service_account = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_awardee_text_changed(self, event: wx.EVT_TEXT):
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__awardee = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_cancel_clicked(self, event: wx.EVT_BUTTON) -> None:
        self.Destroy()
        event.Skip()

    def __on_ok_clicked(self, event) -> None:
        self.__ok_button.Disable()

        # Update config file.
        self.__config["Logon"]["aou_service_account"] = self.__aou_service_account
        self.__config["AoU"]["awardee"] = self.__awardee
        self.__config["Logon"]["pmi_account"] = self.__pmi_account
        self.__config["Logon"]["project"] = self.__project
        self.__config["Logon"]["token_file"] = self.__token_file
        update_config(config=self.__config)

        self.__get_data()
        self.__ok_button.Enable()

    def __on_pmi_account_text_changed(self, event: wx.EVT_TEXT) -> None:
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__pmi_account = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_project_text_changed(self, event: wx.EVT_TEXT) -> None:
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__project = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_restore_aou_service_account_button_clicked(
        self, event: wx.EVT_BUTTON
    ) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["Logon"]["aou_service_account"])
        button.Disable()

    def __on_restore_awardee_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["AoU"]["awardee"])
        button.Disable()

    def __on_restore_marker_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["AoU"]["organization"])
        button.Disable()

    def __on_restore_pmi_account_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["Logon"]["pmi_account"])
        button.Disable()

    def __on_restore_project_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["Logon"]["project"])
        button.Disable()

    def __on_restore_token_file_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__config["Logon"]["token_file"])
        button.Disable()

    def __on_token_file_text_changed(self, event: wx.EVT_TEXT) -> None:
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__token_file = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
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

    # Create the GUI.
    log.info("Instantiating ApiGui object.")
    gui: ApiGui = ApiGui(myconfig)

    try:
        splash.Destroy()
    except RuntimeError:
        pass

    app.MainLoop()
