import datetime as dt
import os

import numpy as np
import pyqtgraph as pg
from inqbus.lidar.components.error import PathDoesNotExist
from pyqtgraph.Qt import QtCore, QtGui

from inqbus.lidar.components.regions import Regions
from inqbus.lidar.scc_gui import util
from inqbus.lidar.scc_gui.log import logger
from inqbus.lidar.scc_gui.axis import DateAxis, HeightAxis
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.histo import Histo
from inqbus.lidar.scc_gui.image import Image
from inqbus.lidar.scc_gui.region import MenuLinearRegionItem
from inqbus.lidar.scc_gui.viewbox import QLFixedViewBox


class LIDARPlot(pg.GraphicsLayoutWidget):

    def setup(self, measurement):
        self.measurement = measurement
        self.title = util.get_MDI_Win_title(measurement.title)
        self.layout()
        self.define_axis()
        self.regions = Regions((0, len(self.time_axis.axis_data)))

        self.setup_countour_plot()
        self.setup_profile_plot()
        self.plot_profile(self.regions.full_range)
        self.setup_histogram()

        self.resize(mc.PLOT_WINDOW_SIZE[0], mc.PLOT_WINDOW_SIZE[1])

#        self.create_menu()

        self.show()

        # Set Heigth Axis to defined maximum value
        viewbox = self.contour_plot.vb
        viewbox.enableAutoRange(viewbox.YAxis, False)
        viewbox.setYRange(
            self.height_axis.range[0],
            self.measurement.z_axis.m_2_bin(mc.MAX_PLOT_ALTITUDE) * 1.0)

        self.create_menu()

    # Actions for the menu
    def create_actions(self):
        """
        Here a list of Actions is provided for the menu:
            util.createMappedAction(
                mapper,
                None,
                "&", self,
                None,
                "export as quality controlled nc files"),
        Creates an action called "export as quality controlled nc files" in the menu which calls the "export as quality controlled nc files" function on the currently active instance
        """
        self.mapper = QtCore.QSignalMapper()
        self.mapper.mapped[str].connect(self.mappedQuicklookAction)
        self._menu_actions = [

            util.createMappedAction(
                self.mapper,
                None,
                "Analyse telecover measurement", self,
                QtGui.QKeySequence(),
                "analyse_telecover"),

            # util.createMappedAction(
            #     self.mapper,
            #     None,
            #     "&was anderes wird passieren", self,
            #     QtGui.QKeySequence(),
            #     "was_anderes"),
        ]

    @QtCore.pyqtSlot(str)
    def mappedQuicklookAction(self, method_name):
        """
        All menu actions of the quicklook menu are mapped by the Signal Mapper to this function.
        Here the currently active quicklook instance will be derived and the function name (String) of the action will be
        called on this instance.
        """
        # find currently active quicklook instance
        active_win = util.get_active_MDI_win()
        # call the function of the action on the instance
        getattr(active_win, str(method_name))()

    # Main menu for quicklook plot
    def create_menu(self):
        """
        Contructs the menu and populates it with the actions defined in create_actions
        :return:
        """
        self.create_actions()
        self._menu = QtGui.QMenu('QA measurements')
        for action in self._menu_actions:
            self._menu.addAction(action)
        menuBar = util.get_main_win().menuBar()
        for action in menuBar.actions():
            if action.menu().title() == "QA measurements":
                menuBar.removeAction(action)
        menuBar.addMenu(self._menu)

    def layout(self):
        # Internal Layout for the contour and the profile plot
        self.contour_profile_layout = self.addLayout(
            colspan=2, border=mc.PLOT_BORDER_COLOR)
        # contour and profile goes to the left top.
        self.addItem(self.contour_profile_layout, 0, 0)

    # Plot specific things
    # ==================================================================================================================
    def define_axis(self):
        # The time axis of the image
        self.time_axis = DateAxis(orientation='bottom')
        # select the data to be displayed
        self.time_axis.axis_data = self.measurement.time_axis.start
        # Set Axis above other display elements
        self.time_axis.setZValue(120)

        # The height axis of the image
        self.height_axis = HeightAxis(orientation='left')
        # select the data to be displayed
        # [rconst.FIRST_VALID_BIN : 500]
        self.height_axis.axis_data = self.measurement.z_axis.height_axis.data
        # Set Axis above other display elements
        self.height_axis.setZValue(130)

    # CONTOUR PLOT

    def setup_countour_plot(self):
        # contourplot with the custom axis
        self.contour_plot = self.contour_profile_layout.addPlot(
            axisItems={'bottom': self.time_axis, 'left': self.height_axis},
            viewBox=QLFixedViewBox(self)
            #            viewBox = pg.ViewBox()
        )

        # limit the panning so yMin is always 0
        self.contour_plot.vb.setLimits(
            yMin=self.measurement.z_axis.header.first_valid_bin)
