""" FileDialogDelegateQt.py: Delegate that pops up a file dialog when double clicked.

Sets the model data to the selected file name.
"""


import os.path
try:
    from PyQt5.QtCore import Qt, QT_VERSION_STR
    from PyQt5.QtWidgets import QStyledItemDelegate, QFileDialog
except ImportError:
    try:
        from PyQt4.QtCore import Qt, QT_VERSION_STR
        from PyQt4.QtGui import QStyledItemDelegate, QFileDialog
    except ImportError:
        raise ImportError("FileDialogDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class FileDialogDelegateQt(QStyledItemDelegate):
    """ Delegate that pops up a file dialog when double clicked.
    Sets the model data to the selected file name.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """ Instead of creating an editor, just popup a modal file dialog
        and set the model data to the selected file name, if any.
        """
        pathToFileName = ""
        if QT_VERSION_STR[0] == '4':
            pathToFileName = QFileDialog.getOpenFileName(None, "Open")
        elif QT_VERSION_STR[0] == '5':
            pathToFileName, temp = QFileDialog.getOpenFileName(None, "Open")
        pathToFileName = str(pathToFileName)  # QString ==> str
        if len(pathToFileName):
            index.model().setData(index, pathToFileName, Qt.EditRole)
            index.model().dataChanged.emit(index, index)  # Tell model to update cell display.
        return None

    def displayText(self, value, locale):
        """ Show file name without path.
        """
        try:
            if QT_VERSION_STR[0] == '4':
                pathToFileName = str(value.toString())  # QVariant ==> str
            elif QT_VERSION_STR[0] == '5':
                pathToFileName = str(value)
            path, fileName = os.path.split(pathToFileName)
            return fileName
        except:
            return ""
