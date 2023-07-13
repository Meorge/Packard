from time import time
from PyQt6.QtWidgets import (
    QGraphicsSceneMouseEvent,
    QGraphicsScene,
)
from PyQt6.QtGui import QPainter, QBrush, QPen, QKeyEvent
from PyQt6.QtCore import QRectF, Qt, QPointF

from story_document_block import StoryDocumentBlock

from constants import (
    CELL_SIZE,
    BG_COLOR,
    GRID_COLOR,
    CONNECTION_COLOR,
    CONNECTION_WIDTH,
    TEMP_NEW_BLOCK_COLOR,
    TEMP_NEW_BLOCK_PEN,
    BLOCK_RECT_SIZE
)


class GraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_connection_target_block: StoryDocumentBlock | None = None
        self.item_creating_new_connection = None
        self.new_connection_target_point = QPointF(0, 0)

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

        for item in self.items():
            if not isinstance(item, StoryDocumentBlock):
                continue
            for conn in item.block_connections:
                painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))
                painter.drawLine(item.rightSide(), conn.leftSide())

        if self.item_creating_new_connection is not None:
            painter.setPen(QPen(CONNECTION_COLOR, CONNECTION_WIDTH))
            painter.drawLine(
                self.item_creating_new_connection.rightSide(),
                self.new_connection_target_point,
            )

            if self.new_connection_target_block is None:
                painter.setBrush(TEMP_NEW_BLOCK_COLOR)
                painter.setPen(TEMP_NEW_BLOCK_PEN)
                painter.drawRoundedRect(
                    QRectF(
                        QPointF(
                            self.new_connection_target_point.x(),
                            self.new_connection_target_point.y()
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
                            self.new_connection_target_block.x(),
                            self.new_connection_target_block.y(),
                        ),
                        self.new_connection_target_block.blockRect().size(),
                    ),
                    10,
                    10,
                )

        return super().drawBackground(painter, rect)

    def blocks(self) -> list[StoryDocumentBlock]:
        return [b for b in self.items() if isinstance(b, StoryDocumentBlock)]
    
    def blocksWithName(self, name: str) -> list[StoryDocumentBlock]:
        return [b for b in self.blocks() if b.name == name]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.item_creating_new_connection is not None:
            # Check if we're overlapping with an existing block, and if so,
            # suggest that we connect to that block
            pos = event.scenePos()
            overlapping_blocks = [
                block
                for block in self.blocks()
                if block.sceneBoundingRect().contains(pos)
            ]
            if len(overlapping_blocks) > 0:
                self.new_connection_target_block = overlapping_blocks[0]
                self.new_connection_target_point = (
                    self.new_connection_target_block.leftSide()
                )
            else:
                self.new_connection_target_block = None
                self.new_connection_target_point = event.scenePos()
            self.update()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.item_creating_new_connection is not None:
            if self.new_connection_target_block is None:
                new_block = StoryDocumentBlock()

                # Calculate position to create this block at
                new_block.setX(self.new_connection_target_point.x())
                new_block.setY(
                    self.new_connection_target_point.y()
                    - new_block.boundingRect().height() / 2
                )

                new_block.name = str(int(time()))
                self.addItem(new_block)
                self.item_creating_new_connection.connectOutputToBlock(new_block)
                

            else:
                self.item_creating_new_connection.connectOutputToBlock(
                    self.new_connection_target_block
                )

            self.new_connection_target_point = QPointF(0, 0)
            self.item_creating_new_connection = None
            self.update()

        return super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Cancel new block creation if escape is pressed mid-drag
        if (
            event.key() == Qt.Key.Key_Escape
            and self.item_creating_new_connection is not None
        ):
            self.new_connection_target_point = QPointF(0, 0)
            self.item_creating_new_connection = None
            self.update()

        elif event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if not isinstance(item, StoryDocumentBlock):
                    continue
                # Find all the blocks that are connected to this block,
                # and remove their link
                for source_block in [
                    i for i in self.items() if isinstance(i, StoryDocumentBlock)
                ]:
                    try:
                        source_block.block_connections.remove(item)
                        print(f"Removed {item.name} from {source_block.name}")
                    except ValueError:
                        pass

                self.removeItem(item)

            self.update()

        return super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.item_creating_new_connection is None:
            new_block = StoryDocumentBlock()
            new_block.setX(event.scenePos().x())
            new_block.setY(event.scenePos().y())
            new_block.name = str(int(time()))
            self.addItem(new_block)

        return super().mouseDoubleClickEvent(event)

    def startCreatingNewConnection(self, source: "StoryDocumentBlock"):
        self.item_creating_new_connection = source

    def refreshBlockConnections(self):
        for block in self.blocks():
            block.analyzeBody()
        self.update()
