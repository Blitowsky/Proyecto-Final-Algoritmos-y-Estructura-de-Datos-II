import sys

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import QTimer

from warehouse.services.wave_builder import WaveBuilder
from warehouse.simulation.simulation import Simulation
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse


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
        
        #Timer que va avanzando la simulacion
        self.timer = QTimer(self)

        #Cada vez que el timer se activa ejecuto un tick
        self.timer.timeout.connect(self.avanzar_simulacion)

        #Tiempo entre ticks
        self.timer.setInterval(300)
        
        
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


    def avanzar_simulacion(self):

        #Si la simulacion ya termino detengo el timer
        if self.simulation.finished:

            self.timer.stop()

            print("Simulacion terminada")
            print(self.simulation.summary())

            return


        #Ejecuto un solo tick
        eventos = self.simulation.step()

        #Muestro por consola los eventos importantes
        for evento in eventos:

            if evento.kind != "move":

                print(evento.describe(self.warehouse))


        #Le digo a PyQt que vuelva a dibujar la ventana
        self.update()


    def paintEvent(self, event):

        painter = QPainter(self)

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

        painter.setPen(QPen(QColor("black"), 2))

        #Empiezo desde la primera arista
        actual = self.warehouse.graph.e.head

        while actual is not None:

            #Cada arista tiene nodo origen, nodo destino y peso
            origen_id, destino_id, peso = actual.value

            #Paso el id de cada nodo a coordenadas (x,y)
            origen_x, origen_y = self.warehouse.node_xy(origen_id)
            destino_x, destino_y = self.warehouse.node_xy(destino_id)

            #Paso las coordenadas del warehouse a la pantalla
            x1, y1 = self.coordenada_a_pixel(origen_x, origen_y)
            x2, y2 = self.coordenada_a_pixel(destino_x, destino_y)

            #Busco el centro de las dos celdas
            x1 += self.escala // 2
            y1 += self.escala // 2

            x2 += self.escala // 2
            y2 += self.escala // 2

            #Dibujo la arista
            painter.drawLine(x1, y1, x2, y2)

            #Paso a la siguiente arista
            actual = actual.nextNode


        # ==================================================
        # CELDAS DE PASILLO
        # ==================================================

        painter.setBrush(QBrush(QColor("black")))

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
                    painter.drawEllipse(xp - 3, yp - 3, 6, 6)


        # ==================================================
        # PRODUCTOS
        # ==================================================

        painter.setBrush(QBrush(QColor("orange")))

        #Recorro el diccionario de productos
        for bucket in self.warehouse.products.dictionary:

            actual_producto = bucket.head

            while actual_producto is not None:

                if actual_producto.value is not None and isinstance(actual_producto.value, tuple):

                    #El producto esta guardado en la segunda posicion de la tupla
                    producto = actual_producto.value[1]
                    
                    #Solo dibujo el producto si todavia tiene stock
                    if producto.stock is None or producto.stock > 0:

                        #Product.x y Product.y obtienen la posicion de su RackCell
                        xp, yp = self.coordenada_a_pixel(producto.x, producto.y)

                        #Dibujo un cuadrado naranja para indicar que hay producto
                        painter.drawRect(xp + self.escala - 12, yp + 4, 8, 8)

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

                painter.setBrush(QBrush(QColor("blue")))

                #Dibujo el picker
                painter.drawEllipse(xp - 10, yp - 10, 20, 20)

                #Muestro su id
                painter.drawText(xp - 20, yp - 15, str(picker.id))

            actual_picker = actual_picker.nextNode


app = QApplication(sys.argv)

#Cargo el escenario
config = load_config("src/data/escenario_basico.json")

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
    algorithm="bfs",
    auto_assign=True
)

#Creo la ventana y le paso el warehouse y la simulacion
ventana = Ventana(warehouse, simulation)

ventana.showMaximized()

app.exec()