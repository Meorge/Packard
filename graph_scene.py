from PyQt6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsScene,
)
from PyQt6.QtGui import (
    QPainter,
    QBrush,
    QPen,
    QKeyEvent,
    QPainterPath,
    QPolygonF,
    QUndoStack,
    QColor
)
from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal, QSizeF, QMarginsF
from add_new_block_widget import AddNewBlockWidget

from story_components import (
    AddLinkBetweenBlocksCommand,
    AddStoryBlockWithLinkToExistingBlockCommand,
    DeleteStoryBlockCommand,
    MoveStoryBlocksCommand,
    Story,
    StoryBlock,
)

from constants import (
    CELL_SIZE,
    BG_COLOR,
    CONNECTION_BEZIER_AMT,
    ERROR_BLOCK_COLOR,
    GRID_COLOR,
    CONNECTION_COLOR,
    CONNECTION_WIDTH,
    TEMP_NEW_BLOCK_COLOR,
    TEMP_NEW_BLOCK_PEN,
    BLOCK_RECT_SIZE,
    BLOCK_COLOR,
    OUTPUT_COLOR,
    OUTPUT_RADIUS,
    BLOCK_RECT_SIZE,
    SELECTED_BLOCK_PEN,
    ERROR_BADGE_COLOR
)


class GraphScene(QGraphicsScene):
    blockAdded = pyqtSignal(QPointF)
    blockRemoved = pyqtSignal(StoryBlock)
    blockSelectionChanged = pyqtSignal()

    def __init__(self, undoStack: QUndoStack, parent=None):
        super().__init__(parent)

        self.__story: Story | None = None

        self.__undoStack = undoStack

        SCENE_SIZE = 500
        self.setSceneRect(0, 0, SCENE_SIZE, SCENE_SIZE)

        self.__selectedBlocks: list[StoryBlock] = []
        self.__selectedBlocksInitialPositions: dict = {}

        self.__mouseDown: bool = False
        self.__mouseDownPos: QPointF | None = None

        self.__newConnectionSourceBlock: StoryBlock = None
        self.__newConnectionTargetBlock: StoryBlock = None
        self.__newConnectionTargetPoint: QPointF | None = None

    def setStory(self, story: Story):
        if self.__story is not None:
            self.__story.stateChanged.disconnect(self.onStateChanged)
        self.__story = story

        if self.__story is not None:
            self.__story.stateChanged.connect(self.onStateChanged)

        self.clear()
        self.__newConnectionSourceBlock = None
        self.__newConnectionTargetBlock = None
        self.__newConnectionTargetPoint = None
        self.onStateChanged()

    def selectedBlocks(self) -> list[StoryBlock]:
        return self.__selectedBlocks.copy()
    
    def onStateChanged(self):
        # totalRect = QRectF()
        # for blockRect in [self.blockRect(b) for b in self.__story.blocks()]:
        #     totalRect = totalRect.united(blockRect)
        # totalRect = totalRect.marginsAdded(QMarginsF(500, 500, 500, 500))
        # self.setSceneRect(totalRect)
        self.update()

    def drawBlock(self, painter: QPainter, block: StoryBlock):
        # Draw the output node
        br = self.blockRect(block)
        painter.setBrush(
            OUTPUT_COLOR
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.outputNodeRect(block))

        hasErrors = len(self.__story.errors().get(block.id(), [])) > 0
        painter.setBrush(ERROR_BLOCK_COLOR if hasErrors else  BLOCK_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setPen(
            SELECTED_BLOCK_PEN
            if block in self.__selectedBlocks
            else QPen(Qt.PenStyle.NoPen)
        )
        painter.drawRoundedRect(
            br,
            10,
            10,
            Qt.SizeMode.AbsoluteSize,
        )

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            br,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            block.title(),
        )

        painter.setPen(QColor(255, 255, 255, 128))
        painter.drawText(
            br.topLeft() - QPointF(0, 8),
            f"{block.pos().x()}, {block.pos().y()}",
        )

    def blockRect(self, block: StoryBlock) -> QRectF:
        return QRectF(
            self.blockBoundingRect(block).x(),
            self.blockBoundingRect(block).y(),
            self.blockBoundingRect(block).width() - OUTPUT_RADIUS,
            self.blockBoundingRect(block).height(),
        )

    def outputNodeRect(self, block: StoryBlock) -> QRectF:
        return QRectF(
            self.blockRect(block).right() - OUTPUT_RADIUS,
            self.blockRect(block).center().y() - OUTPUT_RADIUS,
            OUTPUT_RADIUS * 2,
            OUTPUT_RADIUS * 2,
        )

    def blockBoundingRect(self, block: StoryBlock) -> QRectF:
        return QRectF(block.pos(), BLOCK_RECT_SIZE + QSizeF(OUTPUT_RADIUS, 0))

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

        # Nothing else to draw if there's no story!
        if self.__story is None:
            return

        # Draw start block arrow
        if self.__story.startBlock() is not None:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))
            painter.drawLine(
                QPointF(
                    self.blockRect(self.__story.startBlock()).left() - 100,
                    self.blockRect(self.__story.startBlock()).center().y(),
                ),
                QPointF(
                    self.blockRect(self.__story.startBlock()).left(),
                    self.blockRect(self.__story.startBlock()).center().y(),
                ),
            )
            self.drawArrowhead(
                painter,
                QPointF(
                    self.blockRect(self.__story.startBlock()).left(),
                    self.blockRect(self.__story.startBlock()).center().y(),
                ),
            )

        # Draw connection arrows
        for block in self.__story.blocks():
            targetBlocks = self.__story.getConnectionsForBlock(block)
            for targetBlock in targetBlocks:
                # Find the graphicsitem that this block goes to
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

                path = QPainterPath()
                path.moveTo(
                    QPointF(
                        self.blockRect(block).right(),
                        self.blockRect(block).center().y(),
                    )
                )
                path.cubicTo(
                    QPointF(
                        self.blockRect(block).right() + CONNECTION_BEZIER_AMT,
                        self.blockRect(block).center().y(),
                    ),
                    QPointF(
                        self.blockRect(targetBlock).left() - CONNECTION_BEZIER_AMT,
                        self.blockRect(targetBlock).center().y(),
                    ),
                    QPointF(
                        self.blockRect(targetBlock).left() - 5,
                        self.blockRect(targetBlock).center().y(),
                    ),
                )
                painter.drawPath(path)
                self.drawArrowhead(
                    painter,
                    QPointF(
                        self.blockRect(targetBlock).left(),
                        self.blockRect(targetBlock).center().y(),
                    ),
                )

        # Draw temporary new connection
        if self.__newConnectionSourceBlock is not None and self.__newConnectionTargetPoint is not None:
            block = self.__newConnectionSourceBlock
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))

            path = QPainterPath()
            path.moveTo(
                QPointF(
                    self.blockRect(block).right(),
                    self.blockRect(block).center().y(),
                )
            )

            path.cubicTo(
                QPointF(
                    self.blockRect(block).right() + CONNECTION_BEZIER_AMT,
                    self.blockRect(block).center().y(),
                ),
                self.__newConnectionTargetPoint + QPointF(-CONNECTION_BEZIER_AMT, 0),
                self.__newConnectionTargetPoint + QPointF(-5, 0),
            )
            painter.drawPath(path)

            # Draw arrowhead
            self.drawArrowhead(painter, self.__newConnectionTargetPoint)

            # If we're not trying to link up to an existing block,
            # then draw the outline for a new block
            if self.__newConnectionTargetBlock is None and self.__newConnectionTargetPoint is not None:
                painter.setBrush(TEMP_NEW_BLOCK_COLOR)
                painter.setPen(TEMP_NEW_BLOCK_PEN)
                painter.drawRoundedRect(
                    QRectF(
                        QPointF(
                            self.__newConnectionTargetPoint.x(),
                            self.__newConnectionTargetPoint.y()
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
                            self.__newConnectionTargetBlock.pos().x(),
                            self.__newConnectionTargetBlock.pos().y(),
                        ),
                        self.blockRect(self.__newConnectionTargetBlock).size(),
                    ),
                    10,
                    10,
                )

        # Draw all blocks
        for block in self.__story.blocks():
            self.drawBlock(painter, block)

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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.__mouseDown = True
        self.__mouseDownPos = event.scenePos()
        for block in self.__story.blocks():
            if self.outputNodeRect(block).contains(event.scenePos()):
                event.accept()
                self.__newConnectionSourceBlock = block
                self.__selectedBlocks.clear()
                self.__selectedBlocksInitialPositions.clear()
                self.blockSelectionChanged.emit()
                self.update()
                return

            elif self.blockRect(block).contains(event.scenePos()):
                event.accept()
                self.__selectedBlocks.clear()
                self.__selectedBlocks.append(block)
                self.__selectedBlocksInitialPositions[block] = block.pos()
                self.blockSelectionChanged.emit()
                self.update()
                return

        self.__selectedBlocks.clear()
        self.__selectedBlocksInitialPositions.clear()
        self.blockSelectionChanged.emit()
        self.update()
        return

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # Drag nodes
        if self.__mouseDown:
            # If blocks are selected, and we're dragging them, then we
            # want to move them
            if len(self.__selectedBlocks) > 0:
                delta = event.scenePos() - event.lastScenePos()
                for block in self.__selectedBlocks:
                    block.setPos(block.pos() + delta)
                self.update()

            else:
                # If we're trying to make a new connection, and hovering
                # over an existing block, then snap the connection to
                # that block.
                if self.__newConnectionSourceBlock is not None:
                    for block in self.__story.blocks():
                        if self.blockRect(block).contains(event.scenePos()):
                            self.__newConnectionTargetBlock = block

                            self.__newConnectionTargetPoint = QPointF(
                                self.blockRect(block).left(),
                                self.blockRect(block).center().y(),
                            )
                            self.update()
                            return

                # We're not hovering over a block, so the "ghost" block
                # should just be wherever the cursor is
                self.__newConnectionTargetBlock = None
                self.__newConnectionTargetPoint = event.scenePos()
                self.update()

        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.__mouseDown = False

        # Save mouse down position, and make a command for moving
        # blocks where it sets their position by the delta amount
        if len(self.__selectedBlocks) > 0 and event.scenePos() != self.__mouseDownPos:
            self.__undoStack.push(
                MoveStoryBlocksCommand(
                self.__selectedBlocksInitialPositions.copy(), event.scenePos() - self.__mouseDownPos
                )
            )

        elif self.__newConnectionSourceBlock is not None:
            if self.__newConnectionTargetBlock is not None:
                # Don't create a new block; instead, add a link
                # from the source block to the target block
                self.__undoStack.push(
                    AddLinkBetweenBlocksCommand(
                    self.__newConnectionSourceBlock, self.__newConnectionTargetBlock
                    )
                )
            else:
                # Create a new block, and link the source block to it
                self.__undoStack.push(
                    AddStoryBlockWithLinkToExistingBlockCommand(
                        self.__story, self.__newConnectionSourceBlock, event.scenePos() - QPointF(0, BLOCK_RECT_SIZE.height() / 2)
                    )
                )

        self.__selectedBlocksInitialPositions.clear()
        self.__mouseDownPos = None
        self.__newConnectionTargetPoint = None
        self.__newConnectionSourceBlock = None
        self.__newConnectionTargetBlock = None
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
            self.__undoStack.push(
                DeleteStoryBlockCommand(self.__story, self.__selectedBlocks.copy())
            )
            self.update()

        return super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.__newConnectionSourceBlock is None:
            self.blockAdded.emit(event.scenePos())

        return super().mouseDoubleClickEvent(event)
