from time import time
from PyQt6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsScene,
)
from PyQt6.QtGui import QPainter, QBrush, QPen, QKeyEvent, QPainterPath, QPolygonF
from PyQt6.QtCore import QRectF, Qt, QPointF

from story_document_block import StoryDocumentBlock

from constants import (
    CELL_SIZE,
    BG_COLOR,
    CONNECTION_BEZIER_AMT,
    GRID_COLOR,
    CONNECTION_COLOR,
    CONNECTION_WIDTH,
    TEMP_NEW_BLOCK_COLOR,
    TEMP_NEW_BLOCK_PEN,
    BLOCK_RECT_SIZE,
)


class GraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.newConnectionTargetBlock: StoryDocumentBlock | None = None
        self.itemCreatingNewConnection = None
        self.newConnectionTargetPoint = QPointF(0, 0)
        self.startBlock: StoryDocumentBlock | None = None

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.setBrush(QBrush(BG_COLOR))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRect(rect)

        # Draw grid
        grid_pen = QPen(GRID_COLOR, 2, Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)

        x1 = int(rect.left() - (rect.left() % CELL_SIZE))
        y1 = int(rect.top() - (rect.top() % CELL_SIZE))
        x2 = int(rect.right() + (CELL_SIZE - rect.right()) % CELL_SIZE)
        y2 = int(rect.bottom() + (CELL_SIZE - rect.bottom()) % CELL_SIZE)

        for x in range(int(x1), int(x2 + 1), CELL_SIZE):
            painter.drawLine(x, y1, x, y2)
        for y in range(int(y1), int(y2 + 1), CELL_SIZE):
            painter.drawLine(x1, y, x2, y)

        # Draw start block arrow
        if self.startBlock is not None:
            startBlockSide = self.startBlock.leftSide()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))
            painter.drawLine(
                startBlockSide + QPointF(-100, 0), startBlockSide + QPointF(-5, 0)
            )
            self.drawArrowhead(painter, startBlockSide)

        for item in self.items():
            if not isinstance(item, StoryDocumentBlock):
                continue
            for conn in item.blockConnections:
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

                path = QPainterPath()
                path.moveTo(item.rightSide())
                path.cubicTo(
                    item.rightSide() + QPointF(CONNECTION_BEZIER_AMT, 0),
                    conn.leftSide() + QPointF(-CONNECTION_BEZIER_AMT, 0),
                    conn.leftSide() + QPointF(-5, 0),
                )
                painter.drawPath(path)
                self.drawArrowhead(painter, conn.leftSide())

        if self.itemCreatingNewConnection is not None:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

            path = QPainterPath()
            path.moveTo(self.itemCreatingNewConnection.rightSide())
            path.cubicTo(
                self.itemCreatingNewConnection.rightSide()
                + QPointF(CONNECTION_BEZIER_AMT, 0),
                self.newConnectionTargetPoint + QPointF(-CONNECTION_BEZIER_AMT, 0),
                self.newConnectionTargetPoint + QPointF(-5, 0),
            )
            painter.drawPath(path)

            # Draw arrowhead
            self.drawArrowhead(painter, self.newConnectionTargetPoint)

            if self.newConnectionTargetBlock is None:
                painter.setBrush(TEMP_NEW_BLOCK_COLOR)
                painter.setPen(TEMP_NEW_BLOCK_PEN)
                painter.drawRoundedRect(
                    QRectF(
                        QPointF(
                            self.newConnectionTargetPoint.x(),
                            self.newConnectionTargetPoint.y()
                            - BLOCK_RECT_SIZE.height() / 2,
                        ),
                        BLOCK_RECT_SIZE,
                    ),
                    10,
                    10,
                )
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(TEMP_NEW_BLOCK_PEN)

                painter.drawRoundedRect(
                    QRectF(
                        QPointF(
                            self.newConnectionTargetBlock.x(),
                            self.newConnectionTargetBlock.y(),
                        ),
                        self.newConnectionTargetBlock.blockRect().size(),
                    ),
                    10,
                    10,
                )

        return super().drawBackground(painter, rect)

    def drawArrowhead(self, painter: QPainter, pos: QPointF):
        arrowhead = QPolygonF()
        arrowhead.append(QPointF(0, 0) + pos)
        arrowhead.append(QPointF(-15, -7) + pos)
        arrowhead.append(QPointF(-15, 7) + pos)

        arrowheadPath = QPainterPath()
        arrowheadPath.addPolygon(arrowhead)
        painter.setBrush(CONNECTION_COLOR)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawPath(arrowheadPath)

    def blocks(self) -> list[StoryDocumentBlock]:
        return [b for b in self.items() if isinstance(b, StoryDocumentBlock)]

    def blocksWithName(self, name: str) -> list[StoryDocumentBlock]:
        return [b for b in self.blocks() if b.name == name]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is not None:
            # Check if we're overlapping with an existing block, and if so,
            # suggest that we connect to that block
            pos = event.scenePos()
            overlappingBlocks = [
                block
                for block in self.blocks()
                if block.sceneBoundingRect().contains(pos)
            ]
            if len(overlappingBlocks) > 0:
                self.newConnectionTargetBlock = overlappingBlocks[0]
                self.newConnectionTargetPoint = self.newConnectionTargetBlock.leftSide()
            else:
                self.newConnectionTargetBlock = None
                self.newConnectionTargetPoint = event.scenePos()
            self.update()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is not None:
            if self.newConnectionTargetBlock is None:
                newBlock = StoryDocumentBlock()

                # Calculate position to create this block at
                newBlock.setX(self.newConnectionTargetPoint.x())
                newBlock.setY(
                    self.newConnectionTargetPoint.y()
                    - newBlock.boundingRect().height() / 2
                )

                newBlock.name = str(int(time()))
                self.addItem(newBlock)
                self.itemCreatingNewConnection.connectOutputToBlock(newBlock)

            else:
                self.itemCreatingNewConnection.connectOutputToBlock(
                    self.newConnectionTargetBlock
                )

            self.newConnectionTargetPoint = QPointF(0, 0)
            self.itemCreatingNewConnection = None
            self.update()

        return super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Cancel new block creation if escape is pressed mid-drag
        if (
            event.key() == Qt.Key.Key_Escape
            and self.itemCreatingNewConnection is not None
        ):
            self.newConnectionTargetPoint = QPointF(0, 0)
            self.itemCreatingNewConnection = None
            self.update()

        elif event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if not isinstance(item, StoryDocumentBlock):
                    continue
                # Find all the blocks that are connected to this block,
                # and remove their link
                for sourceBlock in [
                    i for i in self.items() if isinstance(i, StoryDocumentBlock)
                ]:
                    try:
                        sourceBlock.blockConnections.remove(item)
                    except ValueError:
                        pass

                self.removeItem(item)

            self.update()

        return super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is None:
            newBlock = StoryDocumentBlock()
            newBlock.setX(event.scenePos().x())
            newBlock.setY(event.scenePos().y())
            newBlock.name = str(int(time()))
            self.addItem(newBlock)

        return super().mouseDoubleClickEvent(event)

    def startCreatingNewConnection(self, source: "StoryDocumentBlock"):
        self.itemCreatingNewConnection = source

    def refreshBlockConnections(self):
        for block in self.blocks():
            block.analyzeBody()
        self.update()

    def setStartBlock(self, block: "StoryDocumentBlock"):
        self.startBlock = block
        self.update()
