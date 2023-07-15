from time import time
from PyQt6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsScene,
)
from PyQt6.QtGui import QPainter, QBrush, QPen, QKeyEvent, QPainterPath, QPolygonF
from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal

from story_components import Story, StoryBlock
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
    blockAdded = pyqtSignal(StoryBlock)
    blockRemoved = pyqtSignal(StoryBlock)
    def __init__(self, parent=None, state: Story = None):
        super().__init__(parent)
        self.__state = state
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

        print("---")
        for sourceBlockGraphicsItem in self.blocks():
            targetBlocks = self.__state.getConnectionsForBlock(sourceBlockGraphicsItem.storyBlock())
            print(f"Looking at block with name {sourceBlockGraphicsItem.storyBlock().name()} which has connections {targetBlocks}")
            for targetBlock in targetBlocks:
                # Find the graphicsitem that this block goes to
                targetBlockGraphicsItem = None # Issue - this is None
                for block in self.blocks():
                    if block == sourceBlockGraphicsItem.storyBlock():
                        targetBlockGraphicsItem = block
                        break
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

                path = QPainterPath()
                path.moveTo(sourceBlockGraphicsItem.rightSide())
                path.cubicTo(
                    sourceBlockGraphicsItem.rightSide() + QPointF(CONNECTION_BEZIER_AMT, 0),
                    targetBlockGraphicsItem.leftSide() + QPointF(-CONNECTION_BEZIER_AMT, 0),
                    targetBlockGraphicsItem.leftSide() + QPointF(-5, 0),
                )
                painter.drawPath(path)
                self.drawArrowhead(painter, targetBlockGraphicsItem.leftSide())

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

                newBlockPos = QPointF(
                    self.newConnectionTargetPoint.x(),
                    self.newConnectionTargetPoint.y()
                    - CELL_SIZE / 2
                )

                newBlock = StoryBlock(pos=newBlockPos)

                newBlockGraphic = StoryDocumentBlock()
                newBlockGraphic.setData(0, newBlock)
                self.addItem(newBlockGraphic)
                self.blockAdded.emit(newBlock)
                
                self.itemCreatingNewConnection.storyBlock().addConnection(newBlock)

            else:
                self.itemCreatingNewConnection.storyBlock().addConnection(
                    self.newConnectionTargetBlock.storyBlock()
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

                self.blockRemoved.emit(item.data(0))
                self.removeItem(item)

            self.update()

        return super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is None:
            newBlock = StoryBlock(pos=event.scenePos())
            newBlockGraphic = StoryDocumentBlock()
            newBlockGraphic.setData(0, newBlock)
            self.addItem(newBlockGraphic)
            self.blockAdded.emit(newBlock)

        return super().mouseDoubleClickEvent(event)

    def startCreatingNewConnection(self, source: "StoryDocumentBlock"):
        self.itemCreatingNewConnection = source

    def setStartBlock(self, block: "StoryDocumentBlock"):
        self.startBlock = block
        self.update()
