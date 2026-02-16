from typing import (Optional, )
from abc import (abstractmethod, )

from PySide6.QtCore import (Qt, QObject, Slot, )
from PySide6.QtGui import (QMouseEvent, )
from PySide6.QtWidgets import (QTextEdit, QWidget, )


from .editor import (Editor, ValueChangedData, T, )

class PreviewableEditor(Editor[T], ):

    def __init__(self, parent: Optional[QObject] = None, /,
                 labelText: Optional[str] = None, ):
        super().__init__(parent, labelText=labelText, )
        self.__editing_widget = QTextEdit(readOnly=True, acceptRichText=True, )
        self.__editing_widget.setCursor(Qt.CursorShape.PointingHandCursor, )
        self.__editing_widget.mousePressEvent = self.__onMouseClicked
        self.valueChanged.connect(self.__updatePreview, )

    def __onMouseClicked(self, event: QMouseEvent, ):
        if event.button() == Qt.MouseButton.LeftButton:
            old_value = self.getValue()
            self._modify()
            self.onEdited.emit()
            self.valueChanged.emit(ValueChangedData(old_value, self.getValue(), ), )

        event.accept()
    
    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__updatePreview()
        self.__editing_widget.setParent(parent, )
        return self.__editing_widget
    
    @Slot()
    def __updatePreview(self, ):
        self.__editing_widget.setText(self.getPreview(), )
    
    @abstractmethod
    def getPreview(self, ) -> str: ...
    
    @abstractmethod
    def _modify(self, ) -> None: ...

