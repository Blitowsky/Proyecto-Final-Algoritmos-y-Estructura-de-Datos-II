from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.ui.canvas.warehouse_canvas import WarehouseCanvas
from src.ui.canvas.warehouse_scene import WarehouseScene
from src.ui.widgets.simulation_controls import SimulationControls
from src.ui.controllers.ui_controller import UIController

class MainWindow(QMainWindow):
    def __init__(self, graph_data, route_sample):
        super().__init__()
        self.setWindowTitle("Warehouse Wave Picking Simulator - Algoritmos II")
        self.resize(800, 600)

        # Escena y Canvas
        self.scene = WarehouseScene()
        self.scene.load_graph(graph_data.nodes, graph_data.edges)
        self.canvas = WarehouseCanvas(self.scene)

        # Controles y Controlador
        self.controls = SimulationControls()
        self.controller = UIController(self.scene, route_sample)

        # Conexión de señales
        self.controls.play_requested.connect(self.controller.play)
        self.controls.pause_requested.connect(self.controller.pause)
        self.controls.step_requested.connect(self.controller.step_forward)
        self.controls.reset_requested.connect(self.controller.reset)

        self.lbl_status = QLabel("Listo para simular")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.controller.state_changed.connect(lambda cur, vis, msg: self.lbl_status.setText(msg))

        # Layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.canvas)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.controls)
        self.setCentralWidget(central)