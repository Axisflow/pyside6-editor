from typing import (Optional, Iterable, )

from PySide6.QtCore import (QObject, Slot, Qt, )
from PySide6.QtGui import (QPixmap, QIcon, )
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QInputDialog,
    QFileDialog,
    QDialogButtonBox,
)

from .interface.previewable_editor import (PreviewableEditor, ValueChangedData, )
from .management import (ResourceManager, )


class FilePickerTranslation:
    def addButton(self) -> str:
        return "Add"
    def removeButton(self) -> str:
        return "Remove"
    def resourceManagerTitle(self) -> str:
        return "File Manager"
    def dialogTitle(self, labelText: Optional[str]) -> str:
        return f"Select File for {labelText}" if labelText else "Select File"
    def subFolderLabel(self) -> str:
        return "Subfolder (optional):"
    def fileFilter(self, extensions: Optional[Iterable[str]]) -> str:
        if extensions:
            patterns = ' '.join(f"*{ext}" for ext in extensions)
            return f"Allowed ({patterns})"
        else:
            return "All Files (*)"
    def noFileSelected(self) -> str:
        return "(no file)"
    

class FilePicker(PreviewableEditor[str], ):
    def __init__(
        self, resourceManager: ResourceManager,
        allowExtensions: Optional[Iterable[str]] = None,
        parent: Optional[QObject] = None, /,
        labelText: Optional[str] = None,
        windowIcon: Optional[QIcon | QPixmap] = None,
        translation: FilePickerTranslation = FilePickerTranslation(),
    ):
        super().__init__(parent, labelText=labelText, )
        self.__manager = resourceManager
        self.__extensions = set(allowExtensions) if allowExtensions is not None else None
        self.__l18n = translation

        # current selected resource path (string)
        self.__value: Optional[str] = None

        # dialog UI
        self.__dialog = QDialog()
        self.__dialog.setModal(True)
        self.__dialog.setWindowTitle(self.__l18n.resourceManagerTitle())
        if windowIcon:
            self.__dialog.setWindowIcon(windowIcon, )
        self.__layout = QVBoxLayout(self.__dialog)

        self.__list = QListWidget()
        self.__layout.addWidget(self.__list)

        btnRow = QHBoxLayout()
        self.__addBtn = QPushButton(self.__l18n.addButton())
        self.__removeBtn = QPushButton(self.__l18n.removeButton())
        btnRow.addWidget(self.__addBtn)
        btnRow.addWidget(self.__removeBtn)
        self.__layout.addLayout(btnRow)

        self.__buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.__layout.addWidget(self.__buttons)

        # connections
        self.__addBtn.clicked.connect(self.__onAdd)
        self.__removeBtn.clicked.connect(self.__onRemove)
        self.__buttons.accepted.connect(self.__dialog.accept)
        self.__buttons.rejected.connect(self.__dialog.reject)

    def __refreshList(self):
        self.__list.clear()
        resources = self.__manager.listResources(self.__extensions)
        for r in resources:
            # r is ReferenceCountedResource
            self.__list.addItem(r.path)

    @Slot()
    def __onAdd(self, ):
        path, _ = QFileDialog.getOpenFileName(
            self.__dialog, 
            self.__l18n.dialogTitle(self.labelText),
            filter=self.__l18n.fileFilter(self.__extensions),
        )

        if path:
            # add to resource manager (copy into root if needed)
            subFolder = QInputDialog.getText(
                self.__dialog,
                self.__l18n.dialogTitle(self.labelText),
                self.__l18n.subFolderLabel(),
                text="",
            )
            res = self.__manager.addResource(path, True, subFolder=subFolder[0] if subFolder[1] else '')
            # refresh list and select new
            self.__refreshList()
            items = self.__list.findItems(res.path, Qt.MatchFlag.MatchExactly)
            if items:
                self.__list.setCurrentItem(items[0])

    @Slot()
    def __onRemove(self, ):
        item = self.__list.currentItem()
        if not item:
            return
        self.__manager.removeResource(item.text(), True)
        self.__refreshList()

    def getValue(self) -> str:
        return self.__value or ""

    def setValue(self, value: str) -> None:
        oldValue = self.__value
        self.__value = value
        self.__manager.addResource(value, False)  # ensure it's in the manager
        self.valueChanged.emit(ValueChangedData(oldValue, self.__value, ), )

    def getPreview(self) -> str:
        if not self.__value:
            return self.__l18n.noFileSelected()
        # show filename and full path in preview
        return f"{self.__value}"

    def _modify(self) -> None:
        # populate list and pre-select current value
        self.__refreshList()
        if self.__value:
            items = self.__list.findItems(self.__value, Qt.MatchFlag.MatchExactly)
            if items:
                self.__list.setCurrentItem(items[0])

        if self.__dialog.exec() == QDialog.DialogCode.Accepted:
            item = self.__list.currentItem()
            self.__value = item.text() if item else None