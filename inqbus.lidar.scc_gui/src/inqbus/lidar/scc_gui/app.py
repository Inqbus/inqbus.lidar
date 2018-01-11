import os
import sys
import traceback as tb

from PyQt5 import QtCore, QtWidgets, uic, QtGui

import inqbus.lidar.components.params as rp
from inqbus.lidar.components.container import Measurement
from inqbus.lidar.scc_gui import PROJECT_PATH
from inqbus.lidar.scc_gui.log import logger
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.configs.base_config import resource_path, app_name
from inqbus.lidar.scc_gui.quicklook import LIDARPlot
from inqbus.lidar.scc_gui.res_plot import ResultData, ResultPlot
from inqbus.lidar.scc_gui.util import qt2pythonStr

os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

class Ui_MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        uic.loadUi(
            resource_path(
                os.path.join(
                    PROJECT_PATH,
                    'UI/app_design.ui')),
            self)
        self.last_file = None
        self.activeMdiChild = None

    def construct(self):
        self.windowMapper = QtCore.QSignalMapper(self)
        self.windowMapper.mapped[QtWidgets.QWidget].connect(
            self.setActiveSubWindow)

        self.menuNew.actions()[0].triggered.connect(self.newQuicklookPlot)
        self.menuNew.actions()[1].triggered.connect(self.new321Plot)
        self.menuNew.actions()[2].triggered.connect(self.new321PlotFromZip)

        # menu
        self.setup_menu()

    @QtCore.pyqtSlot(QtWidgets.QWidget)
    def setActiveSubWindow(self, window):
        """
        Set active |QMdiSubWindow|.

        :param |QMdiSubWindow| window: |QMdiSubWindow| to activate
        """
        if window:
            self.mdiArea.setActiveSubWindow(window)

    def setup_menu(self):
        self._windowMenu = self.menuBar().addMenu("&Window")
        self.update_menu()
        self._windowMenu.aboutToShow.connect(self.update_menu)

    def update_menu(self):
        self._windowMenu.clear()
        windows = self.mdiArea.subWindowList()

        for i, window in enumerate(windows):
            child = window.widget()

            text = "%d %s" % (i + 1, child.title)
            if i < 9:
                text = '&' + text

            action = self._windowMenu.addAction(text)
            action.setCheckable(True)
            action.setChecked(child == self.activeMdiChild)
            action.triggered.connect(self.windowMapper.map)
            self.windowMapper.setMapping(action, window)

    def setBusy(self):
        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor))

    def endBusy(self):
        QtWidgets.QApplication.restoreOverrideCursor()

    def addAsMDIWindow(self, central_widget):
        MDI_win = QtWidgets.QMdiSubWindow()
        MDI_win.setCentralWidget(central_widget)

    def newQuicklookPlot(self):
        file_path = self.showRawOpenDialog()
        file_name = os.path.basename(file_path)
        log_file = os.path.join(mc.LIDAR_LOG_PATH, file_name[:8] + '_temps.txt')

        if not os.path.exists(mc.LIDAR_LOG_PATH):
            logger.warning("%s can not be found. Check if paths are configured correctly and all directories exist." % mc.LIDAR_LOG_PATH)
        if not file_path:
            # Cancel button pressed
            pass
        else:
            measurement = Measurement.from_nc_file(file_path, log_file)

            MDI_win = QtWidgets.QMdiSubWindow(self)

            GraphicsView = LIDARPlot(MDI_win)
            GraphicsView.setup(measurement)

            MDI_win.setWidget(GraphicsView)
            MDI_win.setWindowTitle(GraphicsView.title)

            self.mdiArea.addSubWindow(MDI_win)
            MDI_win.showMaximized()

    def new321Plot(self):
        try:
            file_path = self.showFolderOpenDialog()

            result_data = ResultData.from_directory(file_path)

            MDI_win = QtWidgets.QMdiSubWindow(self)

            GraphicsView = ResultPlot(MDI_win)
            GraphicsView.setup(result_data)

            MDI_win.setWidget(GraphicsView)
            MDI_win.setWindowTitle(GraphicsView.title)

            self.mdiArea.addSubWindow(MDI_win)
            MDI_win.showMaximized()
        except Exception as e:
            pass

    def new321PlotFromZip(self):
        file_path = self.showZipOpenDialog()

        result_data = ResultData.from_zip(file_path)

        MDI_win = QtWidgets.QMdiSubWindow(self)

        GraphicsView = ResultPlot(MDI_win)
        GraphicsView.setup(result_data)

        MDI_win.setWidget(GraphicsView)
        MDI_win.setWindowTitle(GraphicsView.title)

        self.mdiArea.addSubWindow(MDI_win)
        MDI_win.showMaximized()

    def getCurrentPath(self):
        sender = self.sender()

        if self.last_file:
            filename = self.last_file
        else:
            filename = QtCore.QDir.currentPath()
        return filename

    def showFolderOpenDialog(self):
        sender = self.sender()
        filename = mc.RESULT_DATA_PATH

        file_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open directory including data files",
            QtCore.QDir().filePath(filename))
        return qt2pythonStr(file_path)

    def showRawOpenDialog(self):
        sender = self.sender()
        filename = mc.DATA_PATH
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open raw data file",
            QtCore.QDir().filePath(filename),
            'Zip_files (*.zip);;NC_Files (*.nc *.nc4 *.netcdf)')[0]
        return qt2pythonStr(file_path)

    def showZipOpenDialog(self):
        sender = self.sender()
        filename = mc.RESULT_DATA_PATH
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open raw data file",
            QtCore.QDir().filePath(filename),
            'Zip_files (*.zip)')[0]
        return qt2pythonStr(file_path)


app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon(resource_path('aesir.ico')))

app.main_window = Ui_MainWindow()
app.main_window.resize(mc.PLOT_WINDOW_SIZE[0], mc.PLOT_WINDOW_SIZE[1])
app.main_window.construct()
app.main_window.setWindowTitle(app_name)

app.main_window.show()

sys.exit(app.exec_())