#        self.contour_plot.vb.setLimits(yMax = self.measurement.z_axis.m_2_bin(MAX_PLOT_ALTITUDE) )

        self.contour_plot.setMinimumWidth(700)

        # Display contour as image
        self.img = Image()
        self.contour_plot.addItem(self.img)

        # preprocess the data
        self.data_of_contour_plot()

        # shove the contour data into the image
        self.img.setImage(
            self.contour_data,
            levels=(
                self.contour_data.min(),
                self.contour_max_count),
            autolevels=False)

    def data_of_contour_plot(self):
        # flip the data till we know how to invert the y-axis.
        # Todo: Selection of channels
        self.contour_data = self.measurement.pre_processed_signals[mc.QUICKLOOK_CHANNEL].data
        # Eliminate outliers by calculatng the 99% percentile as maximal count
        # to be displayed.
        self.contour_max_count = np.percentile(
            self.contour_data, mc.PLOT_CONTOUR_DATA_UPPER_PERCENTILE)

    def add_region(self, position):
        """
        Called from the viewbox  self.contour_plot.vb on click of middle mouse button
        The position is given as float value [0,1] where 0 is left and
        :return:
        """
        region = self.region_selector(position)
        self.regions[id(region)] = region

    def delete_region(self, region):
        """
        Called from the regions menu "delete" action
        :return:
        """

        self.contour_plot.vb.removeItem(region)
        del self.regions[id(region)]

    def clear_region_borders(self, region):
        region_start = int(round(region[0], 0))
        region_stop = int(round(region[1], 0))

        return region_start, region_stop

    def save_as_scc(self, a_region):

        region_start, region_stop = self.clear_region_borders(a_region)
        region_stop = min([region_stop, self.measurement.mask.size - 1])

        self.measurement.mask[0: region_start] = 0
        self.measurement.mask[region_stop:] = 0
        if os.path.exists(mc.OUT_PATH):
            self.measurement.write_scc_raw_signal(os.path.join(
                mc.OUT_PATH, self.measurement.scc_raw_filename()))
        else:
            logger.error("%s does not exist." % mc.OUT_PATH)
            raise PathDoesNotExist

    def set_telecover_region(self, a_region, sector_name):
        region_start, region_stop = self.clear_region_borders(a_region)
        region_start = max([region_start, 0])
        region_stop = min([region_stop, self.measurement.mask.size - 1])
        self.measurement.set_telecover_region((region_start, region_stop), sector_name)

    def save_as_depolcal_scc(self, a_region):
        region_start, region_stop = self.clear_region_borders(a_region)
        region_stop = min([region_stop, self.measurement.mask.size - 1])

        self.measurement.mask[0: region_start] = 0
        self.measurement.mask[region_stop:] = 0
        self.measurement.write_scc_depolcal_signal()

    def update_region_masks(self):
        self.measurement.mask[:] = 1
        for r in self.regions.keys():
            if not self.regions[r].isValid:
                rgn = self.regions[r].getRegion()
                self.measurement.mask[round(rgn[0]):round(rgn[1])] = 0

    def get_region_from_time(self, start, end):
        dt_start = dt.datetime.combine(
            self.measurement.time_axis.stop[0], start)
        dt_end = dt.datetime.combine(self.measurement.time_axis.stop[0], end)

        lt_start = np.where(self.measurement.time_axis.stop > dt_start)[0]
        if len(lt_start) > 0:
            start_idx = lt_start[0]
        else:
            QtGui.QMessageBox.about(
                self, "%s is outside of measurement time axis" %
                      (start.strftime('%H:%M:%S')))
