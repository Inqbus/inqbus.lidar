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
from inqbus.lidar.scc_gui.viewbox import FixedViewBox

class ResultData(object):

    @classmethod
    def from_directory(cls, filepath):
        return cls()

class ResultPlot(pg.GraphicsLayoutWidget):

    def setup(self, data):
        pass