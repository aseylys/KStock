""" DateTimeEditDelegateQt.py: Delegate for editing datetime objects with a user specified format.

Format str passed to datetime.strftime() and datetime.strptime().
"""


from datetime import datetime
try:
    from PyQt5.QtCore import Qt, QT_VERSION_STR
    from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
except ImportError:
    try:
        from PyQt4.QtCore import Qt, QT_VERSION_STR
        from PyQt4.QtGui import QStyledItemDelegate, QLineEdit
    except ImportError:
        raise ImportError("DateTimeEditDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class DateTimeEditDelegateQt(QStyledItemDelegate):
    """ Delegate for editing datetime objects with a user specified format.
    The format attribute is a str that is passed to datetime.strftime() and datetime.strptime().
    """
    def __init__(self, format="%c", parent=None):
        QStyledItemDelegate.__init__(self, parent)
        self.format = format

    def createEditor(self, parent, option, index):
        """ Return a QLineEdit for arbitrary representation of a date value in any format.
        """
        editor = QLineEdit(parent)
        date = index.model().data(index, Qt.DisplayRole)
        editor.setText(date.strftime(self.format))
        return editor

    def setModelData(self, editor, model, index):
        """ Only update the model data if the editor's current text conforms to the specified date format.
        """
        try:
            date = datetime.strptime(str(editor.text()), self.format)
            model.setData(index, date, Qt.EditRole)
        except:
            pass  # If the text does not conform to the date format, do nothing.

    def displayText(self, value, locale):
        """ Show the date in the specified format.
        """
        try:
            if QT_VERSION_STR[0] == '4':
                date = value.toPyObject()  # QVariant ==> datetime
            elif QT_VERSION_STR[0] == '5':
                date = value
            return date.strftime(self.format)
        except:
            return ""
