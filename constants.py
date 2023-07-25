from PyQt6.QtGui import QColor, QPen
from PyQt6.QtCore import Qt, QSizeF

BG_COLOR = QColor(25, 27, 30, 255)
GRID_COLOR = QColor(44, 49, 54, 255)
DROP_SHADOW_COLOR = QColor(10, 10, 10, 128)

OUTPUT_COLOR = QColor(120, 120, 140)
CONNECTION_COLOR = QColor(100, 100, 120)
CONNECTION_WIDTH = 3

BLOCK_COLOR = QColor(98, 104, 111, 255)
ERROR_BLOCK_COLOR = QColor(131, 88, 90, 255)
SELECTED_BLOCK_PEN = QPen(QColor(192, 209, 232, 255), 3, Qt.PenStyle.SolidLine)

SELECTED_BLOCK_COLOR = QColor(200, 140, 150)
TEMP_NEW_BLOCK_COLOR = QColor(140, 140, 150, 128)
TEMP_NEW_BLOCK_OUTLINE_COLOR = QColor(150, 150, 190)

TEMP_NEW_BLOCK_PEN = QPen(TEMP_NEW_BLOCK_OUTLINE_COLOR, 2, Qt.PenStyle.DashLine)

CELL_SIZE = 50
DROP_SHADOW_PICKUP_RADIUS = CELL_SIZE
OUTPUT_RADIUS = int(CELL_SIZE / 6)

BLOCK_RECT_SIZE = QSizeF(CELL_SIZE * 3, CELL_SIZE)

CONNECTION_BEZIER_AMT = 75

ERROR_BADGE_COLOR = QColor(184, 47, 47, 255)
