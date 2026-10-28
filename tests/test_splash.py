"""
Tests methods related to class Splash
"""

import time

import pytest
import wx

from src.getmyapidata.splash import MySplashScreen


@pytest.mark.localonly
def test_instantiation_windows() -> None:
    app: wx.App = wx.App(redirect=False)
    splash: MySplashScreen = MySplashScreen("../UCSD_school_of_medicine.png")
    splash.Show()
    time.sleep(1)
    app.Yield()
