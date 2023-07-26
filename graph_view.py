from PyQt6 import QtGui
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtCore import QRect, QPointF, pyqtSignal, QMetaObject

Connection = QMetaObject.Connection

from add_new_block_widget import AddNewBlockWidget, BubbleOverlayWidget


class GraphView(QGraphicsView):
    userConfirmedNewNode = pyqtSignal(str, QPointF)
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

        self.__addNewBlockBubble = BubbleOverlayWidget(
            parent=self, widget=self.__addNewBlockWidget
        )
        self.__addNewBlockBubble.hide()
        self.__addNewBlockWidget.confirmed.connect(self.onUserConfirmedNewNode)


        self.__targetPos: QPointF | None = None

    def onUserRequestedNewNode(self, pos: QPointF) -> None:
        self.__targetPos = pos
        self.__addNewBlockBubble.showAtPos(self.__targetPos.toPoint())
        

    def onUserConfirmedNewNode(self, title: str):
        self.__addNewBlockBubble.hide()
        self.userConfirmedNewNode.emit(title, self.__targetPos)

