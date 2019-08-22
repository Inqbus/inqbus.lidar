import os
from PyQt5 import QtWidgets

from pyqtgraph import LinearRegionItem
from pyqtgraph.Qt import QtGui, QtCore, uic

from inqbus.lidar.components.error import NoCalIdxFound, WrongFileFormat, WrongFileStorage
from inqbus.lidar.scc_gui import PROJECT_PATH
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.configs.base_config import resource_path
from inqbus.lidar.scc_gui.util import qt2pythonStr


class CloudRegionMenu(QtGui.QMenu):
    def __init__(self, view):
        QtGui.QMenu.__init__(self)

        self.view = view

        self.set_cirrus = self.addAction('label as cirrus')
        self.invalid.triggered.connect(self.view.set_cirrus)


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

        self.addSeparator()

        self.save_as_scc = self.addAction('Filter and save as scc file')
        self.save_as_scc.triggered.connect(self.view.save_as_scc)

        self.save_as_depolcal = self.addAction(
            'Filter and save as depol cal file')
        self.save_as_depolcal.triggered.connect(self.view.save_as_depolcal)

        self.addSeparator()
        
        self.quality_menu = self.addMenu('QA tests')
        
        self.telecover_menu = self.quality_menu.addMenu('telecover measurement')

        self.telecover_set_as_north = self.telecover_menu.addAction('set as north')
        self.telecover_set_as_north.triggered.connect(self.view.telecover_set_as_north)

        self.telecover_set_as_east = self.telecover_menu.addAction('set as east')
        self.telecover_set_as_east.triggered.connect(self.view.telecover_set_as_east)

        self.telecover_set_as_south = self.telecover_menu.addAction('set as south')
        self.telecover_set_as_south.triggered.connect(self.view.telecover_set_as_south)

        self.telecover_set_as_west = self.telecover_menu.addAction('set as west')
        self.telecover_set_as_west.triggered.connect(self.view.telecover_set_as_west)

        self.telecover_set_as_north2 = self.telecover_menu.addAction('set as north2')
        self.telecover_set_as_north2.triggered.connect(self.view.telecover_set_as_north2)

#        self.telecover_set_as_rayleigh = self.addAction('telecover - set as Rayleigh')
#        self.telecover_set_as_rayleigh.triggered.connect(self.view.telecover_set_as_rayleigh)

#        self.telecover_set_as_dark = self.addAction('telecover - set as dark')
#        self.telecover_set_as_dark.triggered.connect(self.view.telecover_set_as_dark)

        # self.analyse_telecover = self.addAction('telecover - analyse')
        # self.analyse_telecover.triggered.connect(self.view.analyse_telecover)


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
        self.ui = uic.loadUi(
            resource_path(
                os.path.join(
                    PROJECT_PATH,
                    'UI/save_as_scc_dialog.ui')),
            self)
        self.plot = a_plot
        self.parent_region = a_parent_region

        self.ui.openFile.clicked.connect(self.openFileDialog)

        if not self.plot.measurement.header.measurement_id:
            start_time = self.plot.measurement.time_axis.start[int(round(a_parent_region.getRegion()[0]))]
            new_measurement_id = start_time.strftime('%Y%m%d') + mc.STATION_ID + start_time.strftime('%H%M')
#            self.MeasurementID_Edit.setText(self.plot.measurement.time_axis.start[int(
#                round(a_parent_region.getRegion()[0]))].strftime('%Y%m%d') + mc.STATION_ID + '__')
            self.MeasurementID_Edit.setText(new_measurement_id)
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

    def openFileDialog(self):
        try:
            filepath = self.showSondeOpenDialog()
            self.SondeFile_Edit.setText(filepath)
        except WrongFileStorage:
            QtGui.QMessageBox.about(
                self, "Done", "sonde file must be located under %s" % mc.SONDE_PATH)

    def showSondeOpenDialog(self):
        sender = self.sender()
        filename = mc.SONDE_PATH

        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open sonde data file",
            QtCore.QDir().filePath(filename),
            'Wyoming sonde (*.txt);;GDAS sonde (*gdas*.txt);;Ninjo sonde (*.csv)')[0]

#        if mc.SONDE_PATH in file_path:
        file_path = file_path.replace(mc.SONDE_PATH + '/', '')
        return qt2pythonStr(file_path)
#        else:
#            raise WrongFileStorage


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
        if not self.plot.measurement.header.measurement_id :
            start_time = self.plot.measurement.time_axis.start[int(round(a_parent_region.getRegion()[0]))]
            new_measurement_id = start_time.strftime('%Y%m%d') + mc.STATION_ID + start_time.strftime('%H') + 'dp'
#            self.MeasurementID_Edit.setText(self.plot.measurement.time_axis.start[int(
#                round(a_parent_region.getRegion()[0]))].strftime('%Y%m%d') + mc.STATION_ID + '__')
            self.MeasurementID_Edit.setText(new_measurement_id)
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


class MenuLinearRegionItemHorizontal(LinearRegionItem):
    """
    Region with a seperate menu
    """

    def __init__(self, plot, menu=CloudRegionMenu, **kwargs):
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

    # def mouseClickEvent(self, ev):
    #     if self.moving and ev.button() == QtCore.Qt.RightButton:
    #         super(MenuLinearRegionItem, self).mouseClickEvent(ev)
    #     elif ev.button() == QtCore.Qt.RightButton:
    #         ev.accept()
    #         self.raiseContextMenu(ev)
    #
    # def getMenu(self, ev):
    #     return self.menu
    #
    # def raiseContextMenu(self, ev):
    #     menu = self.getMenu(ev)
    #     menu.popup(ev.screenPos().toPoint())
    #
    # def set_invalid(self):
    #     self.isValid = False
    #     self.setBrush(mc.REGION_INVALID_BRUSH)
    #     self.update()
    #     self.plot.update_region_masks()
    #     self.plot.plot_profile(self.plot.regions.full_range)
    #
    # def delete(self):
    #     self.plot.delete_region(self)
    #     self.plot.update_region_masks()
    #     self.plot.plot_profile(self.plot.regions.full_range)


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
        new_rgn = (rgn[0], len(self.plot.time_axis.axis_data)-1)
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

    def telecover_set_as_north(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'north')


    def telecover_set_as_east(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'east')


    def telecover_set_as_west(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'west')


    def telecover_set_as_south(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'south')


    def telecover_set_as_north2(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'north2')


    def telecover_set_as_rayleigh(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'rayleigh')


    def telecover_set_as_dark(self):
        self.update()
        self.plot.set_telecover_region(self.getRegion(), 'dark')
