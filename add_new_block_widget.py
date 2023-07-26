from PyQt6.QtGui import QPaintEvent, QPainter, QColor, QPainterPath, QPalette
from PyQt6.QtWidgets import QWidget, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, QPointF, QRectF, QRect, QPoint, pyqtSignal

POINTER_HEIGHT = 10
POINTER_WIDTH = 20
PADDING = 1
RECT_PADDING = 5

class AddNewBlockWidget(QWidget):
    confirmed = pyqtSignal(str)
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.__nameEntryWidget = QLineEdit(self)
        self.__nameEntryWidget.setAttribute(
            Qt.WidgetAttribute.WA_MacShowFocusRect, False
        )
        self.__nameEntryFont = self.__nameEntryWidget.font()
        self.__nameEntryFont.setPointSize(15)
        self.__nameEntryWidget.setFont(self.__nameEntryFont)

        self.__ly = QVBoxLayout(self)
        self.__ly.addWidget(self.__nameEntryWidget)

        self.__nameEntryWidget.returnPressed.connect(self.onReturnPressed)

    def onReturnPressed(self):
        self.confirmed.emit(self.__nameEntryWidget.text())
        self.__nameEntryWidget.setText("")


class BubbleOverlayWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, widget: QWidget | None = None):
        super().__init__(parent)
        self.setWidget(widget)


    def setWidget(self, widget: QWidget):
        self.__widget: QWidget | None = widget
        
        if self.__widget is not None:
            self.__widget.setParent(self)
            # self.__widget.setContentsMargins(0, 0, 0, 0)

            self.setGeometry(
                0,
                0,
                RECT_PADDING
                + PADDING
                + self.__widget.sizeHint().width()
                + PADDING
                + RECT_PADDING,
                POINTER_HEIGHT
                + PADDING
                + self.__widget.sizeHint().height()
                + PADDING
                + RECT_PADDING,
            )

            self.__widget.move(
                int(self.bodyRect().left() + PADDING),
                int(
                    self.bodyRect().center().y()
                    - self.__widget.sizeHint().height() / 2
                ),
            )

    def showAtPos(self, pos: QPoint):
        self.setPos(pos)
        self.show()

    def setPos(self, pos: QPoint):
        pos -= QPoint(int(self.rect().width() / 2), 0)
        self.move(pos)

    def paintEvent(self, a0: QPaintEvent) -> None:
        with QPainter(self) as p:
            p: QPainter
            p.setBrush(self.palette().brush(QPalette.ColorRole.Window))
            p.setPen(Qt.GlobalColor.gray)
            p.drawPath(self.createUnionPath())

            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(Qt.GlobalColor.green)
            # p.drawRect(self.rect())

        return super().paintEvent(a0)

    def bodyRect(self) -> QRectF:
        bodyRectHeight = PADDING + self.__widget.sizeHint().height() + PADDING
        return QRectF(
            RECT_PADDING,
            self.rect().height() - bodyRectHeight - RECT_PADDING,
            self.rect().width() - RECT_PADDING * 2,
            bodyRectHeight,
        )

    def createUnionPath(self):
        rectPath = QPainterPath()
        rectPath.addRoundedRect(self.bodyRect(), 5, 5)

        point = QPointF(self.bodyRect().center().x(), 0)
        triPath = QPainterPath()
        triPath.moveTo(point)
        triPath.lineTo(self.rect().center().toPointF() + QPointF(POINTER_WIDTH, 0))
        triPath.lineTo(self.rect().center().toPointF() - QPointF(POINTER_WIDTH, 0))

        return rectPath + triPath