from PyQt6.QtWidgets import QStatusBar, QWidget, QSlider, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt

class StatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        
        self.__numBlocksLabel = StatusBarPushButton("X blocks", self)
        self.__numWordsLabel = StatusBarPushButton("XXX words", self)
        self.__numErrorsLabel = StatusBarPushButton("🚫3", self)

        self.__zoomer = ZoomSlider(self)

        self.addWidget(self.__numBlocksLabel)
        self.addWidget(self.__numWordsLabel)
        self.addWidget(self.__numErrorsLabel)
        self.addPermanentWidget(self.__zoomer)

class StatusBarPushButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None, **kwargs):
        super().__init__(text, parent, **kwargs)
        self.setFlat(True)
        self.setContentsMargins(0,0,0,0)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        # self.setStyleSheet("""QPushButton { padding: 1px; }""")

ZOOM_BUTTON_STEP = 10

class ZoomSlider(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setLayout(QHBoxLayout(spacing=0))

        # TODO: clicking should decrease zoom
        self.__minusLabel = StatusBarPushButton("-", self, clicked=self.zoomOut)
        # self.__minusLabel.clicked.connect(self.zoomOut)

        # TODO: should reflect zoom level
        self.__slider = QSlider(Qt.Orientation.Horizontal)
        self.__slider.setTickInterval(10)
        self.__slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.__slider.valueChanged.connect(self.onZoomChanged)

        # TODO: clicking should increase zoom
        self.__plusLabel = StatusBarPushButton("+", self, clicked=self.zoomIn)

         # TODO: clicking should allow user to set zoom
        self.__zoomAmountLabel = StatusBarPushButton("100%", self)

        self.__slider.setRange(0, 200)
        self.__slider.setSingleStep(1)
        

        self.layout().addWidget(self.__minusLabel)
        self.layout().addWidget(self.__slider)
        self.layout().addWidget(self.__plusLabel)
        self.layout().addWidget(self.__zoomAmountLabel)

        self.layout().setContentsMargins(0,0,0,0)
        self.setContentsMargins(0,0,0,0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.__slider.setValue(100)

    def zoomIn(self):
        self.__slider.setValue(self.__slider.value() + ZOOM_BUTTON_STEP)

    def zoomOut(self):
        self.__slider.setValue(self.__slider.value() - ZOOM_BUTTON_STEP)

    def onZoomChanged(self):
        self.__zoomAmountLabel.setText(f"{self.__slider.value()}%")
        