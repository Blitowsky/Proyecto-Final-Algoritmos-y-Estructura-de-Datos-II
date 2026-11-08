
import os

import sys
import math
import pickle
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QTextEdit,
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QLineEdit,
    QFileDialog, QMessageBox, QDialogButtonBox
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from PyQt6.QtCore import QTimer, Qt


from warehouse.algorithms.wave_generation.order_centroids.product_centroids import ProductCentroidSelector
from warehouse.services.wave_builder import WaveBuilder
from warehouse.simulation.simulation import Simulation
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.domain.direction import N, S, E, O, AMBOS
from warehouse.algorithms.generacioWave import generacionWaves
from warehouse.structures.linkedlist import LinkedList, add


#Tipos de celdas que puede tener el warehouse
from warehouse.domain.cell import HALL, RACK, DOOR, ZONE


class Ventana(QWidget):

    def __init__(self, warehouse, simulation):
        super().__init__()

        #Guardo el warehouse que recibo
        self.warehouse = warehouse
        
        #Guardo la simulacion
        self.simulation = simulation
        self.finalizando = False
        self.resumen_mostrado = False

        #Espacio que dejo alrededor del warehouse
        self.margen = 60

        #Valor inicial, despues se calcula dependiendo del tamaño de la ventana
        self.escala = 1
        
        #Imagenes de la interfaz

        PICKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "construction-worker.png")
        self.imagen_picker = QPixmap(PICKER_PATH)
        PRODUCT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "box.png")
        self.imagen_producto = QPixmap(PRODUCT_PATH)
        
        
        #Timer que va avanzando la simulacion
        self.timer = QTimer(self)

        #Cada vez que el timer se activa ejecuto un tick
        self.timer.timeout.connect(self.avanzar_simulacion)

        #Tiempo entre ticks
        self.timer.setInterval(1)
        
        
        # ==================================================
        # BOTONES
        # ==================================================
        
        
        #Boton para iniciar la simulacion
        self.boton_play = QPushButton("Play", self)
        self.boton_play.setGeometry(30, 10, 80, 30)
        self.boton_play.clicked.connect(self.play)


        #Boton para pausar la simulacion
        self.boton_pause = QPushButton("Pause", self)
        self.boton_pause.setGeometry(120, 10, 80, 30)
        self.boton_pause.clicked.connect(self.pause)


        #Boton para avanzar un solo tick
        self.boton_paso = QPushButton("Paso", self)
        self.boton_paso.setGeometry(210, 10, 80, 30)
        self.boton_paso.clicked.connect(self.paso)

        # Guarda el estado actual (sin avanzar un tick).
        self.boton_guardar = QPushButton("Guardar", self)
        self.boton_guardar.setGeometry(300, 10, 90, 30)
        self.boton_guardar.clicked.connect(self.guardar_simulacion)

        # Completa la simulación sin animar los movimientos intermedios.
        self.boton_finalizar = QPushButton("Finalizar", self)
        self.boton_finalizar.setGeometry(400, 10, 90, 30)
        self.boton_finalizar.clicked.connect(self.finalizar_simulacion)
        
        # ==================================================
        # TICK ACTUAL
        # ==================================================

        self.label_tick = QLabel(f"Tick: {self.simulation.tick}", self)
        self.label_tick.setGeometry(510, 10, 150, 30)
        
        # ==================================================
        # PANEL DE EVENTOS
        # ==================================================

        self.panel_eventos = QTextEdit(self)

        #No permito que el usuario escriba
        self.panel_eventos.setReadOnly(True)

        #Espacio reservado para el panel de eventos
        self.ancho_panel = 400
        self.separacion_panel = 30
        self.margen_derecho = 30

        #Posicion y tamaño
        self.panel_eventos.setGeometry(920, 60, 400, 550)


        #Texto inicial
        self.panel_eventos.setPlainText("Eventos de la simulacion:\n")
        
        # ==================================================
        # ESTADO VISUAL DE LOS PICKERS
        # ==================================================

        self.estado_pickers = {}

        actual_picker = self.warehouse.pickers.head

        while actual_picker is not None:

            picker = actual_picker.value

            if picker is not None:
                self.estado_pickers[picker.id] = "Libre"

            actual_picker = actual_picker.nextNode

    def formatear_evento(self, evento):

        if evento.kind == "start":
            accion = "inicio"

        elif evento.kind == "pick":
            accion = "recogio"

        elif evento.kind == "drop":
            accion = "descargo"

        elif evento.kind == "wait":
            accion = "espera"

        elif evento.kind == "reroute":
            accion = "recalculo su ruta"

        elif evento.kind == "side_step":
            accion = "cedio el paso"

        elif evento.kind == "finish":
            accion = "termino"

        else:
            accion = evento.kind

        texto = (
            "Tick " + str(evento.tick)
            + " | "
            + str(evento.picker)
            + " "
            + accion
        )

        if evento.detail != "":
            texto += ": " + evento.detail

        return texto

    def dibujar_sentido(self, painter, cell, x, y):

        sentido = cell.sentido

        #Si puede circular en ambos sentidos no dibujo flecha
        if sentido == AMBOS:
            return

        #Centro de la celda
        xp, yp = self.coordenada_a_pixel(x, y)

        cx = xp + self.escala // 2
        cy = yp + self.escala // 2

        #Longitud de la flecha
        largo = max(3, self.escala // 3)

        #Defino direccion y color
        if sentido == N:
            dx = 0
            dy = -largo
            color = QColor("blue")

        elif sentido == S:
            dx = 0
            dy = largo
            color = QColor("red")

        elif sentido == E:
            dx = largo
            dy = 0
            color = QColor("green")

        elif sentido == O:
            dx = -largo
            dy = 0
            color = QColor("orange")

        else:
            return

        painter.setPen(QPen(color, 2))

        self.dibujar_flecha(
            painter,
            cx,
            cy,
            cx + dx,
            cy + dy
        )

    def dibujar_punta_flecha(self, painter, x1, y1, x2, y2):

        angulo = math.atan2(y2 - y1, x2 - x1)

        tamano = max(2, min(6, self.escala // 3))

        #La punta queda un poco antes del nodo destino
        distancia_destino = max(2, self.escala // 4)

        punta_x = x2 - math.cos(angulo) * distancia_destino
        punta_y = y2 - math.sin(angulo) * distancia_destino

        angulo1 = angulo + math.radians(150)
        angulo2 = angulo - math.radians(150)

        x3 = punta_x + math.cos(angulo1) * tamano
        y3 = punta_y + math.sin(angulo1) * tamano

        x4 = punta_x + math.cos(angulo2) * tamano
        y4 = punta_y + math.sin(angulo2) * tamano

        painter.drawLine(
            int(punta_x),
            int(punta_y),
            int(x3),
            int(y3)
        )

        painter.drawLine(
            int(punta_x),
            int(punta_y),
            int(x4),
            int(y4)
        )

    def play(self):
        if not self.finalizando and not self.simulation.finished:
            self.timer.start()
        elif self.simulation.finished:
            self.mostrar_resumen()

    def pause(self):
        self.timer.stop()

    def paso(self):
        if self.finalizando:
            return
        self.timer.stop()
        if self.simulation.finished:
            self.mostrar_resumen()
            return
        self.avanzar_simulacion()

    def guardar_simulacion(self):
        """Guarda warehouse y simulation del tick actual en un archivo pickle.

        Se usa un archivo temporal para no destruir un guardado previo
        si la serialización falla.
        """
        if self.finalizando:
            QMessageBox.information(self, "Finalizando", "Esperá a que termine el cálculo para guardar.")
            return

        estaba_corriendo = self.timer.isActive()
        self.timer.stop()
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar simulación", "simulacion.pkl", "Simulaciones (*.pkl)"
        )
        if not ruta:
            if estaba_corriendo and not self.simulation.finished:
                self.timer.start()
            return
        if not ruta.lower().endswith(".pkl"):
            ruta += ".pkl"

        temporal = None
        try:
            # Ambos mantienen el mismo estado y referencias al recuperarse.
            datos = {"warehouse": self.warehouse, "simulation": self.simulation}
            carpeta = os.path.dirname(os.path.abspath(ruta))
            with tempfile.NamedTemporaryFile(mode="wb", dir=carpeta, suffix=".tmp", delete=False) as archivo:
                temporal = archivo.name
                pickle.dump(datos, archivo, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(temporal, ruta)
            temporal = None
            QMessageBox.information(
                self, "Simulación guardada",
                f"Simulación guardada en el tick {self.simulation.tick}:\n{ruta}"
            )
        except Exception as error:
            QMessageBox.critical(
                self, "Error al guardar",
                f"No se pudo guardar la simulación:\n{type(error).__name__}: {error}"
            )
        finally:
            if temporal is not None and os.path.exists(temporal):
                os.remove(temporal)
            if estaba_corriendo and not self.simulation.finished:
                self.timer.start()

    def finalizar_simulacion(self):
        """Calcula hasta el final por lotes, sin mostrar ticks intermedios."""
        if self.finalizando:
            return
        self.timer.stop()
        if self.simulation.finished:
            self.mostrar_resumen()
            return
        self.finalizando = True
        self.boton_play.setEnabled(False)
        self.boton_pause.setEnabled(False)
        self.boton_paso.setEnabled(False)
        self.boton_guardar.setEnabled(False)
        self.boton_finalizar.setEnabled(False)
        # Evita redibujar los pickers y el depósito mientras se calculan los pasos.
        self.setUpdatesEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QTimer.singleShot(0, self._calcular_hasta_final)

    def _calcular_hasta_final(self):
        """Lotes para que Qt siga procesando eventos en simulaciones grandes."""
        error_ocurrido = False
        try:
            for _ in range(500):
                if self.simulation.finished:
                    break
                self.simulation.step()
            if not self.simulation.finished:
                QTimer.singleShot(0, self._calcular_hasta_final)
                return
        except Exception as error:
            error_ocurrido = True
            QMessageBox.critical(
                self, "Error al finalizar",
                f"La simulación se detuvo en el tick {self.simulation.tick}:\n"
                f"{type(error).__name__}: {error}"
            )
        finally:
            # Mantener la interfaz sin actualizaciones hasta completar todos los lotes.
            if self.simulation.finished or error_ocurrido:
                self._terminar_calculo_final()

    def _terminar_calculo_final(self):
        self.finalizando = False
        QApplication.restoreOverrideCursor()
        self.setUpdatesEnabled(True)
        self.label_tick.setText(f"Tick: {self.simulation.tick}")
        self.actualizar_estado_pickers([])
        if self.simulation.finished:
            for picker_id in self.estado_pickers:
                self.estado_pickers[picker_id] = "Terminado"
        self.boton_guardar.setEnabled(True)
        if self.simulation.finished:
            self.mostrar_resumen()
        else:
            self.boton_play.setEnabled(True)
            self.boton_pause.setEnabled(True)
            self.boton_paso.setEnabled(True)
            self.boton_finalizar.setEnabled(True)
        self.update()

    def mostrar_resumen(self):
        if self.resumen_mostrado:
            return
        self.resumen_mostrado = True
        self.timer.stop()
        resumen = self.simulation.summary()
        etiquetas = {
            "ticks": "Ticks",
            "planned_distance": "Distancia planeada",
            "steps": "Pasos realizados",
            "waits": "Esperas",
            "reroutes": "Reenrutamientos",
        }
        lineas = ["=== SIMULACIÓN TERMINADA ==="]
        lineas += [f"{nombre}: {resumen.get(clave, 'N/D')}" for clave, nombre in etiquetas.items()]
        self.panel_eventos.append("\n" + "\n".join(lineas))
        self.boton_play.setEnabled(False)
        self.boton_paso.setEnabled(False)
        self.boton_finalizar.setEnabled(False)
        QMessageBox.information(self, "Resultado de la simulación", "\n".join(lineas))

    def calcular_escala(self):

        #Al ancho de la ventana le resto el espacio
        #que necesita el panel de eventos
        ancho_disponible = (
            self.width()
            - self.margen
            - self.ancho_panel
            - self.separacion_panel
            - self.margen_derecho
        )

        alto_disponible = self.height() - 2 * self.margen

        escala_x = ancho_disponible // self.warehouse.width
        escala_y = alto_disponible // self.warehouse.height

        return max(1, min(escala_x, escala_y))

    def resizeEvent(self, event):

        #Coloco el panel siempre contra el lado derecho
        x_panel = (
            self.width()
            - self.ancho_panel
            - self.margen_derecho
        )

        self.panel_eventos.setGeometry(
            x_panel,
            60,
            self.ancho_panel,
            self.height() - 100
        )

        super().resizeEvent(event)


    def coordenada_a_pixel(self, x, y):

        #La coordenada x crece hacia la derecha
        xp = self.margen + x * self.escala

        #Invierto y porque PyQt comienza arriba a la izquierda
        yp = self.margen + (self.warehouse.height - 1 - y) * self.escala

        return xp, yp

    def actualizar_estado_pickers(self, eventos):

        #Primero establezco un estado base para todos los pickers
        actual_picker = self.warehouse.pickers.head

        while actual_picker is not None:

            picker = actual_picker.value

            if picker is not None:

                #Si no tiene assignment actualmente esta libre
                if picker.assignment is None:
                    self.estado_pickers[picker.id] = "Libre"

                else:
                    self.estado_pickers[picker.id] = "En proceso"

            actual_picker = actual_picker.nextNode


        #Despues uso los eventos del tick para poner un estado mas preciso
        for evento in eventos:

            if evento.kind == "start":
                self.estado_pickers[evento.picker] = "Iniciando"

            elif evento.kind == "move":
                self.estado_pickers[evento.picker] = "Moviendose"

            elif evento.kind == "wait":
                self.estado_pickers[evento.picker] = "Esperando"

            elif evento.kind == "pick":
                self.estado_pickers[evento.picker] = "Recogiendo"

            elif evento.kind == "drop":
                self.estado_pickers[evento.picker] = "Descargando"

            elif evento.kind == "reroute":
                self.estado_pickers[evento.picker] = "Recalculando ruta"

            elif evento.kind == "side_step":
                self.estado_pickers[evento.picker] = "Cediendo paso"

            elif evento.kind == "finish":
                self.estado_pickers[evento.picker] = "Terminado"



    def avanzar_simulacion(self):
        if self.simulation.finished:
            self.mostrar_resumen()
            return

        eventos = self.simulation.step()
        self.actualizar_estado_pickers(eventos)
        self.label_tick.setText(f"Tick: {self.simulation.tick}")

        for evento in eventos:
            if evento.kind != "move":
                texto_evento = self.formatear_evento(evento)
                print(texto_evento)
                self.panel_eventos.append(texto_evento)

        scrollbar = self.panel_eventos.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.update()
        if self.simulation.finished:
            self.mostrar_resumen()

    def dibujar_leyenda_sentidos(self, painter):

        x = 420
        y = 30

        sentidos = [
            ("Norte", QColor("blue")),
            ("Sur", QColor("red")),
            ("Este", QColor("green")),
            ("Oeste", QColor("orange")),
            ("Ambos", QColor("black"))
        ]

        for nombre, color in sentidos:

            #Linea de ejemplo
            painter.setPen(QPen(color, 3))
            painter.drawLine(x, y, x + 20, y)

            #Texto
            painter.setPen(QPen(QColor("black"), 1))
            painter.drawText(
                x + 25,
                y + 5,
                nombre
            )

            #Muevo la siguiente referencia hacia la derecha
            x += 90

    def paintEvent(self, event):

        painter = QPainter(self)
        
        #Dibujo la leyenda de sentidos
        self.dibujar_leyenda_sentidos(painter)

        #Calculo nuevamente la escala cada vez que se dibuja la ventana
        self.escala = self.calcular_escala()


        # ==================================================
        # WAREHOUSE
        # ==================================================

        #Dibujo el borde del warehouse
        painter.setPen(QPen(QColor("black"), 2))
        painter.setBrush(QBrush())

        painter.drawRect(self.margen, self.margen, self.warehouse.width * self.escala, self.warehouse.height * self.escala)


        # ==================================================
        # CELDAS DEL FLOOR
        # ==================================================

        #Recorro toda la cuadricula del warehouse
        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                #Obtengo la celda que esta en (x,y)
                cell = self.warehouse.floor.cell_at(x, y)

                if cell is None:
                    continue

                #Paso las coordenadas del warehouse a coordenadas de pantalla
                xp, yp = self.coordenada_a_pixel(x, y)


                #Si es una celda de rack
                if cell.kind == RACK:

                    painter.setBrush(QBrush(QColor("gray")))

                    painter.drawRect(xp + 3, yp + 3, self.escala - 6, self.escala - 6)

                    #Muestro el nombre del rack solo una vez
                    rack = cell.owner

                    if x == rack.rect.x and y == rack.rect.y:
                        painter.drawText(xp + 5, yp + 20, str(rack.id))


                #Si es una zona de despacho
                elif cell.kind == ZONE:

                    painter.setBrush(QBrush(QColor("lightgreen")))

                    painter.drawRect(xp + 3, yp + 3, self.escala - 6, self.escala - 6)


                #Si es una puerta
                elif cell.kind == DOOR:

                    painter.setBrush(QBrush(QColor("red")))

                    painter.drawRect(xp + 3, yp + 3, self.escala - 6, self.escala - 6)


        # ==================================================
        # ARISTAS DEL GRAFO
        # ==================================================

        actual = self.warehouse.graph.e.head

        while actual is not None:

            origen_id, destino_id, peso = actual.value

            origen_x, origen_y = self.warehouse.node_xy(origen_id)
            destino_x, destino_y = self.warehouse.node_xy(destino_id)

            x1, y1 = self.coordenada_a_pixel(origen_x, origen_y)
            x2, y2 = self.coordenada_a_pixel(destino_x, destino_y)

            #Centro de ambas celdas
            x1 += self.escala // 2
            y1 += self.escala // 2

            x2 += self.escala // 2
            y2 += self.escala // 2


            #Obtengo la celda desde donde sale la arista
            cell_origen = self.warehouse.floor.cell_at(origen_x, origen_y)

            sentido = cell_origen.sentido


            #El color representa el sentido declarado del pasillo
            if sentido == N:
                color_arista = QColor("blue")

            elif sentido == S:
                color_arista = QColor("red")

            elif sentido == E:
                color_arista = QColor("green")

            elif sentido == O:
                color_arista = QColor("orange")

            else:
                #AMBOS o pasillo no declarado
                if self.escala < 15:
                    color_arista = QColor(180, 180, 180)
                else:
                    color_arista = QColor("black")


            if self.escala < 15:
                grosor_arista = 1
            else:
                grosor_arista = 2

            painter.setPen(QPen(color_arista, grosor_arista))


            #Dibujo siempre la arista
            painter.drawLine(x1, y1, x2, y2)


            #Dibujo flecha solamente si esta arista coincide
            #con el sentido declarado del pasillo
            dibujar_flecha = False

            if sentido == N and destino_y > origen_y:
                dibujar_flecha = True

            elif sentido == S and destino_y < origen_y:
                dibujar_flecha = True

            elif sentido == E and destino_x > origen_x:
                dibujar_flecha = True

            elif sentido == O and destino_x < origen_x:
                dibujar_flecha = True


            if dibujar_flecha:
                self.dibujar_punta_flecha(
                    painter,
                    x1,
                    y1,
                    x2,
                    y2
                )


            actual = actual.nextNode


        # ==================================================
        # CELDAS DE PASILLO
        # ==================================================
        
        #Adapto el tamaño de los nodos a la escala
        if self.escala < 15:

            painter.setBrush(QBrush(QColor(150, 150, 150)))
            radio_nodo = 1

        else:

            painter.setBrush(QBrush(QColor("black")))
            radio_nodo = 3

        #Recorro nuevamente toda la cuadricula
        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                cell = self.warehouse.floor.cell_at(x, y)

                #Solo dibujo los nodos que sean pasillos
                if cell is not None and cell.kind == HALL:

                    xp, yp = self.coordenada_a_pixel(x, y)

                    #Busco el centro de la celda
                    xp += self.escala // 2
                    yp += self.escala // 2

                    #Dibujo el nodo del pasillo
                    painter.drawEllipse(xp - radio_nodo, yp - radio_nodo, radio_nodo*2, radio_nodo*2)


        # ==================================================
        # PRODUCTOS
        # ==================================================

        #painter.setBrush(QBrush(QColor("orange")))

        #Recorro el diccionario de productos
        for bucket in self.warehouse.products.dictionary:

            actual_producto = bucket.head

            while actual_producto is not None:

                if actual_producto.value is not None and isinstance(actual_producto.value, tuple):

                    #El producto esta guardado en la segunda posicion de la tupla
                    producto = actual_producto.value[1]
                    
                    #Solo dibujo el producto si todavia tiene stock
                    if producto.stock is None or producto.stock > 0:

                        xp, yp = self.coordenada_a_pixel(producto.x, producto.y)
                        
                        #Tamaño de la caja
                        tamano_producto = min(self.escala // 2, 18)

                        #Dibujo la imagen del producto centrada en la celda
                        painter.drawPixmap(
                            xp + (self.escala - tamano_producto) // 2,
                            yp + (self.escala - tamano_producto) // 2,
                            tamano_producto,
                            tamano_producto,
                            self.imagen_producto
                        )

                actual_producto = actual_producto.nextNode


        # ==================================================
        # PICKERS
        # ==================================================

        #Empiezo desde el primer picker
        actual_picker = self.warehouse.pickers.head

        while actual_picker is not None:

            picker = actual_picker.value

            if picker is not None:

                #picker.node guarda el id del nodo donde esta parado
                #node_xy convierte ese id nuevamente a coordenadas x,y
                x, y = self.warehouse.node_xy(picker.node)

                #Paso esas coordenadas a la pantalla
                xp, yp = self.coordenada_a_pixel(x, y)

                #Busco el centro de la celda
                xp += self.escala // 2
                yp += self.escala // 2

                #Tamaño de la imagen del picker
                tamano_picker = min(self.escala, 30)

                #Dibujo la imagen centrada en la celda
                painter.drawPixmap(
                    xp - tamano_picker // 2,
                    yp - tamano_picker // 2,
                    tamano_picker,
                    tamano_picker,
                    self.imagen_picker
                )
                
                #Dibujo de color negro el id del picker
                painter.setPen(QPen(QColor("black"), 1))

                #Muestro su id
                painter.drawText(
                    xp - 20,
                    yp - tamano_picker // 2 - 5,
                    str(picker.id)
                )
                
                #Obtengo el estado actual del picker
                estado = self.estado_pickers.get(picker.id, "Libre")

                #Muestro el estado debajo del picker
                painter.setPen(QPen(QColor("black"), 2))

                painter.drawText(
                    xp - 30,
                    yp + tamano_picker // 2 + 12,
                    estado
                )
                
                """#Estado actual
                estado = self.estado_pickers.get(picker.id, "Libre")

                #Posicion del texto
                texto_x = xp - 35
                texto_y = yp + tamano_picker // 2 + 14

                #Fondo blanco para que las aristas no molesten
                painter.setPen(QPen(QColor("black"), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))

                painter.drawRect(
                    texto_x - 2,
                    texto_y - 12,
                    75,
                    16
                )

                #Texto del estado
                painter.setPen(QPen(QColor("black"), 1))

                painter.drawText(
                    texto_x,
                    texto_y,
                    estado
                )"""

            actual_picker = actual_picker.nextNode



class DialogoInicio(QDialog):
    """Permite elegir un escenario JSON o recuperar una simulación guardada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar simulación del depósito")
        self.setMinimumWidth(510)
        self.warehouse = None
        self.simulation = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Seleccioná cómo querés iniciar:"))

        self.opcion_nueva = QRadioButton("Crear simulación desde un escenario JSON")
        self.opcion_cargar = QRadioButton("Continuar simulación guardada (.pkl)")
        self.opcion_nueva.setChecked(True)
        layout.addWidget(self.opcion_nueva)
        layout.addWidget(self.opcion_cargar)

        fila_archivo = QHBoxLayout()
        self.ruta_archivo = QLineEdit()
        self.ruta_archivo.setPlaceholderText("Seleccioná un archivo...")
        self.boton_buscar = QPushButton("Examinar...")
        self.boton_buscar.clicked.connect(self.seleccionar_archivo)
        fila_archivo.addWidget(self.ruta_archivo)
        fila_archivo.addWidget(self.boton_buscar)
        layout.addLayout(fila_archivo)

        self.opcion_nueva.toggled.connect(self.cambiar_tipo)
        self.opcion_cargar.toggled.connect(self.cambiar_tipo)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Iniciar")
        botones.accepted.connect(self.preparar_simulacion)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def cambiar_tipo(self):
        self.ruta_archivo.clear()

    def seleccionar_archivo(self):
        base = os.path.dirname(os.path.abspath(__file__))
        if self.opcion_nueva.isChecked():
            directorio = os.path.normpath(os.path.join(base, "..", "data"))
            filtro = "Escenarios JSON (*.json)"
        else:
            directorio = base
            filtro = "Simulaciones guardadas (*.pkl *.pickle)"

        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", directorio, filtro)
        if ruta:
            self.ruta_archivo.setText(ruta)

    def preparar_simulacion(self):
        ruta = self.ruta_archivo.text().strip()
        if not ruta:
            QMessageBox.warning(self, "Falta un archivo", "Seleccioná un archivo para continuar.")
            return
        if not os.path.isfile(ruta):
            QMessageBox.warning(self, "Archivo inexistente", f"No existe el archivo:\n{ruta}")
            return

        try:
            if self.opcion_nueva.isChecked():
                if not ruta.lower().endswith(".json"):
                    raise ValueError("Para crear una simulación seleccioná un archivo .json")

                config = load_config(ruta)
                warehouse, no_valido = build_warehouse(config)
                if warehouse is None:
                    raise ValueError(f"No se pudo crear el warehouse. Detalle: {no_valido}")

                # Conservo el mismo algoritmo de generación de Waves del archivo original.
                waves = generacionWaves(
                    warehouse.orders, warehouse.pickers, warehouse.wave_config
                )
                waves_warehouse = LinkedList()
                for grupo in waves:
                    for wave in grupo:
                        add(waves_warehouse, wave)
                warehouse.waves = waves_warehouse

                simulation = Simulation(
                    warehouse, algorithm="astar", auto_assign=True
                )
            else:
                if not ruta.lower().endswith((".pkl", ".pickle")):
                    raise ValueError("Para continuar seleccioná un archivo .pkl o .pickle")
                # IMPORTANTE: pickle solo se debe abrir si el archivo es confiable.
                with open(ruta, "rb") as archivo:
                    datos = pickle.load(archivo)

                # Soporta guardar directamente Simulation o un dict con ambos objetos.
                if isinstance(datos, Simulation):
                    simulation = datos
                    warehouse = simulation.warehouse
                elif isinstance(datos, dict) and {"warehouse", "simulation"} <= datos.keys():
                    warehouse = datos["warehouse"]
                    simulation = datos["simulation"]
                else:
                    raise ValueError(
                        "El archivo debe contener una Simulation o un diccionario "
                        "con 'warehouse' y 'simulation'."
                    )
                if not isinstance(simulation, Simulation) or warehouse is None:
                    raise ValueError("La simulación guardada no tiene datos válidos.")

            self.warehouse = warehouse
            self.simulation = simulation
            self.accept()
        except Exception as error:
            QMessageBox.critical(
                self, "No se pudo iniciar",
                f"Revisá el archivo elegido o sus datos:\n\n{type(error).__name__}: {error}"
            )


def main():
    app = QApplication(sys.argv)
    dialogo = DialogoInicio()
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return 0

    ventana = Ventana(dialogo.warehouse, dialogo.simulation)
    ventana.label_tick.setText(f"Tick: {dialogo.simulation.tick}")
    ventana.showMaximized()
    resultado = app.exec()
    print(dialogo.simulation.summary())
    return resultado


if __name__ == "__main__":
    sys.exit(main())
