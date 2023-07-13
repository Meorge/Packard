from PyQt6.QtWidgets import (
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsItem,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import QRectF, Qt, QPointF, QSizeF
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

LINK_RE = compile(r"\[\[(.*?)\]\]")


class StoryDocumentBlock(QGraphicsItem):
    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.name = ""
        self.body = ""
        self.blockConnections: list[StoryDocumentBlock] = []
        self.setName("")
        self.setBody("")

        self.hoveringOnOutput = False

        self.creatingNewConnection = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def setName(self, text: str):
        oldName = self.name
        self.name = text
        self.updateNameInOtherBlocks(oldName)
        self.update()

    def setBody(self, text: str):
        self.body = text
        self.analyzeBody()
        self.update()

    def __repr__(self) -> str:
        return f"StoryDocumentBlock({self.name=})"

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
            self.name,
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
        # TODO: find nearest snap point and go there
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

    def connectOutputToBlock(self, target_block: "StoryDocumentBlock"):
        self.setBody(self.body + "\n" + f"[[{target_block.name}]]")

    def analyzeBody(self):
        self.blockConnections.clear()
        if self.scene() is None:
            return

        for target_name in LINK_RE.findall(self.body):
            target_block = self.scene().blocksWithName(target_name)
            if len(target_block) == 1:
                self.blockConnections.append(target_block[0])
            elif len(target_block) <= 0:
                print(f'Uh oh, there\'s no block with the name "{target_name}"')
            else:
                print(
                    f'Uh oh, there are more than one block with the name "{target_name}"'
                )

        self.scene().update()

    def updateNameInOtherBlocks(self, oldName: str):
        if self.scene() is None:
            return

        for block in self.scene().blocks():
            block: StoryDocumentBlock
            updated_body = block.body.replace(f"[[{oldName}]]", f"[[{self.name}]]")
            block.setBody(updated_body)
