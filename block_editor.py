from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QWidget, QLineEdit, QTextEdit, QVBoxLayout, QPushButton
from PyQt6.QtGui import QUndoStack, QUndoCommand
from story_components import (
    SetStoryBlockBodyCommand,
    SetStoryBlockNameCommand,
    SetStoryStartBlockCommand,
    Story,
    StoryBlock,
)


class BlockEditor(QWidget):
    def __init__(
        self, undoStack: QUndoStack, parent: QWidget | None = None, story: Story = None
    ) -> None:
        super().__init__(parent)

        self.__undoStack = undoStack
        self.__story: Story = None

        self.titleField = QLineEdit(parent=self)
        self.titleField.textEdited.connect(self.blockTitleChanged)

        self.isStartBlockField = QPushButton("Make Start Node")
        self.isStartBlockField.clicked.connect(self.blockStartChanged)

        self.bodyField = QTextEdit(parent=self)
        self.bodyField.setAcceptRichText(False)
        self.bodyField.textChanged.connect(self.blockBodyChanged)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.titleField)
        self.layout().addWidget(self.isStartBlockField)
        self.layout().addWidget(self.bodyField)

        self.setStory(story)

    def setStory(self, story: Story):
        # if self.__story is not None:
        #     self.__story.stateChanged.disconnect(self.updateContents)
        self.__story = story
        # self.__story.stateChanged.connect(self.updateContents)

    def setBlock(self, block: StoryBlock):
        self.currentBlock = block
        self.updateContents()

    def updateContents(self):
        if self.currentBlock is not None:
            self.setEnabled(True)

            with QSignalBlocker(self.titleField) as _:
                self.titleField.setText(self.currentBlock.name())

            with QSignalBlocker(self.bodyField) as _:
                self.bodyField.setText(self.currentBlock.body())

        else:
            self.setEnabled(False)

            with QSignalBlocker(self.titleField) as _:
                self.titleField.setText("")

            with QSignalBlocker(self.bodyField) as _:
                self.bodyField.setText("")

    def blockTitleChanged(self):
        if self.currentBlock is None:
            return 
        self.currentBlock.setName(self.titleField.text())

    def blockStartChanged(self):
        if self.currentBlock is None:
            return
        self.__undoStack.push(
            SetStoryStartBlockCommand(self.__story, self.currentBlock)
        )

    def blockBodyChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setBody(self.bodyField.toPlainText())
