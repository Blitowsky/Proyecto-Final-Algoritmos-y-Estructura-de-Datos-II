import warehouse.structures.linkedlist as lk
import math

class CloseDictionary:
    def __init__(self, m: int) -> None:
        self.m = m
        self.dictionary = [lk.LinkedList() for i in range(m)]

    def hash_func(self, value) -> int:
        def to_key(value) -> int:
            s = str(value)
            if s.isdigit():
                return value
            hash_value = 5381
            for char in s:
                hash_value = (hash_value * 33) + ord(char)
            return hash_value
        return to_key(value) % self.m

    def printDict(self) -> None:
        d = self.dictionary
        for i, curr in enumerate(d):
            print(f"[{i}]", end=" ")
            current = curr.head
            while current is not None:
                entry = current.value
                print(entry, end=" -> ")
                current = current.nextNode
            print("None")

    # Ejercicio 2
    def insert(D: CloseDictionary, value, key = None) -> CloseDictionary:
        key = key if key is not None else value

        def to_key(value) -> int:
            s = str(value)
            return int(s) if s.isdigit() else sum(ord(ch) for ch in s)

        hashed_key = D.hash_func(key)
        lk.add(D.dictionary[hashed_key], (to_key(key), value))
        return D

    def search(D: CloseDictionary, value, key = None):
        key = key if key is not None else value

        def to_key(value) -> int:
            s = str(value)
            return int(s) if s.isdigit() else sum(ord(ch) for ch in s)

        hashed_key = D.hash_func(key)
        current = D.dictionary[hashed_key].head
        while current is not None:
            if current.value:
                if current.value[0] == to_key(key):
                    return current.value[1]
            current = current.nextNode

        return None

    def delete(D: CloseDictionary, key: int, value = None) -> CloseDictionary:
        hashed_key = D.hash_func(key)
        col_list = D.dictionary[hashed_key]
        current = col_list.head
        while current is not None:
            if current.value:
                if value is not None :
                    if current.value[1] == value:
                        lk.delete(col_list, current.value)
                        break
                else:
                    if current.value[0] == key:
                        lk.delete(col_list, current.value)
                        break
            current = current.nextNode
        
        return D


class OpenDictionary:
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
        if self.tamaño / self.capacidad >= 0.5:
            self._redimensionar()

        idx_base = self._hash(clave)
        i = 0
        idx_insertar = None

        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]

            if estado == self.VACIO:
                if idx_insertar is None:
                    idx_insertar = idx_actual
                break
            elif estado == self.OCUPADO and c == clave:
                self.tabla[idx_actual][2] = valor
                return
            elif estado == self.ELIMINADO and idx_insertar is None:
                idx_insertar = idx_actual
            i += 1

        self.tabla[idx_insertar] = [self.OCUPADO, clave, valor]
        self.tamaño += 1

    def buscar(self, clave):
        idx_base = self._hash(clave)
        i = 0
        while True:
            idx_actual = (idx_base + i**2) % self.capacidad
            estado, c, v = self.tabla[idx_actual]
            if estado == self.VACIO:
                return None
            elif estado == self.OCUPADO and c == clave:
                return v
            i += 1

    def obtener_elementos(self):
        """Retorna una lista de tuplas (clave, valor) de todos los nodos activos."""
        elementos = []
        for estado, clave, valor in self.tabla:
            if estado == self.OCUPADO:
                elementos.append((clave, valor))
        return elementos

    def _redimensionar(self):
        tabla_antigua = self.tabla
        self.capacidad = self._siguiente_primo(self.capacidad * 2)
        self.tamaño = 0
        self.tabla = [[self.VACIO, None, None] for _ in range(self.capacidad)]
        for estado, clave, valor in tabla_antigua:
            if estado == self.OCUPADO:
                self.insertar(clave, valor)

    def _es_primo(self, n):
        if n <= 1: return False
        if n <= 3: return True
        if n % 2 == 0 or n % 3 == 0: return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0: return False
            i += 6
        return True

    def _siguiente_primo(self, n):
        if n <= 2: return 2
        primo = n if n % 2 != 0 else n + 1
        while not self._es_primo(primo):
            primo += 2
        return primo