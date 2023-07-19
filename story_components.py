from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QObject, QPointF, pyqtSignal
from re import compile
from time import time

LINK_RE = compile(r"\[\[(.*?)\]\]")


class SetStoryBlockNameCommand(QUndoCommand):
    def __init__(self, storyBlock: "StoryBlock", newText: str):
        super().__init__()
        self.__storyBlock = storyBlock
        self.__oldText = self.__storyBlock.name()
        self.__newText = newText

    def undo(self):
        self.__storyBlock.setName(self.__oldText)

    def redo(self):
        self.__storyBlock.setName(self.__newText)


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
        self.setText(f"Move Block" if len(storyBlocks) == 1 else f"Move {len(storyBlocks)} Blocks")
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
    def __init__(self, story: "Story", pos: QPointF):
        super().__init__()
        self.setText("Add Block")
        self.__story = story
        self.__block = StoryBlock(pos=pos)

    def undo(self):
        self.__story.removeBlock(self.__block)

    def redo(self):
        self.__story.addBlock(self.__block)


class AddStoryBlockWithLinkToExistingBlockCommand(QUndoCommand):
    def __init__(self, story: "Story", sourceBlock: "StoryBlock", pos: QPointF):
        super().__init__()
        self.setText("Add and Connect Block")
        self.__story = story
        self.__sourceBlock = sourceBlock
        self.__newBlock = StoryBlock(pos=pos)

    def undo(self):
        self.__sourceBlock.setBody(
            self.__sourceBlock.body()[: -len(f"\n[[{self.__newBlock.name()}]]")]
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
            self.__sourceBlock.body()[: -len(f"\n[[{self.__targetBlock.name()}]]")]
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
    nameChanged = pyqtSignal(object, str)
    bodyChanged = pyqtSignal()
    posChanged = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        name: str | None = None,
        body: str | None = None,
        pos: QPointF | None = None,
    ) -> None:
        super().__init__(parent)
        self.__name: str = name if name is not None else str(int(time()))
        self.__body: str = body if body is not None else ""
        self.__pos: QPointF = pos if pos is not None else QPointF()

    def __repr__(self) -> str:
        return f'<StoryBlock name="{self.__name}">'

    def setPos(self, pos: QPointF):
        self.__pos = pos
        self.posChanged.emit()

    def pos(self) -> QPointF:
        return self.__pos

    def setName(self, name: str):
        oldName = self.__name
        self.__name = name
        self.nameChanged.emit(self, oldName)

    def name(self) -> str:
        return self.__name

    def setBody(self, body: str):
        self.__body = body
        self.bodyChanged.emit()

    def body(self) -> str:
        return self.__body

    def addConnection(self, targetBlock: "StoryBlock"):
        self.setBody(self.body() + "\n" + f"[[{targetBlock.name()}]]")


class Story(QObject):
    stateChanged = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        startBlock: StoryBlock | None = None,
        blocks: list[StoryBlock] | None = None,
    ) -> None:
        super().__init__(parent)
        self.__startBlock: StoryBlock = startBlock
        self.__blocks: list[StoryBlock] = blocks if blocks is not None else []
        if len(self.__blocks) > 0:
            for block in self.__blocks:
                block.setParent(self)
                block.nameChanged.connect(self.updateBlockName)
                block.bodyChanged.connect(self.stateChanged)
                block.posChanged.connect(self.stateChanged)

    def setStartBlock(self, block: StoryBlock):
        self.__startBlock = block
        self.stateChanged.emit()

    def startBlock(self) -> StoryBlock:
        return self.__startBlock

    def blocks(self) -> list[StoryBlock]:
        return self.__blocks.copy()

    def addBlock(self, block: StoryBlock):
        block.setParent(self)
        block.nameChanged.connect(self.updateBlockName)
        block.bodyChanged.connect(self.stateChanged)
        block.posChanged.connect(self.stateChanged)
        self.__blocks.append(block)
        self.stateChanged.emit()

    def removeBlock(self, block: StoryBlock):
        block.nameChanged.disconnect(self.updateBlockName)
        block.bodyChanged.disconnect(self.stateChanged)
        block.posChanged.disconnect(self.stateChanged)
        self.__blocks.remove(block)
        if self.__startBlock == block:
            self.__startBlock = None
        self.stateChanged.emit()

    def updateBlockName(self, block: StoryBlock, oldName: str):
        for otherBlock in self.__blocks:
            otherBlock.setBody(
                otherBlock.body().replace(f"[[{oldName}]]", f"[[{block.name()}]]")
            )
        self.stateChanged.emit()

    def blockWithName(self, name: str):
        for block in self.__blocks:
            if block.name() == name:
                return block
        return None

    def getConnectionsForBlock(self, block: StoryBlock) -> list[StoryBlock]:
        connections: list[StoryBlock] = []
        for targetBlockName in LINK_RE.findall(block.body()):
            targetBlocks = [b for b in self.blocks() if b.name() == targetBlockName]
            if len(targetBlocks) == 1:
                connections.append(targetBlocks[0])
            elif len(targetBlocks) <= 0:
                print(f'No blocks with name "{targetBlockName}"')
            else:
                print(f'Multiple blocks with name "{targetBlockName}"')
        return connections
