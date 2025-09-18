import wx
import wx.adv


class MySplashScreen(wx.adv.SplashScreen):
    def __init__(self, filename: str):
        bmp = wx.Bitmap(filename, wx.BITMAP_TYPE_PNG)
        wx.adv.SplashScreen.__init__(
            self,
            bmp,
            wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
            2500,
            None,
            -1,
        )


if __name__ == "__main__":
    app = wx.App()
    splash_frame = MySplashScreen(r"src/UCSD_school_of_medicine.png")
    splash_frame.Show()
    app.MainLoop()
