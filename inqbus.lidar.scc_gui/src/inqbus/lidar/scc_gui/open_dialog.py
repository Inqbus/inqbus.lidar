import os

from inqbus.lidar.scc_gui.configs import main_config as mc

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QWidget, QTreeView, QVBoxLayout, QPushButton, QFileSystemModel, \
    QDialog, QComboBox, QLineEdit, QMessageBox, QHeaderView, QLabel


class CustomTreeview(QTreeView):
    def __init__(self, initial_path='', filters=[]):
        QTreeView.__init__(self)
        model = QFileSystemModel()

        if filters:
            model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)
            model.setNameFilters(filters)
            model.setNameFilterDisables(True) # just make them unselectable

        model.setRootPath('')

        self.setModel(model)
        self.header().setResizeMode(QHeaderView.ResizeToContents)


        self.expand_path(initial_path)

    def get_path(self):
        index = self.selectedIndexes()[0]
        indexItem = self.model().index(index.row(), 0, index.parent())

        filePath = self.model().filePath(indexItem)

        return filePath

    def expand_path(self, path):
        self.collapseAll()
        path = os.path.normpath(path)
        path_elements = path.split(os.sep)
        cur_path = '/'
        for element in path_elements:
            cur_path = os.path.join(cur_path, element)
            index = self.model().index(cur_path)
            self.expand(index)


class OpenDialog(QDialog):

    def __init__(self, allow_dirs=False, filters=[], initial_path='', help_text=''):

        QWidget.__init__(self)

        self.setMinimumWidth(mc.PLOT_WINDOW_SIZE[0])
        self.setMinimumHeight(mc.PLOT_WINDOW_SIZE[1])

        self.allow_dirs = allow_dirs
        self.selected_path = None
        self.filters = filters

        self.title = 'Open Dialog'

        self.treeView = CustomTreeview(initial_path=initial_path, filters=[])

        self.path_text = QLineEdit()
        self.path_text.setText(initial_path)
        self.treeView.selectionModel().selectionChanged.connect(self.update_text)
        self.path_text.textChanged.connect(self.update_treeview)

        self.help_label = QLabel()
        self.help_label.setText(help_text)

        if filters:
            self.filter_selection = QComboBox()
            for filter in filters:
                self.filter_selection.addItem(str(filter))
            self.filter_selection.currentIndexChanged.connect(self.set_filter)
            self.treeView.model().setNameFilters(self.filters[0])

        layout = QVBoxLayout()

        self.button = QPushButton('Open', self)
        self.button.clicked.connect(self.handleButton)

        layout.addWidget(self.help_label)
        layout.addWidget(self.treeView)
        layout.addWidget(self.path_text)
        layout.addWidget(self.filter_selection)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def update_treeview(self):
        if os.path.exists(self.path_text.text()):
            self.treeView.expand_path(self.path_text.text())

    def update_text(self):
        path = self.treeView.get_path()
        self.path_text.setText(path)

    def handleButton(self):
        path = self.path_text.text()
        print(path)

        if os.path.isdir(path):
            if self.allow_dirs:
                self.selected_path = path
            else:
                self.display_error('Not allowed Type Folder, please select a file instead.')
        else:
            self.selected_path = path

        if self.selected_path:
            self.close_window_success()

    def display_error(self, msg):
        QMessageBox.about(self, "Error", msg)

    def set_filter(self):
        value = self.filter_selection.currentIndex()
        model = self.treeView.model()
        model.setNameFilters(self.filters[value])
        print(model.nameFilters())


    def submitclose(self):
        # do whatever you need with self.selected_path
        self.accept()

    def close_window_success(self):
        self.submitclose()

    @classmethod
    def getFilePath(cls, initial_path='', filters=[], allow_dirs=False, help_text=''):
        window = OpenDialog(initial_path=initial_path,
                            filters=filters, allow_dirs=allow_dirs, help_text=help_text)
        window.show()
        if window.exec_():
            return window.selected_path