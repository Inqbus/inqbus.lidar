# this is crucial for the formation of exe files from this code!
import os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


try:
    import sys
    import win32api
    win32api.SetDllDirectory(sys._MEIPASS)
except BaseException:
    pass


app_name = "Quicklook"
