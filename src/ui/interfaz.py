import sys

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.structures.dictionary import search


class Ventana(QWidget):

    def __init__(self, warehouse):
        super().__init__()

        self.warehouse = warehouse

        self.escala = 60
        self.margen = 30


    def paintEvent(self, event):

        painter = QPainter(self)

        #Warehouse

        painter.drawRect(
            self.margen,
            self.margen,
            self.warehouse.width * self.escala,
            self.warehouse.height * self.escala
        )


        #Racks y Zonas del despacho

        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                cid = y * self.warehouse.width + x

                rack = search(self.warehouse.racks, cid)

                hall = search(self.warehouse.halls, cid)

                # Esquina superior izquierda de la celda
                xp = self.margen + x * self.escala
                yp = self.margen + y * self.escala


                # Si hay un rack en esta celda
                if rack is not None:

                    painter.setBrush(QBrush(QColor("gray")))

                    painter.drawRect(xp + 5, yp + 5, self.escala - 10, self.escala - 10)

                    painter.drawText(xp + 10, yp + 25, str(rack.id))


                # Si es una zona de despacho
                elif hall is not None and hall.zone is not None:

                    painter.setBrush(QBrush(QColor("lightgreen")))

                    painter.drawRect(xp + 5, yp + 5, self.escala - 10, self.escala - 10)


        #Aristas

        painter.setPen(QPen(QColor("black"), 2))

        actual = self.warehouse.graph.e.head

        while actual is not None:

            origen_id, destino_id, peso = actual.value

            hall_origen = search(self.warehouse.halls, origen_id)

            hall_destino = search(self.warehouse.halls, destino_id)

            if hall_origen is not None and hall_destino is not None:

                # Centro del hall origen
                x1 = (self.margen + hall_origen.x * self.escala + self.escala // 2)

                y1 = (self.margen + hall_origen.y * self.escala + self.escala // 2)

                # Centro del hall destino
                x2 = (self.margen + hall_destino.x * self.escala + self.escala // 2)

                y2 = (self.margen + hall_destino.y * self.escala + self.escala // 2)

                painter.drawLine(x1, y1, x2, y2)

            actual = actual.nextNode


        #HallNodes

        painter.setBrush(QBrush(QColor("black")))

        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                cid = y * self.warehouse.width + x

                hall = search(self.warehouse.halls, cid)

                if hall is not None:

                    # Centro de la celda
                    xp = (self.margen + hall.x * self.escala + self.escala // 2)

                    yp = (self.margen + hall.y * self.escala + self.escala // 2)

                    painter.drawEllipse(xp - 4, yp - 4, 8, 8)





app = QApplication(sys.argv)

config = load_config(
    "src/tests/init2.json"
)

warehouse = build_warehouse(config)

ventana = Ventana(warehouse)

ventana.resize(warehouse.width * 60 + 100,warehouse.height * 60 + 100)

ventana.show()

app.exec()