import copy
from datetime import datetime
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QT_VERSION_STR
from PyQt5.QtWidgets import QTableView, QMenu, QInputDialog, QErrorMessage, QDialog, QDialogButtonBox, QVBoxLayout,\
     QTableWidget, QTableWidgetItem
from table.CheckBoxDelegateQt import CheckBoxDelegateQt
from table.FloatEditDelegateQt import FloatEditDelegateQt
from table.DateTimeEditDelegateQt import DateTimeEditDelegateQt
from table.ComboBoxDelegateQt import ComboBoxDelegateQt
from table.PushButtonDelegateQt import PushButtonDelegateQt
from table.FileDialogDelegateQt import FileDialogDelegateQt

def color(move):
    if move == 'R':
        #Red
        return QtGui.QColor(214, 102, 102)
    elif move == 'G':
        #Green
        return QtGui.QColor(102, 214, 102)
    else:
        #Grey
        return QtGui.QColor(144, 144, 144)


def getAttrRecursive(obj, attr):
    """ Recursive introspection (i.e. get the member 'b' of a member 'a' by name as 'a.b').
    """
    try:
        p = attr.index(".")
        obj = getattr(obj, attr[0:p])
        return getAttrRecursive(obj, attr[p+1:])
    except ValueError:
        return getattr(obj, attr)


def setAttrRecursive(obj, attr, value):
    """ Recursive introspection (i.e. set the member 'b' of a member 'a' by name as 'a.b').
    """
    try:
        p = attr.index(".")
        obj = getattr(obj, attr[0:p])
        setAttrRecursive(obj, attr[p+1:], value)
    except ValueError:
        setattr(obj, attr, value)


