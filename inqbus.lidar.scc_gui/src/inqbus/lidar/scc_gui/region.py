import os

from pyqtgraph import LinearRegionItem
from pyqtgraph.Qt import QtGui, QtCore, uic

import inqbus.lidar.components.params as rp
from inqbus.lidar.components.error import NoCalIdxFound, WrongFileFormat
from inqbus.lidar.scc_gui import PROJECT_PATH
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.configs.base_config import resource_path
from inqbus.lidar.scc_gui.util import qt2pythonStr


class RegionMenu(QtGui.QMenu):
    def __init__(self, view):
        QtGui.QMenu.__init__(self)

        self.view = view

        self.invalid = self.addAction('Set region invalid')
        self.invalid.triggered.connect(self.view.set_invalid)

        self.delete = self.addAction('Delete region')
        self.delete.triggered.connect(self.view.delete)

        self.from_start = self.addAction('From start')
        self.from_start.triggered.connect(self.view.from_start)

        self.to_end = self.addAction('To end')
        self.to_end.triggered.connect(self.view.to_end)

        self.period_dialog = self.addAction('Set time period')
        self.period_dialog.triggered.connect(self.view.period_dialog)

        self.show = self.addAction('Show')
        self.show.triggered.connect(self.view.show)

        self.save_as_scc = self.addAction('Filter and save as scc file')
        self.save_as_scc.triggered.connect(self.view.save_as_scc)

        self.save_as_depolcal = self.addAction(
            'Filter and save as depol cal file')
        self.save_as_depolcal.triggered.connect(self.view.save_as_depolcal)


class RegionDialog(QtGui.QDialog):

    def __init__(self, a_parent_region, a_plot):
        super(RegionDialog, self).__init__()
        uic.loadUi(
            resource_path(
                os.path.join(
                    PROJECT_PATH,
                    'UI/region_dialog.ui')),
            self)
        self.plot = a_plot
        self.parent_region = a_parent_region
        FromTime = self.plot.measurement.time_axis.start[int(
            round(a_parent_region.getRegion()[0]))]
        ToTime = self.plot.measurement.time_axis.start[int(
            round(a_parent_region.getRegion()[1]))]
        self.TimeEditFrom.setTime(
            QtCore.QTime(
                FromTime.hour,
                FromTime.minute,
                FromTime.second))
        self.TimeEditFrom.setDisplayFormat('HH:mm:ss')
        self.TimeEditTo.setTime(
            QtCore.QTime(
                ToTime.hour,
                ToTime.minute,
                ToTime.second))
        self.TimeEditTo.setDisplayFormat('HH:mm:ss')

    def accept(self):
        """
        This is called if you click on the OK button
        """
        from_time = self.TimeEditFrom.time().toPyTime()
        to_time = self.TimeEditTo.time().toPyTime()
        new_rgn = self.plot.get_region_from_time(from_time, to_time)

        self.parent_region.setRegion(new_rgn)
        self.parent_region.update()
        super(RegionDialog, self).accept()

    def reject(self):
        """
        This is called if you click on the Cancel button
        """
        super(RegionDialog, self).reject()


class SCC_raw_Params_Dialog(QtGui.QDialog):

    def __init__(self, a_parent_region, a_plot):
        super(SCC_raw_Params_Dialog, self).__init__()
        uic.loadUi(
            resource_path(
                os.path.join(
                    PROJECT_PATH,
                    'UI/save_as_scc_dialog.ui')),
            self)
        self.plot = a_plot
        self.parent_region = a_parent_region
        if self.plot.measurement.header.measurement_id == '':
            self.MeasurementID_Edit.setText(self.plot.measurement.time_axis.start[int(
                round(a_parent_region.getRegion()[0]))].strftime('%Y%m%d') + rp.STATION_ID + '__')
        else:
            self.MeasurementID_Edit.text = self.plot.measurement.header.measurement_id

    def accept(self):
        """
        This is called if you click on the OK button
        """
        self.plot.measurement.header.measurement_id = qt2pythonStr(
            self.MeasurementID_Edit.text())
        self.plot.measurement.header.comment = qt2pythonStr(
            self.Comment_Edit.text())
        try:
            self.plot.measurement.read_sonde(
                qt2pythonStr(self.SondeFile_Edit.text()))
        except FileNotFoundError:
            QtGui.QMessageBox.about(self, "Done", "Sonde: File does not exist")
        except WrongFileFormat:
            QtGui.QMessageBox.about(
                self, "Done", "Sonde: Unexpected File Type")
        else:
            self.plot.save_as_scc(self.parent_region.getRegion())
            super(SCC_raw_Params_Dialog, self).accept()
            QtGui.QMessageBox.about(
                self, "Done", "scc raw data file was created")

    def reject(self):
        """
        This is called if you click on the Cancel button
        """
        super(SCC_raw_Params_Dialog, self).reject()


