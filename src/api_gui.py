import wx
from configparser import ConfigParser

class ApiGui(wx.Dialog):
    def __init__(self, config: ConfigParser):
        wx.Dialog.__init__(self, parent=None, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, title="Get InSite API data")

        # Variables we want to return.
        self.project: str = config["Logon"]['project']
        self.pmi_account: str = config["Logon"]['pmi_account']
        self.aou_service_account: str = config["Logon"]['aou_service_account']
        self.token_file: str = config["Logon"]['token_file']

        sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # Set up this panel.
        my_panel: wx.Panel = wx.Panel(self)

        # Create sizer.
        grid: wx.GridBagSizer = wx.GridBagSizer(hgap=5, vgap=5)

        # Title
        font: wx.Font = wx.Font(18,
                                family=wx.FONTFAMILY_ROMAN,
                                style = wx.FONTSTYLE_NORMAL,
                                weight=wx.FONTWEIGHT_BOLD)
        title_text: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="Get InSite API data")
        title_text.SetFont(font)
        grid.Add(title_text, pos=(0,0), span=(1,2), flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=5)
        grid.AddGrowableCol(idx=1, proportion=1)

        project_label: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="Project")
        grid.Add(project_label, pos = (1,0), flag=wx.ALIGN_RIGHT, border=5)
        self.project_text: wx.TextCtrl = wx.TextCtrl(my_panel, id=wx.ID_ANY, value=self.project)
        grid.Add(self.project_text, pos=(1,1), flag=wx.EXPAND | wx.ALIGN_LEFT, border=5)

        pmi_account_label: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="PMI Account")
        grid.Add(pmi_account_label, pos = (2,0), flag=wx.ALIGN_RIGHT, border=5)
        self.pmi_account_text: wx.TextCtrl = wx.TextCtrl(my_panel, id=wx.ID_ANY, value=self.pmi_account)
        grid.Add(self.pmi_account_text, pos=(2,1), flag=wx.EXPAND | wx.ALL, border=5)

        aou_account_label: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="AoU Service Account")
        grid.Add(aou_account_label, pos = (3,0), flag=wx.ALIGN_RIGHT, border=5)
        self.aou_account_text: wx.TextCtrl = wx.TextCtrl(my_panel, id=wx.ID_ANY, value=self.aou_service_account)
        grid.Add(self.aou_account_text, pos=(3,1), flag=wx.EXPAND | wx.ALL, border=5)

        token_file_label: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="Token File")
        grid.Add(token_file_label, pos = (4,0), flag=wx.ALIGN_RIGHT, border=5)
        self.token_file_text: wx.TextCtrl = wx.TextCtrl(my_panel, id=wx.ID_ANY, value=self.token_file)
        grid.Add(self.token_file_text, pos=(4,1), flag=wx.EXPAND | wx.ALL, border=5)

        self.status_text: wx.StaticText = wx.StaticText(my_panel, id=wx.ID_ANY, label="Ready")
        grid.Add(self.status_text, pos=(5,0), span=(1,2), flag=wx.EXPAND | wx.ALL, border=5)

        ok_button: wx.Button = wx.Button(my_panel, id=wx.ID_ANY, label="Request Data", style=wx.BORDER_SUNKEN)
        grid.Add(ok_button, pos=(6,0), flag=wx.ALL, border=5)
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok_clicked)

        cancel_button: wx.Button = wx.Button(my_panel, id=wx.ID_ANY, label="Cancel", style=wx.BORDER_SUNKEN)
        grid.Add(cancel_button, pos=(6,1), flag=wx.ALL, border=5)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel_clicked)
        my_panel.SetSizerAndFit(grid)

        # Finish at Frame level.
        sizer.Add(my_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

    def on_ok_clicked(self, event):
        self.aou_service_account = self.aou_account_text.GetValue()
        self.pmi_account = self.pmi_account_text.GetValue()
        self.project = self.project_text.GetValue()
        self.token_file = self.token_file_text.GetValue()
        self.EndModal(wx.ID_OK)

    def on_cancel_clicked(self, event):
        self.EndModal(wx.ID_CANCEL)

    def set_status(self, status: str):
        self.status_text.SetLabel(status)

