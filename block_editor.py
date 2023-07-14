import typing
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLineEdit, QTextEdit, QVBoxLayout, QPushButton

from story_document_block import StoryDocumentBlock


class BlockEditor(QWidget):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)

        self.titleField = QLineEdit()
        self.titleField.textChanged.connect(self.blockTitleChanged)

        self.isStartBlockField = QPushButton("Make Start Node")
        self.isStartBlockField.clicked.connect(self.blockStartChanged)

        self.bodyField = QTextEdit()
        self.bodyField.textChanged.connect(self.blockBodyChanged)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.titleField)
        self.layout().addWidget(self.isStartBlockField)
        self.layout().addWidget(self.bodyField)

    def setBlock(self, block: StoryDocumentBlock):
        self.currentBlock = block
        if self.currentBlock is not None:
            self.setEnabled(True)
            self.titleField.setText(self.currentBlock.name)
            self.bodyField.setText(self.currentBlock.body)
        else:
            self.setEnabled(False)
            self.titleField.setText("")
            self.bodyField.setText("")

    def blockTitleChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setName(self.titleField.text())

    def blockStartChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setIsStartBlock()

    def blockBodyChanged(self):
        if self.currentBlock is None:
            return
        self.currentBlock.setBody(self.bodyField.toPlainText())
