import sys
import math
import os
import inspect
import time
from html import escape
from collections import Counter
import clustering.spectral as cs

from warehouse.algorithms.wave_generation.spectral_waves import SpectralWaveSelector
#from warehouse.algorithms.wave_generation.order_centroids.product_centroids import ProductCentroidSelector
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QTextEdit, QDialog,
    QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDialogButtonBox,
    QFileDialog, QLineEdit, QMessageBox, QScrollArea, QTextBrowser
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt

from warehouse.services.wave_builder import WaveBuilder
from warehouse.simulation.simulation import Simulation
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.persistence.save_load import (
    load_warehouse, load_simulation, save_simulation
)
from warehouse.domain.direction import N, S, E, O, AMBOS


#Tipos de celdas que puede tener el warehouse
from warehouse.domain.cell import HALL, RACK, DOOR, ZONE


#estrategia del centroide
from warehouse.algorithms.generacioWave import generacionWaves

# ==================================================
# MENU OPCIONES DE ESTRATEGIA
# ==================================================

class DialogoEstrategia(QDialog):
    """Pantalla inicial: elegir fuente y estrategia (si no se reanuda)."""

    def __init__(self, max_zonas=1000):
        super().__init__()
        self.setWindowTitle("Inicio de la simulacion")
        self.setMinimumWidth(540)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("¿Como queres iniciar?"))
        self.combo_origen = QComboBox()
        self.combo_origen.addItem("Crear warehouse nuevo desde un JSON", "nuevo")
        self.combo_origen.addItem("Reanudar una simulacion guardada (.pkl)", "simulacion")
        layout.addWidget(self.combo_origen)

        layout.addWidget(QLabel("Archivo de origen:"))
        fila_archivo = QHBoxLayout()
        self.ruta_archivo = QLineEdit()
        self.ruta_archivo.setPlaceholderText("Selecciona el archivo JSON o PKL")
        fila_archivo.addWidget(self.ruta_archivo)
        self.boton_examinar = QPushButton("Examinar...")
        self.boton_examinar.clicked.connect(self.elegir_archivo)
        fila_archivo.addWidget(self.boton_examinar)
        layout.addLayout(fila_archivo)

        layout.addWidget(QLabel("Estrategia de generacion de Waves:"))
        self.combo_estrategia = QComboBox()
        self.combo_estrategia.addItem("Centroide", "centroide")
        self.combo_estrategia.addItem("Clustering espectral", "clustering")
        layout.addWidget(self.combo_estrategia)

        layout.addWidget(QLabel("Cantidad de zonas (K):"))
        self.spin_k = QSpinBox()
        self.spin_k.setRange(1, max(1, max_zonas))
        self.spin_k.setValue(min(4, max(1, max_zonas)))
        layout.addWidget(self.spin_k)

        layout.addWidget(QLabel("Metrica del clustering:"))
        self.combo_metrica = QComboBox()
        self.combo_metrica.addItem("Topologica", "t")
        self.combo_metrica.addItem("Euclidiana", "e")
        layout.addWidget(self.combo_metrica)

        self.label_ayuda = QLabel("")
        self.label_ayuda.setWordWrap(True)
        layout.addWidget(self.label_ayuda)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

        # Accion independiente: comparar ambos metodos sin abrir la animacion.
        self.boton_resultados = self.botones.addButton(
            "Resultado", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.boton_resultados.clicked.connect(self.abrir_resultados)
        layout.addWidget(self.botones)

        self.combo_origen.currentIndexChanged.connect(self.actualizar_origen)
        self.combo_estrategia.currentIndexChanged.connect(self.actualizar_opciones)
        self.actualizar_origen()

    def actualizar_origen(self):
        origen = self.origen()
        self.ruta_archivo.setText({
            "nuevo": "src/data/escenario_grande.json",
            "warehouse": "warehouse.pkl",
            "simulacion": "simulation.pkl",
        }[origen])
        self.label_ayuda.setText({
            "nuevo": "Se crea el warehouse desde el escenario y se generan las waves.",
            "warehouse": "Se recupera el warehouse. Si ya tiene waves, se conservan.",
            "simulacion": "Se recuperan el tick, los pickers y las waves sin reiniciar la simulacion.",
        }[origen])
        self.actualizar_opciones()

    def actualizar_opciones(self):
        # Reanudar una simulacion no debe volver a generar las waves.
        permite_elegir = self.origen() != "simulacion"
        self.combo_estrategia.setEnabled(permite_elegir)
        usa_clustering = permite_elegir and self.estrategia() == "clustering"
        self.spin_k.setEnabled(usa_clustering)
        self.combo_metrica.setEnabled(usa_clustering)

    def elegir_archivo(self):
        origen = self.origen()
        filtro = ("Archivos JSON (*.json)" if origen == "nuevo"
                  else "Archivos guardados (*.pkl)")
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", self.ruta_archivo.text() or os.getcwd(), filtro
        )
        if archivo:
            self.ruta_archivo.setText(archivo)

    def abrir_resultados(self):
        """Usa el mismo JSON seleccionado cuando la fuente es 'nuevo'."""
        ruta = self.archivo()
        if self.origen() != "nuevo" or not ruta.lower().endswith(".json"):
            ruta = os.path.abspath("src/data/escenario_grande.json")
        dialogo = DialogoResultados(ruta, self.k_zonas(), self.metrica(), self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.opciones_resultados = dialogo.opciones()
            # Codigo 2: salir del dialogo inicial en modo comparacion.
            self.done(2)

    def accept(self):
        ruta = self.archivo()
        if not ruta or not os.path.isfile(ruta):
            QMessageBox.warning(
                self, "Archivo no encontrado",
                "Selecciona un archivo existente para iniciar la simulacion."
            )
            return
        super().accept()

    def archivo(self):
        return os.path.abspath(os.path.expanduser(self.ruta_archivo.text().strip())) if self.ruta_archivo.text().strip() else ""

    def origen(self):
        return self.combo_origen.currentData()

    def estrategia(self):
        return self.combo_estrategia.currentData()

    def k_zonas(self):
        return self.spin_k.value()

    def metrica(self):
        return self.combo_metrica.currentData()


# ==================================================
# PARAMETROS PARA COMPARAR LOS DOS METODOS
# ==================================================

class DialogoResultados(QDialog):
    """Pide el mismo JSON, el numero K y la metrica para la comparacion."""

    def __init__(self, ruta_json, k=4, metrica="t", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comparar resultados: centroide vs espectral")
        self.setMinimumWidth(570)
        layout = QVBoxLayout(self)
        descripcion = QLabel(
            "Se construira el warehouse dos veces desde este JSON, "
            "una por estrategia. Ambas simulaciones se ejecutaran sin mostrar la cuadricula."
        )
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        layout.addWidget(QLabel("Escenario JSON (el mismo para ambos algoritmos):"))
        fila = QHBoxLayout()
        self.ruta_archivo = QLineEdit(ruta_json)
        fila.addWidget(self.ruta_archivo)
        boton = QPushButton("Examinar...")
        boton.clicked.connect(self.elegir_archivo)
        fila.addWidget(boton)
        layout.addLayout(fila)

        layout.addWidget(QLabel("Cantidad de zonas K del clustering espectral:"))
        self.spin_k = QSpinBox()
        self.spin_k.setRange(1, 1000)
        self.spin_k.setValue(max(1, int(k)))
        layout.addWidget(self.spin_k)

        layout.addWidget(QLabel("Metrica de distancias para clustering:"))
        self.combo_metrica = QComboBox()
        self.combo_metrica.addItem("Topologica", "t")
        self.combo_metrica.addItem("Euclidiana", "e")
        self.combo_metrica.setCurrentIndex(1 if metrica == "e" else 0)
        layout.addWidget(self.combo_metrica)

        nota = QLabel(
            "K solo se aplica al clustering espectral. Si hay menos productos "
            "pendientes que K, se usara la cantidad de productos disponibles."
        )
        nota.setWordWrap(True)
        layout.addWidget(nota)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Comparar")
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

    def elegir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar escenario JSON",
            self.ruta_archivo.text() or os.getcwd(),
            "Archivos JSON (*.json)"
        )
        if ruta:
            self.ruta_archivo.setText(ruta)

    def accept(self):
        ruta = self.ruta_archivo.text().strip()
        if not ruta or not os.path.isfile(os.path.expanduser(ruta)) or not ruta.lower().endswith(".json"):
            QMessageBox.warning(
                self, "Escenario invalido", "Selecciona un archivo JSON existente."
            )
            return
        super().accept()

    def opciones(self):
        return {
            "json": os.path.abspath(os.path.expanduser(self.ruta_archivo.text().strip())),
            "k": self.spin_k.value(),
            "metrica": self.combo_metrica.currentData(),
        }


# ==================================================
# VENTANA INTERFAZ GRAFICA
# ==================================================


class Ventana(QWidget):

    def __init__(self, warehouse, simulation, zonas_espectrales=None, estrategia="centroide",
                 k_zonas=None, metrica=None, zona_producto_guardada=None,
                 cantidad_zonas_guardadas=None, reanudada=False):
        super().__init__()

        #Guardo el warehouse que recibo
        self.warehouse = warehouse
        
        #Guardo la simulacion
        self.simulation = simulation
        
        #Guardo las zonas generadas por clustering
        self.zonas_espectrales = zonas_espectrales
        
        #Guardo la estrategia utilizada
        self.estrategia = estrategia
        self.k_zonas = k_zonas
        self.metrica = metrica

        #Diccionario para saber rapidamente
        #a que zona pertenece cada producto
        self.zona_producto = dict(zona_producto_guardada or {})
        self.cantidad_zonas = cantidad_zonas_guardadas or 0

        if self.zonas_espectrales is not None:
            self.cantidad_zonas = len(self.zonas_espectrales)

            numero_zona = 1

            for zona in self.zonas_espectrales:

                for producto in zona:

                    self.zona_producto[producto.id] = numero_zona

                numero_zona += 1

        #Espacio que dejo alrededor del warehouse
        self.margen = 60

        #Valor inicial, despues se calcula dependiendo del tamaño de la ventana
        self.escala = 1
        
        #Imagenes de la interfaz
        assets_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets"
        )

        self.imagen_picker = QPixmap(
            os.path.join(assets_dir, "construction-worker.png")
        )

        self.imagen_producto = QPixmap(
            os.path.join(assets_dir, "box.png")
        )
        
        
        #Timer que va avanzando la simulacion
        self.timer = QTimer(self)

        #Cada vez que el timer se activa ejecuto un tick
        self.timer.timeout.connect(self.avanzar_simulacion)

        #Intervalo inicial entre ticks
        self.intervalo_actual = 300

        #Tiempo entre ticks
        self.timer.setInterval(
            self.intervalo_actual
        )
        
        
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
        
        #Guardar el estado completo de Simulation (y su warehouse)
        self.boton_guardar = QPushButton("Guardar", self)
        self.boton_guardar.setGeometry(300, 10, 100, 30)
        self.boton_guardar.clicked.connect(self.guardar_simulacion)

        #Boton para mostrar la velocidad actual
        self.label_velocidad = QLabel("Intervalo: 300 ms", self)

        #Boton para acelerar al doble
        self.boton_acelerar = QPushButton("x2", self)

        self.boton_acelerar.clicked.connect(self.acelerar_simulacion)

        #Boton para volver a la velocidad inicial
        self.boton_velocidad_normal = QPushButton("x1",self)

        self.boton_velocidad_normal.clicked.connect(self.restablecer_velocidad)
        
        # ==================================================
        # TICK ACTUAL
        # ==================================================

        self.label_tick = QLabel(f"Tick: {self.simulation.tick}", self)
        self.label_tick.setGeometry(410, 8, 120, 25)
        
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

        #Texto inicial
        self.panel_eventos.setPlainText("Eventos de la simulacion:\n")
        if reanudada:
            self.panel_eventos.append(
                f"=== SIMULACION REANUDADA EN TICK {self.simulation.tick} ==="
            )
            # Evitar bloquear la UI si se guardo una simulacion muy larga.
            eventos_recientes = [e for e in self.simulation.events if e.kind != "move"][-300:]
            for evento in eventos_recientes:
                self.panel_eventos.append(self.formatear_evento(evento))
        
        # ==================================================
        # INFORMACION DE ESTRATEGIA
        # ==================================================

        if self.estrategia == "centroide":

            texto_estrategia = "Estrategia: Centroide"

        elif self.estrategia == "clustering":

            nombre_metrica = (
                "Topologica"
                if self.metrica == "t"
                else "Euclidiana"
            )

            texto_estrategia = (
                f"Estrategia: Clustering espectral | "
                f"K={self.k_zonas} | {nombre_metrica}"
            )

        else:
            texto_estrategia = "Estrategia: no registrada en el archivo guardado"

        self.label_estrategia = QLabel(
            texto_estrategia,
            self
        )

        self.label_estrategia.setStyleSheet(
            "font-weight: bold;"
        )
        
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

        self.actualizar_estado_pickers([])

    def color_zona(self, zona):

        if zona is None:
            return QColor("black")

        cantidad_zonas = self.cantidad_zonas

        if cantidad_zonas == 0:
            return QColor("black")

        #Distribuyo los colores alrededor del circulo HSV
        tono = int(
            ((zona - 1) * 359)
            / cantidad_zonas
        )

        return QColor.fromHsv(
            tono,
            180,
            220
        )


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

    def guardar_simulacion(self):
        """Guardar el estado en un .pkl, sin serializar widgets de PyQt."""
        estaba_corriendo = self.timer.isActive()
        self.timer.stop()
        try:
            ruta, _ = QFileDialog.getSaveFileName(
                self, "Guardar simulacion", "simulation.pkl",
                "Simulaciones (*.pkl)"
            )
            if not ruta:
                return
            if not ruta.lower().endswith(".pkl"):
                ruta += ".pkl"

            metadatos = {
                "estrategia": self.estrategia,
                "k_zonas": self.k_zonas,
                "metrica": self.metrica,
                "zona_producto": dict(self.zona_producto),
                "cantidad_zonas": self.cantidad_zonas,
            }
            # save_load.py serializa Simulation, que ya contiene warehouse.
            save_simulation(self.simulation, ruta, metadata=metadatos)
            self.panel_eventos.append(
                f"Simulacion guardada en tick {self.simulation.tick}: {ruta}"
            )
            QMessageBox.information(
                self, "Guardado exitoso", f"Simulacion guardada en:\n{ruta}"
            )
        except Exception as error:
            QMessageBox.critical(
                self, "Error al guardar", f"No se pudo guardar la simulacion:\n{error}"
            )
        finally:
            if estaba_corriendo and not self.simulation.finished:
                self.timer.start()

    def play(self):

        #Si la simulacion no termino, comienzo el timer
        if not self.simulation.finished:
            self.timer.start()


    def pause(self):

        #Detengo el timer
        self.timer.stop()


    def paso(self):

        #Si termino no hago nada
        if self.simulation.finished:
            return

        #Avanzo solamente un tick
        self.avanzar_simulacion()

    def acelerar_simulacion(self):

        #Si ya estamos al maximo, no hago nada
        if self.intervalo_actual == 0:
            return

        #Reduzco el intervalo a la mitad
        self.intervalo_actual = (
            self.intervalo_actual // 2
        )

        #Aplico el nuevo intervalo al timer
        self.timer.setInterval(
            self.intervalo_actual
        )

        #Actualizo el texto mostrado
        self.label_velocidad.setText(
            f"Intervalo: {self.intervalo_actual} ms"
        )

        #Si llego a cero, deshabilito el boton
        self.boton_acelerar.setEnabled(
            self.intervalo_actual > 0
        )


    def restablecer_velocidad(self):

        #Vuelvo al intervalo original
        self.intervalo_actual = 300

        self.timer.setInterval(
            self.intervalo_actual
        )

        self.label_velocidad.setText(
            "Intervalo: 300 ms"
        )

        #Vuelvo a habilitar el boton x2
        self.boton_acelerar.setEnabled(True)

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

        #Calculo la posicion del panel derecho
        x_panel = (
            self.width()
            - self.ancho_panel
            - self.margen_derecho
        )

        # ==================================================
        # ESTRATEGIA
        # ==================================================

        self.label_estrategia.setGeometry(
            x_panel,
            8,
            self.ancho_panel,
            26
        )

        # ==================================================
        # VELOCIDAD
        # ==================================================

        self.label_velocidad.setGeometry(
            x_panel,
            40,
            160,
            28
        )

        self.boton_acelerar.setGeometry(
            x_panel + 170,
            40,
            75,
            28
        )

        self.boton_velocidad_normal.setGeometry(
            x_panel + 255,
            40,
            75,
            28
        )

        # ==================================================
        # PANEL DE EVENTOS
        # ==================================================

        self.panel_eventos.setGeometry(
            x_panel,
            80,
            self.ancho_panel,
            self.height() - 120
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

        #Si la simulacion ya termino detengo el timer
        if self.simulation.finished:

            self.timer.stop()

            self.panel_eventos.append("")
            self.panel_eventos.append("=== SIMULACION TERMINADA ===")

            resumen = self.simulation.summary()

            self.panel_eventos.append(
                "Ticks: " + str(resumen["ticks"])
            )

            self.panel_eventos.append(
                "Distancia planeada: " + str(resumen["planned_distance"])
            )

            self.panel_eventos.append(
                "Pasos realizados: " + str(resumen["steps"])
            )

            self.panel_eventos.append(
                "Esperas: " + str(resumen["waits"])
            )

            self.panel_eventos.append(
                "Reenrutamientos: " + str(resumen["reroutes"])
            )

            return


        #Ejecuto un solo tick
        eventos = self.simulation.step()
        
        self.actualizar_estado_pickers(eventos)
        
        #Actualizo el tick mostrado en pantalla
        self.label_tick.setText(
            "Tick: " + str(self.simulation.tick)
        )

        #Muestro por consola los eventos importantes
        for evento in eventos:

            if evento.kind != "move":

                texto_evento = self.formatear_evento(evento)
                print(texto_evento)
                self.panel_eventos.append(texto_evento)

        #Bajo automaticamente al ultimo evento
        scrollbar = self.panel_eventos.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        #Le digo a PyQt que vuelva a dibujar la ventana
        self.update()

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
        if self.escala < 20:
            radio_nodo = 1
        else:
            radio_nodo = 2

        #Evito que el contorno aumente el tamaño del nodo
        painter.setPen(Qt.PenStyle.NoPen)

        #Color de relleno del nodo
        painter.setBrush(QBrush(QColor(90, 90, 90)))

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

                        zona = self.zona_producto.get(
                            producto.id
                        )

                        if zona is not None:

                            color = self.color_zona(zona)

                            painter.setPen(
                                QPen(color, 3)
                            )

                            painter.setBrush(
                                QBrush()
                            )

                            painter.drawRect(
                                xp + 1,
                                yp + 1,
                                self.escala - 2,
                                self.escala - 2
                            )
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


def registrar_waves_generadas(warehouse, resultado):
    """Admite generacionWaves de 1 o 3 parametros y listas por picker."""
    if resultado is None:
        return

    def recorrer(valor):
        if valor is None:
            return
        if hasattr(valor, "orders") and hasattr(valor, "status"):
            yield valor
        elif hasattr(valor, "head"):
            actual = valor.head
            while actual is not None:
                yield from recorrer(actual.value)
                actual = actual.nextNode
        elif isinstance(valor, (list, tuple)):
            for item in valor:
                yield from recorrer(item)

    from warehouse.structures.linkedlist import add
    existentes = {id(w) for w in warehouse.waves if w is not None}
    for wave in recorrer(resultado):
        if id(wave) not in existentes:
            add(warehouse.waves, wave)
            existentes.add(id(wave))


def generar_waves_centroide(warehouse):
    """Compatible con ambas firmas presentes en distintas ramas del proyecto."""
    cantidad_parametros = len(inspect.signature(generacionWaves).parameters)
    if cantidad_parametros == 1:
        resultado = generacionWaves(warehouse)
    else:
        resultado = generacionWaves(
            warehouse.orders, warehouse.pickers, warehouse.wave_config
        )
    registrar_waves_generadas(warehouse, resultado)
    return resultado


# ==================================================
# RESULTADOS COMPARABLES SIN ANIMACION
# ==================================================

def medir_resultado_desde_json(ruta_json, metodo, k_zonas, metrica, progreso=None, interrumpido=None):
    """Construye un warehouse independiente, crea waves y ejecuta la simulacion.

    Devuelve exclusivamente valores simples para poder presentarlos desde la UI.
    Se reconstruye desde el JSON en cada llamada: no reutiliza pedidos, reservas
    ni pickers mutados por la estrategia anterior.
    """
    if metodo not in ("centroide", "clustering"):
        raise ValueError(f"Estrategia desconocida: {metodo}")
    if interrumpido and interrumpido():
        raise InterruptedError("Comparacion cancelada")

    t_total = time.perf_counter()
    t = time.perf_counter()
    config = load_config(ruta_json)
    warehouse = build_warehouse(config)
    tiempo_carga = time.perf_counter() - t

    pedidos = [o for o in warehouse.orders if o is not None]
    pickers = [p for p in warehouse.pickers if p is not None]
    unidades_pedidas = sum(o.total_units for o in pedidos)
    peso_pedido = sum(o.total_weight for o in pedidos)
    rechazos = [
        f"{getattr(r, 'order_id', '?')}: {getattr(r, 'reason', str(r))}"
        for r in getattr(warehouse, "rejected_orders", [])
    ]

    if interrumpido and interrumpido():
        raise InterruptedError("Comparacion cancelada")

    t = time.perf_counter()
    zonificacion = None
    k_efectivo = None
    zones_sizes = []
    por_picker = Counter()
    rechazos_waves = []

    if metodo == "centroide":
        if progreso:
            progreso("Generando waves por centroide...")
        waves_por_picker = generar_waves_centroide(warehouse)
        # En el metodo centroide la salida es una lista de waves por picker.
        # No confundir indice de picker con orden de las waves creadas.
        if isinstance(waves_por_picker, (list, tuple)):
            for i, grupo in enumerate(waves_por_picker):
                if i >= len(pickers):
                    break
                if hasattr(grupo, "total_units"):
                    cantidad = 1
                elif hasattr(grupo, "__iter__"):
                    cantidad = sum(1 for w in grupo if w is not None)
                else:
                    cantidad = 0
                por_picker[str(pickers[i].id)] += cantidad
    else:
        if progreso:
            progreso("Calculando el clustering espectral...")
        productos = cs.extract_pending_products(warehouse)
        if not productos:
            raise ValueError("No hay productos pendientes para clusterizar.")
        k_efectivo = min(k_zonas, len(productos))
        zonificacion = cs.main(
            warehouse=warehouse, k_zones=k_efectivo, metric=metrica
        )
        zones_sizes = [len(z) for z in zonificacion]
        selector = SpectralWaveSelector(
            warehouse=warehouse,
            spectral_zones=zonificacion,
            pickers=warehouse.pickers,
            verbose=False,
        )
        _, rejected = WaveBuilder(
            warehouse, selector=selector, pickers=warehouse.pickers
        ).build()
        rechazos_waves = [
            f"{r.order.id}: {r.reason}" for r in rejected if r is not None
        ]
        for wave in warehouse.waves:
            if wave is None:
                continue
            # Las waves del espectral guardan el picker en planned_shares.
            for picker, _shares in (wave.planned_shares or []):
                por_picker[str(picker.id)] += 1

    tiempo_waves = time.perf_counter() - t
    waves = [w for w in warehouse.waves if w is not None]
    unidades_waves = sum(w.total_units for w in waves)
    peso_waves = sum(w.total_weight for w in waves)
    detalles_waves = [
        (str(w.id), w.total_units, round(w.total_weight, 2), w.product_count)
        for w in waves
    ]

    # Simulacion completa SIN ventana ni Timer. Conserva las mismas reglas
    # de recorrido bfs y auto_asignacion usadas en el modo grafico.
    if progreso:
        progreso(f"Ejecutando {metodo} sin animacion (0 ticks)...")
    simulacion = Simulation(warehouse, algorithm="bfs", auto_assign=True)
    t = time.perf_counter()
    while not simulacion.finished:
        if interrumpido and interrumpido():
            raise InterruptedError("Comparacion cancelada")
        if simulacion.tick >= simulacion.max_ticks:
            raise RuntimeError(
                f"La simulacion de {metodo} no termino despues de "
                f"{simulacion.max_ticks} ticks."
            )
        simulacion.step()
        if progreso and simulacion.tick % 250 == 0:
            progreso(f"Ejecutando {metodo} sin animacion ({simulacion.tick} ticks)...")
    tiempo_sim = time.perf_counter() - t
    resumen = simulacion.summary()

    return {
        "metodo": metodo,
        "k_pedido": k_zonas if metodo == "clustering" else None,
        "k_efectivo": k_efectivo,
        "zonas": len(zonificacion) if zonificacion is not None else None,
        "zonas_productos": zones_sizes,
        "metrica": metrica if metodo == "clustering" else None,
        "pedidos": len(pedidos),
        "pickers": len(pickers),
        "rechazados": rechazos,
        "rechazos_waves": rechazos_waves,
        "waves": len(waves),
        "unidades_pedidas": unidades_pedidas,
        "peso_pedido": peso_pedido,
        "unidades_waves": unidades_waves,
        "peso_waves": peso_waves,
        "cobertura": (100.0 * unidades_waves / unidades_pedidas)
                     if unidades_pedidas else 100.0,
        "promedio_peso_wave": (peso_waves / len(waves)) if waves else 0.0,
        "por_picker": dict(por_picker),
        "detalles_waves": detalles_waves,
        "tiempo_carga": tiempo_carga,
        "tiempo_waves": tiempo_waves,
        "tiempo_sim": tiempo_sim,
        "tiempo_total": time.perf_counter() - t_total,
        "finalizo": simulacion.finished,
        "ticks": resumen["ticks"],
        "asignaciones": resumen["assignments"],
        "distancia": resumen["planned_distance"],
        "pasos": resumen["steps"],
        "esperas": resumen["waits"],
        "reenrutamientos": resumen["reroutes"],
        "pasos_laterales": resumen["side_steps"],
    }


class TrabajadorResultados(QThread):
    """Ejecuta el calculo en un hilo, sin bloquear el hilo principal de PyQt."""
    progreso = pyqtSignal(str)
    resultado = pyqtSignal(str, object)
    error = pyqtSignal(str, str)

    def __init__(self, opciones, parent=None):
        super().__init__(parent)
        self.opciones = dict(opciones)

    def run(self):
        for metodo in ("centroide", "clustering"):
            if self.isInterruptionRequested():
                break
            self.progreso.emit(f"Procesando {metodo}...")
            try:
                datos = medir_resultado_desde_json(
                    self.opciones["json"], metodo,
                    self.opciones["k"], self.opciones["metrica"],
                    progreso=self.progreso.emit,
                    interrumpido=self.isInterruptionRequested,
                )
                if self.isInterruptionRequested():
                    break
                self.resultado.emit(metodo, datos)
            except InterruptedError:
                break
            except Exception as error:
                self.error.emit(metodo, str(error))
        self.progreso.emit("Comparacion terminada.")


def _celda_html(valor):
    return escape(str(valor))


def _fila_html(nombre, valor):
    return (
        "<tr><td style='padding:5px 12px 5px 0'><b>" + _celda_html(nombre) +
        "</b></td><td style='padding:5px'>" + _celda_html(valor) + "</td></tr>"
    )


def html_detalle_resultados(datos):
    """Presenta metricas comunes y detalles por wave."""
    partes = ["<div style='font-size:13px'>", "<table cellspacing='0'>"]
    filas = [
        ("Pedidos validos", datos["pedidos"]),
        ("Pedidos rechazados al cargar", len(datos["rechazados"])),
        ("Pickers disponibles", datos["pickers"]),
        ("Waves generadas", datos["waves"]),
        ("Unidades demandadas / agrupadas", f'{datos["unidades_pedidas"]} / {datos["unidades_waves"]}'),
        ("Peso total de las waves", f'{datos["peso_waves"]:.2f} kg'),
        ("Cobertura de la demanda", f'{datos["cobertura"]:.1f}%'),
        ("Peso promedio por wave", f'{datos["promedio_peso_wave"]:.2f} kg'),
        ("Tiempo de generacion de waves", f'{datos["tiempo_waves"]:.3f} s'),
        ("Tiempo de ejecucion sin animacion", f'{datos["tiempo_sim"]:.3f} s'),
        ("Ticks hasta finalizar", datos["ticks"]),
        ("Asignaciones completadas", datos["asignaciones"]),
        ("Distancia planeada total", f'{datos["distancia"]:.1f} pasos'),
        ("Pasos efectivamente realizados", datos["pasos"]),
        ("Esperas", datos["esperas"]),
        ("Reenrutamientos", datos["reenrutamientos"]),
        ("Pasos laterales", datos["pasos_laterales"]),
    ]
    if datos["metodo"] == "clustering":
        filas.insert(0, (
            "Clustering configurado", f'K solicitado={datos["k_pedido"]}; '
            f'K efectivo={datos["k_efectivo"]}; '
            f'metrica={"Topologica" if datos["metrica"] == "t" else "Euclidiana"}'
        ))
        filas.insert(1, (
            "Productos por zona", ", ".join(str(x) for x in datos["zonas_productos"])
        ))
    partes += [_fila_html(nombre, valor) for nombre, valor in filas]
    partes.append("</table>")

    if datos["por_picker"]:
        partes.append("<h3>Waves por picker</h3><ul>")
        for picker_id, cantidad in sorted(datos["por_picker"].items()):
            partes.append(f"<li>Picker {_celda_html(picker_id)}: {_celda_html(cantidad)} waves</li>")
        partes.append("</ul>")

    if datos["rechazados"] or datos["rechazos_waves"]:
        partes.append("<h3>Pedidos rechazados / waves no asignadas</h3><ul>")
        for rechazo in datos["rechazados"] + datos["rechazos_waves"]:
            partes.append(f"<li>{_celda_html(rechazo)}</li>")
        partes.append("</ul>")

    partes.append("<h3>Detalle de waves (primeras 50)</h3>")
    partes.append(
        "<table cellspacing='0' cellpadding='5' border='1' "
        "style='border-collapse:collapse'><tr><th>Wave</th><th>Unidades</th>"
        "<th>Peso (kg)</th><th>Productos distintos</th></tr>"
    )
    for identificador, unidades, peso, productos in datos["detalles_waves"][:50]:
        partes.append(
            "<tr><td>" + _celda_html(identificador) + "</td><td>" +
            _celda_html(unidades) + "</td><td>" + _celda_html(peso) +
            "</td><td>" + _celda_html(productos) + "</td></tr>"
        )
    partes.append("</table>")
    if datos["waves"] > 50:
        partes.append(f"<p>Mostrando 50 de {datos['waves']} waves.</p>")
    partes.append("</div>")
    return "".join(partes)


def html_tabla_comparativa(centroide, clustering):
    """Contrasta solo metricas calculadas del mismo modo en ambas estrategias."""
    formato = [
        ("Waves", "waves", "{}"),
        ("Unidades agrupadas", "unidades_waves", "{}"),
        ("Cobertura (%)", "cobertura", "{:.1f}"),
        ("Peso total (kg)", "peso_waves", "{:.1f}"),
        ("Tiempo generacion (s)", "tiempo_waves", "{:.3f}"),
        ("Tiempo simulacion (s)", "tiempo_sim", "{:.3f}"),
        ("Ticks", "ticks", "{}"),
        ("Asignaciones", "asignaciones", "{}"),
        ("Distancia planeada", "distancia", "{:.1f}"),
        ("Pasos realizados", "pasos", "{}"),
        ("Esperas", "esperas", "{}"),
        ("Reenrutamientos", "reenrutamientos", "{}"),
        ("Pasos laterales", "pasos_laterales", "{}"),
    ]
    partes = [
        "<h2>Comparacion final</h2>",
        "<table cellspacing='0' cellpadding='8' border='1' style='border-collapse:collapse'>",
        "<tr style='background-color:#e8eef8'><th>Metrica</th>"
        "<th>Centroide</th><th>Clustering espectral</th></tr>",
    ]
    for titulo, clave, fmt in formato:
        partes.append(
            "<tr><td>" + _celda_html(titulo) + "</td><td align='right'>" +
            _celda_html(fmt.format(centroide[clave])) + "</td><td align='right'>" +
            _celda_html(fmt.format(clustering[clave])) + "</td></tr>"
        )
    partes.append("</table>")
    partes.append(
        "<p><i>Ambos calculos parten de dos warehouses creados por separado "
        "desde el mismo JSON; algoritmo de recorrido BFS. "
        "La cantidad de waves por si sola no indica que una estrategia sea mejor. "
        "Los tiempos pueden variar segun el equipo y la carga del sistema.</i></p>"
    )
    return "".join(partes)


class VentanaResultados(QWidget):
    """Muestra centroide, clustering debajo y una tabla final de comparacion."""

    def __init__(self, opciones):
        super().__init__()
        self.setWindowTitle("Resultados - Centroide vs Clustering espectral")
        self.resize(1050, 820)
        self.datos = {}
        layout = QVBoxLayout(self)
        encabezado = QLabel("COMPARACION DE RESULTADOS")
        encabezado.setStyleSheet("font-size:20px; font-weight:bold")
        layout.addWidget(encabezado)
        descripcion = QLabel(
            f"Escenario: {opciones['json']}\n"
            f"K elegido: {opciones['k']} | "
            f"Metrica: {'Topologica' if opciones['metrica'] == 't' else 'Euclidiana'} | "
            "Recorrido: BFS"
        )
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)
        self.estado = QLabel("Preparando comparacion...")
        layout.addWidget(self.estado)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        columnas = QVBoxLayout(contenido)
        columnas.setSpacing(14)

        columnas.addWidget(QLabel("1. RESULTADOS DEL CENTROIDE"))
        self.centroide = QTextBrowser()
        self.centroide.setMinimumHeight(330)
        self.centroide.setHtml("<i>Calculando resultados del centroide...</i>")
        columnas.addWidget(self.centroide)

        columnas.addWidget(QLabel("2. RESULTADOS DEL CLUSTERING ESPECTRAL"))
        self.clustering = QTextBrowser()
        self.clustering.setMinimumHeight(330)
        self.clustering.setHtml("<i>Se iniciara al terminar el centroide...</i>")
        columnas.addWidget(self.clustering)

        self.comparacion = QTextBrowser()
        self.comparacion.setMinimumHeight(430)
        self.comparacion.setHtml("<i>La tabla comparativa aparecera al finalizar ambos metodos.</i>")
        columnas.addWidget(self.comparacion)
        scroll.setWidget(contenido)
        layout.addWidget(scroll)

        fila = QHBoxLayout()
        self.cancelar = QPushButton("Cancelar calculo")
        self.cancelar.clicked.connect(self.cancelar_calculo)
        fila.addWidget(self.cancelar)
        fila.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.close)
        fila.addWidget(cerrar)
        layout.addLayout(fila)

        self.worker = TrabajadorResultados(opciones, self)
        self.worker.progreso.connect(self.estado.setText)
        self.worker.resultado.connect(self.mostrar_resultado)
        self.worker.error.connect(self.mostrar_error)
        self.worker.finished.connect(self.calculo_finalizado)
        self.worker.start()

    def mostrar_resultado(self, metodo, datos):
        self.datos[metodo] = datos
        panel = self.centroide if metodo == "centroide" else self.clustering
        panel.setHtml(html_detalle_resultados(datos))
        if "centroide" in self.datos and "clustering" in self.datos:
            self.comparacion.setHtml(
                html_tabla_comparativa(
                    self.datos["centroide"], self.datos["clustering"]
                )
            )

    def mostrar_error(self, metodo, mensaje):
        panel = self.centroide if metodo == "centroide" else self.clustering
        panel.setHtml(
            "<h3>No se pudo completar este metodo</h3><p>" +
            _celda_html(mensaje) + "</p>"
        )
        self.estado.setText(f"Error en {metodo}: {mensaje}")
        self.comparacion.setHtml(
            "<p>No se puede construir una comparacion completa si alguno "
            "de los metodos falla. Revisa los mensajes de error.</p>"
        )

    def cancelar_calculo(self):
        if self.worker.isRunning():
            self.worker.requestInterruption()
            self.estado.setText("Cancelacion solicitada; finalizara al terminar la tarea actual.")
            self.cancelar.setEnabled(False)

    def calculo_finalizado(self):
        self.cancelar.setEnabled(False)
        if self.worker.isInterruptionRequested():
            self.estado.setText("Comparacion cancelada.")
        elif len(self.datos) == 2:
            self.estado.setText("Comparacion finalizada. Ambos metodos completados.")
        else:
            self.estado.setText("Comparacion finalizada con errores; consulta cada seccion.")

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.cancelar_calculo()
            QMessageBox.information(
                self, "Calculo en curso",
                "Se solicito detener el calculo. Cierra la ventana cuando termine."
            )
            event.ignore()
            return
        super().closeEvent(event)


