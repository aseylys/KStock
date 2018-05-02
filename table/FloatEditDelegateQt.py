from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit


class FloatEditDelegateQt(QStyledItemDelegate):
    ''' 
    Delegate for editing float values with arbitrary precision that may also be in scientific notation.
    Based on a QLineEdit rather than Qt's default QDoubleSpinBox that limits values to two decimal places
    and cannot handle scientific notation.
    '''
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        ''' 
        Return a QLineEdit for arbitrary representation of a float value.
        '''
        editor = QLineEdit(parent)
        value = index.model().data(index, Qt.DisplayRole)
        editor.setText(str(value))
        return editor


    def setModelData(self, editor, model, index):
        ''' 
        Cast the QLineEdit text to a float value, and update the model with this value.
        '''
        try:
            value = float(editor.text())
            model.setData(index, value, Qt.EditRole)
        except:
            pass  # If we can't cast the user's input to a float, don't do anything.
