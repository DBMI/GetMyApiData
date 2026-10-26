"""
Tests methods related to class Splash
"""

import sys
import time

import pytest
import wx

from src.getmyapidata.splash import MySplashScreen


@pytest.mark.skipif(
    sys.platform == "linux" or sys.platform == "linux2",
    reason="Requires Windows GUI environment",
)
def test_instantiation() -> None:
    app: wx.App = wx.App(redirect=False)
    splash: MySplashScreen = MySplashScreen("../UCSD_school_of_medicine.png")
    splash.Show()
    time.sleep(1)
    app.Yield()
