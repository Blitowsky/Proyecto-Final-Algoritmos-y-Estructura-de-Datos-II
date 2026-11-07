from warehouse.algorithms.oredenarPedidos import ordenarPedidos
from warehouse.domain.wave import Wave
import math

def generacionWaves(ordenes, pickers, config):
    pedidos = ordenarPedidos(ordenes)
    picker = []
    currentNode = pickers.head
    while currentNode is not None:
        picker.append(currentNode.value)
        currentNode = currentNode.nextNode
    lista = listaDeWaveParaTodasLasOrdenes(pedidos, config, picker)
    return lista

def generadorDeWaves(pedidos, config, pickers):
    indexPed = 0     
    waves_por_picker = [[] for _ in range(len(pickers))]
    while pedidos is not None:
        for i in range(len(pickers)):             
            capasidad = pickers[i].capacity
            muestra = pedidos[0]
            if muestra[0].peso_restante > capasidad:                    
                wave = Wave(str(indexPed), config)
                indexPed += 1                
                wave.add_partial_order(muestra[0], capasidad)   
                waves_por_picker[i].append(wave)   
                if muestra[0].state =="EN_WAVE":
                    pedidos.pop(0)                             
            else:
                muestra = pedidos.pop(0)               
                pedCercanos = listaPedMinimo(pedidos, muestra[2])
                wave = Wave(str(indexPed), config)
                indexPed += 1
                wave.add_order(muestra[0])
                capasidad -= wave.total_weight                
                for ped, val in pedCercanos:
                    if wave.order_count< config.max_orders:
                        if wave.fits(ped) and capasidad - ped.total_weight >= 0 :
                            wave.add_order(ped) 
                            capasidad -= ped.total_weight                       
                            pedidos = [t for t in pedidos if t[0] != ped]
                        else:                            
                            wave.add_partial_order(ped, capasidad)                            
                            if ped =="EN_WAVE":
                                pedidos = [t for t in pedidos if t[0] != ped]
                            break
                    else:
                        break

                waves_por_picker[i].append(wave)
            if not pedidos:
                break
        if not pedidos:
            break
    return waves_por_picker

def listaPedMinimo(pedidos, muestra):
    listaPedido = []
    for ped, val, cen in pedidos:
        listaPedido.append((ped ,math.dist(muestra, cen)))
    listaPedido.sort(key=lambda x: x[1])
    return listaPedido

def listaDeWaveParaTodasLasOrdenes(pedidos, config, pickers):
    indexPed = 0     
    waves_por_picker = [[] for _ in range(len(pickers))]
    while pedidos is not None:
        for i in range(len(pickers)):  
            capasidad = pickers[i].capacity
            muestra = pedidos.pop(0)
            pedCercanos = listaPedMinimo(pedidos, muestra[2])
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
                pedidos = [t for t in pedidos if t[0] != ped]                      
        listaWave.append(wave)
        if not pedidos:
            break
    return listaWave



def pedMinimo(pedidos, muestra, maxProducto):
    disMin=100000000
    for ped, val, cen in pedidos:
        if math.dist(muestra,cen)<disMin and ped.total_units<= maxProducto:
            disMin = math.dist(muestra,cen)
            pedido=ped
            valor=val
            centro=cen
    return (pedido,valor,centro)

def generacionWavesPruebas(ordenes, pickers, config):
    pedidos = ordenarPedidos(ordenes)
    picker = []

    currentNode = pickers.head
    while currentNode is not None:
        picker.append(currentNode.value)
        currentNode = currentNode.nextNode

    lista = generadorDeWaves(pedidos, config, picker)

    cantdePed = 0
    contadorPedidos = {}

    for i in range(len(picker)):
        print(f"Picker {i} con un peso de {picker[i].capacity}")

        for wave in lista[i]:
            suma = 0
            print(f"    Wave {wave.id}")

            currentNode = wave.orders.head

            while currentNode is not None:
                pedido = currentNode.value
                pedido_id = pedido.id

                # Contar apariciones del pedido
                contadorPedidos[pedido_id] = contadorPedidos.get(pedido_id, 0) + 1

                print(f"       {pedido_id} con un peso de {pedido.total_weight}")            

                suma += pedido.total_weight
                currentNode = currentNode.nextNode
                cantdePed += 1

            

            nodePed = wave.lines.head
            sumaLine=0
            while nodePed is not None:
                sumaLine += nodePed.value.weight
                print(
                    f"           producto: {nodePed.value.product.id} "
                    f"con una cantidad de: {nodePed.value.qty}"
                )
                nodePed = nodePed.nextNode

            print(f"la suma1 es {suma} y la de la linea es:{sumaLine}")

        print()

    print(f"Total de apariciones de pedidos: {cantdePed}")

    # Mostrar todas las apariciones
    print("\n===== APARICIONES POR PEDIDO =====")

    for pedido_id, cantidad in contadorPedidos.items():
        print(f"Pedido {pedido_id}: {cantidad} veces")

    # Mostrar únicamente los pedidos repetidos
    print("\n===== PEDIDOS REPETIDOS =====")

    for pedido_id, cantidad in contadorPedidos.items():
        if cantidad > 1:
            print(f"Pedido {pedido_id}: {cantidad} veces")

    print(f"\nPedidos únicos: {len(contadorPedidos)}")

    return lista

"""

def generacionWavesPruebas2(ordenes, pickers, config):
    pedidos = ordenarPedidos(ordenes)
    picker =[]
    currentNode = pickers.head
    while currentNode is not None:
        picker.append(currentNode.value)
        currentNode = currentNode.nextNode

    lista= generadorDeWaves(pedidos,config,picker)
    cantdePed=0
    
    for i in range(len(picker)):
        print(f"Picker {i} con un peso de {picker[i].capacity}")
        for wave in lista[i]:
            suma=0
            print(f"    Wave {wave.id}")
            currentNode = wave.orders.head
            while currentNode is not None:
                 print(f"       {currentNode.value.id} con un peso de {currentNode.value.total_weight}")
                 nodePed = currentNode.value.lines.head
                 while nodePed is not None:
                     print(f"           producto: {nodePed.value.product.id} con una cantidad de: {nodePed.value.qty}")
                     nodePed=nodePed.nextNode
                 suma+=currentNode.value.total_weight
                 currentNode = currentNode.nextNode
                 cantdePed += 1
            print(suma)
        print()
    
    
    print(cantdePed)
    
    return lista
    #for wave in lista:
    #    print( wave.id+" con esta cantidad de pedidos "+ str(wave.total_units))
  
"""

    