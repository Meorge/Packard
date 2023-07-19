from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QWidget, QLineEdit, QTextEdit, QPlainTextEdit, QVBoxLayout, QPushButton
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

        self.idField = QLineEdit(parent=self)
        self.idField.setPlaceholderText("Page ID")
        self.idField.textEdited.connect(self.blockIdChanged)

        self.isStartBlockField = QPushButton("Make Start Node")
        self.isStartBlockField.clicked.connect(self.blockStartChanged)

        self.bodyField = QPlainTextEdit(parent=self)
        # self.bodyField.setAcceptRichText(False)
        self.bodyField.textChanged.connect(self.blockBodyChanged)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.titleField)
        self.layout().addWidget(self.idField)
        self.layout().addWidget(self.isStartBlockField)
        self.layout().addWidget(self.bodyField)

        self.setStory(story)

    def setStory(self, story: Story):
        self.__story = story

    def setBlock(self, block: StoryBlock):
        self.currentBlock = block
        self.updateContents()

    def updateContents(self):
        if self.currentBlock is not None:
            self.setEnabled(True)

            with QSignalBlocker(self.titleField) as _:
                self.titleField.setText(self.currentBlock.title())

            with QSignalBlocker(self.idField) as _:
                self.idField.setText(self.currentBlock.id())

            with QSignalBlocker(self.bodyField) as _:
                self.bodyField.setPlainText(self.currentBlock.body())

        else:
            self.setEnabled(False)

            with QSignalBlocker(self.titleField) as _:
                self.titleField.setText("")

            with QSignalBlocker(self.idField) as _:
                self.idField.setText("")

            with QSignalBlocker(self.bodyField) as _:
                self.bodyField.setPlainText("")

    def blockTitleChanged(self):
        if self.currentBlock is None:
            return 
        self.currentBlock.setTitle(self.titleField.text())

    def blockIdChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setId(self.idField.text())

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
