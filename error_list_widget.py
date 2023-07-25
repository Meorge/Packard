from PyQt6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from saver import error_to_string
from story_components import Story

TYPE_ROLE = Qt.ItemDataRole.UserRole + 0
BLOCK_ID_ROLE = Qt.ItemDataRole.UserRole + 1
CONTENT_ROLE = Qt.ItemDataRole.UserRole + 2


class ErrorListWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.__story: Story | None = None

        self.__listWidget = QTreeWidget(self)  # , columnCount=1)
        self.__listWidget.setHeaderHidden(True)
        self.__listWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)

        self.__monospaceFont = QFont("Courier")
        self.__monospaceFont.setStyleHint(QFont.StyleHint.TypeWriter)

        self.__ly = QVBoxLayout(self)
        self.__ly.addWidget(self.__listWidget)
        
    def setStory(self, story: Story):
        if self.__story is not None:
            self.__story.errorsReevaluated.disconnect(self.onErrorsReevaluated)
        self.__story = story
        self.__story.errorsReevaluated.connect(self.onErrorsReevaluated)

    def onErrorsReevaluated(self):
        while self.__listWidget.topLevelItemCount() > 0:
            self.__listWidget.takeTopLevelItem(0)
            
        # Each QTreeWidgetItem has the following data:
        # 0 - whether it's a "block" or an "error"
        # 1 - the ID for the block
        # 2 - if it's an error, the error data
        for blockId, errors in self.__story.errors().items():
            if len(errors) <= 0:
                continue

            blockIdItem = QTreeWidgetItem(self.__listWidget)
            blockIdItem.setData(0, TYPE_ROLE, "block")
            blockIdItem.setData(0, BLOCK_ID_ROLE, blockId)
            blockIdItem.setData(0, CONTENT_ROLE, None)
            blockIdItem.setFont(0, self.__monospaceFont)
            blockIdItem.setText(0, blockId)

            for error in errors:
                newItem = QTreeWidgetItem(blockIdItem)
                newItem.setData(0, TYPE_ROLE, "error")
                newItem.setData(0, BLOCK_ID_ROLE, blockId)
                newItem.setData(0, CONTENT_ROLE, error)
                l = QLabel(error_to_string(error), wordWrap=True)
                self.__listWidget.setItemWidget(newItem, 0, l)

    def onItemDoubleClicked(self, item: QTreeWidgetItem, col: int):
        itemType = item.data(0, TYPE_ROLE)
        blockId = item.data(0, BLOCK_ID_ROLE)
        content = item.data(0, CONTENT_ROLE)
        if itemType == "block":
            # Go to block
            ...
        elif itemType == "error":
            # Go to block then go to line with error?
            ...

        print(f"{item} double clicked on column {col}")
