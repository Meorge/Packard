from PyQt6 import QtGui
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsView,
    QWidget,
    QDockWidget,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QAction, QKeySequence, QUndoStack, QCloseEvent, QTransform
from sys import argv
from block_editor import BlockEditor
from error_list_widget import ErrorListWidget
from graph_scene import GraphScene
from graph_view import GraphView
from id_ify import id_ify
from status_bar import StatusBar
from saver import errors_as_list, load_story, save_story, compile_story_to_html
from os.path import basename

from story_components import (
    AddStoryBlockCommand,
    DeleteStoryBlockCommand,
    Story,
    StoryBlock,
)


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.undoStack = QUndoStack(self)
        self.currentStoryPath: str | None = None

        self.currentStory: Story | None = None

        self.graphScene = GraphScene(parent=self, undoStack=self.undoStack)
        self.graphView = GraphView(self.graphScene, parent=self)

        self.graphScene.blockAdded.connect(self.graphView.onUserRequestedNewNode)
        self.graphView.userConfirmedNewNode.connect(self.blockAdded)
        # self.graphScene.blockAdded.connect(self.blockAdded)
        self.graphScene.blockRemoved.connect(self.blockRemoved)

        

        self.setCentralWidget(self.graphView)

        self.graphScene.blockSelectionChanged.connect(self.onSelectionChanged)

        # set up editor
        self.editor = BlockEditor(undoStack=self.undoStack, parent=self)
        self.onSelectionChanged()
        self.editorDockWidget = QDockWidget("Editor")
        self.editorDockWidget.setWidget(self.editor)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.editorDockWidget)

        # Set up error pane
        self.errorPaneContents = ErrorListWidget(self)
        self.errorPaneDockWidget = QDockWidget("Errors")
        self.errorPaneDockWidget.setWidget(self.errorPaneContents)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.errorPaneDockWidget)


        # Status bar
        self.__statusBar = StatusBar(self)
        self.setStatusBar(self.__statusBar)
        self.__statusBar.zoomSet.connect(self.onZoomSet)

        self.__statusBar.setToggleErrorPaneAction(self.errorPaneDockWidget.toggleViewAction())

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

        self.setStory(Story())

        self.updateWindowTitle()



    def onSave(self) -> bool:
        if self.currentStoryPath is None:
            return self.onSaveAs()

        save_story(self.currentStoryPath, self.currentStory.data())
        self.currentStory.resetModified()
        return True

    def onSaveAs(self) -> bool:
        saveLocation = QFileDialog.getExistingDirectory(self, "Save Story As...")

        if saveLocation == "":
            return False

        storyData = self.currentStory.data()

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


        self.currentStoryPath = openLocation

        self.setStory(newStory)

        self.updateWindowTitle()

    def setStory(self, story: Story):
        if self.currentStory is not None:
            self.currentStory.stateChanged.disconnect(self.updateWindowTitle)
        self.currentStory = story

        if self.currentStory is not None:
            self.currentStory.stateChanged.connect(self.updateWindowTitle)

        self.graphScene.setStory(self.currentStory)
        self.errorPaneContents.setStory(self.currentStory)
        self.editor.setStory(self.currentStory)
        self.__statusBar.setStory(self.currentStory)

    def onCompileStory(self):
        totalErrors = errors_as_list(self.currentStory.errors())
        if len(totalErrors) > 0:
            errorString = f"{'were' if len(totalErrors) != 1 else 'was'} {len(totalErrors)} error{'s' if len(totalErrors) != 1 else ''}"
            QMessageBox.critical(
                self,
                "Could not compile story",
                f"""The story could not be compiled because there {errorString}.
                Please fix the errors and try again.""",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok,
            )
            return False
    
        compileLocation = QFileDialog.getExistingDirectory(self, "Compile Story...")

        if compileLocation == "":
            return

        self.onSave()
        compile_story_to_html(compileLocation, self.currentStoryPath)

    def updateWindowTitle(self):
        title = "Packard - "
        title += (
            basename(self.currentStoryPath)
            if self.currentStoryPath is not None
            else "Untitled Story"
        )
        if self.currentStory.modified():
            title += " (Unsaved)"
        self.setWindowTitle(title)

    def onSelectionChanged(self):
        selectedItems = self.graphScene.selectedBlocks()
        if len(selectedItems) == 1:
            self.editor.setBlock(selectedItems[0])
        else:
            self.editor.setBlock(None)

    def blockAdded(self, title: str, pos: QPointF):
        self.undoStack.push(AddStoryBlockCommand(self.currentStory, title=title, id=id_ify(title), pos=pos))

    def blockRemoved(self, block: StoryBlock):
        self.undoStack.push(DeleteStoryBlockCommand(self.currentStory, block))

    def onZoomSet(self, zoomAmount: float):
        tr = QTransform()
        tr.scale(zoomAmount / 100.0, zoomAmount / 100.0)
        self.graphView.setTransform(tr)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.currentStory.modified():
            box = QMessageBox.question(
                self,
                "",
                "There are unsaved changes in this story. Do you want to save?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
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
