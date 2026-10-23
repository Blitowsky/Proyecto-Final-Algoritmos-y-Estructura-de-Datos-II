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

    maxPicker = len(picker)
    indexPed, id = 0, 0
    waves = []
    #wave = Wave(str(id), config)
    muesta=pedidos[0]
    lista= unaWavePorPicker(pedidos,config,picker)
    print("nueva funcion")

    for wave in lista:
        print( wave.id+" con esta cantidad de pedidos "+ str(wave.total_units))


"""
#Pruebo si devuelve lista o no con sus respectivos valores.
    print(str(muesta[0].id) + " , " + str(muesta[1]))
    for ped, val, cen in lista:
        print(ped.id + " tien una valor de: " + str(val) + " con respecto a " +str(muesta[2]) + " con centro: " + str(cen) )

    maxPedido = config.max_orders
    maxProducto = config.max_products

    orden = pedidos[0]
    #agregar la funcionalidad de que si supera agarrar solo una parte.
    if orden[0].total_units <= maxProducto:
        maxProducto -= orden[0].total_units
        maxPedido -= 1
        wave.add_order(orden[0])
        pedidos.remove(orden)

    pedido = pedMinimo(pedidos, orden[2 ], maxProducto)
    wave.add_order(pedido[0])
    maxProducto -= pedido[0].total_units
    print(pedido[0].id)
    pedidos.remove(pedido)

"""   
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
                print("aca")
                print(ped.id+" pedido eliminado")
                pedidos = [t for t in pedidos if t[0] != ped]
                for ped, val, cen in pedidos:
                    print()
                    print(ped.id+"quedan")
        print()
        listaWave.append(wave)
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

    