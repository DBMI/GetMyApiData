"""
Module: Contains class ApiGui, which creates the GUI
        users can use to request All of Us participant data.
"""

import logging
import os
from collections.abc import Callable
from tkinter import filedialog

import wx
import wx.adv

from src.getmyapidata.aou_package import AouPackage
from src.getmyapidata.common import get_exe_version
from src.getmyapidata.convert_to_hp_format import HealthProConverter
from src.getmyapidata.gcloud_tools import GCloudTools, gcloud_tools_installed
from src.getmyapidata.insite_api import InSiteAPI
from src.getmyapidata.my_logging import setup_logging


# pylint: disable=too-few-public-methods,too-many-instance-attributes
class ApiGui(wx.Dialog):
    """
    GUI for entering AoU variables and request participant data.

    Attributes:
    ----------
    no public attributes

    Methods
    -------
    no public methods
    """

    def __init__(self) -> None:
        """
        Initialise the ApiGui class.
        """
        self.__log: logging.Logger = setup_logging(
            log_filename=os.path.join(
                os.getcwd(),
                "api_gui.log",
            )
        )

        self.__log.info("Instantiating Api Gui.")
        wx.Dialog.__init__(
            self,
            parent=None,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            title="Get InSite API data",
        )  # pylint: disable=no-member

        # Dictionaries of controls linking text controls with their restore buttons.
        # Two dictionaries so we can go from text ctrl => restore button
        #  and restore button => text ctrl
        self.__buttons_and_text_boxes: dict = {}
        self.__text_boxes_and_buttons: dict = {}

        # Variables we need for data request.
        self.__aou_package: AouPackage = AouPackage()

        sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Set up this panel.
        self.__my_panel: wx.Panel = wx.Panel(self)

        # Create sizer.
        self.__my_grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        # Title
        self.__add_title(label="Get InSite API data")

        # AWARDEE
        self.__add_controls(
            1,
            "Awardee",
            self.__aou_package.awardee,
            self.__on_awardee_text_changed,
            self.__on_restore_awardee_button_clicked,
        )

        # PROJECT NAME
        self.__add_controls(
            2,
            "Project",
            self.__aou_package.project,
            self.__on_project_text_changed,
            self.__on_restore_project_button_clicked,
        )

        # PMI OPS ACCOUNT
        self.__add_controls(
            3,
            "PMI Account",
            self.__aou_package.pmi_account,
            self.__on_pmi_account_text_changed,
            self.__on_restore_pmi_account_button_clicked,
        )

        # AOU SERVICE ACCOUNT
        self.__add_controls(
            4,
            "AoU Service Account",
            self.__aou_package.aou_service_account,
            self.__on_aou_service_account_text_changed,
            self.__on_restore_aou_service_account_button_clicked,
        )

        # LOCATION OF TOKEN FILE
        self.__add_controls(
            5,
            "Token File",
            self.__aou_package.token_file,
            self.__on_token_file_text_changed,
            self.__on_restore_token_file_button_clicked,
        )

        # CHECK THAT GCLOUD TOOLS ARE INSTALLED.
        if gcloud_tools_installed():

            # PROGRESS BAR
            self.__gauge = wx.Gauge(self.__my_panel, range=100, size=wx.Size(350, 25))
            self.__my_grid.Add(
                self.__gauge,
                pos=(6, 1),
                flag=wx.EXPAND | wx.ALL,
                border=5,
            )

            # STATUS BOX
            self.__status_text: wx.StaticText = wx.StaticText(
                self.__my_panel, id=wx.ID_ANY, label="Ready"
            )
            self.__my_grid.Add(
                self.__status_text,
                pos=(7, 1),
                span=(1, 2),
                flag=wx.EXPAND | wx.ALL,
                border=5,
            )

            # OK BUTTON
            self.__ok_button: wx.Button = wx.Button(
                self.__my_panel,
                id=wx.ID_ANY,
                label="Request Data",
                style=wx.BORDER_SUNKEN,
            )
            self.__enable_if_inputs_complete()
            self.__my_grid.Add(self.__ok_button, pos=(8, 0), flag=wx.ALL, border=5)
            self.__ok_button.Bind(wx.EVT_BUTTON, self.__on_ok_clicked)
        else:
            link_label = "Must first install GCloud tools"
            link_url = "https://cloud.google.com/sdk/docs/install"
            hyperlink = wx.adv.HyperlinkCtrl(self.__my_panel, -1, link_label, link_url)

            self.__my_grid.Add(
                hyperlink, pos=(6, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5
            )

        # CANCEL BUTTON
        cancel_button: wx.Button = wx.Button(
            self.__my_panel, id=wx.ID_ANY, label="Cancel", style=wx.BORDER_SUNKEN
        )
        self.__my_grid.Add(cancel_button, pos=(8, 1), flag=wx.ALL, border=5)
        cancel_button.Bind(wx.EVT_BUTTON, self.__on_cancel_clicked)

        # VERSION INFO
        footnote_font: wx.Font = wx.Font(
            10,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_ITALIC,
            weight=wx.FONTWEIGHT_NORMAL,
        )
        version_text: wx.StaticText = wx.StaticText(
            self.__my_panel,
            id=wx.ID_ANY,
            label="Version: " + get_exe_version(self.__log),
        )
        version_text.SetFont(footnote_font)
        self.__my_grid.Add(version_text, pos=(8, 2), flag=wx.ALIGN_LEFT, border=5)

        # Connect grid sizer to panel.
        self.__my_panel.SetSizerAndFit(self.__my_grid)

        # Pop-up menu upon right-click.
        self.__my_panel.Bind(wx.EVT_RIGHT_DOWN, self.__on_show_menu)

        # Finish at Frame level.
        sizer.Add(self.__my_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()
        self.ShowModal()

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __add_controls(
        self,
        row: int,
        label: str,
        default: str,
        text_changed_fn: Callable,
        restore_fn: Callable,
    ) -> None:
        """
        Lets us pop in a label, text control and restore button, complete with callbacks and links.

        Parameters
        ----------
        row: int                    Where does this go on the panel?
        label: str                  What do we call this variable?
        default: str                Initial value of text ctrl
        text_changed_fn: Callable   Event handler for when text is changed
        restore_fn: Callable        Event handler for when Restore button is clicked

        Returns
        -------
        None
        """
        control_label: wx.StaticText = wx.StaticText(
            self.__my_panel, id=wx.ID_ANY, label=label
        )
        self.__my_grid.Add(control_label, pos=(row, 0), flag=wx.ALIGN_RIGHT, border=5)
        text_control: wx.TextCtrl = wx.TextCtrl(
            self.__my_panel, id=wx.ID_ANY, value=default
        )
        text_control.Bind(wx.EVT_TEXT, text_changed_fn)
        self.__my_grid.Add(
            text_control, pos=(row, 1), flag=wx.EXPAND | wx.ALL, border=5
        )
        restore_button: wx.Button = wx.Button(
            self.__my_panel,
            id=wx.ID_ANY,
            label="Restore",
            size=wx.Size(50, 25),
            style=wx.BORDER_SUNKEN,
        )
        restore_button.Disable()
        self.__my_grid.Add(restore_button, pos=(row, 2), flag=wx.ALL, border=5)
        restore_button.Bind(wx.EVT_BUTTON, restore_fn)
        self.__text_boxes_and_buttons[text_control] = restore_button
        self.__buttons_and_text_boxes[restore_button] = text_control

    def __add_title(self, label: str) -> None:
        """
        Adds a title at the top of the panel.

        Parameters
        ----------
        label: str

        Returns
        -------
        None
        """

        # Title
        title_font: wx.Font = wx.Font(
            18,
            family=wx.FONTFAMILY_ROMAN,
            style=wx.FONTSTYLE_NORMAL,
            weight=wx.FONTWEIGHT_BOLD,
        )
        title_text: wx.StaticText = wx.StaticText(
            self.__my_panel,
            id=wx.ID_ANY,
            label=label,
        )
        title_text.SetFont(title_font)
        self.__my_grid.Add(
            title_text,
            pos=(0, 0),
            span=(1, 2),
            flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
            border=5,
        )
        self.__my_grid.AddGrowableCol(idx=1, proportion=1)

    def __enable_if_inputs_complete(self) -> None:
        """
        Checks to see if it's OK to enable the "Request Data" button.

        Returns
        -------
        None
        """
        if self.__aou_package.inputs_complete():
            self.__ok_button.Enable()
        else:
            self.__ok_button.Disable()

    def __get_data(self) -> None:
        """
        Creates a GCloudTool and InSiteAPI objects & uses them to authenticate and request data.

        Returns
        -------
        None
        """
        self.__set_status("Calling GCloudTools...")
        gcloud_mgr: GCloudTools = GCloudTools(
            aou_package=self.__aou_package,
            log_level=self.__log.getEffectiveLevel(),
            status_fn=self.__set_status,
        )
        self.__set_status("Requesting token...")
        token: str = gcloud_mgr.get_token()

        # Get data from InSiteAPI.
        self.__set_status("Instantiating InSiteAPI object...")
        api_mgr: InSiteAPI = InSiteAPI(
            log_directory=self.__aou_package.log_directory,
            progress_fn=self.__set_progress,
            status_fn=self.__set_status,
            log_level=self.__log.getEffectiveLevel(),
        )
        self.__set_status("Requesting InSiteAPI data...")
        data: dict = api_mgr.request_data(
            aou_package=self.__aou_package,
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
        self.__set_status("Converting to HealthPro format.")
        hp_converter: HealthProConverter = HealthProConverter(
            log_directory=self.__aou_package.log_directory,
            data_directory=data_directory,
            status_fn=self.__set_status,
        )
        hp_converter.convert()
        self.__set_status(f"Complete. Results in {data_directory}.")

    def __get_destination_directory(self) -> str:
        """
        Asks user where they want the participant data to be saved.

        Returns
        -------
        directory_path: str
        """
        initial_dir: str

        try:
            initial_dir = self.__aou_package.data_directory
        except KeyError:
            initial_dir = "/"

        # Open the directory selection dialog
        directory_path: str = filedialog.askdirectory(
            title="Select Directory to Save AoU Participants File",
            initialdir=initial_dir,  # Optional: Set an initial directory
        )

        if directory_path:
            self.__aou_package.data_directory = directory_path

        return directory_path

    def __on_aou_service_account_text_changed(self, event: wx.EVT_TEXT) -> None:
        """
        Event handler for when user changes this text control:
            1) Updates the property
            2) Enables the Restore button
            3) Enables the Request Data button if all inputs now OK

        Parameters
        ----------
        event : wx.EVT_TEXT

        Returns
        -------
        None
        """
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_package.aou_service_account = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_awardee_text_changed(self, event: wx.EVT_TEXT) -> None:
        """
        Event handler for when user changes this text control:
            1) Updates the property
            2) Enables the Restore button
            3) Enables the Request Data button if all inputs now OK

        Parameters
        ----------
        event : wx.EVT_TEXT

        Returns
        -------
        None
        """

        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_package.awardee = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_cancel_clicked(self, event: wx.EVT_BUTTON) -> None:
        """
        Event handler for when user cancels Cancel button:

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        self.Destroy()
        event.Skip()

    # pylint: disable=unused-argument
    def __on_ok_clicked(self, event) -> None:
        """
        Event handler for when user completes Request Data button.

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        self.__ok_button.Disable()

        # Update config file.
        self.__aou_package.update_config()

        self.__get_data()
        self.__ok_button.Enable()

    def __on_menu_select(self, event: wx.EVT_MENU) -> None:
        """
        Sets logging level.

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        event_label: str = event.GetEventObject().GetLabel(event.GetId())

        if "INFO" in event_label:
            self.__log.setLevel(logging.INFO)
        elif "DEBUG" in event_label:
            self.__log.setLevel(logging.DEBUG)

    def __on_pmi_account_text_changed(self, event: wx.EVT_TEXT) -> None:
        """
        Event handler for when user changes this text control:
            1) Updates the property
            2) Enables the Restore button
            3) Enables the Request Data button if all inputs now OK

        Parameters
        ----------
        event : wx.EVT_TEXT

        Returns
        -------
        None
        """
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_package.pmi_account = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_project_text_changed(self, event: wx.EVT_TEXT) -> None:
        """
        Event handler for when user changes this text control:
            1) Updates the property
            2) Enables the Restore button
            3) Enables the Request Data button if all inputs now OK

        Parameters
        ----------
        event : wx.EVT_TEXT

        Returns
        -------
        None
        """
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_package.project = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __on_restore_aou_service_account_button_clicked(
        self, event: wx.EVT_BUTTON
    ) -> None:
        """
        Restore button handler

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__aou_package.restore_aou_service_account())
        button.Disable()

    def __on_restore_awardee_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        """
        Restore button handler

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__aou_package.restore_awardee())
        button.Disable()

    def __on_restore_pmi_account_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        """
        Restore button handler

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__aou_package.restore_pmi_account())
        button.Disable()

    def __on_restore_project_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        """
        Restore button handler

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__aou_package.restore_project())
        button.Disable()

    def __on_restore_token_file_button_clicked(self, event: wx.EVT_BUTTON) -> None:
        """
        Restore button handler

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        button: wx.Button = event.GetEventObject()
        text_ctrl: wx.TextCtrl = self.__buttons_and_text_boxes[button]
        text_ctrl.SetValue(self.__aou_package.restore_token_file())
        button.Disable()

    def __on_show_menu(self, event: wx.EVT_MENU) -> None:
        """
        Event handler for when user RIGHT-clicks the panel to select a logging level.

        Parameters
        ----------
        event

        Returns
        -------
        None
        """
        menu: wx.Menu = wx.Menu()
        item1: wx.MenuItem = menu.Append(wx.ID_ANY, "Set logging level: INFO")
        item2: wx.MenuItem = menu.Append(wx.ID_ANY, "Set logging level: DEBUG")
        self.Bind(wx.EVT_MENU, self.__on_menu_select, item1)
        self.Bind(wx.EVT_MENU, self.__on_menu_select, item2)
        self.PopupMenu(menu, event.GetPosition())
        menu.Destroy()

    def __on_token_file_text_changed(self, event: wx.EVT_TEXT) -> None:
        """
        Event handler for when user changes this text control:
            1) Updates the property
            2) Enables the Restore button
            3) Enables the Request Data button if all inputs now OK

        Parameters
        ----------
        event : wx.EVT_TEXT

        Returns
        -------
        None
        """
        text_ctrl_source: wx.TextCtrl = event.GetEventObject()
        self.__aou_package.token_file = text_ctrl_source.GetValue()
        restore_button: wx.Button = self.__text_boxes_and_buttons[text_ctrl_source]
        restore_button.Enable()
        self.__enable_if_inputs_complete()

    def __set_progress(self, pct: int) -> None:
        """
        Sets value of progress bar.

        Parameters
        ----------
        pct: int        Percentage completion

        Returns
        -------
        None
        """
        self.__gauge.SetValue(pct)
        wx.Yield()

    def __set_status(self, status: str) -> None:
        """
        Sets value of text status bar.

        Parameters
        ----------
        status: str

        Returns
        -------
        None
        """
        self.__log.info(status)
        self.__status_text.SetLabel(status)
        wx.Yield()
