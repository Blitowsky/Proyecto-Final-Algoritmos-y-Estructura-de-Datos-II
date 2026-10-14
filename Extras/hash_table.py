import math

class TablaHashCuadratica:
    VACIO = 0
    OCUPADO = 1
    ELIMINADO = 2

    def __init__(self, capacidad_inicial=11):
        self.capacidad = self._siguiente_primo(capacidad_inicial)
        self.tamaño = 0
        self.tabla = [[self.VACIO, None, None] for _ in range(self.capacidad)]

    def _hash(self, clave):
        k = abs(hash(clave))
        A = (math.sqrt(5) - 1) / 2
        return math.floor(self.capacidad * ((k * A) % 1))

    def insertar(self, clave, valor):
        # Paso 4.1: Verificar factor de carga (límite estricto 50% para quadratic probing)
        if self.tamaño / self.capacidad >= 0.5:
            self._redimensionar()

        idx_base = self._hash(clave)
        i = 0
        idx_insertar = None

        # Bucle de exploración
        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]

            if estado == self.VACIO:
                # Si encontramos un vacío y no vimos un ELIMINADO antes, insertamos aquí
                if idx_insertar is None:
                    idx_insertar = idx_actual
                break
            
            elif estado == self.OCUPADO and c == clave:
                # Sub-caso: La clave ya existe, solo actualizamos los adyacentes
                self.tabla[idx_actual][2] = valor
                return
            
            elif estado == self.ELIMINADO and idx_insertar is None:
                # Guardamos la primera "tumba" que vemos para reutilizarla, 
                # pero seguimos buscando por si la clave ya existe más adelante
                idx_insertar = idx_actual
            
            i += 1

        # Inserción final en el índice determinado
        self.tabla[idx_insertar] = [self.OCUPADO, clave, valor]
        self.tamaño += 1

    def buscar(self, clave):
        # Paso 5: Búsqueda
        idx_base = self._hash(clave)
        i = 0

        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]

            if estado == self.VACIO:
                # Si topamos con un vacío, la clave definitivamente no está
                return None
            
            elif estado == self.OCUPADO and c == clave:
                # Encontramos el elemento, retornamos su lista de adyacentes
                return v
            
            # Si el estado es ELIMINADO o es OCUPADO pero con otra clave, seguimos iterando
            i += 1

    def eliminar(self, clave):
        # Paso 6: Eliminación Lógica
        idx_base = self._hash(clave)
        i = 0

        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]

            if estado == self.VACIO:
                return False # No se encontró la clave
            
            elif estado == self.OCUPADO and c == clave:
                # Marcamos como tumba, borramos los datos para liberar memoria y restamos tamaño
                self.tabla[idx_actual] = [self.ELIMINADO, None, None]
                self.tamaño -= 1
                return True
            
            i += 1

    def _redimensionar(self):
        # Paso 7: Rehashing
        capacidad_antigua = self.capacidad
        tabla_antigua = self.tabla

        # Doblamos la capacidad y buscamos el siguiente número primo
        self.capacidad = self._siguiente_primo(capacidad_antigua * 2)
        self.tamaño = 0
        self.tabla = [[self.VACIO, None, None] for _ in range(self.capacidad)]

        # Re-insertar todos los elementos ocupados en la nueva tabla
        for estado, clave, valor in tabla_antigua:
            if estado == self.OCUPADO:
                self.insertar(clave, valor)

    # --- Funciones Auxiliares Matemáticas ---
    def _es_primo(self, n):
        if n <= 1: return False
        if n <= 3: return True
        if n % 2 == 0 or n % 3 == 0: return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _siguiente_primo(self, n):
        if n <= 2:
            return 2
        primo = n if n % 2 != 0 else n + 1
        while not self._es_primo(primo):
            primo += 2
        return primo

    def imprimir_lista_adyacencia(grafo_hash):
        """
        Imprime por consola la lista de adyacencia almacenada en la Tabla Hash.
        Útil para testear que los parsers cargaron los datos correctamente.
        """
        print("\n--- Lista de Adyacencia (Grafo en Memoria) ---")
        
        # Verificamos si el grafo está vacío
        if grafo_hash.tamaño == 0:
            print("El grafo está vacío.")
            print("----------------------------------------------\n")
            return

        # Iteramos sobre el arreglo interno de la tabla hash
        for celda in grafo_hash.tabla:
            estado = celda[0]
            clave = celda[1]
            adyacentes = celda[2]
            
            # Solo imprimimos si la celda está ocupada con datos válidos
            if estado == grafo_hash.OCUPADO:
                print(f"[{clave}] -> {adyacentes}")
                
        print("----------------------------------------------\n")