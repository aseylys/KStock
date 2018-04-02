""" CheckBoxDelegateQt.py: Delegate for editing bool values via a checkbox with no label centered in its cell.
"""


try:
    from PyQt5.QtCore import Qt, QEvent, QPoint, QRect
    from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionButton, QStyle, QApplication
except ImportError:
    try:
        from PyQt4.QtCore import Qt, QEvent, QPoint, QRect
        from PyQt4.QtGui import QStyledItemDelegate, QStyleOptionButton, QStyle, QApplication
    except ImportError:
        raise ImportError("CheckBoxDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class CheckBoxDelegateQt(QStyledItemDelegate):
    """ Delegate for editing bool values via a checkbox with no label centered in its cell.
    Does not actually create a QCheckBox, but instead overrides the paint() method to draw the checkbox directly.
    Mouse events are handled by the editorEvent() method which updates the model's bool value.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """ Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """ Paint a checkbox without the label.
        """
        checked = bool(index.model().data(index, Qt.DisplayRole))
        opts = QStyleOptionButton()
        opts.state |= QStyle.State_Active
        if index.flags() & Qt.ItemIsEditable:
            opts.state |= QStyle.State_Enabled
        else:
            opts.state |= QStyle.State_ReadOnly
        if checked:
            opts.state |= QStyle.State_On
        else:
            opts.state |= QStyle.State_Off
        opts.rect = self.getCheckBoxRect(option)
        QApplication.style().drawControl(QStyle.CE_CheckBox, opts, painter)

    def editorEvent(self, event, model, option, index):
        """ Change the data in the model and the state of the checkbox if the
        user presses the left mouse button and this cell is editable. Otherwise do nothing.
        """
        if not (index.flags() & Qt.ItemIsEditable):
            return False
        if event.button() == Qt.LeftButton:
            if event.type() == QEvent.MouseButtonRelease:
                if self.getCheckBoxRect(option).contains(event.pos()):
                    self.setModelData(None, model, index)
                    return True
            elif event.type() == QEvent.MouseButtonDblClick:
                if self.getCheckBoxRect(option).contains(event.pos()):
                    return True
        return False

    def setModelData(self, editor, model, index):
        """ Toggle the boolean state in the model.
        """
        checked = not bool(index.model().data(index, Qt.DisplayRole))
        model.setData(index, checked, Qt.EditRole)

    def getCheckBoxRect(self, option):
        """ Get rect for checkbox centered in option.rect.
        """
        # Get size of a standard checkbox.
        opts = QStyleOptionButton()
        checkBoxRect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, opts, None)
        # Center checkbox in option.rect.
        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        checkBoxTopLeftCorner = QPoint(x + w / 2 - checkBoxRect.width() / 2, y + h / 2 - checkBoxRect.height() / 2)
        return QRect(checkBoxTopLeftCorner, checkBoxRect.size())
