"""Qt compatibility helpers for modern PyQt.

FlatCAM 8.x was written against PyQt4, where widgets lived in QtGui and many
Qt enums were available as unscoped attributes.  Prefer PyQt6 when available,
then fall back to PyQt5, while exposing the small PyQt4-shaped surface the app
uses internally.
"""

import sys
import types


try:
    from PyQt6 import QtCore, QtGui as _QtGui, QtWidgets
    QT_API = "PyQt6"
except ImportError:
    try:
        from PyQt5 import QtCore, QtGui as _QtGui, QtWidgets
        QT_API = "PyQt5"
    except ImportError as exc:
        raise ImportError(
            "FlatCAM requires PyQt6 or PyQt5. Install dependencies with "
            "`python3 -m pip install -r requirements.txt`."
        ) from exc


def _copy_public_attrs(source, target):
    for name in dir(source):
        if not name.startswith("_"):
            setattr(target, name, getattr(source, name))


QtGui = types.ModuleType(__name__ + ".QtGui")
_copy_public_attrs(_QtGui, QtGui)
_copy_public_attrs(QtWidgets, QtGui)
QtGui.QItemSelectionModel = QtCore.QItemSelectionModel

Qt = types.ModuleType(__name__ + ".Qt")
Qt.Qt = QtCore.Qt
_copy_public_attrs(QtCore, Qt)
_copy_public_attrs(_QtGui, Qt)
_copy_public_attrs(QtWidgets, Qt)


def _alias_enum(container, enum_name, names):
    enum = getattr(container, enum_name, None)
    if enum is None:
        return
    for name in names:
        if hasattr(container, name) or not hasattr(enum, name):
            continue
        try:
            setattr(container, name, getattr(enum, name))
        except Exception:
            pass


_alias_enum(QtCore.Qt, "AlignmentFlag", [
    "AlignLeft", "AlignRight", "AlignHCenter", "AlignTop", "AlignVCenter"
])
_alias_enum(QtCore.Qt, "DockWidgetArea", [
    "AllDockWidgetAreas", "BottomDockWidgetArea"
])
_alias_enum(QtCore.Qt, "KeyboardModifier", ["ControlModifier"])
_alias_enum(QtCore.Qt, "Key", ["Key_Delete", "Key_Space"])
_alias_enum(QtCore.Qt, "ItemDataRole", ["DisplayRole", "DecorationRole", "CheckStateRole"])
_alias_enum(QtCore.Qt, "ItemFlag", ["ItemIsSelectable", "ItemIsEnabled"])
_alias_enum(QtCore.Qt, "CheckState", ["Unchecked", "Checked"])
_alias_enum(QtCore.Qt, "ScrollBarPolicy", ["ScrollBarAlwaysOff", "ScrollBarAsNeeded"])
_alias_enum(QtCore.Qt, "GlobalColor", ["white", "black", "darkGreen"])

_alias_enum(QtGui.QFrame, "Shape", ["StyledPanel"])
_alias_enum(QtGui.QFrame, "Shadow", ["Plain"])
_alias_enum(QtGui.QHeaderView, "ResizeMode", ["ResizeToContents", "Stretch"])
_alias_enum(QtGui.QMessageBox, "StandardButton", ["Ok", "Cancel"])
_alias_enum(QtGui.QMessageBox, "Icon", ["Information", "Warning", "Critical"])
_alias_enum(QtGui.QSizePolicy, "Policy", ["Ignored", "Maximum"])
_alias_enum(QtGui.QTextCursor, "MoveOperation", ["End"])
_alias_enum(QtGui.QKeySequence, "StandardKey", [
    "InsertParagraphSeparator", "MoveToNextLine", "MoveToPreviousLine",
    "MoveToNextPage", "MoveToPreviousPage"
])
_alias_enum(QtGui.QAbstractItemView, "SelectionMode", ["ExtendedSelection"])
_alias_enum(QtGui.QItemSelectionModel, "SelectionFlag", ["Select", "Deselect"])
_alias_enum(QtCore.QEvent, "Type", ["Resize"])
_alias_enum(QtGui.QDockWidget, "DockWidgetFeature", [
    "DockWidgetMovable", "DockWidgetFloatable", "DockWidgetClosable"
])

Qt.Checked = QtCore.Qt.Checked
Qt.Unchecked = QtCore.Qt.Unchecked

if not hasattr(QtCore, "QVariant"):
    QtCore.QVariant = lambda value=None: value

if not hasattr(QtCore, "SIGNAL"):
    QtCore.SIGNAL = lambda signature: signature


def _find_signal(sender, signature):
    name = signature.split("(", 1)[0]
    if hasattr(sender, name):
        return getattr(sender, name)

    for attr_name in dir(sender):
        try:
            attr = getattr(sender, attr_name)
        except Exception:
            continue
        if not hasattr(attr, "connect"):
            continue
        signal_name = getattr(attr, "signal", "")
        if signal_name and signal_name.lstrip("0123456789").split("(", 1)[0] == name:
            return attr

    raise AttributeError("Signal %s not found on %r" % (signature, sender))


def _qt4_connect(self, sender, signal, slot):
    if isinstance(signal, str):
        signal = _find_signal(sender, signal)
    return signal.connect(slot)


if not hasattr(QtCore.QObject, "connect"):
    QtCore.QObject.connect = _qt4_connect


def _add_exec_alias(cls):
    if hasattr(cls, "exec") and not hasattr(cls, "exec_"):
        def _exec(self, *args, **kwargs):
            return self.exec(*args, **kwargs)

        cls.exec_ = _exec


for _cls in (QtWidgets.QApplication, QtWidgets.QDialog, QtWidgets.QMessageBox, QtCore.QEventLoop):
    _add_exec_alias(_cls)

if not hasattr(QtGui.QHeaderView, "setResizeMode") and hasattr(QtGui.QHeaderView, "setSectionResizeMode"):
    def _set_resize_mode(self, *args):
        return self.setSectionResizeMode(*args)

    QtGui.QHeaderView.setResizeMode = _set_resize_mode


def _qt4_file_dialog_result(result):
    if isinstance(result, tuple):
        return result[0]
    return result


_get_open_file_name = QtGui.QFileDialog.getOpenFileName
_get_open_file_names = QtGui.QFileDialog.getOpenFileNames
_get_save_file_name = QtGui.QFileDialog.getSaveFileName


def _qt4_get_open_file_name(*args, **kwargs):
    return _qt4_file_dialog_result(_get_open_file_name(*args, **kwargs))


def _qt4_get_open_file_names(*args, **kwargs):
    return _qt4_file_dialog_result(_get_open_file_names(*args, **kwargs))


def _qt4_get_save_file_name(*args, **kwargs):
    return _qt4_file_dialog_result(_get_save_file_name(*args, **kwargs))


QtGui.QFileDialog.getOpenFileName = staticmethod(_qt4_get_open_file_name)
QtGui.QFileDialog.getOpenFileNames = staticmethod(_qt4_get_open_file_names)
QtGui.QFileDialog.getSaveFileName = staticmethod(_qt4_get_save_file_name)

class _QAppProxy:
    def __getattr__(self, name):
        app = QtWidgets.QApplication.instance()
        if app is None:
            raise AttributeError("No QApplication instance is available")
        return getattr(app, name)


QtGui.qApp = _QAppProxy()


sys.modules[__name__ + ".QtCore"] = QtCore
sys.modules[__name__ + ".QtGui"] = QtGui
sys.modules[__name__ + ".Qt"] = Qt

__all__ = ["Qt", "QtCore", "QtGui", "QT_API"]
