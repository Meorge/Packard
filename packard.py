from PyQt6 import QtGui
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsView,
    QWidget,
    QDockWidget,
    QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QAction, QKeySequence, QUndoStack, QCloseEvent
from sys import argv
from block_editor import BlockEditor
from graph_scene import GraphScene
from story_document_block import StoryBlockGraphicsItem
from saver import load_story, save_story, compile_story_to_html
from os.path import basename

from story_components import AddStoryBlockCommand, DeleteStoryBlockCommand, Story, StoryBlock


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.undoStack = QUndoStack(self)
        self.currentStoryPath: str | None = None

        self.currentStory = Story(self)
        self.currentStory.stateChanged.connect(self.updateWindowTitle)

        self.graphScene = GraphScene(parent=self, undoStack=self.undoStack, story=self.currentStory)

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

        self.graphScene.blockSelectionChanged.connect(self.onSelectionChanged)

        # set up editor
        self.editor = BlockEditor(undoStack=self.undoStack, parent=self, story=self.currentStory)
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


        self.editMenu = self.menuBar().addMenu("&Edit")

        self.undoAction = self.undoStack.createUndoAction(self)
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo)
        self.redoAction = self.undoStack.createRedoAction(self)
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo)

        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveAsAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.compileStoryAction)

        self.editMenu.addAction(self.undoAction)
        self.editMenu.addAction(self.redoAction)

        self.updateWindowTitle()

    def onSave(self) -> bool:
        if self.currentStoryPath is None:
            return self.onSaveAs()
        save_story(self.currentStoryPath, self.storyObjectToDict())
        self.currentStory.resetModified()
        return True

    def storyObjectToDict(self):
        return {
            "start": self.currentStory.startBlock().id(),
            "blocks": [
                {
                    "x": block.pos().x(),
                    "y": block.pos().y(),
                    "title": block.title(),
                    "id": block.id(),
                    "body": block.body(),
                }
                for block in self.currentStory.blocks()
            ],
        }

    def onSaveAs(self) -> bool:
        saveLocation = QFileDialog.getExistingDirectory(self, "Save Story As...")

        if saveLocation == "":
            return False

        storyData = self.storyObjectToDict()

        # TODO: handle errors in saving story
        save_story(saveLocation, storyData)

        self.currentStoryPath = saveLocation

        self.currentStory.resetModified()
        self.updateWindowTitle()
        return True

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
                title=blockData["title"],
                body=blockData["body"],
                id=blockData["id"],
                pos=QPointF(blockData["x"], blockData["y"]),
            )
            blocks.append(newBlock)
            if blockData["id"] == storyData["start"]:
                startBlock = newBlock

        newStory = Story(startBlock=startBlock, blocks=blocks)

        self.currentStory.stateChanged.disconnect(self.updateWindowTitle)
        self.currentStory = newStory
        self.currentStory.stateChanged.connect(self.updateWindowTitle)
        self.currentStoryPath = openLocation



        self.graphScene.setStory(self.currentStory)
        self.editor.setStory(self.currentStory)

        self.updateWindowTitle()

    def onCompileStory(self):
        compileLocation = QFileDialog.getExistingDirectory(self, "Compile Story...")

        if compileLocation == "":
            return

        self.onSave()
        compile_story_to_html(compileLocation, self.currentStoryPath)

    def updateWindowTitle(self):
        title = "Packard - "
        title += basename(self.currentStoryPath) if self.currentStoryPath is not None else "Untitled Story"
        if self.currentStory.modified():
            title += " (Unsaved)"
        self.setWindowTitle(title)

    def onSelectionChanged(self):
        selectedItems = self.graphScene.selectedBlocks()
        if len(selectedItems) == 1:
            self.editor.setBlock(selectedItems[0])
        else:
            self.editor.setBlock(None)

    def blockAdded(self, pos: QPointF):
        self.undoStack.push(AddStoryBlockCommand(self.currentStory, pos))

    def blockRemoved(self, block: StoryBlock):
        self.undoStack.push(DeleteStoryBlockCommand(self.currentStory, block))


    def closeEvent(self, event: QCloseEvent) -> None:
        if self.currentStory.modified():
            box = QMessageBox.question(
                self,
                "",
                "There are unsaved changes in this story. Do you want to save?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if box == QMessageBox.StandardButton.Save:
                if self.onSave():
                    event.accept()
                else:
                    event.ignore()
            elif box == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
            
        else:
            event.accept()


app = QApplication(argv)
mainWindow = MainWindow()
mainWindow.show()
app.exec()
