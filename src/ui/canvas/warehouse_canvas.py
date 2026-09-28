from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QPainter

class WarehouseCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        # Habilitar suavizado de bordes para una visualización clara
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Fondo oscuro acorde a la paleta
        self.setStyleSheet("background-color: #1e272c; border: 1px solid #34495e;")