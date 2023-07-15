from PyQt6.QtCore import QObject, QPointF
from re import compile

LINK_RE = compile(r"\[\[(.*?)\]\]")

class StoryBlock(QObject):
    def __init__(self, parent: QObject | None = None, pos: QPointF | None = None) -> None:
        super().__init__(parent)
        self.__name: str = ""
        self.__body: str = ""
        self.__pos: QPointF = pos if pos is not None else QPointF()
        self.__cachedConnections: list[StoryBlock] = []

    def setPos(self, pos: QPointF):
        self.__pos = pos

    def pos(self) -> QPointF:
        return self.__pos
    
    def setName(self, name: str):
        self.__name = name

    def name(self) -> str:
        return self.__name
    
    def setBody(self, body: str):
        self.__body = body

    def body(self) -> str:
        return self.__body
    
    def connections(self) -> list["StoryBlock"]:
        return self.__cachedConnections.copy()
    
    def addConnection(self, targetBlock: "StoryBlock"):
        self.setBody(self.body() + "\n" + f"[[{targetBlock.name()}]]")
        # self.parent().getConnectionsForBlock(self)
        # print(f"Connections for block {self.name()} are now {self.connections()}")
    

class Story(QObject):
    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.__startBlock: StoryBlock = None
        self.__blocks: list[StoryBlock] = []

    def setStartBlock(self, block: StoryBlock):
        self.__startBlock = block

    def startBlock(self) -> StoryBlock:
        return self.__startBlock
    
    def blocks(self) -> list[StoryBlock]:
        return self.__blocks.copy()
    
    def addBlock(self, block: StoryBlock):
        block.setParent(self)
        self.__blocks.append(block)
        self.getConnectionsForBlock(block)

    def removeBlock(self, block: StoryBlock):
        self.__blocks.remove(block)
        if self.__startBlock == block:
            self.__startBlock = None

    def updateBlockName(self, block: StoryBlock, oldName: str):
        for block in self.__blocks:
            block.setBody(
                block.body().replace(f"[[{oldName}]]", f"[[{block.name()}]]")
            )

    def getConnectionsForBlock(self, block: StoryBlock) -> list[StoryBlock]:
        connections: list[StoryBlock] = []
        for targetBlockName in LINK_RE.findall(block.body()):
            targetBlocks = [b for b in self.blocks() if b.name() == targetBlockName]
            if len(targetBlocks) == 1:
                connections.append(targetBlocks[0])
            elif len(targetBlocks) <= 0:
                print(f"No blocks with name \"{targetBlockName}\"")
            else:
                print(f"Multiple blocks with name \"{targetBlockName}\"")

        print(f"Looking for connections out from block {block.name()} - found {connections}")
        return connections