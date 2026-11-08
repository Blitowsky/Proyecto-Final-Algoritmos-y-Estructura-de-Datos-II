import sys
from PyQt6.QtWidgets import QApplication
from src.ui.app_window import MainWindow

class MockGraphData:
    """Datos simulados hasta que tu equipo entregue el módulo core/graph."""
    def __init__(self):
        self.nodes = {
            "DESPACHO": (200, 450, "dispatch"),
            "N1": (200, 350, "intersection"),
            "N2": (350, 350, "intersection"),
            "N3": (500, 350, "intersection"),
            "N4": (200, 150, "intersection"),
            "N5": (350, 150, "intersection"),
            "N6": (500, 150, "intersection"),
            "P01": (200, 50, "rack"),
        }
        self.edges = [
            ("DESPACHO", "N1"),
            ("N1", "N2"), ("N2", "N3"),
            ("N1", "N4"), ("N2", "N5"), ("N3", "N6"),
            ("N4", "N5"), ("N5", "N6"),
            ("N4", "P01"),
        ]

def main():
    app = QApplication(sys.argv)

    # Escenario y ruta de prueba (ida y vuelta al despacho)
    mock_graph = MockGraphData()
    mock_route = ["DESPACHO", "N1", "N4", "P01", "N4", "N5", "N2", "N1", "DESPACHO"]

    window = MainWindow(mock_graph, mock_route)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()