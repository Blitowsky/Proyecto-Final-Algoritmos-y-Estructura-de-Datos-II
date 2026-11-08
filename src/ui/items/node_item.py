from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtGui import QBrush, QPen, QColor
from src.ui.styles import colors

class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id: str, x: float, y: float, node_type: str, radius: float = 12):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)
        self.node_id = node_id
        self.node_type = node_type
        self.setPen(QPen(QColor("#2c3e50"), 2))
        self.reset_state()

    def reset_state(self):
        if self.node_type == "dispatch":
            self.setBrush(QBrush(colors.COLOR_NODE_DISPATCH))
        elif self.node_type == "rack":
            self.setBrush(QBrush(colors.COLOR_NODE_RACK))
        else:
            self.setBrush(QBrush(colors.COLOR_NODE_DEFAULT))

    def set_active(self):
        """Nodo donde se encuentra el picker actualmente."""
        self.setBrush(QBrush(colors.COLOR_PICKER_ACTIVE))

    def set_visited(self):
        """Nodo que ya fue transitado."""
        self.setBrush(QBrush(colors.COLOR_NODE_VISITED))