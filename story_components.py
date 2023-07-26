from enum import unique
from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QObject, QPointF, pyqtSignal
from re import compile, escape
from time import time
from saver import check_story_for_errors, errors_as_list
from story_link import LINK_RE


class SetStoryBlockNameCommand(QUndoCommand):
    def __init__(self, storyBlock: "StoryBlock", newText: str):
        super().__init__()
        self.__storyBlock = storyBlock
        self.__oldText = self.__storyBlock.title()
        self.__newText = newText

    def undo(self):
        self.__storyBlock.setTitle(self.__oldText)

    def redo(self):
        self.__storyBlock.setTitle(self.__newText)


class SetStoryBlockBodyCommand(QUndoCommand):
    def __init__(self, storyBlock: "StoryBlock", newText: str):
        super().__init__()
        self.__storyBlock = storyBlock
        self.__oldText = self.__storyBlock.body()
        self.__newText = newText

    def undo(self):
        self.__storyBlock.setBody(self.__oldText)

    def redo(self):
        self.__storyBlock.setBody(self.__newText)


class MoveStoryBlocksCommand(QUndoCommand):
    def __init__(self, storyBlocks: dict["StoryBlock", QPointF], delta: QPointF):
        super().__init__()
        self.setText(
            f"Move Block"
            if len(storyBlocks) == 1
            else f"Move {len(storyBlocks)} Blocks"
        )
        self.__storyBlocks = storyBlocks
        self.__delta = delta

    def undo(self):
        for block, initialPos in self.__storyBlocks.items():
            block.setPos(block.pos() - self.__delta)

    def redo(self):
        for block, initialPos in self.__storyBlocks.items():
            block.setPos(initialPos + self.__delta)


class SetStoryStartBlockCommand(QUndoCommand):
    def __init__(self, story: "Story", newStartBlock: "StoryBlock"):
        super().__init__()
        self.setText("Set Start Block")
        self.__story = story
        self.__oldBlock = self.__story.startBlock()
        self.__newBlock = newStartBlock

    def undo(self):
        self.__story.setStartBlock(self.__oldBlock)

    def redo(self):
        self.__story.setStartBlock(self.__newBlock)


class AddStoryBlockCommand(QUndoCommand):
    def __init__(self, story: "Story", title: str, id: str, pos: QPointF):
        super().__init__()
        self.setText("Add Block")
        self.__story = story
        self.__block = StoryBlock(title=title, id=id, pos=pos)

    def undo(self):
        self.__story.removeBlock(self.__block)

    def redo(self):
        self.__story.addBlock(self.__block)


class AddStoryBlockWithLinkToExistingBlockCommand(QUndoCommand):
    def __init__(
        self,
        story: "Story",
        sourceBlock: "StoryBlock",
        title: str,
        id: str,
        pos: QPointF,
    ):
        super().__init__()
        self.setText("Add and Connect Block")
        self.__story = story
        self.__sourceBlock = sourceBlock
        self.__newBlock = StoryBlock(title=title, id=id, pos=pos)

    def undo(self):
        self.__sourceBlock.setBody(
            self.__sourceBlock.body()[: -len(f"\n[[{self.__newBlock.title()}]]")]
        )
        self.__story.removeBlock(self.__newBlock)

    def redo(self):
        self.__story.addBlock(self.__newBlock)
        self.__sourceBlock.addConnection(self.__newBlock)


class AddLinkBetweenBlocksCommand(QUndoCommand):
    def __init__(self, sourceBlock: "StoryBlock", targetBlock: "StoryBlock"):
        super().__init__()
        self.setText("Link Blocks")
        self.__sourceBlock = sourceBlock
        self.__targetBlock = targetBlock

    def undo(self):
        self.__sourceBlock.setBody(
            self.__sourceBlock.body()[: -len(f"\n[[{self.__targetBlock.title()}]]")]
        )

    def redo(self):
        self.__sourceBlock.addConnection(self.__targetBlock)


class DeleteStoryBlockCommand(QUndoCommand):
    def __init__(self, story: "Story", blocks: list["StoryBlock"]):
        super().__init__()
        self.setText("Delete Block")
        self.__story = story
        self.__blocks = blocks

    def undo(self) -> None:
        for b in self.__blocks:
            self.__story.addBlock(b)

    def redo(self) -> None:
        for b in self.__blocks:
            self.__story.removeBlock(b)


