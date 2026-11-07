from warehouse.structures.linkedlist import LinkedList, add, delete
from warehouse.structures.dictionary import Dictionary, search, insert

from warehouse.domain.product import Product
from warehouse.domain.order import Order
from warehouse.domain.location import DispatchZone
# from warehouse.domain.picker import Picker
from warehouse.domain.route import Route

class WaveConfig:
    def __init__(self, max_orders: int, max_products: int) -> None:
        for name, value in (("max_orders", max_orders), ("max_products", max_products)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} en la config del wave debe ser un entero positivo.")
        self.max_orders: int = max_orders
        self.max_products: int = max_products

class WaveLine:
    def __init__(self, product: Product, qty: int) -> None:
        self.product: Product = product
        self.qty: int = qty

    @property
    def weight(self) -> float:
        return self.product.weight * self.qty

class Wave:
    def __init__(self, wave_id: str, config: WaveConfig) -> None:
        self.id = wave_id
        self.config: WaveConfig = config

        self.orders: LinkedList = LinkedList()
        self.lines: LinkedList = LinkedList()
        self.line_index: Dictionary = Dictionary(2 * config.max_products + 1)

        self.order_count: int = 0
        self.product_count: int = 0
        self.total_units: int = 0
        self.total_weight: float = 0.0
        self.top_priority: int = 0

        self.status: str = "created"
        self.assignments: LinkedList = LinkedList()
        self.assignment_count: int = 0

    def why_not(self, order: Order) -> str|None:
        if order.state != "PENDIENTE":
            return f"El pedido {order.id} está {order.state}, solo se pueden añadir pedidos en PENDIENTE a una nueva wave."
        if self.order_count >= self.config.max_orders:
            return f"La wave {self.id} esta llena (max_orders {self.config.max_orders})."

        new_products = 0
        line = order.lines.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            if search(self.line_index, line.value.product.id) is None:
                new_products += 1
            available = line.value.product.available
            #if available is not None and line.value.qty > available:
            #    return f"El pedido {order.id} pide {line.value.qty} {line.value.product.id}, pero solo quedan {available} sin reservar."
            line = line.nextNode

        if self.product_count + new_products > self.config.max_products:
            return f"El pedido {order.id} llevaría a la wave {self.id} a {self.product_count + new_products} productos distintos (max_products {self.config.max_products})."

        return None

    def fits(self, order: Order) -> bool:
        return self.why_not(order) is None

    def add_order(self, order: Order) -> None:
        reason = self.why_not(order)
        if reason is not None:
            raise ValueError(reason)

        line = order.lines.head
        while line is not None:
            if line.value.product.id=="P136":
                print(f"estoy en la ordenr {order.id}")
                print(f"adline norm {line.value.qty}\n")
                print(f"{line.value.resto}")
            if line.value is None:
                continue

            pid = line.value.product.id
            product_line = search(self.line_index, pid)
            if product_line is not None:
                product_line.qty += line.value.qty
            else:    
                hasta = line.value.resto
                if hasta == 0:
                    line = line.nextNode
                    continue
                else:                
                    wave_line = WaveLine(line.value.product, line.value.qty)
                    add(self.lines, wave_line)
                    insert(self.line_index, wave_line, pid)                    
                    self.product_count += 1
            self.total_units += line.value.qty
            self.total_weight += line.value.weight

            line = line.nextNode

        add(self.orders, order)
        self.order_count += 1
        if order.priority > self.top_priority:
            self.top_priority = order.priority
        order.assign_to(self)
        

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
                                    capacity -= line.value.product.weight
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
                                capacity -= line.value.product.weight
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
            

    def release_stock(self) -> None:
        line = self.lines.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            line.value.product.release(line.value.qty)

class Assignment:
    def __init__(
        self, 
        wave: Wave, 
        picker, 
        zone: DispatchZone,
        shares: LinkedList,
        stops: LinkedList
    ) -> None:
        self.wave: Wave = wave
        self.picker = picker
        self.zone: DispatchZone = zone
        self.shares: LinkedList = shares
        self.stops: LinkedList = stops
        self.weight: float = 0.0
        self.units: int = 0

        line = shares.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            self.weight += line.value.product.weight * line.value.qty
            self.units += line.value.qty
            line = line.nextNode

        self.route: Route|None = None
        self.status: str = "assigned"



