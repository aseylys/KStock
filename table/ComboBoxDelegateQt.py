""" ComboBoxDelegateQt.py: Delegate for editing a list of choices via a combobox.

Choices can be a list of values (e.g. [1, 3, 10, 100])
or a list of (key, value) tuples (e.g. [('A', MyObject()), ('B', MyObject())]).
In the latter case, the view only displays the keys (e.g. 'A', 'B') whereas
the model data reflects the values (e.g. MyObject instances).
"""


import copy
try:
    from PyQt5.QtCore import Qt, QVariant
    from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox
except ImportError:
    try:
        from PyQt4.QtCore import Qt, QVariant
        from PyQt4.QtGui import QStyledItemDelegate, QComboBox
    except ImportError:
        raise ImportError("ComboBoxDelegateQt: Requires PyQt5 or PyQt4.")


__author__ = "Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>"


class ComboBoxDelegateQt(QStyledItemDelegate):
    """ Delegate for editing a list of choices via a combobox.
    The choices attribute is a list of either values or (key, value) tuples.
    In the first case, the str rep of the values are directly displayed in the combobox.
    In the latter case, the str rep of only the keys are displayed in the combobox, and the values can be any object.
        Although only the keys are displayed in the view, the model data is set to the actual values, not the keys.
    Upon selection, view will display the str rep of either the value itself or its key if it exists.

    For example:
        To select from some integers, set choices = [1, 3, 10, 100].
            Combobox entries will be '1', '3', '10' and '100'.
            Upon selection model data will be set to the selected integer value and view will show the str rep of this value.
        To select from two of your custom objects, set choices = [('A', MyObject()), ('B', MyObject())]
            Combobox entries will be 'A' and 'B'.
            Upon selection model data will be set to the selected MyObject instance and view will show its key (either 'A' or 'B')..
    """
    def __init__(self, choices=None, parent=None):
        QStyledItemDelegate.__init__(self, parent)
        self.choices = choices if (choices is not None and type(choices) is list) else []

    def createEditor(self, parent, option, index):
        """ Return QComboBox with list of choices (either values or their associated keys if they exist).
        """
        try:
            editor = QComboBox(parent)
            value = index.model().data(index, Qt.DisplayRole)
            for i, choice in enumerate(self.choices):
                if (type(choice) is tuple) and (len(choice) == 2):
                    # choice is a (key, value) tuple.
                    key, val = choice
                    editor.addItem(str(key))  # key MUST be representable as a str.
                    if val == value:
                        editor.setCurrentIndex(i)
                else:
                    # choice is a value.
                    editor.addItem(str(choice))  # choice MUST be representable as a str.
                    if choice == value:
                        editor.setCurrentIndex(i)
            return editor
        except:
            return None

    def setModelData(self, editor, model, index):
        """ Set model data to current choice (if choice is a key, set data to its associated value).
        """
        try:
            choice = self.choices[editor.currentIndex()]
            if (type(choice) is tuple) and (len(choice) == 2):
                # choice is a (key, value) tuple.
                key, val = choice
                value = copy.deepcopy(val)  # Deepcopy of val in case it is a complex object.
            else:
                # choice is a value.
                value = choice
            model.setData(index, value, Qt.EditRole)
            index.model().dataChanged.emit(index, index)  # Tell model to update cell display.
        except:
            pass

    def displayText(self, value, locale):
        """ Show str rep of current choice (or choice key if choice is a (key, value) tuple).
        """
        try:
            if type(value) == QVariant:
                value = value.toPyObject()  # QVariant ==> object
            for choice in self.choices:
                if (type(choice) is tuple) and (len(choice) == 2):
                    # choice is a (key, value) tuple.
                    # Display the key, not the value.
                    key, val = choice
                    if val == value:
                        return str(key)
                else:
                    # choice is a value.
                    # Display it's str rep.
                    if choice == value:
                        return str(choice)
            # If value is not in our list of choices, show str rep of value.
            return str(value)
        except:
            return ""
