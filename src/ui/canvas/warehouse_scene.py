from PyQt6.QtWidgets import QGraphicsScene, QGraphicsLineItem
from PyQt6.QtGui import QPen
from src.ui.items.node_item import NodeItem
from src.ui.styles import colors

class WarehouseScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes: dict[str, NodeItem] = {}

    def load_graph(self, nodes_data: dict, edges_data: list):
        self.clear()
        self.nodes.clear()

        # Dibujar aristas
        pen = QPen(colors.COLOR_EDGE, 3)
        for u, v in edges_data:
            x1, y1, _ = nodes_data[u]
            x2, y2, _ = nodes_data[v]
            self.addLine(x1, y1, x2, y2, pen)

        # Dibujar nodos
        for node_id, (x, y, n_type) in nodes_data.items():
            item = NodeItem(node_id, x, y, n_type)
            self.addItem(item)
            self.nodes[node_id] = item

    def update_picker_position(self, current_id: str, visited_ids: list):
        for node_id, item in self.nodes.items():
            if node_id == current_id:
                item.set_active()
            elif node_id in visited_ids:
                item.set_visited()
            else:
                item.reset_state()