class ObjListTableModel(QAbstractTableModel):
    """ Qt model interface for specified attributes from a dynamic list of arbitrary objects.

    All objects in the list should be of the same type.
    Default is objects are rows and properties are columns.

    Displayed properties are specified as a list of dicts whose keys may include:
    'attr': Name of an object attribute. If specified, data() and setData() will get/set the attribute's value
        for the associated object.
        - May be a path to a child attribute such as "path.to.a.child.attr".
    'header': Text to display in the table's property header.
    'dtype': Attribute type. If not specified, this is inferred either from the templateObject or an object in the list.
    'mode': "Read/Write" or "Read Only". If not specified, defaults to "Read/Write".
    'choices': List of values or (key, value) tuples. If specified, the values (or their keys if they exist) are presented in a combo box.
    'action': Name of a special action associated with this cell. Actions include:
        "button": Clicking on the cell is treated as a button press.
            - setData() calls the object's method specified by the property's 'attr' key.
        "fileDialog": Double clicking on the cell pops up a file dialog.
            - setData() sets the property's 'attr' value to the "path/to/filename" returned form the dialog.
            - If you want some file loading script to run each time the file name is set, set 'attr' to the object
              @property.setter that set's the file name and runs the script.
    'text': String used by certain properties. For example, used to specify a datetime's format or a button's text.

    By specifying each object property (or action) displayed in the model/view as a dict,
    it is easy to simply add new key:value pairs for new custom delegates, and extend the model/view
    code to check for these properties. Furthermore, specifying properties in this way makes for
    easily readable code when adding properties to a model/view. For example:
        properties = [
            {'attr': "name",        'header': "Person", 'isReadOnly': True},  # Read only column of object.name strings.
            {'attr': "age",         'header': "Age"                       },  # Read/Write column of object.age integers.
            {'attr': "birthday",    'header': "D.O.B.", 'text': "%x"      },  # Read/Write column of object.birthday datetimes (format="%x").
            {'attr': "friend.name", 'header': "Friend"                    }]  # Read/Write column of object.friend.name strings.

    :param objects (list): List of objects.
    :param properties (list): List of property dicts {'attr'=str, 'header'=str, 'isReadOnly'=bool, 'choices'=[], ...}
    :param isRowObjects (bool): If True, objects are rows and properties are columns, otherwise vice-versa.
    :param isDynamic (bool): If True, objects can be inserted/deleted, otherwise not.
    :param templateObject (object): Object that will be deep copied to create new objects when inserting into the list.
    """
    def __init__(self, objects = None, properties = None, isRowObjects = True, isDynamic = True, templateObject = None, parent = None):
        QAbstractTableModel.__init__(self, parent)
        self.objects = objects if (objects is not None) else []
        self.properties = properties if (properties is not None) else []
        self.isRowObjects = isRowObjects
        self.isDynamic = isDynamic
        self.templateObject = templateObject


    def getObject(self, index):
        if not index.isValid():
            return None
        objectIndex = index.row() if self.isRowObjects else index.column()
        try:
            return self.objects[objectIndex]
        except IndexError:
            return None


    def getProperty(self, index):
        if not index.isValid():
            return None
        propertyIndex = index.column() if self.isRowObjects else index.row()
        try:
            return self.properties[propertyIndex]
        except IndexError:
            return None


    def rowCount(self, parent = None, *args, **kwargs):
        return len(self.objects) if self.isRowObjects else len(self.properties)


    def columnCount(self, parent = None, *args, **kwargs):
        return len(self.properties) if self.isRowObjects else len(self.objects)


    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return None
        obj = self.getObject(index)
        prop = self.getProperty(index)
        if role == Qt.BackgroundRole:
            return color(obj.D)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if (obj is None) or (prop is None):
            return None
        try:
            if role in [Qt.DisplayRole, Qt.EditRole]:
                return getAttrRecursive(obj, prop['attr'])
        except:
            return None
        return None


    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return False
        obj = self.getObject(index)
        prop = self.getProperty(index)
        if (obj is None) or (prop is None):
            return None
        try:
            action = prop.get('action', None)
            if action is not None:
                if action == "button":
                    getAttrRecursive(obj, prop['attr'])()  # Call obj.attr()
                    return True
                elif action == "fileDialog":
                    pass  # File loading handled via @property.setter obj.attr below. Otherwise just sets the file name text.
            if role == Qt.EditRole:
                if type(value) == QVariant:
                    value = value.toPyObject()
                if (QT_VERSION_STR[0] == '4') and (type(value) == QString):
                    value = str(value)
                setAttrRecursive(obj, prop['attr'], value)
                return True
        except:
            return False
        return False


    def flags(self, index):
        flags = QAbstractTableModel.flags(self, index)
        if not index.isValid():
            return flags
        prop = self.getProperty(index)
        if prop is None:
            return flags
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsSelectable
        mode = prop.get('mode', "Read/Write")
        if "Write" in mode:
            flags |= Qt.ItemIsEditable
        return flags


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if ((orientation == Qt.Horizontal) and self.isRowObjects) or ((orientation == Qt.Vertical) and not self.isRowObjects):
            # Display property headers.
            try:
                return self.properties[section]['header']  # Property header.
            except (IndexError, KeyError):
                return None
        else:
            # Display object indices (1-based).
            return (section + 1) if (0 <= section < len(self.objects)) else None


    def insertObjects(self, i, num = 1):
        if ((len(self.objects) == 0) and (self.templateObject is None)) or (num <= 0):
            return False
        i = min([max([0, i]), len(self.objects)])  # Clamp i to within [0, # of objects].
        if self.isRowObjects:
            self.beginInsertRows(QModelIndex(), i, i + num - 1)
        else:
            self.beginInsertColumns(QModelIndex(), i, i + num - 1)
        for objectIndex in range(i, i + num):
            if self.templateObject is not None:
                self.objects.insert(objectIndex, copy.deepcopy(self.templateObject))
            elif len(self.objects):
                copyIndex = min([max([0, objectIndex]), len(self.objects) - 1])  # Clamp objectIndex to a valid object index.
                self.objects.insert(objectIndex, copy.deepcopy(self.objects[copyIndex]))
        if self.isRowObjects:
            self.endInsertRows()
        else:
            self.endInsertColumns()
        return True


    def removeObjects(self, i, num = 1):
        if (len(self.objects) == 0) or (num <= 0):
            return False
        i = min([max([0, i]), len(self.objects) - 1])  # Clamp i to a valid object index.
        num = min([num, len(self.objects) - i])  # Clamp num to a valid number of objects.
        if num == len(self.objects):
            # Make sure we have a template for inserting objects later.
            if self.templateObject is None:
                self.templateObject = self.objects[0]
        if self.isRowObjects:
            self.beginRemoveRows(QModelIndex(), i, i + num - 1)
            del self.objects[i:i+num]
            self.endRemoveRows()
        else:
            self.beginRemoveColumns(QModelIndex(), i, i + num - 1)
            del self.objects[i:i+num]
            self.endRemoveColumns()
        return True


    def moveObjects(self, indices, moveToIndex):
        if len(self.objects) <= 1:
            return False
        try:
            if type(indices) is not list:
                indices = list(indices)
            for i, idx in enumerate(indices):
                indices[i] = min([max([0, idx]), len(self.objects) - 1])  # Clamp indices to valid object indices.
            moveToIndex = min([max([0, moveToIndex]), len(self.objects) - 1])  # Clamp moveToIndex to a valid object index.
            self.beginResetModel()
            objectsToMove = []
            for i in indices:
                objectsToMove.append(self.objects[i])
            for i in reversed(indices):
                del self.objects[i]
            for i, obj in enumerate(objectsToMove):
                j = moveToIndex + i
                j = min([max([0, j]), len(self.objects)])  # Clamp j to within [0, # of objects].
                self.objects.insert(j, obj)
            self.endResetModel()
            return True
        except:
            return False


    def clearObjects(self):
        if len(self.objects):
            if self.templateObject is None:
                self.templateObject = self.objects[0]
            self.beginResetModel()
            del self.objects[:]
            self.endResetModel()


    def propertyType(self, propertyIndex):
        try:
            prop = self.properties[propertyIndex]
            if 'dtype' in prop.keys():
                return prop['dtype']
            elif 'attr' in prop.keys():
                if self.templateObject is not None:
                    return type(getAttrRecursive(self.templateObject, prop['attr']))
                elif len(self.objects) > 0:
                    return type(getAttrRecursive(self.objects[0], prop['attr']))
        except:
            return None
        return None


