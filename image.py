from typing import Optional, Iterable

from PySide6.QtCore import (QObject, Slot, Qt, )
from PySide6.QtGui import (QPixmap, QIcon, )
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QInputDialog,
    QDialogButtonBox,
)

from .interface.previewable_editor import (PreviewableEditor, ValueChangedData, )
from .management import (ResourceManager, )


class ImagePickerTranslation:
    def addButton(self) -> str:
        return "Add"
    def removeButton(self) -> str:
        return "Remove"
    def resourceManagerTitle(self) -> str:
        return "Image Manager"
    def dialogTitle(self, labelText: Optional[str]) -> str:
        return f"Select Image for {labelText}" if labelText else "Select Image"
    def subFolderLabel(self) -> str:
        return "Subfolder (optional):"
    def imageFilter(self, extensions: Optional[Iterable[str]]) -> str:
        if extensions:
            patterns = ' '.join(f"*{ext}" for ext in extensions)
            return f"Images ({patterns})"
        else:
            return "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
    def noImageSelected(self) -> str:
        return "(no image)"


class ImagePicker(PreviewableEditor[str], ):
    DEFAULT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

    def __init__(
        self, resourceManager: ResourceManager,
        allowExtensions: Optional[Iterable[str]] = None,
        parent: Optional[QObject] = None, /,
        labelText: Optional[str] = None,
        windowIcon: Optional[QIcon | QPixmap] = None,
        translation: ImagePickerTranslation = ImagePickerTranslation(),
    ):
        super().__init__(parent, labelText=labelText, )
        self.__manager = resourceManager
        self.__extensions = set(allowExtensions) if allowExtensions is not None else self.DEFAULT_EXTENSIONS
        self.__i18n = translation

        self.__value: Optional[str] = None

        self.__dialog = QDialog()
        self.__dialog.setModal(True)
        self.__dialog.setWindowTitle(self.__i18n.resourceManagerTitle())
        if windowIcon:
            self.__dialog.setWindowIcon(windowIcon)
        self.__layout = QVBoxLayout(self.__dialog)

        self.__list = QListWidget()
        self.__list.setIconSize(QPixmap(64, 64).size())
        self.__layout.addWidget(self.__list)

        btnRow = QHBoxLayout()
        self.__addBtn = QPushButton(self.__i18n.addButton())
        self.__removeBtn = QPushButton(self.__i18n.removeButton())
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
            item = QListWidgetItem(f"{r.path}")
            pix = QPixmap(
                self.__manager.getRootPath() + "/" +
                self.__manager.getPathResolver().importPathToRelativePath(r.path, )
            )
            if not pix.isNull():
                icon = QIcon(pix.scaled(
                    128, 128, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ), )
                item.setIcon(icon, )
            self.__list.addItem(item, )

    @Slot()
    def __onAdd(self, ):
        path, _ = QFileDialog.getOpenFileName(
            self.__dialog,
            self.__i18n.dialogTitle(self.labelText),
            filter=self.__i18n.imageFilter(self.__extensions),
        )
        if path:
            subFolder = QInputDialog.getText(
                self.__dialog,
                self.__i18n.dialogTitle(self.labelText),
                self.__i18n.subFolderLabel(),
                text="",
            )
            res = self.__manager.addResource(
                path, True, subFolder=subFolder[0] if subFolder[1] else ''
            )
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
        if value:
            self.__manager.addResource(value, False)
        self.valueChanged.emit(ValueChangedData(oldValue, self.__value, ))

    def getPreview(self) -> str:
        if not self.__value:
            return self.__i18n.noImageSelected()
        path = self.__value.replace("\\", "/")
        return f'''
            <div style="display:flex;align-items:center">
                <img src="file:///{
                        self.__manager.getRootPath() + "/" +
                        self.__manager.getPathResolver().importPathToRelativePath(path, )
                }" width="48" height="48" style="margin-right:6px;border:1px solid #000"/>
                        {self.__value}
            </div>
        '''.strip()

    def _modify(self) -> None:
        self.__refreshList()
        if self.__value:
            items = self.__list.findItems(self.__value, Qt.MatchFlag.MatchExactly)
            if items:
                self.__list.setCurrentItem(items[0])

        if self.__dialog.exec() == QDialog.DialogCode.Accepted:
            item = self.__list.currentItem()
            self.__value = item.text() if item else None
