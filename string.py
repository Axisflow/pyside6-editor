from typing import (Optional, )

from PySide6.QtCore import (QObject, Slot, )
from PySide6.QtWidgets import (QWidget, QLineEdit, )


from .interface.editor import (Editor, ValueChangedData, )

class StringEditor(Editor[str], ):
    def __init__(self, parent: Optional[QObject] = None, /, labelText: Optional[str] = None, ):
        super().__init__(parent, labelText=labelText, )
        self.__editor = QLineEdit("", )
        self.__editor.textEdited.connect(self.onEdited, )
        self.__editor.textChanged.connect(self.__onTextChanged, )

    @Slot(str, )
    def __onTextChanged(self, _: str, ):
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def getValue(self, ) -> str:
        return self.__editor.text()
    
    def setValue(self, value: str, ):
        self.__editor.setText(str(value, ) if value is not None else "", )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor
