"""Visualizador de pedidos ponderados para el proyecto Warehouse (PyQt6).

Entrada: warehouse y lista devuelta por ordenarPedidos(warehouse.orders).
No modifica pedidos, waves ni simulación.
"""

import math
import sys

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPolygonF
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QCheckBox,
    QAbstractItemView,
)


COLORES = [
    "#e53935", "#1e88e5", "#43a047", "#8e24aa", "#fb8c00",
    "#00897b", "#6d4c41", "#d81b60", "#3949ab", "#7cb342",
    "#00acc1", "#c0ca33", "#5e35b1", "#f4511e", "#039be5",
    "#7e57c2", "#558b2f", "#ad1457", "#546e7a", "#f9a825",
]


def recorrer_lista_enlazada(lista):
    """Itera la LinkedList propia usando .head / .nextNode."""
    actual = lista.head
    while actual is not None:
        if actual.value is not None:
            yield actual.value
        actual = actual.nextNode


def productos_de_pedido(pedido):
    """Devuelve [(producto, cantidad), ...] en el orden de las líneas."""
    resultado = []
    for linea in recorrer_lista_enlazada(pedido.lines):
        resultado.append((linea.product, linea.qty))
    return resultado


class PlanoPedidos(QWidget):
    def __init__(self, warehouse, pedidos_ponderados):
        super().__init__()
        self.warehouse = warehouse
        self.pedidos_ponderados = pedidos_ponderados
        self.pedido_seleccionado = None  # None = todos
        self.solo_top10 = False
        self.mostrar_etiquetas = True
        self.setMinimumSize(760, 580)

    def pedidos_visibles(self):
        if self.pedido_seleccionado is not None:
            return [p for p in self.pedidos_ponderados
                    if str(p[0].id) == self.pedido_seleccionado]
        if self.solo_top10:
            return self.pedidos_ponderados[:10]
        return self.pedidos_ponderados

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))

        ancho = self.warehouse.width
        alto = self.warehouse.height
        margen = 45
        lado = min((self.width() - 2 * margen) / ancho,
                   (self.height() - 2 * margen) / alto)
        lado = max(1.0, lado)
        x0 = (self.width() - ancho * lado) / 2
        y0 = (self.height() - alto * lado) / 2

        # Coordenada de celda -> centro en píxeles.
        # Igual que en interfaz.py, el eje Y crece hacia arriba.
        def centro_celda(x, y):
            return QPointF(x0 + (x + 0.5) * lado,
                           y0 + (alto - y - 0.5) * lado)

        # Fondo del plano
        painter.setPen(QPen(QColor("#263238"), 2))
        painter.setBrush(QBrush(QColor("#fafafa")))
        painter.drawRect(QRectF(x0, y0, ancho * lado, alto * lado))

        # Cuadrícula
        painter.setPen(QPen(QColor("#e0e0e0"), 0.6))
        for x in range(1, ancho):
            xp = x0 + x * lado
            painter.drawLine(QPointF(xp, y0), QPointF(xp, y0 + alto * lado))
        for y in range(1, alto):
            yp = y0 + y * lado
            painter.drawLine(QPointF(x0, yp), QPointF(x0 + ancho * lado, yp))

        # Celdas reales del warehouse: RACK, DOOR y ZONE
        # El import es local para usar las mismas constantes del proyecto.
        from warehouse.domain.cell import RACK, DOOR, ZONE

        tipos = {
            RACK: QColor("#b0bec5"),
            DOOR: QColor("#ef5350"),
            ZONE: QColor("#a5d6a7"),
        }
        painter.setPen(Qt.PenStyle.NoPen)
        for y in range(alto):
            for x in range(ancho):
                celda = self.warehouse.floor.cell_at(x, y)
                if celda is not None and celda.kind in tipos:
                    p = centro_celda(x, y)
                    painter.setBrush(QBrush(tipos[celda.kind]))
                    painter.drawRect(QRectF(p.x() - lado / 2, p.y() - lado / 2,
                                            lado, lado))

        # Ejes / referencias
        painter.setPen(QPen(QColor("#455a64"), 1))
        for x in range(0, ancho, 5):
            painter.drawText(QPointF(x0 + (x + 0.5) * lado - 5,
                                     y0 + alto * lado + 16), str(x))
        for y in range(0, alto, 5):
            painter.drawText(QPointF(x0 - 30,
                                     y0 + (alto - y - 0.5) * lado + 4), str(y))

        # Puntos y centroides: un color distinto por pedido.
        # Si hay muchos pedidos, algunos colores se reutilizan.
        # Etiquetas completas solo cuando hay un pedido seleccionado.
        visibles = self.pedidos_visibles()
        detalle = len(visibles) == 1

        for pedido, ponderacion, (cx, cy) in visibles:
            indice = next(i for i, entrada in enumerate(self.pedidos_ponderados)
                          if entrada[0] is pedido)
            color = QColor(COLORES[indice % len(COLORES)])
            puntos = productos_de_pedido(pedido)

            for producto, cantidad in puntos:
                p = centro_celda(producto.x, producto.y)
                radio = min(7.0, max(3.0, lado * 0.27))
                painter.setPen(QPen(QColor("white"), 1.2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(p, radio, radio)
                if detalle and self.mostrar_etiquetas:
                    painter.setPen(QPen(QColor("#263238"), 1))
                    painter.drawText(QPointF(p.x() + radio + 2,
                                              p.y() - radio - 2),
                                     f"{producto.id} (x{cantidad})")

            # Centroide (media de las posiciones, puede quedar fuera de racks).
            centro = centro_celda(cx, cy)
            radio_externo = min(15.0, max(8.0, lado * 0.58))
            poligono = QPolygonF()
            for i in range(10):
                angulo = -math.pi / 2 + i * math.pi / 5
                radio = radio_externo if i % 2 == 0 else radio_externo * 0.43
                poligono.append(QPointF(centro.x() + radio * math.cos(angulo),
                                         centro.y() + radio * math.sin(angulo)))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#111111"), 1.5))
            painter.drawPolygon(poligono)

            if self.mostrar_etiquetas and (detalle or len(visibles) <= 10):
                painter.setPen(QPen(QColor("#111111"), 1))
                etiqueta = (f"{pedido.id}  P={ponderacion:.3f}"
                            if detalle else str(pedido.id))
                painter.drawText(QPointF(centro.x() + radio_externo + 3,
                                         centro.y() - 3), etiqueta)


class VentanaPedidos(QWidget):
    def __init__(self, warehouse, pedidos_ponderados):
        super().__init__()
        self.setWindowTitle("Warehouse - Ponderación, productos y centroides")
        self.resize(1480, 850)
        self.datos = list(pedidos_ponderados)
        self.plano = PlanoPedidos(warehouse, self.datos)

        layout = QHBoxLayout(self)
        layout.addWidget(self.plano, stretch=3)

        lateral = QVBoxLayout()
        layout.addLayout(lateral, stretch=2)
        lateral.addWidget(QLabel("Pedidos ordenados por ponderación"))

        self.selector = QComboBox()
        self.selector.addItem("Todos los pedidos", None)
        self.selector.addItem("Top 10", "__top10__")
        for pedido, valor, centro in self.datos:
            self.selector.addItem(f"{pedido.id}   |   P={valor:.3f}", str(pedido.id))
        self.selector.currentIndexChanged.connect(self.cambiar_seleccion)
        lateral.addWidget(self.selector)

        self.check_etiquetas = QCheckBox("Mostrar etiquetas")
        self.check_etiquetas.setChecked(True)
        self.check_etiquetas.toggled.connect(self.cambiar_etiquetas)
        lateral.addWidget(self.check_etiquetas)

        self.tabla = QTableWidget(len(self.datos), 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Pedido", "Prioridad", "Ponderación", "Centroide", "Productos"]
        )
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.cellClicked.connect(self.seleccionar_fila)

        for fila, (pedido, valor, (cx, cy)) in enumerate(self.datos):
            valores = [str(pedido.id), str(pedido.priority), f"{valor:.3f}",
                       f"({cx:.1f}, {cy:.1f})",
                       str(len(productos_de_pedido(pedido)))]
            for col, contenido in enumerate(valores):
                item = QTableWidgetItem(contenido)
                item.setForeground(QColor(COLORES[fila % len(COLORES)]))
                self.tabla.setItem(fila, col, item)

        lateral.addWidget(self.tabla, stretch=1)
        lateral.addWidget(QLabel(
            "● Producto del pedido     ★ Centroide\n"
            "Gris: rack    Verde: zona    Rojo: puerta\n"
            "P = 0.7 × prioridad + 0.3 × (1 - distancia normalizada)"
        ))

    def cambiar_seleccion(self):
        valor = self.selector.currentData()
        self.plano.solo_top10 = valor == "__top10__"
        self.plano.pedido_seleccionado = (
            None if valor in (None, "__top10__") else valor
        )
        self.plano.update()

    def cambiar_etiquetas(self, activo):
        self.plano.mostrar_etiquetas = activo
        self.plano.update()

    def seleccionar_fila(self, fila, columna):
        # Índices 0=Todos, 1=Top10, 2...=pedidos ordenados.
        self.selector.setCurrentIndex(fila + 2)


# USO DESDE TU PROYECTO, después de construir el warehouse:
# from warehouse.algorithms.oredenarPedidos import ordenarPedidos  # ajustá la ruta real
# app = QApplication(sys.argv)
# config = load_config("src/data/escenario_grande.json")
# warehouse, noValido = build_warehouse(config)
# pedidos_ponderados = ordenarPedidos(warehouse.orders)
# ventana = VentanaPedidos(warehouse, pedidos_ponderados)
# ventana.showMaximized()
# sys.exit(app.exec())
