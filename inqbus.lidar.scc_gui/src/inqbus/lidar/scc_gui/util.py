# -*- coding: utf-8 -*-

from datetime import datetime

from PyQt5 import QtCore, QtGui

from inqbus.lidar.scc_gui import fixunicode


def qt2pythonStr(qt_string):
    return fixunicode.fix_bad_unicode(str(qt_string))


def totimestamp(dt, epoch=datetime(1970, 1, 1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def get_main_app():
    """
    Return the main application
    :return:
    """
    return QtCore.QCoreApplication.instance()


def get_main_win():
    """
    Return the main window
    :return:
    """
    return get_main_app().main_window


def get_MDI_area():
    """
    Return the MDI area
    :return:
    """
    return get_main_win().mdiArea


def get_active_MDI_win():
    """
    Return the active MDI window
    :return:
    """
    active_sub_win = get_MDI_area().activeSubWindow()
    if active_sub_win:
        return active_sub_win.widget()
    return None


def get_MDI_windows():
    """
    Return iterator over all MDI windows
    :return:
    """
    sub_win_list = get_MDI_area().subWindowList()
    return sub_win_list


def get_MDI_Win_title(title):
    count = 0
    for win in get_MDI_windows():
        if win.windowTitle().startswith(title):
            count += 1
    if count == 0:
        return title
    else:
        return "%s-%s" % (title, count)


def createMappedAction(mapper, icon, text, parent, shortcut, methodName):
    """Create |QAction| that is mapped via methodName to call.
    :param mapper: mapper instance

    :param icon: icon associated with |QAction|
    :type icon: |QIcon| or None
    :param str text: the |QAction| descriptive text
    :param QObject parent: the parent |QObject|
    :param QKeySequence shortcut: the shortcut |QKeySequence|
    :param str methodName: name of method to call when |QAction| is
                           triggered
    :rtype: |QAction|"""

    if icon is not None:
        action = QtGui.QAction(icon, text, parent,
                               shortcut=shortcut,
                               triggered=mapper.map)
    else:
        action = QtGui.QAction(text, parent,
                               shortcut=shortcut,
                               triggered=mapper.map)
    mapper.setMapping(action, methodName)
    return action
