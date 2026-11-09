from warehouse.algorithms.oredenarPedidos import ordenarPedidos
from warehouse.domain.wave import Wave
from warehouse.structures.linkedlist import LinkedList, add
import math

def generacionWaves(warehouse):
    pedidos = ordenarPedidos(warehouse.orders)
    picker = []
    currentNode = warehouse.pickers.head
    while currentNode is not None:
        picker.append(currentNode.value)
        currentNode = currentNode.nextNode
    lista = generadorDeWaves(pedidos, warehouse.wave_config, picker)

    wavesWareHouse = LinkedList()
    for wave in lista:
        for w in wave:
            add(wavesWareHouse,w)
    warehouse.waves=wavesWareHouse

    

def generadorDeWaves(pedidos, config, pickers):
    """Agrupa pedidos por cercanía con reparto de unidades y reserva real.

    ``pedidos`` contiene tuplas (Order, ponderación, centroide). Se consume
    una copia; las cantidades ya asignadas están en ``OrderLine.usado``.
    """
    pendientes = list(pedidos)
    waves_por_picker = [[] for _ in pickers]
    if pendientes and not pickers:
        raise ValueError("No hay pickers para preparar los pedidos.")
    index_wave = 0
    EPS = 1e-9

    def puede_tomar(order, capacity):
        return any(
            line is not None and line.resto > 0
            and line.product.weight <= capacity + EPS
            and (line.product.available is None or line.product.available > 0)
            for line in order.lines
        )

    while pendientes:
        hubo_avance = False
        for i, picker in enumerate(pickers):
            if not pendientes:
                break
            # Puede haber pedidos cuyo producto pese más que la capacidad del
            # picker actual; buscar uno viable sin descartarlos.
            muestra = next((t for t in pendientes if puede_tomar(t[0], picker.capacity)), None)
            if muestra is None:
                continue

            wave = Wave(str(index_wave), config)
            capacidad = picker.capacity

            def agregar_pedido(pedido):
                nonlocal capacidad
                antes = wave.total_weight
                if (pedido.state == "PENDIENTE"
                    and pedido.peso_restante <= capacidad + EPS
                    and wave.fits(pedido)):
                    wave.add_order(pedido)
                else:
                    wave.add_partial_order(pedido, capacidad)
                capacidad = max(0.0, capacidad - (wave.total_weight - antes))
                # Una orden se elimina de pendientes solo cuando TODAS sus
                # líneas se han asignado (no por pasar a EN_WAVE).
                if all(l is None or l.resto == 0 for l in pedido.lines):
                    pendientes[:] = [t for t in pendientes if t[0] is not pedido]

            agregar_pedido(muestra[0])
            # Buscar cercanos al pedido inicial, sin incluirlo de nuevo.
            cercanos = listaPedMinimo(
                [t for t in pendientes if t[0] is not muestra[0]], muestra[2]
            )
            for pedido, _ in cercanos:
                if wave.order_count >= config.max_orders or capacidad <= EPS:
                    break
                if puede_tomar(pedido, capacidad):
                    agregar_pedido(pedido)

            if wave.total_units > 0:
                waves_por_picker[i].append(wave)
                index_wave += 1
                hubo_avance = True

        if not hubo_avance:
            faltantes = [
                f"{t[0].id}: " + ", ".join(
                    f"{l.product.id} x{l.resto}" for l in t[0].lines if l and l.resto > 0
                ) for t in pendientes
            ]
            raise ValueError(
                "No se pueden asignar las unidades restantes a ningún picker. "
                "Verificá el peso unitario, stock y capacidad. Pedidos: "
                + "; ".join(faltantes)
            )

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
            capacidad = pickers[i].capacity
            muestra = pedidos.pop(0)
            pedCercanos = listaPedMinimo(pedidos, muestra[2])
            wave = Wave(str(indexPed), config)
            indexPed += 1
            wave.add_order(muestra[0])
            capacidad -= wave.total_weight
            for ped, val in pedCercanos:
                if wave.fits(ped) and capacidad - ped.total_weight >= 0 :
                    wave.add_order(ped)
                    capacidad -= ped.total_weight                    
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
        capacidad = pickers[i].capacity
        muestra = pedidos.pop(0)
        pedCercanos = listaPedMinimo(pedidos, muestra[2])
        wave = Wave(str(indexPed), config)
        indexPed += 1
        wave.add_order(muestra[0])
        capacidad -= wave.total_weight
        for ped, val in pedCercanos:
            if wave.fits(ped) and capacidad + ped.total_weight < pickers[i].capacity :
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

    