class ObjListTable(QTableView):
    """ Qt view for a ObjListTableModel model.

    Right clicking in the view's row or column headers brings up a context menu for inserting/deleting/moving objects
    in the list (optional), or setting an attribute's value for all objects simultaneously.

    Delegates:
    bool: CheckBoxWithoutLabelDelegateQt() - centered check box (no label)
    float: FloatEditDelegateQt() - allows arbitrary precision and scientific notation
    datetime: DateTimeEditDelegateQt("date format") - datetime displayed according to "date format"
    combobox: ComboBoxDelegateQt([choice values or (key, value) tuples]) - list of choice values (or keys if they exist)
    buttons: PushButtonDelegateQt("button text") - clickable button, model's setData() handles the click
    files: FileDialogDelegateQt() - popup a file dialog, model's setData(pathToFileName) handles the rest
    """
    def __init__(self, model = None, parent = None):
        QTableView.__init__(self, parent)

        # Custom delegates.
        self._checkBoxDelegate = CheckBoxDelegateQt()
        self._floatEditDelegate = FloatEditDelegateQt()
        self._dateTimeEditDelegates = []  # Each of these can have different formats.
        self._comboBoxDelegates = []  # Each of these can have different choices.
        self._pushButtonDelegates = []  # Each of these can have different text.
        self._fileDialogDelegate = FileDialogDelegateQt()


    def setModel(self, model):
        if type(model) is not ObjListTableModel:
            raise RuntimeError("ObjListTable.setModel: Model type MUST be ObjListTableModel.")

        QTableView.setModel(self, model)

        # Clear current delegate lists.
        self._dateTimeEditDelegates = []  # Each of these can have different formats.
        self._comboBoxDelegates = []  # Each of these can have different choices.
        self._pushButtonDelegates = []  # Each of these can have different text.

        # Assign custom delegates.
        for i, prop in enumerate(model.properties):
            dtype = model.propertyType(i)
            if 'choices' in prop.keys():
                self._comboBoxDelegates.append(ComboBoxDelegateQt(prop['choices']))
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._comboBoxDelegates[-1])
                else:
                    self.setItemDelegateForRow(i, self._comboBoxDelegates[-1])
            elif prop.get('action', "") == "fileDialog":
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._fileDialogDelegate)
                else:
                    self.setItemDelegateForRow(i, self._fileDialogDelegate)
            elif prop.get('action', "") == "button":
                self._pushButtonDelegates.append(PushButtonDelegateQt(prop.get('text', "")))
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._pushButtonDelegates[-1])
                else:
                    self.setItemDelegateForRow(i, self._pushButtonDelegates[-1])
            elif dtype is bool:
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._checkBoxDelegate)
                else:
                    self.setItemDelegateForRow(i, self._checkBoxDelegate)
            elif dtype is float:
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._floatEditDelegate)
                else:
                    self.setItemDelegateForRow(i, self._floatEditDelegate)
            elif dtype is datetime:
                self._dateTimeEditDelegates.append(DateTimeEditDelegateQt(prop.get('text', '%c')))
                if model.isRowObjects:
                    self.setItemDelegateForColumn(i, self._dateTimeEditDelegates[-1])
                else:
                    self.setItemDelegateForRow(i, self._dateTimeEditDelegates[-1])

        # Resize columns to fit content.
        self.resizeColumnsToContents()


    def clearObjects(self):
        self.model().clearObjects()


    def setPropertyForAllObjects(self):
        selectedPropertyIndices = self.selectedColumns() if self.model().isRowObjects else self.selectedRows()
        if len(selectedPropertyIndices) != 1:
            errorDialog = QErrorMessage(self)
            rowOrColumn = "column" if self.model().isRowObjects else "row"
            errorDialog.showMessage("Must select a single property " + rowOrColumn + ".")
            errorDialog.exec_()
            return
        try:
            propertyIndex = selectedPropertyIndices[0]
            dtype = self.model().propertyType(propertyIndex)
            if dtype is None:
                return
            obj = self.model().objects[0]
            prop = self.model().properties[propertyIndex]
            if "Write" not in prop.get('mode', "Read/Write"):
                return
            model = ObjListTableModel([obj], [prop], self.model().isRowObjects, False)
            view = ObjListTable(model)
            dialog = QDialog(self)
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            vbox = QVBoxLayout(dialog)
            vbox.addWidget(view)
            vbox.addWidget(buttons)
            dialog.setWindowModality(Qt.WindowModal)
            dialog.exec_()
            for objectIndex, obj in enumerate(self.model().objects):
                row = objectIndex if self.model().isRowObjects else propertyIndex
                col = propertyIndex if self.model().isRowObjects else objectIndex
                index = self.model().index(row, col)
                if objectIndex == 0:
                    value = self.model().data(index)
                else:
                    if prop.get('action', '') == "fileDialog":
                        try:
                            getAttrRecursive(obj, prop['attr'])(value)
                            self.model().dataChanged.emit(index, index)  # Tell model to update cell display.
                        except:
                            self.model().setData(index, value)
                            self.model().dataChanged.emit(index, index)  # Tell model to update cell display.
                    else:
                        self.model().setData(index, value)
                        self.model().dataChanged.emit(index, index)  # Tell model to update cell display.
        except:
            pass


