""" PushButtonDelegateQt.py: Delegate for a clickable button in a model view.

Calls the model's setData() method when clicked, wherein the button clicked action should be handled.
"""


try:
    from PyQt5.QtCore import Qt, QEvent, QT_VERSION_STR
    from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionButton, QStyle, QApplication
except ImportError:
    try:
        from PyQt4.QtCore import Qt, QEvent, QT_VERSION_STR
        from PyQt4.QtGui import QStyledItemDelegate, QStyleOptionButton, QStyle, QApplication
    except ImportError:
        raise ImportError("PushButtonDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class PushButtonDelegateQt(QStyledItemDelegate):
    """ Delegate for a clickable button in a model view.
    Calls the model's setData() method when clicked, wherein the button clicked action should be handled.
    """
    def __init__(self, text="", parent=None):
        QStyledItemDelegate.__init__(self, parent)
        self.text = text
        self._isMousePressed = False

    def createEditor(self, parent, option, index):
        """ Important, otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """ Draw button in cell.
        """
        opts = QStyleOptionButton()
        opts.state |= QStyle.State_Active
        opts.state |= QStyle.State_Enabled
        if QT_VERSION_STR[0] == '4':
            opts.state |= (QStyle.State_Sunken if self._isMousePressed else QStyle.State_Raised)
        elif QT_VERSION_STR[0] == '5':
            # When raised in PyQt5, white text cannot be seen on white background.
            # Should probably fix this by initializing form styled button, but for now I'll just sink it all the time.
            opts.state |= QStyle.State_Sunken
        opts.rect = option.rect
        opts.text = self.text
        QApplication.style().drawControl(QStyle.CE_PushButton, opts, painter)

    def editorEvent(self, event, model, option, index):
        """ Handle mouse events in cell.
        On left button release in this cell, call model's setData() method,
            wherein the button clicked action should be handled.
        Currently, the value supplied to setData() is the button text, but this is arbitrary.
        """
        if event.button() == Qt.LeftButton:
            if event.type() == QEvent.MouseButtonPress:
                if option.rect.contains(event.pos()):
                    self._isMousePressed = True
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                self._isMousePressed = False
                if option.rect.contains(event.pos()):
                    model.setData(index, self.text, Qt.EditRole)  # Model should handle button click action in its setData() method.
                    return True
        return False