def iniciar():
    app = QApplication(sys.argv)
    dialogo = DialogoEstrategia()

    while True:
        eleccion = dialogo.exec()
        if eleccion == 2:
            ventana = VentanaResultados(dialogo.opciones_resultados)
            ventana.showMaximized()
            return app.exec()
        if eleccion != QDialog.DialogCode.Accepted:
            return 0

        try:
            origen = dialogo.origen()
            estrategia = dialogo.estrategia()
            zonas_espectrales = None
            K_ZONAS = None
            METRICA = None
            zona_producto_guardada = None
            cantidad_zonas_guardadas = None
            reanudada = False

            if origen == "simulacion":
                # MUY IMPORTANTE: no crear warehouse, waves ni Simulation nuevamente.
                simulation, metadata = load_simulation(dialogo.archivo())
                warehouse = simulation.warehouse
                estrategia = metadata.get("estrategia", "desconocida")
                K_ZONAS = metadata.get("k_zonas")
                METRICA = metadata.get("metrica")
                zona_producto_guardada = metadata.get("zona_producto")
                cantidad_zonas_guardadas = metadata.get("cantidad_zonas")
                reanudada = True
            else:
                if origen == "warehouse":
                    warehouse = load_warehouse(dialogo.archivo())
                    # Un warehouse aislado no tiene walkers ni el contador tick.
                    for picker in warehouse.pickers:
                        assignment = getattr(picker, "assignment", None) if picker is not None else None
                        if assignment is not None and assignment.status == "running":
                            raise ValueError(
                                "Este warehouse tiene asignaciones en curso. "
                                "Para continuar el avance debes cargar una simulacion (.pkl)."
                            )
                else:
                    config = load_config(dialogo.archivo())
                    warehouse = build_warehouse(config)

                # Si el warehouse ya tenia waves, se mantienen tal cual.
                if warehouse.waves.head is None:
                    if estrategia == "centroide":
                        generar_waves_centroide(warehouse)
                    else:
                        productos = cs.extract_pending_products(warehouse)
                        if not productos:
                            raise ValueError(
                                "No hay productos pendientes para clustering espectral."
                            )
                        K_ZONAS = min(dialogo.k_zonas(), len(productos))
                        METRICA = dialogo.metrica()
                        zonas_espectrales = cs.main(
                            warehouse=warehouse, k_zones=K_ZONAS, metric=METRICA
                        )
                        selector = SpectralWaveSelector(
                            warehouse=warehouse,
                            spectral_zones=zonas_espectrales,
                            pickers=warehouse.pickers
                        )
                        WaveBuilder(
                            warehouse, selector=selector, pickers=warehouse.pickers
                        ).build()
                elif estrategia == "clustering":
                    # No regenerar waves existentes ni recalcular sus agrupaciones.
                    K_ZONAS = dialogo.k_zonas()
                    METRICA = dialogo.metrica()

                simulation = Simulation(
                    warehouse, algorithm="bfs", auto_assign=True
                )
            break
        except Exception as error:
            QMessageBox.critical(
                dialogo, "No se pudo iniciar",
                f"Error al cargar o crear la simulacion:\n{error}"
            )
            # Dejar al usuario corregir la ruta sin cerrar la aplicacion.

    ventana = Ventana(
        warehouse,
        simulation,
        zonas_espectrales,
        estrategia=estrategia,
        k_zonas=K_ZONAS,
        metrica=METRICA,
        zona_producto_guardada=zona_producto_guardada,
        cantidad_zonas_guardadas=cantidad_zonas_guardadas,
        reanudada=reanudada,
    )
    ventana.showMaximized()
    return app.exec()


if __name__ == "__main__":
    sys.exit(iniciar())