class Transactions(QTableWidget):
    #Custom QTableWidget 
    def __init__(self, parent = None):
        QTableWidget.__init__(self, parent)


    def bought(self, tick):
        _row = self.rowCount()
        self.insertRow(_row)
        data = [tick.T, tick.PQ, tick.C, '']
        for item in range(len(data)):
            tItem = QTableWidgetItem(str(data[item]))
            tItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(_row, item, tItem)


    def sold(self, tick):
        results = self.findItems(tick.T, Qt.MatchExactly)
        if results:
            for row in results:
                _row = row.row()
                if not self.item(_row, 3).text():
                    tItem = QTableWidgetItem(str(tick.C))
                    tItem.setTextAlignment(Qt.AlignCenter)
                    self.setItem(_row, 3, tItem)

                    for j in range(self.columnCount()):
                        if tick.prevProfit > 0:
                            self.item(_row, j).setBackground(color('G'))
                        elif tick.prevProfit < 0:
                            self.item(_row, j).setBackground(color('R'))
                        else:
                            self.item(_row, j).setBackground(color('NA'))
        else:
            _row = self.rowCount()
            self.insertRow(_row)
            data = [tick.T, tick.Q, tick.AP, tick.C]
            for item in range(len(data)):
                tItem = QTableWidgetItem(str(data[item]))
                tItem.setTextAlignment(Qt.AlignCenter)
                self.setItem(_row, item, tItem)

            for j in range(self.columnCount()):
                if tick.C > tick.AP:
                    self.item(_row, j).setBackground(color('G'))
                elif tick.AP < tick.C:
                    self.item(_row, j).setBackground(color('R'))
                else:
                    self.item(_row, j).setBackground(color('NA'))