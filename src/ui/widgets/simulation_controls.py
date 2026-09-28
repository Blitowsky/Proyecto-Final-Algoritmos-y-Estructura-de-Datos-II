from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class SimulationControls(QWidget):
    # Señales para notificar al controlador sin acoplarse a él
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    step_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self.btn_play = QPushButton("Iniciar / Continuar")
        self.btn_pause = QPushButton("Pausar")
        self.btn_step = QPushButton("Paso a paso")
        self.btn_reset = QPushButton("Reiniciar")

        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_step)
        layout.addWidget(self.btn_reset)

        self.btn_play.clicked.connect(self.play_requested.emit)
        self.btn_pause.clicked.connect(self.pause_requested.emit)
        self.btn_step.clicked.connect(self.step_requested.emit)
        self.btn_reset.clicked.connect(self.reset_requested.emit)