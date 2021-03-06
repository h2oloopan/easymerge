from PyQt4 import QtGui
from tmp.dummy import Dummy
from merger.analyzer import Analyzer
import os
import time
from merger.Result import Result


class Background(QtGui.QWidget):
    def __init__(self):
        super(Background, self).__init__()
        self._list = QtGui.QListWidget(self)
        self._tabs = QtGui.QTabWidget(self)
        self._result = QtGui.QTextEdit(self)
        self._log = QtGui.QTextBrowser(self)
        self._eval = QtGui.QTextBrowser(self)
        self._merge = QtGui.QPushButton('Merge', self)
        self._unmerge = QtGui.QPushButton('Unmerge', self)
        self._analyze = QtGui.QPushButton('Analyze', self)
        self._open = QtGui.QPushButton('Open Source', self)
        self._source = QtGui.QLineEdit(self)
        self._source.setReadOnly(True)
        self._path = ''
        self._sets = []
        self.initUI()
        self.log('EasyMerge started')
        self.log('UI initialization completed')
        self.log('Please pick source tree to analyze')


    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(self._open, 0, 0, 1, 1)
        grid.addWidget(self._source, 0, 1, 1, 1)
        grid.addWidget(self._analyze, 0, 2, 1, 1)
        grid.addWidget(self._list, 1, 0, 1, 1)
        grid.addWidget(self._tabs, 1, 1, 1, 2)
        grid.addWidget(self._result, 2, 1, 2, 2)
        #grid.addWidget(self._info, 2, 0, 1, 1)

        #merge and unmerge buttons
        box = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        box.addWidget(self._merge)
        box.addWidget(self._unmerge)
        grid.addLayout(box, 3, 0, 1, 1)

        #log and eval
        box2 = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        box2.addWidget(self._log)
        box2.addWidget(self._eval)
        grid.addLayout(box2, 2, 0, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)

        self.setLayout(grid)

        #binding events
        self._open.clicked.connect(self.openClicked)
        self._analyze.clicked.connect(self.analyzeClicked)
        self._merge.clicked.connect(self.mergeClicked)
        self._unmerge.clicked.connect(self.unmergeClicked)
        self._list.itemClicked.connect(self.listClicked)

    def log(self, text):
        now = time.strftime('%c')
        text = '[' + now + '] - \n    ' + text
        self._log.insertPlainText(text + '\n')
        f = open('log.txt', 'a+')
        f.write(text + '\n')
        f.close()


    def populateEval(self, index):
        #Populate evaluation information for one clone set
        curSet = self._sets[index]
        re = curSet.re
        sets = curSet.get_caller()
        
        dummy  = 'Mergeable ' + str(index + 1) + ' evaluation:\n'
        counter = 1
        for key in sets:
            dummy += 'File ' + str(index + 1) + ': ' + key[0] + '\n'
            dummy += 'File ' + str(index + 1) + ' Path: ' + key[3] + '\n'
            counter += 1

        dummy += 'External references: ' + str(re[1]) + '\n'
        dummy += 'Extra return parameters: ' + str(re[2]) + '\n'
        dummy += 'Clone length: ' + str(re[0]) + ' lines\n'
        
        result = re[0] * 0.5 - re[1] - re[2] * 2 - re[3] * 1.8
        
        if result > 8:
            dummy += 'Merge is recommended\n'
        elif result > 0:
            dummy += 'Merge is somewhat recommended\n'
        else:
            dummy += 'Merge is not recommended\n'
            
        self._eval.clear()
        self._eval.insertPlainText(dummy)
        return dummy

    def warn(self, msg):
        box = QtGui.QMessageBox(self)
        box.setText(msg)
        box.exec_()

    def openClicked(self):
        sender = self.sender()
        self._path = str(QtGui.QFileDialog.getExistingDirectory(sender, 'Select source code directory'))
        self._source.setText(self._path)


    def analyzeClicked(self):
        if self._path == '':
            self.warn('Please select source code directory first by clicking [Open Source]')
        else:
            #analyze
            self.log('Start running CloneDigger...')
            analyzer = Analyzer()
            result = analyzer.analyze(self._path)
            self.updateUI(result)


    def updateUI(self, sets):
        self._sets = sets
        self._list.clear()
        counter = 1
        for set in sets:
            item = QtGui.QListWidgetItem('Merge ' + str(counter))
            item.setForeground(QtGui.QColor('green'))
            self._list.addItem(item)
            counter += 1

        self.log(str(counter - 1) + ' mergeable clone sets found')

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
        browser = QtGui.QTextEdit(self)
        f = open(title)
        lines = f.readlines()
        f.close()
        counter = 1
        for line in lines:
            indent = ''
            for i in range(0, 6 - len(str(counter))):
                indent += ' '
            indent += str(counter) + ':    '

            if counter == start + 1:
                browser.insertHtml('###REMOVE CODE BELOW###')
                browser.insertPlainText('\n')
            elif counter == end + 2:
                browser.insertHtml('###REMOVE CODE ABOVE###')
                browser.insertPlainText('\n')
                browser.insertPlainText('###REPLACE WITH###')
                browser.insertPlainText('\n')
                browser.insertPlainText(replacement)
                browser.insertPlainText('###REPLACE END###')
                browser.insertPlainText('\n')
            #this actually print the line
            browser.insertPlainText(indent + line)

            counter += 1

        block = browser.document().findBlockByLineNumber(start + 10)
        cursor = browser.textCursor()
        cursor.setPosition(block.position())
        browser.setFocus()
        browser.setTextCursor(cursor)
        return browser

    def listClicked(self, item):
        index = item.listWidget().currentRow()
        curSet = self._sets[index]

        #_code
        self._result.clear()
        self._result.insertPlainText(curSet.get_code())

        sets = curSet.get_caller()
        #_caller
        self.populateTabs(sets)

        #evaluation
        log = self.populateEval(index)
        self.log(log)


    def mergeClicked(self):
        item = self._list.currentItem()
        index = self._list.currentRow()
        sets = self._sets[index].get_caller()
        redness = item.foreground().color().red()
        if redness == 0:
            #green
            item.setForeground(QtGui.QColor('red'))
            info = 'Files:\n'
            for key in sets:
                info += key[0] + '\n'
            info += 'merged.\n'
            self.log(info)
        else:
            #red
            self.warn('Item has already been merged!')

        color = str(item.foreground().color().red())
        print color
        print 'mergining...'

    def unmergeClicked(self):
        item = self._list.currentItem()
        index = self._list.currentRow()
        sets = self._sets[index].get_caller()
        redness = item.foreground().color().red()
        if redness == 0:
            #green
            self.warn('Item has not been merged yet!')
        else:
            #red
            item.setForeground(QtGui.QColor('green'))
            info = 'Files:\n'
            for key in sets:
                info += key[0] + '\n'
            info == 'unmerged.\n'
            self.log(info)
        print 'unmerging...'

