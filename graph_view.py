from PyQt6 import QtGui
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtCore import QRect

from add_new_block_widget import AddNewBlockWidget

class GraphView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget | None = None):
        super().__init__(scene, parent)
        self.setRenderHints(
            self.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setMouseTracking(True)


        # Widget overlay
        self.__addNewBlockWidget = AddNewBlockWidget(self)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.__addNewBlockWidget.setPos(event.pos())
        return super().mouseMoveEvent(event)
        