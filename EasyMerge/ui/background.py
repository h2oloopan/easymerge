from PyQt4 import QtGui
from tmp.dummy import Dummy

class Background(QtGui.QWidget):
    def __init__(self):
        super(Background, self).__init__()
        self._list = QtGui.QListWidget(self)
        self._tabs = QtGui.QTabWidget(self)
        self._result = QtGui.QTextBrowser(self)
        self._merge = QtGui.QPushButton('Merge', self)
        self._unmerge = QtGui.QPushButton('Unmerge', self)
        self._analyze = QtGui.QPushButton('Analyze', self)
        self._open = QtGui.QPushButton('Open Source', self)
        self._source = QtGui.QLineEdit(self)
        self._source.setReadOnly(True)
        self._path = ''
        self._sets = []
        self.initUI()

    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(self._open, 0, 0, 1, 1)
        grid.addWidget(self._source, 0, 1, 1, 1)
        grid.addWidget(self._analyze, 0, 2, 1, 1)
        grid.addWidget(self._list, 1, 0, 2, 1)
        grid.addWidget(self._tabs, 1, 1, 1, 2)
        grid.addWidget(self._result, 2, 1, 2, 2)

        box = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        box.addWidget(self._merge)
        box.addWidget(self._unmerge)
        grid.addLayout(box, 3, 0, 1, 1)

        #grid.addWidget(self._merge, 3, 0, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        self.setLayout(grid)

        #binding events
        self._open.clicked.connect(self.openClicked)
        self._analyze.clicked.connect(self.analyzeClicked)
        self._merge.clicked.connect(self.mergeClicked)
        self._unmerge.clicked.connect(self.unmergeClicked)

    def openClicked(self):
        sender = self.sender()
        self._path = str(QtGui.QFileDialog.getExistingDirectory(sender, 'Select source code directory'))
        self._source.setText(self._path)


    def analyzeClicked(self):
        if self._path == '':
            msg = QtGui.QMessageBox(self)
            msg.setText('Please select source code directory first by clicking [Open Source]')
            msg.exec_()
        else:
            #analyze
            sets = Dummy().do()
            self.updateUI(sets)

    def updateUI(self, sets):
        self._sets = sets
        for set in sets:
            item = QtGui.QListWidgetItem(str(set))
            item.setForeground(QtGui.QColor('red'))
            self._list.addItem(item)


    def mergeClicked(self):
        print 'mergining...'

    def unmergeClicked(self):
        print 'unmerging...'