#        else:
#            pass
        lt_end = np.where(self.measurement.time_axis.stop > dt_end)[0]
        if len(lt_end) > 0:
            end_idx = lt_end[0]
        else:
            QtGui.QMessageBox.about(
                self, "%s is outside of measurement time axis" %
                (end.strftime('%H:%M:%S')))
        return(start_idx, end_idx)

    def region_selector(self, position):
        region = MenuLinearRegionItem(
            self, values=[
                0, 1], orientation=pg.LinearRegionItem.Vertical)

        start = self.img.mapFromScene(position).x(
        ) - mc.REGION_INITIAL_WIDTH_IN_BINS / 2
        end = start + mc.REGION_INITIAL_WIDTH_IN_BINS
        region.setRegion((start, end))
        region.setZValue(1000)

        self.contour_plot.vb.addItem(region)
        return region

    def region_of_interest(self):
        # Custom ROI for selecting an image region
        pass

    def isocurve_on_contour(self):
        # Isocurve drawing
        # ToDo Set resonable initial level
        self.iso = pg.IsocurveItem(level=0.8, pen=mc.PLOT_ISO_COLOR)
        # set the cnvas to draw the isoline to the contour image
        self.iso.setParentItem(self.img)
        # build isocurves from smoothed data
        self.iso.setData(
            pg.gaussianFilter(
                self.contour_data,
                mc.PLOT_ISO_SMOOTH_FILTER_RANGE))
        # draw isoline above the image
        self.iso.setZValue(5)
        pass

    # PROFILE PLOT
    def setup_profile_plot(self):
        # Profile plot at the right side
        self.profile = self.contour_profile_layout.addPlot()
        self.profile.hideAxis('left')
        self.profile.setLabel('bottom', text='counts', units='counts/s')
        self.profile.setXRange(0, 1E8)
        # Synchronize the Y-Axis of contour and profile plot
        self.profile.setYLink(self.contour_plot)
        # Todo connect region chnge with profile plotting

    def plot_profile(self, a_region):
        # set the data content for the profile
        # min_time, max_time = self.region.getRegion()

        self.profile.setXRange(0, 1E8)
        min_time = round(a_region[0])
        max_time = round(a_region[1])
        (min_alt_idx, max_alt_idx) = self.profile.viewRange()[1]
        clear = True
        for chan in self.measurement.pre_processed_signals:
            masked_data = self.measurement.pre_processed_signals[chan].data[self.measurement.mask, :]
            (x_ax_min, x_ax_max) = self.profile.viewRange()[0]
            avrg_data = masked_data[min_time:max_time, :].mean(axis=0)
            min_data = avrg_data[int(min_alt_idx):int(max_alt_idx)].min()
            max_data = avrg_data[int(min_alt_idx):int(max_alt_idx)].max()
            self.profile.setXRange(min(x_ax_min, min_data), max(x_ax_max, max_data))

            self.profile.plot(avrg_data,
                              np.arange(len(self.measurement.z_axis.height_axis.data)),
                              pen=mc.PLOT_PROFILE_COLOR[chan],
                              clear=clear)
            clear = False  # clear only before drawing of the first plot.

    # HISTOGRAM and COLORBAR

    def setup_histogram(self):
        # Contrast/color control
        self.hist = Histo()
        self.hist.setImageItem(self.img)
        self.addItem(self.hist, 1, 0)

        # Draggable line for setting isocurve level
        self.isoLine = pg.InfiniteLine(
            angle=90, movable=True, pen=mc.PLOT_ISO_COLOR)
        self.hist.vb.addItem(self.isoLine)
        # makes user interaction a little easier
        self.hist.vb.setMouseEnabled(y=False)
        self.isoLine.setValue(0.8)
        # ToDo resonable default for isoline
        # bring iso line above contrast controls
        self.isoLine.setZValue(1000)
        # set handler for redraw of iso line on end of drag of iso line
        self.isoLine.sigPositionChangeFinished.connect(self.updateIsocurve)

        # set min/max of the histogram
        self.contour_min_count = self.contour_data.min()

        self.hist.setLevels(self.contour_min_count, self.contour_max_count)
        # set min/max of the histogram scale
        self.hist.setHistogramRange(
            self.contour_min_count,
            self.contour_max_count)
        self.hist.axis.setRange(self.contour_min_count, self.contour_max_count)

    def updateIsocurve(self):
        if hasattr(self, 'iso'):
            self.iso.setLevel(self.isoLine.value())

    def analyse_telecover(self):
        if self.measurement.telecover_data['profiles'] != {}:
            self.measurement.analyse_telecover()
            QtGui.QMessageBox.about(
                self, "Done", "telecover measurement was analyzed")
        else:
            QtGui.QMessageBox.about(
                self, "Error", "no telecover sector measurements defined")


