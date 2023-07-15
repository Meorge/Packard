from PyQt6.QtCore import QObject, QPointF, pyqtSignal
from re import compile
from time import time

LINK_RE = compile(r"\[\[(.*?)\]\]")


class StoryBlock(QObject):
    nameChanged = pyqtSignal(object, str)
    bodyChanged = pyqtSignal()
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
        self.__blocks.append(block)
        self.stateChanged.emit()


    def removeBlock(self, block: StoryBlock):
        block.nameChanged.disconnect(self.updateBlockName)
        block.bodyChanged.disconnect(self.stateChanged)
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
