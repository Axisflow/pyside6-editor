from typing import (Optional, Tuple, )

from PySide6.QtCore import (QObject, Slot, )
from PySide6.QtWidgets import (QWidget, QSpinBox, )


from .interface.editor import (Editor, ValueChangedData, )

class IntegerEditor(Editor[int], ):
    def __init__(self, range: Tuple[int, int], parent: Optional[QObject] = None, /, labelText: Optional[str] = None, ):
        super().__init__(parent, labelText=labelText, )
        self.__editor = QSpinBox()
        self.__editor.setRange(*range)
        self.__editor.editingFinished.connect(self.onEdited, )
        self.__editor.valueChanged.connect(self.__onValueChanged, )

    @Slot(int, )
    def __onValueChanged(self, val: int, ):
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def getValue(self, ) -> int:
        return int(self.__editor.value())
    
    def setValue(self, value: int, ):
        self.__editor.setValue(int(value, ) if value is not None else 0, )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor
