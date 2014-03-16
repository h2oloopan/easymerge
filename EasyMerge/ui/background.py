from PyQt4 import QtGui
from tmp.dummy import Dummy
from merger.analyzer import Analyzer
import os
from merger.Result import Result

class Background(QtGui.QWidget):
    def __init__(self):
        super(Background, self).__init__()
        self._list = QtGui.QListWidget(self)
        self._tabs = QtGui.QTabWidget(self)
        self._result = QtGui.QTextBrowser(self)
        self._info = QtGui.QTextBrowser(self)
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
        grid.addWidget(self._list, 1, 0, 1, 1)
        grid.addWidget(self._tabs, 1, 1, 1, 2)
        grid.addWidget(self._result, 2, 1, 2, 2)
        grid.addWidget(self._info, 2, 0, 1, 1)

        box = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        box.addWidget(self._merge)
        box.addWidget(self._unmerge)
        grid.addLayout(box, 3, 0, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        self.setLayout(grid)

        #binding events
        self._open.clicked.connect(self.openClicked)
        self._analyze.clicked.connect(self.analyzeClicked)
        self._merge.clicked.connect(self.mergeClicked)
        self._unmerge.clicked.connect(self.unmergeClicked)
        self._list.itemClicked.connect(self.listClicked)


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
            analyzer = Analyzer()
            result = analyzer.analyze(self._path)
            self.updateUI(result)

    def updateUI(self, sets):
        self._sets = sets
        self._list.clear()
        counter = 1
        for set in sets:
            item = QtGui.QListWidgetItem('Merge ' + str(counter))
            item.setForeground(QtGui.QColor('red'))
            self._list.addItem(item)
            counter += 1

    def populateTabs(self, sets):
        self._tabs.clear()
        counter = 0
        for key in sets:
            title = key[0]
            start = key[1]
            end = key[2]
            replacement = str(sets[key])
            text = self.generateText(title, start, end, replacement)
            self._tabs.addTab(text, os.path.split(title)[1])
            self._tabs.setTabToolTip(counter, title)
            counter += 1

    def generateText(self, title, start, end, replacement):
        browser = QtGui.QTextBrowser(self)
        f = open(title)
        lines = f.readlines()
        counter = 0
        for line in lines:
            indent = ''
            for i in range(0, 6 - len(str(counter))):
                indent += ' '
            indent += str(counter) + ':    '
            browser.insertPlainText(indent + line)
            counter += 1

        block = browser.document().findBlockByLineNumber(start + 15)
        cursor = browser.textCursor()
        cursor.setPosition(block.position())
        browser.setFocus()
        browser.setTextCursor(cursor)
        return browser

    def listClicked(self, item):
        index = item.listWidget().currentRow()
        curSet = self._sets[index]
        #debug
        curSet.output()

        #_code
        self._result.clear()
        self._result.insertPlainText(curSet.get_code())

        #_caller
        self.populateTabs(curSet.get_caller())



    def mergeClicked(self):
        print 'mergining...'

    def unmergeClicked(self):
        print 'unmerging...'

