from typing import (Optional, Iterable, )

from PySide6.QtCore import (QObject, Slot, )
from PySide6.QtWidgets import (QWidget, QLineEdit, )


from .interface.editor import (Editor, ValueChangedData, )

class PrefixStringEditor(Editor[str], ):
    def __init__(
        self,
        prefixes: Iterable[str] = [""],
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__editor = QLineEdit("", )
        # 預設可接受的前綴（優先順序會用在自動補前綴時）
        self.__prefixes = prefixes if prefixes else [""]
        # 阻擋因程式設定文字造成的遞迴或多重事件
        self.__suppress = False

        self.__editor.textEdited.connect(self.onEdited, )
        self.__editor.textChanged.connect(self.__onTextChanged, )

    def __ensurePrefix(self, text: str, ) -> str:
        if not text:
            return text
        for p in self.__prefixes:
            if text.startswith(p, ) or p.startswith(text, ):
                return text
        return next(iter(self.__prefixes)) + text

    @Slot(str, )
    def __onTextChanged(self, text: str, ):
        if self.__suppress:
            return
        new_text = self.__ensurePrefix(text, )
        if new_text != text:
            # 程式設定新文字，暫停內建信號，避免遞迴
            self.__suppress = True
            self.__editor.blockSignals(True, )
            self.__editor.setText(new_text, )
            self.__editor.blockSignals(False, )
            self.__suppress = False
            # 發出 valueChanged，new value 已為 new_text
            self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )
        else:
            self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def getValue(self, ) -> str:
        return self.__editor.text()

    def setValue(self, value: str, ):
        text = str(value, ) if value is not None else ""
        text = self.__ensurePrefix(text, )
        self.__editor.setText(text, )

    def bindEditingWidget(self, parent: Optional[QWidget] = None, ):
        self.__editor.setParent(parent, )
        return self.__editor
