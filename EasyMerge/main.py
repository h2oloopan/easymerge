'''
Created on Mar 4, 2014

@author: Shengying
'''

import sys
from ui.background import Background
from PyQt4 import QtGui

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    bg = Background()
    bg.setWindowTitle('EasyMerge - Clone Refactor')
    bg.showMaximized()
    sys.exit(app.exec_())
