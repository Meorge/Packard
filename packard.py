from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsView,
    QWidget,
    QDockWidget,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPainter, QAction, QKeySequence
from sys import argv
from block_editor import BlockEditor
from graph_scene import GraphScene
from story_document_block import StoryDocumentBlock
from saver import load_story, save_story

from constants import CELL_SIZE


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.graph_scene = GraphScene()
        self.graph_view = QGraphicsView(self.graph_scene, parent=self)
        self.graph_view.setRenderHints(
            self.graph_view.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.graph_view.setMouseTracking(True)

        self.setCentralWidget(self.graph_view)

        block1 = StoryDocumentBlock()
        block1.name = "Block 1"
        block2 = StoryDocumentBlock()
        block2.name = "Block 2"
        block2.setX(CELL_SIZE * 5)
        block2.setY(CELL_SIZE * 3)

        block1.setBody("[[Block 2]]")

        self.graph_scene.addItem(block1)
        self.graph_scene.addItem(block2)

        self.graph_scene.selectionChanged.connect(self.onSelectionChanged)

        # set up editor
        self.editor = BlockEditor(self)
        self.onSelectionChanged()

        self.editorDockWidget = QDockWidget("Editor")
        self.editorDockWidget.setWidget(self.editor)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.editorDockWidget)

        # menu bar
        self.fileMenu = self.menuBar().addMenu("&File")
        self.saveAsAction = QAction("&Save As", self)
        self.saveAsAction.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.saveAsAction.triggered.connect(self.onSaveAs)
        self.fileMenu.addAction(self.saveAsAction)

        self.openAction = QAction("&Open", self)
        self.openAction.setShortcut(QKeySequence.StandardKey.Open)
        self.openAction.triggered.connect(self.onOpen)
        self.fileMenu.addAction(self.openAction)

    def onSaveAs(self):
        save_story(self.graph_scene.blocks())

    def onOpen(self):
        list_of_block_data = load_story("story")

        self.graph_scene.clear()

        for block_data in list_of_block_data:
            new_block = StoryDocumentBlock()
            new_block.setName(block_data["name"])
            new_block.setX(block_data["x"])
            new_block.setY(block_data["y"])
            new_block.setBody(block_data["body"])
            self.graph_scene.addItem(new_block)

        self.graph_scene.refreshBlockConnections()

    def onSelectionChanged(self):
        selectedItems = self.graph_scene.selectedItems()
        if len(selectedItems) == 1:
            self.editor.setBlock(selectedItems[0])
        else:
            self.editor.setBlock(None)


app = QApplication(argv)
main_window = MainWindow()
main_window.show()
app.exec()
