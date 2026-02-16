from typing import (Optional, Callable, Iterable, List, )

from PySide6.QtCore import (Qt, QObject, Slot, )
from PySide6.QtGui import (QPixmap, QIcon, )
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout, # for arranging index labels and editors in a grid
    QLabel,      # for index labels
    QPushButton, # for add/remove buttons
    QDialog,     # for the editor dialog
)


from .previewable_editor import (PreviewableEditor, ValueChangedData, Editor, T, )

class ArrayEditor(Editor[Iterable[T]], ):
    def __init__(self,
                 editorBuilder: Callable[[int], Editor[T]],
                 parent: Optional[QObject] = None,
                 /,
                 labelText: Optional[str] = None,
                 newItemLabel: str = '',
    ):
        super().__init__(parent, labelText=labelText, )
        self.__editorBuilder = editorBuilder
        self.__editors: List[Editor[T]] = []
        self.__allowChangeItem = True

        self.__editor = QWidget()
        self.__layout = QGridLayout(self.__editor, )
        self.__layout.setContentsMargins(0, 0, 0, 0)

        # First row is for adding new items
        # Layout will be:(0, new item editor, add button)
        ## zero label
        self.__layout.addWidget(
            QLabel(newItemLabel, self.__editor, ), 0,
            0, alignment=Qt.AlignmentFlag.AlignRight,
        )
        ## new item editor
        self.__newItemEditor = self.__editorBuilder(0, )
        self.__layout.addWidget(self.__newItemEditor.bindEditingWidget(self.__editor, ), 0, 1, )
        ## add button
        self.__addButton = QPushButton("+", self.__editor, )
        self.__addButton.clicked.connect(self.__onAddButtonClicked, )
        self.__layout.addWidget(self.__addButton, 0, 2, )

    @Slot()
    def __genValueChangedData(self, _):
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )
    
    @Slot()
    def __onAddButtonClicked(self, ):
        if self.__allowChangeItem:
            self.__allowChangeItem = False
            self.__addItem(self.__newItemEditor.getValue(), )
            self.__allowChangeItem = True

    def __addItemWithoutSignal(self, itemValue: T, ):
        newIndex = len(self.__editors) + 1
        editor = self.__editorBuilder(newIndex, )
        editor.setValue(itemValue, )
        editor.onEdited.connect(self.onEdited, )
        editor.valueChanged.connect(self.__genValueChangedData, )
        self.__editors.append(editor, )
        self.__layout.addWidget(
            QLabel(editor.labelText, self.__editor, ), newIndex,
            0, alignment=Qt.AlignmentFlag.AlignRight,
        )
        self.__layout.addWidget(editor.bindEditingWidget(self.__editor, ), newIndex, 1, )
        removeButton = QPushButton("-", self.__editor, )
        removeButton.clicked.connect(lambda: self.__removeItem(newIndex, ), )
        self.__layout.addWidget(removeButton, newIndex, 2, )

    def __addItem(self, itemValue: T, ):
        self.__addItemWithoutSignal(itemValue, )
        self.onEdited.emit()
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def __setLayoutItemParent(self, row: int, column: int, parent: Optional[QWidget], ):
        item = self.__layout.itemAtPosition(row, column)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                widget.setParent(parent, )
                return widget
        return None

    def __removeItem(self, index: int, ):
        if self.__allowChangeItem:
            self.__allowChangeItem = False
            oldValue = self.getValue()
            oldValue.pop(index - 1, )
            self.setValue(oldValue, )
            self.onEdited.emit()
            self.__allowChangeItem = True

    def getValue(self, ) -> List[T]:
        return [self.__editors[i].getValue() for i in range(len(self.__editors))]
    
    def setValue(self, value: Iterable[T], ):
        # Clear existing editors
        for i in range(len(self.__editors), ):
            self.__setLayoutItemParent(i + 1, 0, None, ) # remove index label
            self.__setLayoutItemParent(i + 1, 2, None, ) # remove remove button
            editorToRemove = self.__editors[i]
            if editorToRemove is not None: # Remove editor and its widgets
                editorToRemove.bindEditingWidget(None, )
        self.__editors.clear()

        # Add new editors based on the provided value
        for item in value:
            self.__addItemWithoutSignal(item, )
        
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor

class PreviewableArrayEditor(PreviewableEditor[Iterable[T]], ):
    def __init__(
        self,
        editorBuilder: Callable[[int], Editor[T]],
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
        windowIcon: Optional[QPixmap | QIcon] = None,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__arrayEditor = ArrayEditor(editorBuilder, parent, labelText=labelText, )
        self.__arrayEditor.onEdited.connect(self.onEdited, )
        self.__arrayEditor.valueChanged.connect(self.__genValueChangedData, )
        self.__dialog = QDialog(modal=True, )
        if windowIcon is not None:
            self.__dialog.setWindowIcon(QIcon(windowIcon, ))
        self.__layout = QGridLayout(self.__dialog, )
        self.__layout.addWidget(self.__arrayEditor.bindEditingWidget(self.__dialog, ), 0, 0, )

    @Slot()
    def __genValueChangedData(self, data: ValueChangedData[List[T]], ):
        self.valueChanged.emit(data, )

    def getPreview(self, ) -> str:
        return f"[{', '.join(str(item) for item in self.getValue())}]"
    
    def getValue(self, ) -> Iterable[T]:
        return self.__arrayEditor.getValue()
    
    def setValue(self, value: Iterable[T], ):
        self.__arrayEditor.setValue(value, )

    def _modify(self) -> None:
        self.__dialog.setWindowTitle(self.__arrayEditor.labelText, )
        self.__dialog.show()
        self.__dialog.exec()

