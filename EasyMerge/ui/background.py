from PyQt4 import QtGui

class Background(QtGui.QWidget):
    def __init__(self):
        super(Background, self).__init__()
        self._list = QtGui.QListWidget(self)
        self._tabs = QtGui.QTabWidget(self)
        self._result = QtGui.QTextBrowser(self)
        self._merge = QtGui.QPushButton('Merge', self)
        self._analyze = QtGui.QPushButton('Analyze', self)
        self._open = QtGui.QPushButton('Open Source', self)
        self._source = QtGui.QLineEdit(self)
        self.initUI()

    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(self._open, 0, 0, 1, 1)
        grid.addWidget(self._source, 0, 1, 1, 1)
        grid.addWidget(self._analyze, 0, 2, 1, 1)
        grid.addWidget(self._list, 1, 0, 2, 1)
        grid.addWidget(self._tabs, 1, 1, 1, 2)
        grid.addWidget(self._result, 2, 1, 2, 2)
        grid.addWidget(self._merge, 3, 0, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        self.setLayout(grid)

