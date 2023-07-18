from time import time
from PyQt6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsScene,
)
from PyQt6.QtGui import QPainter, QBrush, QPen, QKeyEvent, QPainterPath, QPolygonF, QUndoStack
from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal

from story_components import SetStoryBlockPosCommand, Story, StoryBlock
from story_document_block import StoryBlockGraphicsItem

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
    blockAdded = pyqtSignal(QPointF)
    blockRemoved = pyqtSignal(StoryBlock)

    def __init__(self, undoStack: QUndoStack, parent=None, story: Story = None):
        super().__init__(parent)

        self.__undoStack = undoStack

        self.__story = story
        self.__story.stateChanged.connect(self.onStateChanged)
        # self.__story.stateChanged.connect(self.update)

        self.newConnectionTargetBlock: StoryBlockGraphicsItem | None = None
        self.itemCreatingNewConnection = None
        self.newConnectionTargetPoint = QPointF(0, 0)

    def setStory(self, story: Story):
        self.__story.stateChanged.disconnect(self.onStateChanged)
        self.__story = story
        self.__story.stateChanged.connect(self.onStateChanged)
        self.clear()
        self.newConnectionTargetBlock = None
        self.itemCreatingNewConnection = None
        self.newConnectionTargetPoint = QPointF(0, 0)

        for block in self.__story.blocks():
            newBlockGraphic = StoryBlockGraphicsItem(block=block)
            self.addItem(newBlockGraphic)

        self.update()

    def onStateChanged(self):
        for block in self.blockGraphicsItems():
            block.setPos(block.storyBlock().pos())
        self.update()

    def getGraphicsItemFromStoryBlock(
        self, block: StoryBlock
    ) -> StoryBlockGraphicsItem:
        for blockGraphicsItem in self.blockGraphicsItems():
            if blockGraphicsItem.storyBlock() == block:
                return blockGraphicsItem
        return None

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
        if self.__story.startBlock() is not None:
            startBlockSide = self.getGraphicsItemFromStoryBlock(
                self.__story.startBlock()
            ).leftSide()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))
            painter.drawLine(
                startBlockSide + QPointF(-100, 0), startBlockSide + QPointF(-5, 0)
            )
            self.drawArrowhead(painter, startBlockSide)

        for sourceBlockGraphicsItem in self.blockGraphicsItems():
            targetBlocks = self.__story.getConnectionsForBlock(
                sourceBlockGraphicsItem.storyBlock()
            )
            for targetBlock in targetBlocks:
                # Find the graphicsitem that this block goes to
                targetBlockGraphicsItem = None
                for blockGraphicsItem in self.blockGraphicsItems():
                    if blockGraphicsItem.data(0) == targetBlock:
                        targetBlockGraphicsItem = blockGraphicsItem
                        break
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

                path = QPainterPath()
                path.moveTo(sourceBlockGraphicsItem.rightSide())
                path.cubicTo(
                    sourceBlockGraphicsItem.rightSide()
                    + QPointF(CONNECTION_BEZIER_AMT, 0),
                    targetBlockGraphicsItem.leftSide()
                    + QPointF(-CONNECTION_BEZIER_AMT, 0),
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

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.GlobalColor.green)
        painter.drawRect(self.sceneRect())
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

    def blockGraphicsItems(self) -> list[StoryBlockGraphicsItem]:
        return [b for b in self.items() if isinstance(b, StoryBlockGraphicsItem)]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is not None:
            # Check if we're overlapping with an existing block, and if so,
            # suggest that we connect to that block
            pos = event.scenePos()
            overlappingBlocks = [
                block
                for block in self.blockGraphicsItems()
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
                    self.newConnectionTargetPoint.y() - CELL_SIZE / 2,
                )

                # TODO: make this a command!!
                # newBlock = StoryBlock(pos=newBlockPos)

                # newBlockGraphic = StoryBlockGraphicsItem(block=newBlock)

                # self.addItem(newBlockGraphic)
                self.blockAdded.emit(newBlockPos)

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

        # TODO: make this a command!!
        elif event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if not isinstance(item, StoryBlockGraphicsItem):
                    continue

                self.blockRemoved.emit(item.data(0))
                self.removeItem(item)

            self.update()

        return super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.itemCreatingNewConnection is None:
            # newBlock = StoryBlock(pos=event.scenePos())
            # newBlockGraphic = StoryBlockGraphicsItem(block=newBlock)
            # self.addItem(newBlockGraphic)
            self.blockAdded.emit(event.scenePos())

        return super().mouseDoubleClickEvent(event)

    def startCreatingNewConnection(self, source: "StoryBlockGraphicsItem"):
        self.itemCreatingNewConnection = source

    def setStoryBlockPos(self, storyBlock: StoryBlock, newPos: QPointF):
        self.__undoStack.push(SetStoryBlockPosCommand(storyBlock=storyBlock, newPos=newPos))