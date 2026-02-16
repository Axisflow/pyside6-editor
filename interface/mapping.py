from typing import (Optional, Dict, Any, )

from PySide6.QtCore import (Qt, QObject, Slot, )
from PySide6.QtGui import (QIcon, QPixmap, )
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout, # for arranging index labels and editors in a grid
    QScrollArea,
    QTabWidget,
    QLabel,      # for index labels
    QDialog,     # for the editor dialog
)


from .previewable_editor import (PreviewableEditor, ValueChangedData, Editor, T, )

class VStringMappingEditor(Editor[Dict[str, Any]], ):
    def __init__(
        self,
        editors: Dict[str, Editor[Any]],
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__editors = editors
        self.__allowEmitChange = True

        # Use a QScrollArea so the mapping editor becomes scrollable
        self.__editor = QScrollArea()
        self.__editor.setWidgetResizable(True)

        # Content widget hosts the grid layout for labels and editors
        self.__content = QWidget()
        self.__layout = QGridLayout(self.__content, )
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__editor.setWidget(self.__content)

        for i, editor in enumerate(self.__editors.values()):
            self.__layout.addWidget(
                QLabel(editor.labelText, self.__content, ), i,
                0, alignment=Qt.AlignmentFlag.AlignRight
            )
            self.__layout.addWidget(editor.bindEditingWidget(self.__content, ), i, 1, )
            editor.onEdited.connect(self.onEdited, )
            editor.valueChanged.connect(self.__genValueChangedData, )

    @Slot()
    def __genValueChangedData(self, _):
        if self.__allowEmitChange:
            self.valueChanged.emit(ValueChangedData(None, self.getValue(), ))
    
    def getValue(self, ) -> Dict[str, Any]:
        return {k: e.getValue() for k, e in self.__editors.items()}
    
    def setValue(self, value: Dict[str, Any], ) -> None:
        self.__allowEmitChange = False
        for k, v in value.items():
            if k in self.__editors:
                self.__editors[k].setValue(v, )
        self.__allowEmitChange = True
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor
    

class TabStringMappingEditor(Editor[Dict[str, Any]], ):
    def __init__(
        self,
        editors: Dict[str, Editor[Any]],
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__editors = editors
        self.__allowEmitChange = True

        self.__editor = QTabWidget()
        for editor in self.__editors.values():
            # Wrap each editor's widget in a scroll area so tab content can scroll
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = editor.bindEditingWidget(scroll)
            scroll.setWidget(content)
            self.__editor.addTab(scroll, editor.labelText)
            editor.onEdited.connect(self.onEdited)
            editor.valueChanged.connect(self.__genValueChangedData)

    @Slot()
    def __genValueChangedData(self, _, ):
        if self.__allowEmitChange:
            self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )
    
    def getValue(self, ) -> Dict[str, Any]:
        return {k: e.getValue() for k, e in self.__editors.items()}
    
    def setValue(self, value: Dict[str, Any], ) -> None:
        self.__allowEmitChange = False
        for k, v in value.items():
            if k in self.__editors:
                self.__editors[k].setValue(v, )
        self.__allowEmitChange = True
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor

class VStringMappingPreviewableEditor(PreviewableEditor[Dict[str, Any]], ):
    def __init__(
        self,
        editors: Dict[str, Editor[Any]],
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
        windowIcon: Optional[QPixmap | QIcon] = None,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__mappingEditor = VStringMappingEditor(editors, parent, labelText=labelText, )
        self.__mappingEditor.onEdited.connect(self.onEdited, )
        self.__mappingEditor.valueChanged.connect(self.__genValueChangedData, )
        self.__dialog = QDialog(modal=True, )
        if windowIcon is not None:
            self.__dialog.setWindowIcon(QIcon(windowIcon, ))
        self.__layout = QGridLayout(self.__dialog, )
        self.__layout.addWidget(self.__mappingEditor.bindEditingWidget(self.__dialog, ), 0, 0, )

    @Slot()
    def __genValueChangedData(self, data: ValueChangedData[Dict[str, Any]], ):
        self.valueChanged.emit(data, )
    
    def getPreview(self, ) -> str:
        return ", ".join(f"{k}: {v}" for k, v in self.getValue().items())
    
    def getValue(self, ) -> Dict[str, Any]:
        return self.__mappingEditor.getValue()
    
    def setValue(self, value: Dict[str, Any], ):
        self.__mappingEditor.setValue(value, )

    def _modify(self) -> None:
        self.__dialog.setWindowTitle(self.__mappingEditor.labelText, )
        self.__dialog.show()
        self.__dialog.exec()

