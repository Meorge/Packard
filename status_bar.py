from PyQt6.QtWidgets import QStatusBar, QWidget, QSlider, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal

from story_components import Story

class StatusBar(QStatusBar):
    zoomSet = pyqtSignal(float)
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.__story: Story | None = None
        self.__numBlocksLabel = StatusBarPushButton("X blocks", self)
        self.__numErrorsLabel = StatusBarPushButton("🚫3", self)

        #self.__zoomer = ZoomSlider(self)
        #self.__zoomer.zoomSet.connect(self.zoomSet)

        self.addWidget(self.__numBlocksLabel)
        self.addWidget(self.__numErrorsLabel)
        #self.addPermanentWidget(self.__zoomer)


    def setStory(self, story: Story):
        if self.__story is not None:
            self.__story.stateChanged.disconnect(self.onStoryStateChanged)
            self.__story.errorsReevaluated.disconnect(self.onStoryErrorsReevaluated)
        self.__story = story
        if self.__story is not None:
            self.__story.stateChanged.connect(self.onStoryStateChanged)
            self.__story.errorsReevaluated.connect(self.onStoryErrorsReevaluated)

        self.onStoryStateChanged()
        self.onStoryErrorsReevaluated()

    def setToggleErrorPaneAction(self, action: QAction):
        self.__numErrorsLabel.clicked.connect(action.trigger)

    def onStoryStateChanged(self):
        self.__numBlocksLabel.setText(f"{len(self.__story.blocks())} blocks")

    def onStoryErrorsReevaluated(self):
        self.__numErrorsLabel.setText(f"🚫{len(self.__story.errorsAsList())}")

        

class StatusBarPushButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None, **kwargs):
        super().__init__(text, parent, **kwargs)
        self.setFlat(True)
        self.setContentsMargins(0,0,0,0)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        # self.setStyleSheet("""QPushButton { padding: 1px; }""")

ZOOM_BUTTON_STEP = 10

class ZoomSlider(QWidget):
    zoomSet = pyqtSignal(float)
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
        self.zoomSet.emit(self.__slider.value())
        