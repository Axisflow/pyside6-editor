from typing import (Optional, TypeVar, Generic, )
from abc import (abstractmethod, )

from PySide6.QtCore import (QObject, Signal, )
from PySide6.QtWidgets import (QWidget, )


T = TypeVar("T", )
class ValueChangedData(Generic[T], ):
    def __init__(self, oldValue: Optional[T], newValue: T, ):
        """
        Maybe None if the old value is not available or not applicable
        """
        self.oldValue = oldValue
        self.newValue = newValue


class Editor(QObject, Generic[T], ):
    onEdited = Signal()
    valueChanged = Signal(ValueChangedData, )

    def __init__(self, parent: Optional[QObject] = None, /, labelText: Optional[str] = None, ):
        super().__init__(parent, )
        self.labelText = labelText or "……"

    @abstractmethod
    def bindEditingWidget(self, parent: Optional[QWidget] = None, ) -> QWidget: ...

    @abstractmethod
    def getValue(self, ) -> T: ...

    @abstractmethod
    def setValue(self, value: T, ) -> None: ...

    