class SCC_DPcal_Params_Dialog(QtGui.QDialog):

    def __init__(self, a_parent_region, a_plot):
        super(SCC_DPcal_Params_Dialog, self).__init__()
        uic.loadUi(
            resource_path(
                os.path.join(
                    PROJECT_PATH,
                    'UI/save_as_sccDPcal_dialog.ui')),
            self)
        self.plot = a_plot
        self.parent_region = a_parent_region
        if self.plot.measurement.header.measurement_id == '':
            self.MeasurementID_Edit.setText(self.plot.measurement.time_axis.start[int(
                round(a_parent_region.getRegion()[0]))].strftime('%Y%m%d') + rp.STATION_ID + '__')
        else:
            self.MeasurementID_Edit.text = self.plot.measurement.header.measurement_id

    def accept(self):
        """
        This is called if you click on the OK button
        """
        self.plot.measurement.header.measurement_id = qt2pythonStr(
            self.MeasurementID_Edit.text)
        self.plot.measurement.header.comment = qt2pythonStr(
            self.Comment_Edit.text)

        try:
            self.plot.save_as_depolcal_scc(self.parent_region.getRegion())
            super(SCC_DPcal_Params_Dialog, self).accept()
            QtGui.QMessageBox.about(
                self, "Done", "scc depolcal file was created")
        except NoCalIdxFound:
            QtGui.QMessageBox.about(self, "Done", "No Cal Idx Found")

    def reject(self):
        """
        This is called if you click on the Cancel button
        """
        super(SCC_DPcal_Params_Dialog, self).reject()


class MenuLinearRegionItem(LinearRegionItem):
    """
    Region with a seperate menu
    """

    def __init__(self, plot, menu=RegionMenu, **kwargs):
        """
        Takes additional kwarg menu which is a menu instance
        :param kwargs:
        :return:
        """

        super(MenuLinearRegionItem, self).__init__(**kwargs)
        self.menu = menu(self)
        self.plot = plot
        self.isValid = True
        self.setBrush(mc.REGION_NORMAL_BRUSH)

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            super(MenuLinearRegionItem, self).mouseClickEvent(ev)
        elif ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            self.raiseContextMenu(ev)

    def getMenu(self, ev):
        return self.menu

    def raiseContextMenu(self, ev):
        menu = self.getMenu(ev)
        menu.popup(ev.screenPos().toPoint())

    def set_invalid(self):
        self.isValid = False
        self.setBrush(mc.REGION_INVALID_BRUSH)
        self.update()
        self.plot.update_region_masks()
        self.plot.plot_profile(self.plot.regions.full_range)

    def delete(self):
        self.plot.delete_region(self)
        self.plot.update_region_masks()
        self.plot.plot_profile(self.plot.regions.full_range)

    def from_start(self):
        rgn = self.getRegion()
        new_rgn = (0, rgn[1])
        self.setRegion(new_rgn)
        self.update()

    def to_end(self):
        rgn = self.getRegion()
        new_rgn = (rgn[0], len(self.plot.time_axis.axis_data))
        self.setRegion(new_rgn)
        self.update()

    def show(self):
        self.update()
        self.plot.plot_profile(self.getRegion())

    def save_as_scc(self):
        dialog = SCC_raw_Params_Dialog(self, self.plot)
        dialog.exec_()

    def save_as_depolcal(self):
        dialog = SCC_DPcal_Params_Dialog(self, self.plot)
        dialog.exec_()

    def period_dialog(self):
        dialog = RegionDialog(self, self.plot)
        dialog.exec_()
