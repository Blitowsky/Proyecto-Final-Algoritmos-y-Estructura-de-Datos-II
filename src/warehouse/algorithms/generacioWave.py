from warehouse.algorithms.oredenarPedidos import ordenarPedidos
from warehouse.domain.wave import Wave
import math


def generacionWaves(ordenes, pickers, config):
    pedidos = ordenarPedidos(ordenes)
    picker =[]
    currentNode = pickers.head
    while currentNode is not None:
        picker.append(currentNode.value)
        currentNode = currentNode.nextNode

    lista= listaDeWaveParaTodasLasOrdenes(pedidos,config,picker)

    for i in range(len(picker)):
        print(f"Picker {i} con un peso de {picker[i].capacity}")
        for wave in lista[i]:
            suma=0
            print(f"Wave {wave.id}")
            currentNode = wave.orders.head
            while currentNode is not None:
                 print(f"    {currentNode.value.id} con un peso de {currentNode.value.total_weight}")
                 suma+=currentNode.value.total_weight
                 currentNode = currentNode.nextNode
            print(suma)
        print()
        
    return lista
    #for wave in lista:
    #    print( wave.id+" con esta cantidad de pedidos "+ str(wave.total_units))

def listaDeWaveParaTodasLasOrdenes(pedidos, config, pickers):
    indexPed = 0     
    waves_por_picker = [[] for _ in range(len(pickers))]
    while pedidos is not None:
        for i in range(len(pickers)):  
            capasidad = pickers[i].capacity
            muestra = pedidos.pop(0)
            #print(f"{i} en {muestra[0].id}")
            pedCercanos = listaPedMinimo(pedidos, muestra[2])
            wave = Wave(str(indexPed), config)
            indexPed += 1
            wave.add_order(muestra[0])
            capasidad -= wave.total_weight
            for ped, val in pedCercanos:
                if wave.fits(ped) and capasidad - ped.total_weight >= 0 :
                    #print(f"agrego {ped.id} a la wave {wave.id}")
                    wave.add_order(ped)
                    capasidad -= ped.total_weight
                    """
                    print("aca")
                    print(ped.id+" pedido eliminado")
                    """
                    pedidos = [t for t in pedidos if t[0] != ped]
                    """
                    for ped, val, cen in pedidos:
                        print()
                        print(ped.id+"quedan")
                    """        
            waves_por_picker[i].append(wave)
            if not pedidos:
                break
        if not pedidos:
                        break
    return waves_por_picker

 
def unaWavePorPicker(pedidos, config, pickers):
    indexPed = 0
    listaWave = []
    for i in range(len(pickers)):
        capasidad = pickers[i].capacity
        muestra = pedidos.pop(0)
        pedCercanos = listaPedMinimo(pedidos, muestra[2])
        wave = Wave(str(indexPed), config)
        indexPed += 1
        wave.add_order(muestra[0])
        capasidad -= wave.total_weight
        for ped, val in pedCercanos:
            if wave.fits(ped) and capasidad + ped.total_weight < pickers[i].capacity :
                wave.add_order(ped)
                """
                print("aca")
                print(ped.id+" pedido eliminado")
                """
                pedidos = [t for t in pedidos if t[0] != ped]
                """
                for ped, val, cen in pedidos:
                    print()
                    print(ped.id+"quedan")
                """        
        listaWave.append(wave)
        if not pedidos:
            break
    return listaWave




def listaPedMinimo(pedidos, muestra):
    listaPedido = []
    for ped, val, cen in pedidos:
        listaPedido.append((ped ,math.dist(muestra, cen)))
    listaPedido.sort(key=lambda x: x[1])
    return listaPedido


def pedMinimo(pedidos, muestra, maxProducto):
    disMin=100000000
    for ped, val, cen in pedidos:
        if math.dist(muestra,cen)<disMin and ped.total_units<= maxProducto:
            disMin = math.dist(muestra,cen)
            pedido=ped
            valor=val
            centro=cen
    return (pedido,valor,centro)

    