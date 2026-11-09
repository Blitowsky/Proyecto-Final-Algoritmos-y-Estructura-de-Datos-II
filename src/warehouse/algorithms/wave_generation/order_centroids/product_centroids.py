
import math

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Wave
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.order import Order


class ProductCentroidSelector:
    def __init__(self, warehouse: WareHouse, ordenes: LinkedList) -> None:
        self.warehouse: WareHouse = warehouse
        self.ordenes: LinkedList = ordenes

    def sort(self) -> list[Order]:
        return [order[0] for order in self.ordenarPedidos()]

    def next_order(self, wave, candidates, fits):
        for order in candidates:
            if fits(order):
                return order
        return None

    def stop_orderer(self):
        pass

    def generate_waves(self) -> LinkedList:
        pedidos = self.ordenarPedidos()
        picker = []
        currentNode = self.warehouse.pickers.head
        while currentNode is not None:
            picker.append(currentNode.value)
            currentNode = currentNode.nextNode

        lista= self._listaDeWaveParaTodasLasOrdenes(pedidos, self.warehouse.wave_config, picker)
        cantdePed=0
        waves = LinkedList()
        
        for i in range(len(picker)):
            print(f"Picker {i} con un peso de {picker[i].capacity}")
            for wave in lista[i]:
                add(waves, wave)
                suma=0
                print(f"Wave {wave.id}")
                currentNode = wave.orders.head
                while currentNode is not None:
                    if currentNode.value is not None:
                         print(f"    {currentNode.value.id} con un peso de {currentNode.value.total_weight}")
                         suma+=currentNode.value.total_weight
                    currentNode = currentNode.nextNode
                    cantdePed += 1
                print(suma)
            print()
        print(cantdePed)
        
        return waves

    def _listaDeWaveParaTodasLasOrdenes(self, pedidos, config, pickers) -> list[list[Wave]]:
        indexPed = 0     
        waves_por_picker = [[] for _ in range(len(pickers))]
        while pedidos is not None:
            for i in range(len(pickers)):  
                capasidad = pickers[i].capacity
                muestra = pedidos.pop(0)
                pedCercanos = self._listaPedMinimo(pedidos, muestra[2])
                wave = Wave(str(indexPed), config)
                indexPed += 1
                wave.add_order(muestra[0])
                capasidad -= wave.total_weight
                for ped, val in pedCercanos:
                    if wave.fits(ped) and capasidad - ped.total_weight >= 0 :
                        wave.add_order(ped)
                        capasidad -= ped.total_weight
                        pedidos = [t for t in pedidos if t[0] != ped]
                waves_por_picker[i].append(wave)
                if not pedidos:
                    break
            if not pedidos:
                break
        return waves_por_picker

     
    def _unaWavePorPicker(self, pedidos, config, pickers):
        indexPed = 0
        listaWave = []
        for i in range(len(pickers)):
            capasidad = pickers[i].capacity
            muestra = pedidos.pop(0)
            pedCercanos = self._listaPedMinimo(pedidos, muestra[2])
            wave = Wave(str(indexPed), config)
            indexPed += 1
            wave.add_order(muestra[0])
            capasidad -= wave.total_weight
            for ped, val in pedCercanos:
                if wave.fits(ped) and capasidad + ped.total_weight < pickers[i].capacity :
                    wave.add_order(ped)
                    pedidos = [t for t in pedidos if t[0] != ped]
            listaWave.append(wave)
            if not pedidos:
                break
        return listaWave


    def _listaPedMinimo(self, pedidos, muestra):
        listaPedido = []
        for ped, val, cen in pedidos:
            listaPedido.append((ped ,math.dist(muestra, cen)))
        listaPedido.sort(key=lambda x: x[1])
        return listaPedido


    def pedMinimo(self, pedidos, muestra, maxProducto):
        disMin=100000000
        for ped, val, cen in pedidos:
            if math.dist(muestra,cen)<disMin and ped.total_units<= maxProducto:
                disMin = math.dist(muestra,cen)
                pedido=ped
                valor=val
                centro=cen
        return (pedido,valor,centro)

    def ordenarPedidos(self):
        ordenes = self.ordenes
        nodeOrder=ordenes.head
        if nodeOrder is None or nodeOrder.value is None:
            raise ValueError("No se puede ordenar una lista de pedidos vacía.")
        nodeLine=nodeOrder.value.lines.head
        pedidosPonderados = []

        while nodeOrder is not None:
            if nodeOrder.value is None:
                nodeOrder = nodeOrder.nextNode
                continue

            disMin = 1000000000
            disMax, contador, disManhattan, suma = 0, 0, 0, 0
            currentNodeLineA =nodeLine
            currentNodeLineB = nodeLine.nextNode  
            centro = self.centroide(currentNodeLineA)
            while currentNodeLineB is not None and currentNodeLineA is not None:
                disX = abs(currentNodeLineA.value.product.x - currentNodeLineB.value.product.x)
                disY = abs(currentNodeLineA.value.product.y - currentNodeLineB.value.product.y)
                disManhattan = disX + disY
                contador += 1
                if disManhattan > disMax:
                    disMax = disManhattan
                if disManhattan < disMin:
                    disMin = disManhattan
                suma += disX + disY 
                disManhattan = 0
                if currentNodeLineB.nextNode is None:
                    currentNodeLineA = currentNodeLineA.nextNode
                    if currentNodeLineA is not None:
                        currentNodeLineB = currentNodeLineA.nextNode
                else:
                    currentNodeLineB=currentNodeLineB.nextNode
            if suma == 0:
    # estan en la misma posicion
                pedidosPonderados.append((nodeOrder.value, self.ponderar(nodeOrder.value.priority,0) , centro))
            elif disMin == disMax:
    # si se encuentran a la misma distancia no nos dice nada si esta lejo o no 
                pedidosPonderados.append((nodeOrder.value, self.ponderar(nodeOrder.value.priority,0.5) , centro))
            else:
                disMedia = suma / contador                
                disNormal = (disMedia - disMin) / (disMax - disMin)
                pedidosPonderados.append((nodeOrder.value, self.ponderar(nodeOrder.value.priority,disNormal) , centro))

            nodeOrder = nodeOrder.nextNode
            if nodeOrder is not None and nodeOrder.value is not None:
                nodeLine=nodeOrder.value.lines.head

        pedidosPonderados.sort(key=lambda x: x[1], reverse=True)
        
        return pedidosPonderados

    def ponderar(self, prioridad, val):
        #uso el complemento para que a la hora de ponderar tenga mas peso estar cerca 
        # que estar lejos, sino si el valor es 0(quiere decir que esta cerca)
        # al ponderar 0 * 0.3 me da cero y si tengo un resultado de 1 (estan lejos)
        # la ponderacion me da 0.3
        ponderacion=0.7 * prioridad + 0.3 * (1 -val) 
        return ponderacion

    def centroide(self, node):
        currenNode = node
        x, y, contador =0, 0, 0
        while currenNode is not None:
            x += currenNode.value.product.x
            y += currenNode.value.product.y
            contador +=1
            currenNode = currenNode.nextNode
        return (x/contador , y/contador)

