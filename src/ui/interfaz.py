import sys

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.structures.dictionary import search


class Ventana(QWidget):

    def __init__(self, warehouse):
        super().__init__()

        #Guardo el warehouse que recibo
        self.warehouse = warehouse

        #Espacio que dejo alrededor del warehouse
        self.margen = 30

        #La escala se calcula dependiendo del tamaño de la ventana
        #Comienza con un valor inicial 1
        self.escala = 1


    def calcular_escala(self):

        #Espacio disponible para dibujar dentro de la ventana
        ancho_disponible = self.width() - 2 * self.margen
        alto_disponible = self.height() - 2 * self.margen

        #Calculo cuanto puede medir cada celda para que entre por ancho y por alto
        escala_x = ancho_disponible // self.warehouse.width
        escala_y = alto_disponible // self.warehouse.height

        #Uso la escala mas chica para asegurarme de que entre todo el warehouse
        return max(1, min(escala_x, escala_y))


    def coordenada_a_pixel(self, x, y):

        #La coordenada x crece normalmente hacia la derecha
        xp = self.margen + x * self.escala

        #Invierto y porque en el warehouse el (0,0) esta abajo a la izquierda,
        #pero en PyQt esta arriba a la izquierda
        yp = self.margen + (self.warehouse.height - 1 - y) * self.escala

        return xp, yp


    def paintEvent(self, event):

        painter = QPainter(self)

        #Cada vez que se dibuja la ventana vuelvo a calcular la escala
        self.escala = self.calcular_escala()


        # ==================================================
        # WAREHOUSE
        # ==================================================

        #Dibujo el borde del warehouse
        painter.drawRect(self.margen, self.margen, self.warehouse.width * self.escala, self.warehouse.height * self.escala)


        # ==================================================
        # RACKS Y ZONAS DE DESPACHO
        # ==================================================

        #Recorro todas las celdas del warehouse
        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                #Obtengo el id de la celda
                cid = y * self.warehouse.width + x

                #Busco si en esta celda hay un rack
                rack = search(self.warehouse.racks, cid)

                #Busco si en esta celda hay un hall
                hall = search(self.warehouse.halls, cid)

                #Paso las coordenadas del warehouse a coordenadas de la pantalla
                xp, yp = self.coordenada_a_pixel(x, y)


                #Si hay un rack en esta celda lo dibujo
                if rack is not None:

                    painter.setBrush(QBrush(QColor("gray")))

                    painter.drawRect(xp + 5, yp + 5, self.escala - 10, self.escala - 10)

                    painter.drawText(xp + 10, yp + 25, str(rack.id))


                #Si el hall pertenece a una zona de despacho la dibujo
                elif hall is not None and hall.zone is not None:

                    painter.setBrush(QBrush(QColor("lightgreen")))

                    painter.drawRect(xp + 5, yp + 5, self.escala - 10, self.escala - 10)


        # ==================================================
        # ARISTAS
        # ==================================================

        painter.setPen(QPen(QColor("black"), 2))

        #Empiezo desde la primera arista del grafo
        actual = self.warehouse.graph.e.head

        while actual is not None:

            #Cada arista tiene origen, destino y peso
            origen_id, destino_id, peso = actual.value

            #Busco los HallNodes correspondientes al origen y destino
            hall_origen = search(self.warehouse.halls, origen_id)
            hall_destino = search(self.warehouse.halls, destino_id)

            if hall_origen is not None and hall_destino is not None:

                #Obtengo la esquina superior izquierda de cada celda
                x1, y1 = self.coordenada_a_pixel(hall_origen.x, hall_origen.y)
                x2, y2 = self.coordenada_a_pixel(hall_destino.x, hall_destino.y)

                #Me muevo hasta el centro de cada celda
                x1 += self.escala // 2
                y1 += self.escala // 2

                x2 += self.escala // 2
                y2 += self.escala // 2

                #Dibujo la arista entre los dos HallNodes
                painter.drawLine(x1, y1, x2, y2)

            #Paso a la siguiente arista
            actual = actual.nextNode


        # ==================================================
        # HALL NODES
        # ==================================================

        painter.setBrush(QBrush(QColor("black")))

        #Recorro nuevamente todas las celdas
        for y in range(self.warehouse.height):

            for x in range(self.warehouse.width):

                cid = y * self.warehouse.width + x

                #Busco si existe un HallNode en esta celda
                hall = search(self.warehouse.halls, cid)

                if hall is not None:

                    #Obtengo la esquina de la celda
                    xp, yp = self.coordenada_a_pixel(hall.x, hall.y)

                    #Busco el centro de la celda
                    xp += self.escala // 2
                    yp += self.escala // 2

                    #Dibujo el HallNode
                    painter.drawEllipse(xp - 4, yp - 4, 8, 8)


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

                    #Busco la celda donde esta guardado el producto
                    xp, yp = self.coordenada_a_pixel(producto.x, producto.y)

                    #Dibujo un cuadrado naranja para indicar que hay un producto
                    painter.drawRect(xp + self.escala - 17, yp + 7, 10, 10)

                #Paso al siguiente producto
                actual_producto = actual_producto.nextNode


        # ==================================================
        # PICKERS
        # ==================================================

        #Empiezo desde el primer picker
        actual_picker = self.warehouse.pickers.head

        while actual_picker is not None:

            picker = actual_picker.value

            if picker is not None:

                #picker.node tiene el id del HallNode donde esta parado el picker
                hall_picker = search(self.warehouse.halls, picker.node)

                if hall_picker is not None:

                    #Busco la celda donde esta parado
                    xp, yp = self.coordenada_a_pixel(hall_picker.x, hall_picker.y)

                    #Busco el centro de la celda
                    xp += self.escala // 2
                    yp += self.escala // 2

                    painter.setBrush(QBrush(QColor("blue")))

                    #Dibujo el picker
                    painter.drawEllipse(xp - 10, yp - 10, 20, 20)

                    #Muestro el id del picker
                    painter.drawText(xp - 20, yp - 15, str(picker.id))

            #Paso al siguiente picker
            actual_picker = actual_picker.nextNode


app = QApplication(sys.argv)

#Cargo el archivo JSON que quiero probar
config = load_config("src/tests/prueba.json")

#Construyo el warehouse a partir del JSON
warehouse = build_warehouse(config)

#Creo la ventana y le paso el warehouse
ventana = Ventana(warehouse)

#Abro la ventana maximizada para aprovechar el tamaño de la pantalla
ventana.showMaximized()

app.exec()