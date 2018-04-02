""" FloatEditDelegateQt.py: Delegate for editing float values
with arbitrary precision that may also be in scientific notation.
"""


try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
except ImportError:
    try:
        from PyQt4.QtCore import Qt
        from PyQt4.QtGui import QStyledItemDelegate, QLineEdit
    except ImportError:
        raise ImportError("FloatEditDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class FloatEditDelegateQt(QStyledItemDelegate):
    """ Delegate for editing float values with arbitrary precision that may also be in scientific notation.
    Based on a QLineEdit rather than Qt's default QDoubleSpinBox that limits values to two decimal places
    and cannot handle scientific notation.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """ Return a QLineEdit for arbitrary representation of a float value.
        """
        editor = QLineEdit(parent)
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(str(value))
        return editor

    def setModelData(self, editor, model, index):
        """ Cast the QLineEdit text to a float value, and update the model with this value.
        """
        try:
            value = float(editor.text())
            model.setData(index, value, Qt.EditRole)
        except:
            pass  # If we can't cast the user's input to a float, don't do anything.
