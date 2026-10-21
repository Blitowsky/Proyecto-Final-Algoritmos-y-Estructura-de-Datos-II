def ordenarPedidos(ordenes):
    nodeOrder=ordenes.head
    nodeLine=nodeOrder.value.lines.head
    pedidosPonderados = []

    while nodeOrder is not None:

        disMin = 1000000000
        disMax, contador, disManhattan, suma = 0 
        currentNodeLineA =nodeLine
        currentNodeLineB = nodeLine.nextNode  

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
            pedidosPonderados.append((nodeOrder.value.id , ponderar(nodeOrder.value.priority,0)))
        elif disMin == disMax:
# si se encuentran a la misma distancia no nos dice nada si esta lejo o no 
            pedidosPonderados.append((nodeOrder.value.id , ponderar(nodeOrder.value.priority,0.5)))
        else:
            disMedia = suma / contador                
            disNormal = (disMedia - disMin) / (disMax - disMin)
            pedidosPonderados.append((nodeOrder.value.id , ponderar(nodeOrder.value.priority,disNormal)))

        nodeOrder = nodeOrder.nextNode
        if nodeOrder is not None:
            nodeLine=nodeOrder.value.lines.head

    pedidosPonderados.sort(key=lambda x: x[1], reverse=True)
    
# prueba de valores
#    for pedido, val in pedidosPonderados:
#        print(pedido+" tiene val: "+ str(val))

    return pedidosPonderados

def ponderar(prioridad, val):
    #uso el complemento para que a la hora de ponderar tenga mas peso estar cerca 
    # que estar lejos, sino si el valor es 0(quiere decir que esta cerca)
    # al ponderar 0 * 0.3 me da cero y si tengo un resultado de 1 (estan lejos)
    # la ponderacion me da 0.3
    ponderacion=0.7 * prioridad + 0.3 * (1 -val) 
    return ponderacion