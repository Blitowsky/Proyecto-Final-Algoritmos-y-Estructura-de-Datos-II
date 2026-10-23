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
    index, id=0, 0
    waves = []
    

    
    wave = Wave(str(id), config)
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

    
        


def pedMinimo(pedidos, muestra, maxProducto):
    disMin=100000000
    for ped, val, cen in pedidos:
        if math.dist(muestra,cen)<disMin and ped.total_units<= maxProducto:
            disMin = math.dist(muestra,cen)
            pedido=ped
            valor=val
            centro=cen
    return (pedido,valor,centro)

    