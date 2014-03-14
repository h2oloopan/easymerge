from PyQt4 import QtGui

class Background(QtGui.QWidget):
    def __init__(self):
        super(Background, self).__init__()
        self._list = QtGui.QListWidget(self)
        self._tabs = QtGui.QTabWidget(self)
        self._result = QtGui.QTextBrowser(self)
        self._merge = QtGui.QPushButton('Merge', self)
        self.initUI()

    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(self._list, 0, 0, 2, 1)
        grid.addWidget(self._tabs, 0, 1, 1, 1)
        grid.addWidget(self._result, 1, 1, 2, 1)
        grid.addWidget(self._merge, 2, 0, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        self.setLayout(grid)

