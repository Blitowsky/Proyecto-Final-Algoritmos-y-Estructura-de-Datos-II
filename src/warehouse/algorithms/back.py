def listaDeWaveParaTodasLasOrdenes(pedidos, config, pickers):
    indexPed = 0     
    waves_por_picker = [[] for _ in range(len(pickers))]
    pedidoAPartir= []
    while pedidos is not None:
        for i in range(len(pickers)):  
            flag=True
            capasidad = pickers[i].capacity
            while pedidos is not None or flag :
                muestra = pedidos.pop(0)
                if muestra[0].total_weight > capasidad:
                      pedidoAPartir.append(muestra)
                else:
                      flag=False
                if not pedidos:
                    break

            #muestra = pedidos.pop(0)
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



def add_partial_order(self, order: Order, capacity: float) -> None:
            reason = self.why_not(order)
            
            if reason is not None:
                raise ValueError(reason)
    
            line = order.lines.head
            while line is not None:
                #print(f"el pedido es {order.id} {line.value.product.id} su peso es: {line.value.weight} y necesita cantidad: {line.value.qty}")
                if line.value is None:
                    line = line.nextNode
                    continue
                """
                if line.value.qty==0:
                    line = line.nextNode
                    continue
                
                if line.value.product.id=="P136":
                    print(f"estoy en la ordenr {order.id}")
                    print(f"pasepor aca {line.value.qty}\n")
                """
                pid = line.value.product.id
                product_line = search(self.line_index, pid)

                if product_line is not None:
                    product_line.qty += line.value.qty                    
                else:
                    if line.value.weight <= capacity:
                        if line.value.usado == 0:                            
                            capacity -= line.value.weight
                            wave_line = WaveLine(line.value.product, line.value.qty)
                            add(self.lines, wave_line)
                            insert(self.line_index, wave_line, pid)
                            """
                            order.line_count -=1
                            order.total_units -= line.value.qty
                            """ 
                            order.total_weight -= line.value.weight     

                            line.value.usado = line.value.qty

                            self.product_count += 1
                            self.total_units += line.value.qty
                            self.total_weight += line.value.weight                                             
                            #delete(order.lines, line.value)
                        else:                            
                            contador=0
                            carga=0
                            hasta = line.value.resto 

                            for i in range(hasta):
                                if carga + line.value.product.weight < capacity:
                                    carga +=line.value.product.weight
                                    #line.value.qty -=1
                                    contador +=1
                                    #capacity -= line.value.product.weight
                                else:
                                    break
                            line.value.usado = contador
                            #line.value.qty -= contador
                            wave_line = WaveLine(line.value.product, contador)
                            add(self.lines, wave_line)
                            insert(self.line_index, wave_line, pid)
                            """
                            order.total_units -= contador
                            """ 
                            order.total_weight -= contador * line.value.product.weight      
                                        
                            self.product_count += 1
                            self.total_units += contador
                            self.total_weight += contador * line.value.product.weight 
                            break 

                    else:                        
                        contador=0
                        carga=0
                        hasta = line.value.resto
                        for i in range(hasta):
                            if carga + line.value.product.weight < capacity:
                                carga +=line.value.product.weight
                                #line.value.qty -=1
                                contador +=1
                                #capacity -= line.value.product.weight
                            else:
                                break
                        if contador != 0:
                            line.value.usado = contador
                            #line.value.qty -= contador
                            wave_line = WaveLine(line.value.product, contador)
                            add(self.lines, wave_line)
                            insert(self.line_index, wave_line, pid)
                            """
                            order.total_units -= contador
                            """ 
                            order.total_weight -= contador * line.value.product.weight      
                                        
                            self.product_count += 1
                            self.total_units += contador
                            self.total_weight += contador * line.value.product.weight 
                        break                                          
            
                line = line.nextNode   
    
            add(self.orders, order)
            self.order_count += 1
            if order.priority > self.top_priority:
                self.top_priority = order.priority
            if line is None:
                order.assign_to(self)