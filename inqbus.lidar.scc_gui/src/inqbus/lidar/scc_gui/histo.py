from pyqtgraph import HistogramLUTItem, Point
from pyqtgraph.Qt import QtGui
from pyqtgraph.graphicsItems.AxisItem import *
from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.graphicsItems.LinearRegionItem import *
from pyqtgraph.graphicsItems.PlotDataItem import *
from pyqtgraph.graphicsItems.ViewBox import *

from inqbus.lidar.scc_gui.gradient import Gradient
from inqbus.lidar.scc_gui.configs.main_config import GRADIENT


class Histo(HistogramLUTItem):
    """
    Customizing HistogramLUTItem (rotated)
    """

    def __init__(self, image=None, fillHistogram=True):
        """
        If *image* (ImageItem) is provided, then the control will be automatically linked to the image and changes to the control will be immediately reflected in the image's appearance.
        By default, the histogram is rendered with a fill. For performance, set *fillHistogram* = False.
        """
        GraphicsWidget.__init__(self)
        self.lut = None
        self.imageItem = lambda: None  # fake a dead weakref

        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)
        self.vb = ViewBox(parent=self)
        self.vb.setMaximumHeight(152)
        self.vb.setMinimumHeight(45)
        self.vb.setMouseEnabled(x=False, y=True)
        self.gradient = Gradient()
        self.gradient.setOrientation('bottom')
        self.gradient.restoreState(GRADIENT)
        self.region = LinearRegionItem([0, 1], LinearRegionItem.Vertical)
        self.region.setZValue(1000)
        self.vb.addItem(self.region)
        self.axis = AxisItem(
            'top',
            linkView=self.vb,
            maxTickLength=-10,
            parent=self)
        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.vb, 1, 0)
        self.layout.addItem(self.gradient, 2, 0)
        self.range = None
        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)
        self.vb.setFlag(self.gradient.ItemStacksBehindParent)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.region.sigRegionChanged.connect(self.regionChanging)
        self.region.sigRegionChangeFinished.connect(self.regionChanged)
        self.vb.sigRangeChanged.connect(self.viewRangeChanged)
        self.plot = PlotDataItem()

        self.fillHistogram(fillHistogram)

        self.vb.addItem(self.plot)
        self.autoHistogramRange()

        if image is not None:
            self.setImageItem(image)

    def paint(self, p, *args):
        pen = self.region.lines[0].pen
        rgn = self.getLevels()
        p1 = self.vb.mapFromViewToItem(self, Point(
            rgn[0], self.vb.viewRect().center().y()))
        p2 = self.vb.mapFromViewToItem(self, Point(
            rgn[1], self.vb.viewRect().center().y()))
        gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
        for pen in [fn.mkPen('k', width=3), pen]:
            p.setPen(pen)
            p.drawLine(p1, gradRect.topLeft())
            p.drawLine(p2, gradRect.topRight())
            p.drawLine(gradRect.topLeft(), gradRect.topRight())
            p.drawLine(gradRect.bottomLeft(), gradRect.bottomRight())
