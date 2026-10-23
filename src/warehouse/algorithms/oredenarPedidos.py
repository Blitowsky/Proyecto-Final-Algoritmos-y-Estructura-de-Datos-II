def ordenarPedidos(ordenes):
    nodeOrder=ordenes.head
    nodeLine=nodeOrder.value.lines.head
    pedidosPonderados = []

    while nodeOrder is not None:

        disMin = 1000000000
        disMax, contador, disManhattan, suma = 0, 0, 0, 0
        currentNodeLineA =nodeLine
        currentNodeLineB = nodeLine.nextNode  
        centro = centroide(currentNodeLineA)
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
            pedidosPonderados.append((nodeOrder.value , ponderar(nodeOrder.value.priority,0) , centro))
        elif disMin == disMax:
# si se encuentran a la misma distancia no nos dice nada si esta lejo o no 
            pedidosPonderados.append((nodeOrder.value , ponderar(nodeOrder.value.priority,0.5) , centro))
        else:
            disMedia = suma / contador                
            disNormal = (disMedia - disMin) / (disMax - disMin)
            pedidosPonderados.append((nodeOrder.value , ponderar(nodeOrder.value.priority,disNormal) , centro))

        nodeOrder = nodeOrder.nextNode
        if nodeOrder is not None:
            nodeLine=nodeOrder.value.lines.head

    pedidosPonderados.sort(key=lambda x: x[1], reverse=True)
    
# prueba de valores
#    for pedido, val, cen in pedidosPonderados:
#        print(pedido.id+" tiene val: "+ str(val)+ " su centro es: "+ str(cen[:]))

    return pedidosPonderados

def ponderar(prioridad, val):
    #uso el complemento para que a la hora de ponderar tenga mas peso estar cerca 
    # que estar lejos, sino si el valor es 0(quiere decir que esta cerca)
    # al ponderar 0 * 0.3 me da cero y si tengo un resultado de 1 (estan lejos)
    # la ponderacion me da 0.3
    ponderacion=0.7 * prioridad + 0.3 * (1 -val) 
    return ponderacion

def centroide(node):
    currenNode = node
    x, y, contador =0, 0, 0
    while currenNode is not None:
        x += currenNode.value.product.x
        y += currenNode.value.product.y
        contador +=1
        currenNode = currenNode.nextNode
    return (x/contador , y/contador)