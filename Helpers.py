from PyQt5 import uic, QtCore, QtGui, QtWidgets
import json, re, os, logging


class AddTick(*uic.loadUiType('ui/addtick.ui')[::-1]):
    #The dialog that pops up to add a Ticker to the queue
    def __init__(self, ticks, parent = None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)
        completer = QtWidgets.QCompleter()
        completer.setCaseSensitivity(False)
        self.tickEdit.setCompleter(completer)

        model = QtCore.QStringListModel()
        completer.setModel(model)
        model.setStringList(ticks)

        self.okBut.clicked.connect(self.accept)
        self.cancelBut.clicked.connect(self.close)


class InitTest(*uic.loadUiType('ui/InitTest.ui')[::-1]):
    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)

        try:
            from resources.NASDAQ import tickCurrents

            nTest = tickCurrents('NVDA')
            if nTest:
                if nTest['LTP']:
                    self.setStates(self.nState, True)
                else:
                    self.setStates(self.nState, False)
            else: self.setStates(self.nState)
        except ImportError:
            self.setStates(self.nState)

        try:
            from Robinhood import Robinhood
            rTest = Robinhood()
            self.setStates(self.rState, True)
        except:
            self.setStates(self.rState)


    def setStates(self, button, state = False):
        '''
        Sets the button settings depending on the state of the test

        Args:
            button (QtWidgets.QPushButton): button to be changed
            state (bool): state of test

        Returns:
            None
        '''
        if state:
            button.setStyleSheet('background-color: rgb(85, 170, 127);')
            button.setText('Passed')
            button.setEnabled(False)
        else:
            button.setStyleSheet('background-color: rgb(170, 0, 0);')
            button.setText('Failed')
            button.setEnabled(True)
            

    def closeEvent(self, event):
           if not any(button.isEnabled() for button in [self.rState, self.nState]):
                self.accept()


class Api(*uic.loadUiType('ui/api.ui')[::-1]):
    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)

        self.setupUi(self)

        self.okBut.clicked.connect(self.ok)
        self.cancelBut.clicked.connect(self.close)

        #Determines if .cfg file already exists and sets data
        #if it does
        if os.path.isfile('core.cfg'):
            with open('core.cfg', 'r') as fileIn:
                try:
                    data = json.load(fileIn)
                    self.userEdit.setText(data['API']['User'])
                    self.passEdit.setText(data['API']['Password'])
                except json.decoder.JSONDecodeError:
                    pass


    def ok(self):
        #Writes the key and secret to the core.cfg file
        #then closes dialog
        if self.userEdit.text() and self.passEdit.text():
            self.user = self.userEdit.text()
            self.password = self.passEdit.text()

            self.accept()
            
        else:
            QtWidgets.QMessageBox.critical(
                None, 
                'Invalid Keys', 
                'Both Key and Secret Must Be Inputted', 
                QMessageBox.Ok
            )


class TimeThread(QtCore.QThread):
    #Threaded Timer, allows for background updates every 5 seconds, can be changed
    update = QtCore.pyqtSignal()

    def __init__(self, int = 5, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        self.int = int * 1000

    def run(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update.emit)
        self.timer.start(self.int)
        
        self.exec_()


def cleanComp(s):
    #Cleans the name of the company
    s = re.sub(r'[^A-Za-z0-9 ]', '', s)
    return re.sub(r'[, ]? Bond|Fund|Trust|com|Inc|Corp(oration)?|Company[.]?', '', 
            s.strip(), flags = re.I).strip()