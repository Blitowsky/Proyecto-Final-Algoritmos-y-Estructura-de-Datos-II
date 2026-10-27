import sys
import math

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from PyQt6.QtCore import QTimer

from warehouse.services.wave_builder import WaveBuilder
from warehouse.simulation.simulation import Simulation
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.domain.direction import N, S, E, O, AMBOS


#Tipos de celdas que puede tener el warehouse
from warehouse.domain.cell import HALL, RACK, DOOR, ZONE


class Ventana(QWidget):

    def __init__(self, warehouse, simulation):
        super().__init__()

        #Guardo el warehouse que recibo
        self.warehouse = warehouse
        
        #Guardo la simulacion
        self.simulation = simulation

        #Espacio que dejo alrededor del warehouse
        self.margen = 60

        #Valor inicial, despues se calcula dependiendo del tamaño de la ventana
        self.escala = 1
        
        #Imagenes de la interfaz
        self.imagen_picker = QPixmap("src/ui/assets/construction-worker.png")
        self.imagen_producto = QPixmap("src/ui/assets/box.png")
        
        
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
        
        # ==================================================
        # TICK ACTUAL
        # ==================================================

        self.label_tick = QLabel("Tick: 0", self)
        self.label_tick.setGeometry(310, 10, 100, 30)
        
        # ==================================================
        # PANEL DE EVENTOS
        # ==================================================

        self.panel_eventos = QTextEdit(self)

        #No permito que el usuario escriba
        self.panel_eventos.setReadOnly(True)

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

    def calcular_escala(self):

        #Espacio disponible para dibujar dentro de la ventana
        ancho_disponible = self.width() - 2 * self.margen
        alto_disponible = self.height() - 2 * self.margen

        #Calculo cuanto puede medir cada celda
        escala_x = ancho_disponible // self.warehouse.width
        escala_y = alto_disponible // self.warehouse.height

        #Uso la escala mas chica para asegurarme de que entre todo
        return max(1, min(escala_x, escala_y))


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


app = QApplication(sys.argv)

#Cargo el escenario
config = load_config("src/data/escenario_grande.json")

#Construyo el warehouse
warehouse = build_warehouse(config)

#Creo las waves a partir de los pedidos
waves, rejected = WaveBuilder(
    warehouse,
    pickers=warehouse.pickers
).build()

#Creo la simulacion
simulation = Simulation(
    warehouse,
    algorithm="astar",
    auto_assign=True
)

#Creo la ventana y le paso el warehouse y la simulacion
ventana = Ventana(warehouse, simulation)

ventana.showMaximized()

app.exec()