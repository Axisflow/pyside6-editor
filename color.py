from typing import (Optional, Callable, )

from PySide6.QtCore import (Qt, QObject, )
from PySide6.QtGui import (QPixmap, QIcon, )
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QSpinBox,
    QDialogButtonBox,
)


from .interface.previewable_editor import (PreviewableEditor, ValueChangedData, )

class RGBAPicker(PreviewableEditor[str], ):
    @staticmethod
    def formatRGBA(r: int, g: int, b: int, a: int) -> str:
        return "rgba({}, {}, {}, {})".format(r, g, b, a / 255.0)

    @staticmethod
    def parseRGBA(value: str) -> tuple[int, int, int, int]:
        try:
            r, g, b, a = [float(x.strip()) for x in value[5:-1].split(",")]
            return int(r), int(g), int(b), int(a * 255)
        except (ValueError, IndexError):
            return 0, 0, 0, 0

    def __init__(
        self,
        parent: Optional[QObject] = None,
        /,
        labelText: Optional[str] = None,
        windowIcon: Optional[QIcon | QPixmap] = None,
        formatter: Callable[[int, int, int, int], str] = formatRGBA,
        parser: Callable[[str], tuple[int, int, int, int]] = parseRGBA,
    ):
        super().__init__(parent, labelText=labelText, )
        self.__formatter = formatter
        self.__parser = parser

        # dialog used to edit A,R,G,B
        self.__dialog = QDialog()
        self.__dialog.setModal(True, )
        if windowIcon:
            self.__dialog.setWindowIcon(windowIcon, )
        self.__layout = QGridLayout(self.__dialog, )

        self.__layout.addWidget(QLabel("A:"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.__spinA = QSpinBox()
        self.__layout.addWidget(self.__spinA, 0, 1, )

        self.__layout.addWidget(QLabel("R:"), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.__spinR = QSpinBox()
        self.__layout.addWidget(self.__spinR, 1, 1, )

        self.__layout.addWidget(QLabel("G:"), 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.__spinG = QSpinBox()
        self.__layout.addWidget(self.__spinG, 2, 1, )

        self.__layout.addWidget(QLabel("B:"), 3, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.__spinB = QSpinBox()
        self.__layout.addWidget(self.__spinB, 3, 1, )

        # color sample
        self.__sample = QLabel()
        self.__sample.setFixedSize(64, 64, )
        self.__layout.addWidget(self.__sample, 0, 2, 4, 1, )

        # update sample on spin changes
        for s in (self.__spinA, self.__spinR, self.__spinG, self.__spinB, ):
            s.setRange(0, 255, )
            s.valueChanged.connect(self.__updateSample, )

        # buttons
        self.__buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, )
        self.__buttons.accepted.connect(self.__dialog.accept, )
        self.__buttons.rejected.connect(self.__dialog.reject, )
        self.__layout.addWidget(self.__buttons, 4, 0, 1, 3, )

    def __updateSample(self, _=None):
        a = self.__spinA.value()
        r = self.__spinR.value()
        g = self.__spinG.value()
        b = self.__spinB.value()
        # use rgba CSS with normalized alpha
        alpha = a / 255.0
        self.__sample.setStyleSheet(
            f"background-color: rgba({r},{g},{b},{alpha}); border: 1px solid #000;"
        )

    def getValue(self) -> str:
        a = self.__spinA.value()
        r = self.__spinR.value()
        g = self.__spinG.value()
        b = self.__spinB.value()
        return self.__formatter(r, g, b, a)

    def setValue(self, value: str) -> None:
        r, g, b, a = self.__parser(value)
        self.__spinA.setValue(a)
        self.__spinR.setValue(r)
        self.__spinG.setValue(g)
        self.__spinB.setValue(b)
        self.valueChanged.emit(ValueChangedData(None, self.getValue(), ), )

    def getPreview(self) -> str:
        r, g, b, a = self.__parser(self.getValue())
        alpha = a / 255.0
        return f"""
            <div style="display:flex;align-items:center">
                <div style="width:18px;height:12px;margin-right:6px;border:1px solid #000;background:rgba({r},{g},{b},{alpha})">
                </div>
                #{a:02X}{r:02X}{g:02X}{b:02X}
            </div>
        """

    def _modify(self) -> None:
        # populate dialog with current value
        r, g, b, a = self.__parser(self.getValue())
        self.__spinA.setValue(a)
        self.__spinR.setValue(r)
        self.__spinG.setValue(g)
        self.__spinB.setValue(b)
        self.__updateSample()

        if self.__dialog.exec() == QDialog.DialogCode.Accepted:
            # apply chosen value
            self.setValue(self.getValue())

