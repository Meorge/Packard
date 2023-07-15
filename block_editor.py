import typing
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, pyqtSignal, QSignalBlocker
from PyQt6.QtWidgets import QWidget, QLineEdit, QTextEdit, QVBoxLayout, QPushButton
from story_components import Story, StoryBlock


class BlockEditor(QWidget):
    def __init__(self, parent: QWidget | None = None, story: Story = None) -> None:
        super().__init__(parent)

        self.__story = story

        self.titleField = QLineEdit(parent=self)
        self.titleField.textChanged.connect(self.blockTitleChanged)

        self.isStartBlockField = QPushButton("Make Start Node")
        self.isStartBlockField.clicked.connect(self.blockStartChanged)

        self.bodyField = QTextEdit(parent=self)
        self.bodyField.setAcceptRichText(False)
        self.bodyField.textChanged.connect(self.blockBodyChanged)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.titleField)
        self.layout().addWidget(self.isStartBlockField)
        self.layout().addWidget(self.bodyField)

    def setBlock(self, block: StoryBlock):
        self.currentBlock = block
        if self.currentBlock is not None:
            self.setEnabled(True)
            print(f"BlockEditor setBlock - change title and body to match current block")

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
        self.__story.setStartBlock(self.currentBlock)

    def blockBodyChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setBody(self.bodyField.toPlainText())
