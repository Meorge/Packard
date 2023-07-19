from PyQt6.QtWidgets import (
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsItem,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import QRectF, Qt, QPointF, QSizeF, pyqtSignal, QObject
from re import compile

from constants import (
    SELECTED_BLOCK_COLOR,
    BLOCK_COLOR,
    OUTPUT_COLOR,
    OUTPUT_RADIUS,
    BLOCK_RECT_SIZE,
    DROP_SHADOW_COLOR,
    DROP_SHADOW_PICKUP_RADIUS,
    SELECTED_BLOCK_PEN,
)
from story_components import StoryBlock

LINK_RE = compile(r"\[\[(.*?)\]\]")


class StoryBlockGraphicsItem(QGraphicsItem, QObject):
    def __init__(self, parent: QGraphicsItem | None = None, block: StoryBlock = None) -> None:
        super().__init__(parent)
        self.hoveringOnOutput = False
        self.creatingNewConnection = False
        self.lastPos: QPointF = None
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setStoryBlock(block)

    def scene(self) -> "GraphScene":
        return super().scene()
    
    def setStoryBlock(self, block: StoryBlock):
        self.setData(0, block)
        self.setPos(block.pos())
        self.lastPos = self.scenePos()

    def storyBlock(self) -> StoryBlock:
        return self.data(0)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = ...,
    ) -> None:
        painter.setBrush(BLOCK_COLOR)
        painter.setPen(
            SELECTED_BLOCK_PEN if self.isSelected() else QPen(Qt.PenStyle.NoPen)
        )
        painter.drawRoundedRect(
            self.blockRect(),
            10,
            10,
            Qt.SizeMode.AbsoluteSize,
        )

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            self.blockRect(),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.storyBlock().title(),
        )

        painter.drawText(
            self.blockRect(),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            f"{self.x()}, {self.y()}",
        )

        # Draw the output node
        painter.setBrush(OUTPUT_COLOR.lighter(150 if self.hoveringOnOutput else 100))
        painter.drawEllipse(self.outputNodeRect())

    def blockRect(self) -> QRectF:
        return QRectF(
            self.boundingRect().x(),
            self.boundingRect().y(),
            self.boundingRect().width() - OUTPUT_RADIUS,
            self.boundingRect().height(),
        )

    def outputNodeRect(self) -> QRectF:
        return QRectF(
            self.blockRect().right() - OUTPUT_RADIUS,
            self.blockRect().center().y() - OUTPUT_RADIUS,
            OUTPUT_RADIUS * 2,
            OUTPUT_RADIUS * 2,
        )

    def boundingRect(self) -> QRectF:
        return QRectF(QPointF(0, 0), BLOCK_RECT_SIZE + QSizeF(OUTPUT_RADIUS, 0))

    def leftSide(self) -> QPointF:
        return QPointF(
            self.sceneBoundingRect().left(),
            self.sceneBoundingRect().center().y(),
        )

    def rightSide(self) -> QPointF:
        return self.mapToScene(self.outputNodeRect().center())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.outputNodeRect().contains(event.pos()):
            self.scene().startCreatingNewConnection(self)
            event.ignore()
        else:
            return super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.lastPos != self.scenePos():
            # TODO: make this a signal that the scene picks up on and creates an event for!
            self.scene().setStoryBlockPos(self.storyBlock(), self.scenePos())
            # self.storyBlock().setPos(self.scenePos())
            self.lastPos = self.scenePos()
            
        return super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self.outputNodeRect().contains(event.pos()):
            self.hoveringOnOutput = True
        self.scene().update(self.mapRectToScene(self.outputNodeRect()))
        return super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self.outputNodeRect().contains(event.pos()):
            self.hoveringOnOutput = True
            self.scene().update(self.mapRectToScene(self.outputNodeRect()))
        elif not self.outputNodeRect().contains(
            event.pos()
        ) and self.outputNodeRect().contains(event.lastPos()):
            self.hoveringOnOutput = False
            self.scene().update(self.mapRectToScene(self.outputNodeRect()))
        return super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.hoveringOnOutput = False
        self.scene().update(self.mapRectToScene(self.outputNodeRect()))
        return super().hoverLeaveEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.scene().update()
        return super().mouseMoveEvent(event)