"""Visualizador independiente de Waves para el proyecto Warehouse (PyQt6).

Entrada: warehouse, waves_por_picker, donde waves_por_picker es la lista de
listas que devuelve generacionWaves(warehouse.orders, warehouse.pickers,
warehouse.wave_config).

No modifica waves, pedidos ni el estado de la simulacion.
"""

from __future__ import annotations

import math
from collections import defaultdict

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QCheckBox, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView,
)


COLORES = [
    "#1573c7", "#db6224", "#188856", "#9b4cc2", "#cc3e58",
    "#138caa", "#ad8421", "#6750aa", "#d24f9f", "#5e7a26",
    "#ef8a17", "#397e7b", "#8d5342", "#6289d8", "#a33760",
]


def iterar_linkedlist(lista):
    """Itera tanto la LinkedList propia (head / nextNode) como una lista Python."""
    if lista is None:
        return
    if hasattr(lista, "head"):
        nodo = lista.head
        while nodo is not None:
            if nodo.value is not None:
                yield nodo.value
            nodo = nodo.nextNode
    else:
        yield from lista


def datos_productos(pedido):
    """Devuelve (id, x, y, cantidad) de todas las lineas de un pedido."""
    salida = []
    for linea in iterar_linkedlist(pedido.lines):
        producto = linea.product
        salida.append((str(producto.id), float(producto.x), float(producto.y),
                       getattr(linea, "qty", 1)))
    return salida


def centroide(pedido):
    productos = datos_productos(pedido)
    if not productos:
        return None
    # Misma convencion que ordenarPedidos: cada linea pesa igual, no por cantidad.
    return (sum(p[1] for p in productos) / len(productos),
            sum(p[2] for p in productos) / len(productos))


def centroide_wave(wave):
    """Centro visual: promedio no ponderado de los centroides de sus pedidos."""
    centros = [centroide(p) for p in iterar_linkedlist(wave.orders)]
    centros = [c for c in centros if c is not None]
    if not centros:
        return None
    return sum(c[0] for c in centros) / len(centros), sum(c[1] for c in centros) / len(centros)


def color_con_alpha(color, alpha):
    c = QColor(color)
    c.setAlpha(alpha)
    return c


class VistaPlano(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QColor("#f8fafc"))
        self.setMinimumSize(480, 400)
        self._ajuste_inicial = True

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def ajustar(self):
        if self.scene() is not None:
            self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._ajuste_inicial:
            self.ajustar()