class StoryBlock(QObject):
    titleChanged = pyqtSignal(object, str)
    idChanged = pyqtSignal(object, str)
    bodyChanged = pyqtSignal()
    posChanged = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        title: str | None = None,
        id: str | None = None,
        body: str | None = None,
        pos: QPointF | None = None,
    ) -> None:
        super().__init__(parent)
        self.__title: str = title if title is not None else "Untitled Passage"
        self.__id: str = id if id is not None else str(int(time()))
        self.__body: str = body if body is not None else ""
        self.__pos: QPointF = pos if pos is not None else QPointF()

    def __repr__(self) -> str:
        return f'<StoryBlock title="{self.__title}" id="{self.__id}">'

    def parent(self) -> "Story":
        return super().parent()

    def setPos(self, pos: QPointF):
        self.__pos = pos
        self.posChanged.emit()

    def pos(self) -> QPointF:
        return self.__pos

    def setTitle(self, name: str):
        oldName = self.__title
        self.__title = name
        self.titleChanged.emit(self, oldName)

    def title(self) -> str:
        return self.__title

    def setId(self, id: str):
        oldId = self.__id
        self.__id = id
        self.idChanged.emit(self, oldId)

    def id(self) -> str:
        return self.__id

    def setBody(self, body: str):
        self.__body = body
        self.bodyChanged.emit()

    def body(self) -> str:
        return self.__body

    def addConnection(self, targetBlock: "StoryBlock"):
        self.setBody(
            self.body() + "\n" + f"[[{targetBlock.title()}->{targetBlock.id()}]]"
        )


class Story(QObject):
    stateChanged = pyqtSignal()
    errorsReevaluated = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        startBlock: StoryBlock | None = None,
        blocks: list[StoryBlock] | None = None,
    ) -> None:
        super().__init__(parent)
        self.__startBlock: StoryBlock = startBlock
        self.__blocks: list[StoryBlock] = blocks if blocks is not None else []
        self.__modified: bool = False
        self.stateChanged.connect(self.onStateChanged)
        if len(self.__blocks) > 0:
            for block in self.__blocks:
                block.setParent(self)
                self.makeBlockConnections(block)

    def resetModified(self):
        self.__modified = False

    def modified(self) -> bool:
        return self.__modified

    def onStateChanged(self):
        self.__cachedErrors = check_story_for_errors(self.data())
        self.__modified = True

    def makeBlockConnections(self, block: StoryBlock):
        block.setParent(self)
        block.titleChanged.connect(self.stateChanged)
        block.idChanged.connect(self.updateBlockId)
        block.bodyChanged.connect(self.stateChanged)
        block.posChanged.connect(self.stateChanged)

        block.titleChanged.connect(self.errorsReevaluated)
        block.idChanged.connect(self.errorsReevaluated)
        block.bodyChanged.connect(self.errorsReevaluated)

    def disconnectBlockSignals(self, block: StoryBlock):
        block.setParent(None)
        block.titleChanged.disconnect(self.stateChanged)
        block.idChanged.disconnect(self.updateBlockId)
        block.bodyChanged.disconnect(self.stateChanged)
        block.posChanged.disconnect(self.stateChanged)

        block.titleChanged.disconnect(self.errorsReevaluated)
        block.idChanged.disconnect(self.errorsReevaluated)
        block.bodyChanged.disconnect(self.errorsReevaluated)

    def setStartBlock(self, block: StoryBlock):
        self.__startBlock = block
        self.stateChanged.emit()

    def startBlock(self) -> StoryBlock:
        return self.__startBlock

    def blocks(self) -> list[StoryBlock]:
        return self.__blocks.copy()

    def addBlock(self, block: StoryBlock):
        if block in self.blocks():
            return

        self.makeBlockConnections(block)
        self.__blocks.append(block)

        if len(self.__blocks) == 1:
            self.setStartBlock(block)

        self.stateChanged.emit()
        self.errorsReevaluated.emit()

    def removeBlock(self, block: StoryBlock):
        self.disconnectBlockSignals(block)
        self.__blocks.remove(block)
        if self.__startBlock == block:
            self.__startBlock = None
        self.stateChanged.emit()
        self.errorsReevaluated.emit()

    def updateBlockId(self, block: StoryBlock, oldId: str):
        b = compile(r"\[\[(.*?)->" + escape(oldId) + r"\]\]")
        for otherBlock in self.__blocks:
            otherBlock.setBody(
                b.sub(
                    r"[[\1->" + block.id().replace("\\", r"\\") + r"]]",
                    otherBlock.body(),
                )
            )
        self.stateChanged.emit()

    def getConnectionsForBlock(self, block: StoryBlock) -> list[StoryBlock]:
        connections: list[StoryBlock] = []
        for _, targetBlockId in LINK_RE.findall(block.body()):
            targetBlocks = [b for b in self.blocks() if b.id() == targetBlockId]
            if len(targetBlocks) == 1:
                connections.append(targetBlocks[0])
        return connections

    def errors(self) -> dict[str, list[dict]]:
        return check_story_for_errors(self.data())

    def errorsAsList(self) -> list[dict]:
        return errors_as_list(self.errors())

    def data(self) -> dict:
        return {
            "start": self.startBlock().id()
            if isinstance(self.startBlock(), StoryBlock)
            else None,
            "blocks": [
                {
                    "x": block.pos().x(),
                    "y": block.pos().y(),
                    "title": block.title(),
                    "id": block.id(),
                    "body": block.body(),
                }
                for block in self.blocks()
            ],
        }
