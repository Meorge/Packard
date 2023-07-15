from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsView,
    QWidget,
    QDockWidget,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QAction, QKeySequence
from sys import argv
from block_editor import BlockEditor
from graph_scene import GraphScene
from story_document_block import StoryBlockGraphicsItem
from saver import load_story, save_story, compile_story_to_html
from os.path import basename

from story_components import Story, StoryBlock


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.currentStoryPath: str | None = None

        self.currentStory = Story(self)

        self.graphScene = GraphScene(self, story=self.currentStory)

        self.graphScene.blockAdded.connect(self.blockAdded)
        self.graphScene.blockRemoved.connect(self.blockRemoved)

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
        self.editor = BlockEditor(parent=self, story=self.currentStory)
        self.onSelectionChanged()

        self.editorDockWidget = QDockWidget("Editor")
        self.editorDockWidget.setWidget(self.editor)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.editorDockWidget)

        # menu bar
        self.fileMenu = self.menuBar().addMenu("&File")

        self.saveAction = QAction(
            "&Save",
            parent=self,
            shortcut=QKeySequence.StandardKey.Save,
            triggered=self.onSave,
        )
        self.saveAsAction = QAction(
            "&Save As...",
            parent=self,
            shortcut=QKeySequence.StandardKey.SaveAs,
            triggered=self.onSaveAs,
        )
        self.openAction = QAction(
            "&Open...",
            parent=self,
            shortcut=QKeySequence.StandardKey.Open,
            triggered=self.onOpen,
        )
        self.compileStoryAction = QAction(
            "&Compile...",
            parent=self,
            shortcut=QKeySequence("Ctrl+Shift+E"),
            triggered=self.onCompileStory,
        )

        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveAsAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.compileStoryAction)

        self.setWindowTitle("Packard - Untitled Story")

    def onSave(self):
        if self.currentStoryPath is None:
            self.onSaveAs()
            return
        save_story(self.currentStoryPath, self.storyObjectToDict())

    def storyObjectToDict(self):
        return {
            "start": self.currentStory.startBlock().name(),
            "blocks": [
                {
                    "x": block.pos().x(),
                    "y": block.pos().y(),
                    "name": block.name(),
                    "body": block.body(),
                }
                for block in self.currentStory.blocks()
            ],
        }

    def onSaveAs(self):
        saveLocation = QFileDialog.getExistingDirectory(self, "Save Story As...")

        if saveLocation == "":
            return

        storyData = self.storyObjectToDict()

        # TODO: handle errors in saving story
        save_story(saveLocation, storyData)

        self.currentStoryPath = saveLocation

        self.setWindowTitle(f"Packard - {basename(self.currentStoryPath)}")

    def onOpen(self):
        openLocation = QFileDialog.getExistingDirectory(self, "Open Story...")
        if openLocation == "":
            return

        # TODO: handle errors in loading story
        storyData = load_story(openLocation)

        blocks = []
        startBlock = None
        for blockData in storyData["blocks"]:
            newBlock = StoryBlock(
                name=blockData["name"],
                body=blockData["body"],
                pos=QPointF(blockData["x"], blockData["y"]),
            )
            blocks.append(newBlock)
            if blockData["name"] == storyData["start"]:
                startBlock = newBlock

        newStory = Story(startBlock=startBlock, blocks=blocks)

        self.currentStory = newStory

        self.currentStoryPath = openLocation

        self.graphScene.setStory(self.currentStory)

        self.setWindowTitle(f"Packard - {basename(self.currentStoryPath)}")

    def onCompileStory(self):
        compileLocation = QFileDialog.getExistingDirectory(self, "Compile Story...")

        if compileLocation == "":
            return

        self.onSave()
        compile_story_to_html(compileLocation, self.currentStoryPath)

    def onSelectionChanged(self):
        selectedItems = self.graphScene.selectedItems()
        if len(selectedItems) == 1:
            self.editor.setBlock(selectedItems[0].data(0))
        else:
            self.editor.setBlock(None)

    def blockAdded(self, block: StoryBlock):
        self.currentStory.addBlock(block)

    def blockRemoved(self, block: StoryBlock):
        self.currentStory.removeBlock(block)


app = QApplication(argv)
mainWindow = MainWindow()
mainWindow.show()
app.exec()