class VentanaWaves(QMainWindow):
    """Plano y arbol Picker -> Wave -> Pedido; compatible con LinkedList propia."""

    CELDA = 22

    def __init__(self, warehouse, waves_por_picker, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.waves_por_picker = waves_por_picker
        self.width_cells = int(warehouse.width)
        self.height_cells = int(warehouse.height)
        self.pickers = list(iterar_linkedlist(warehouse.pickers))
        self._indices_waves = {}
        self._arbol_items = {}
        self._seleccion = ("todo", None, None, None)

        self.setWindowTitle("Warehouse | Visualizacion de Waves y pedidos")
        self.resize(1540, 920)

        principal = QWidget()
        self.setCentralWidget(principal)
        layout = QHBoxLayout(principal)
        separador = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(separador)

        lateral = QWidget()
        izq = QVBoxLayout(lateral)
        self.titulo = QLabel("Waves por picker")
        fuente = QFont()
        fuente.setPointSize(14)
        fuente.setBold(True)
        self.titulo.setFont(fuente)
        izq.addWidget(self.titulo)
        izq.addWidget(QLabel("Seleccioná un picker, una Wave o un pedido:"))

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Picker / Wave / Pedido", "Peso (kg)"])
        self.arbol.setColumnWidth(0, 265)
        self.arbol.itemSelectionChanged.connect(self.seleccion_cambiada)
        izq.addWidget(self.arbol, 5)

        self.ver_ids = QCheckBox("Mostrar identificadores sobre la grilla")
        self.ver_ids.setChecked(True)
        self.ver_ids.toggled.connect(self.dibujar)
        izq.addWidget(self.ver_ids)

        self.ver_conexiones = QCheckBox("Conectar centroides con el centro de la Wave")
        self.ver_conexiones.setChecked(True)
        self.ver_conexiones.toggled.connect(self.dibujar)
        izq.addWidget(self.ver_conexiones)

        self.btn_todos = QPushButton("Mostrar todas las Waves")
        self.btn_todos.clicked.connect(self.mostrar_todo)
        izq.addWidget(self.btn_todos)

        self.btn_ajustar = QPushButton("Ajustar zoom")
        self.btn_ajustar.clicked.connect(lambda: self.vista.ajustar())
        izq.addWidget(self.btn_ajustar)

        izq.addWidget(QLabel("Pedidos visibles (cada fila pertenece a una Wave):"))
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Picker", "Wave", "Pedido", "Prioridad", "Peso (kg)", "Centroide"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        izq.addWidget(self.tabla, 4)

        separador.addWidget(lateral)

        derecha = QWidget()
        der = QVBoxLayout(derecha)
        self.resumen = QLabel("")
        self.resumen.setWordWrap(True)
        der.addWidget(self.resumen)
        self.vista = VistaPlano()
        self.escena = QGraphicsScene(self)
        self.vista.setScene(self.escena)
        der.addWidget(self.vista, 1)
        self.leyenda = QLabel(
            "● Producto (color por Wave, o por pedido al seleccionar una Wave)   "
            "★ Centroide del pedido   ◆ Centro visual de la Wave   "
            "Línea punteada = relación visual, NO recorrido del picker"
        )
        self.leyenda.setWordWrap(True)
        der.addWidget(self.leyenda)
        separador.addWidget(derecha)
        separador.setStretchFactor(0, 0)
        separador.setStretchFactor(1, 1)
        separador.setSizes([485, 1055])

        self.construir_arbol()
        self.dibujar()
        self.vista.ajustar()

    def construir_arbol(self):
        self.arbol.clear()
        self._indices_waves = {}
        self._arbol_items = {}

        root = QTreeWidgetItem(["TODOS LOS PICKERS", ""])
        root.setData(0, Qt.ItemDataRole.UserRole, ("todo", None, None, None))
        self.arbol.addTopLevelItem(root)

        contador = 0
        for i, waves in enumerate(self.waves_por_picker):
            picker = self.pickers[i] if i < len(self.pickers) else None
            pid = str(picker.id) if picker is not None else f"Picker {i + 1}"
            cap = getattr(picker, "capacity", None)
            etiqueta = f"{pid} (cap. {cap:g} kg)" if isinstance(cap, (int, float)) else pid
            nodo_picker = QTreeWidgetItem([etiqueta, ""])
            nodo_picker.setData(0, Qt.ItemDataRole.UserRole, ("picker", i, None, None))
            self.arbol.addTopLevelItem(nodo_picker)
            for j, wave in enumerate(waves):
                self._indices_waves[(i, j)] = contador
                contador += 1
                pedidos = list(iterar_linkedlist(wave.orders))
                peso = sum(float(getattr(p, "total_weight", 0) or 0) for p in pedidos)
                nodo_wave = QTreeWidgetItem(
                    [f"Wave {wave.id} ({len(pedidos)} pedidos)", f"{peso:.2f}"]
                )
                nodo_wave.setData(0, Qt.ItemDataRole.UserRole, ("wave", i, j, None))
                nodo_picker.addChild(nodo_wave)
                for k, pedido in enumerate(pedidos):
                    p_peso = float(getattr(pedido, "total_weight", 0) or 0)
                    nodo_pedido = QTreeWidgetItem([str(pedido.id), f"{p_peso:.2f}"])
                    nodo_pedido.setData(0, Qt.ItemDataRole.UserRole, ("pedido", i, j, k))
                    nodo_wave.addChild(nodo_pedido)
            nodo_picker.setExpanded(True)
        self.arbol.setCurrentItem(root)

    def mostrar_todo(self):
        self.arbol.setCurrentItem(self.arbol.topLevelItem(0))

    def seleccion_cambiada(self):
        items = self.arbol.selectedItems()
        if items:
            self._seleccion = items[0].data(0, Qt.ItemDataRole.UserRole)
        else:
            self._seleccion = ("todo", None, None, None)
        self.dibujar()

    def waves_visibles(self):
        tipo, pi, wi, oi = self._seleccion
        for i, waves in enumerate(self.waves_por_picker):
            if tipo in ("picker", "wave", "pedido") and i != pi:
                continue
            for j, wave in enumerate(waves):
                if tipo in ("wave", "pedido") and j != wi:
                    continue
                pedidos = list(iterar_linkedlist(wave.orders))
                if tipo == "pedido":
                    pedidos = [pedidos[oi]] if oi is not None and oi < len(pedidos) else []
                yield i, j, wave, pedidos

    def xy(self, x, y):
        """La coordenada (0,0) del warehouse esta abajo a la izquierda."""
        return QPointF((x + 0.5) * self.CELDA,
                       (self.height_cells - y - 0.5) * self.CELDA)

    def texto(self, x, y, s, color="#253448", size=8, negrita=False):
        it = self.escena.addText(str(s))
        f = it.font()
        f.setPointSize(size)
        f.setBold(negrita)
        it.setFont(f)
        it.setDefaultTextColor(QColor(color))
        it.setPos(x, y)
        it.setZValue(20)
        return it

    def estrella(self, cx, cy, color, radio=9, puntas=5):
        puntos = QPolygonF()
        for n in range(2 * puntas):
            a = -math.pi / 2 + n * math.pi / puntas
            r = radio if n % 2 == 0 else radio * 0.42
            puntos.append(QPointF(cx + math.cos(a) * r, cy + math.sin(a) * r))
        self.escena.addPolygon(puntos, QPen(QColor("#182334"), 1), QBrush(QColor(color)))

    def dibujar_suelo(self):
        cell = self.CELDA
        self.escena.setSceneRect(-28, -28, self.width_cells * cell + 56,
                                self.height_cells * cell + 56)
        self.escena.addRect(0, 0, self.width_cells * cell,
                            self.height_cells * cell, QPen(QColor("#415064"), 2),
                            QBrush(QColor("#ffffff")))
        # Cuadricula 1x1
        pen = QPen(QColor("#e6e9ee"), 0.7)
        for x in range(1, self.width_cells):
            self.escena.addLine(x * cell, 0, x * cell, self.height_cells * cell, pen)
        for y in range(1, self.height_cells):
            self.escena.addLine(0, y * cell, self.width_cells * cell, y * cell, pen)
        for x in range(0, self.width_cells, 5):
            self.texto(x * cell + 2, -23, x, size=7)
        for y in range(0, self.height_cells, 5):
            self.texto(-25, (self.height_cells - y - 1) * cell, y, size=7)

        for y in range(self.height_cells):
            for x in range(self.width_cells):
                cell_obj = self.warehouse.floor.cell_at(x, y)
                if cell_obj is None:
                    continue
                # Comparar con constantes reales evita asumir el tipo de enum/string.
                from warehouse.domain.cell import RACK, DOOR, ZONE
                if cell_obj.kind == RACK:
                    color = QColor("#bfc4cc")
                elif cell_obj.kind == DOOR:
                    color = QColor("#e9a7a0")
                elif cell_obj.kind == ZONE:
                    color = QColor("#b8e4c2")
                else:
                    continue
                xp = x * self.CELDA
                yp = (self.height_cells - 1 - y) * self.CELDA
                self.escena.addRect(xp + 1, yp + 1, cell - 2, cell - 2,
                                    QPen(Qt.PenStyle.NoPen), QBrush(color))

    def dibujar(self, *_):
        if not hasattr(self, "escena"):
            return
        self.escena.clear()
        self.dibujar_suelo()
        visible = list(self.waves_visibles())
        tipo = self._seleccion[0]
        filas = []
        num_waves = 0
        total_peso = 0
        total_pedidos = 0

        for i, j, wave, pedidos in visible:
            num_waves += 1
            color_wave = COLORES[self._indices_waves[(i, j)] % len(COLORES)]
            centro_w = centroide_wave(wave)
            if centro_w is None:
                continue
            ww = self.xy(*centro_w)
            for k, pedido in enumerate(pedidos):
                # Seleccionando una Wave, cada pedido se diferencia por color.
                color = COLORES[k % len(COLORES)] if tipo in ("wave", "pedido") else color_wave
                prod = datos_productos(pedido)
                cp = centroide(pedido)
                peso = float(getattr(pedido, "total_weight", 0) or 0)
                total_pedidos += 1
                total_peso += peso
                picker_id = str(self.pickers[i].id) if i < len(self.pickers) else f"PK_{i+1}"
                filas.append((picker_id, str(wave.id), str(pedido.id),
                              str(getattr(pedido, "priority", "")), f"{peso:.2f}",
                              f"({cp[0]:.1f}, {cp[1]:.1f})" if cp else "-"))
                if cp is not None:
                    pc = self.xy(*cp)
                    if self.ver_conexiones.isChecked():
                        pl = QPen(color_con_alpha(color, 130), 1.5, Qt.PenStyle.DashLine)
                        self.escena.addLine(pc.x(), pc.y(), ww.x(), ww.y(), pl)
                    self.estrella(pc.x(), pc.y(), color, radio=9)
                    if self.ver_ids.isChecked():
                        self.texto(pc.x() + 10, pc.y() - 22, str(pedido.id), color,
                                   size=8, negrita=True)
                for producto_id, x, y, cantidad in prod:
                    p = self.xy(x, y)
                    punto = self.escena.addEllipse(p.x() - 5, p.y() - 5, 10, 10,
                                                   QPen(QColor("#172235"), 1),
                                                   QBrush(QColor(color)))
                    punto.setZValue(9)
                    punto.setToolTip(
                        f"Picker: {picker_id}\nWave: {wave.id}\nPedido: {pedido.id}"
                        f"\nProducto: {producto_id}\nCantidad: {cantidad}"
                        f"\nUbicacion: ({x:g}, {y:g})"
                    )
                    if self.ver_ids.isChecked() and tipo == "pedido":
                        self.texto(p.x() + 6, p.y() + 1, producto_id,
                                   color, size=8)
            # Marcador distinto para el centro VISUAL de toda la wave.
            if tipo != "pedido":
                diamante = QPolygonF([
                    QPointF(ww.x(), ww.y() - 12), QPointF(ww.x() + 12, ww.y()),
                    QPointF(ww.x(), ww.y() + 12), QPointF(ww.x() - 12, ww.y())
                ])
                self.escena.addPolygon(diamante, QPen(QColor("#172235"), 2),
                                       QBrush(QColor(color_wave)))
                if self.ver_ids.isChecked():
                    self.texto(ww.x() + 12, ww.y() + 7,
                               f"W{wave.id}", color_wave, size=9, negrita=True)

        self.tabla.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            for c, valor in enumerate(fila):
                self.tabla.setItem(r, c, QTableWidgetItem(valor))

        cap = sum(len(waves) for waves in self.waves_por_picker)
        self.resumen.setText(
            f"Vista: {tipo.upper()} | Waves visibles: {num_waves} / {cap} | "
            f"Pedidos visibles: {total_pedidos} | "
            f"Peso de los pedidos visibles: {total_peso:.2f} kg\n"
            "Zoom con la rueda del mouse; arrastrá el plano para desplazarte. "
            "Pasá el cursor sobre un punto para ver a qué pedido y Wave pertenece."
        )


# Uso desde interfaz.py:
#   waves = generacionWaves(warehouse.orders, warehouse.pickers, warehouse.wave_config)
#   ventana_waves = VentanaWaves(warehouse, waves)
#   ventana_waves.show()
