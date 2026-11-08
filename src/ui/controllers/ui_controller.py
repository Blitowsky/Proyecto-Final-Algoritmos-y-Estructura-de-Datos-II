from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class UIController(QObject):
    state_changed = pyqtSignal(str, list, str) # current, visited, status_msg

    def __init__(self, scene, route: list):
        super().__init__()
        self.scene = scene
        self.route = route
        self.step_index = 0

        self.timer = QTimer()
        self.timer.setInterval(700)
        self.timer.timeout.connect(self.step_forward)

    def play(self):
        if self.step_index >= len(self.route):
            self.reset()
        self.timer.start()

    def pause(self):
        self.timer.stop()

    def step_forward(self):
        if self.step_index < len(self.route):
            current = self.route[self.step_index]
            visited = self.route[:self.step_index]
            self.scene.update_picker_position(current, visited)
            self.step_index += 1
            msg = f"Picker en: {current} ({self.step_index}/{len(self.route)})"
            self.state_changed.emit(current, visited, msg)
        else:
            self.timer.stop()
            self.state_changed.emit("", self.route, "Simulación finalizada.")

    def reset(self):
        self.timer.stop()
        self.step_index = 0
        self.scene.update_picker_position("", [])
        self.state_changed.emit("", [], "Simulación reiniciada.")