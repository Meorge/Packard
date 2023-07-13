from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsView,
    QWidget,
    QDockWidget,
    QFileDialog
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
        self.currentStoryPath: str | None = None

        self.graphScene = GraphScene()
        self.graphView = QGraphicsView(self.graphScene, parent=self)
        self.graphView.setRenderHints(
            self.graphView.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.graphView.setMouseTracking(True)

        self.setCentralWidget(self.graphView)

        self.graphScene.selectionChanged.connect(self.onSelectionChanged)

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

    def onSave(self):
        if self.currentStoryPath is None:
            self.onSaveAs()
            return
        save_story(self.currentStoryPath, self.graphScene.blocks())

    def onSaveAs(self):
        saveLocation = QFileDialog.getExistingDirectory(
            self,
            "Save Story As..."
        )

        if saveLocation == '':
            return
        
        # TODO: handle errors in saving story
        save_story(saveLocation, self.graphScene.blocks())

        self.currentStoryPath = saveLocation

    def onOpen(self):
        openLocation = QFileDialog.getExistingDirectory(
            self,
            "Open Story..."
        )
        if openLocation == '':
            return
        
        # TODO: handle errors in loading story
        blockDataList = load_story(openLocation)

        self.currentStoryPath = openLocation

        self.graphScene.clear()
        for block_data in blockDataList:
            new_block = StoryDocumentBlock()
            new_block.setName(block_data["name"])
            new_block.setX(block_data["x"])
            new_block.setY(block_data["y"])
            new_block.setBody(block_data["body"])
            self.graphScene.addItem(new_block)

        self.graphScene.refreshBlockConnections()

    def onSelectionChanged(self):
        selectedItems = self.graphScene.selectedItems()
        if len(selectedItems) == 1:
            self.editor.setBlock(selectedItems[0])
        else:
            self.editor.setBlock(None)


app = QApplication(argv)
mainWindow = MainWindow()
mainWindow.show()
app.exec()
