import NumPy as np
import math 

class HashTable:

    VACIO = 0
    OCUPADO = 1
    ELIMINADO = 2


    def __init__(self, size):
        self.size = size    
        self.table = [[self.VACIO,None,None] for _ in range(size)]
    
    def _hash(self, key):
        k = abs(hash(key))
        A = (math.sqrt(5) - 1) / 2
        return math.floor(self.size * ((k * A) % 1))

    def insert(self, key, value):
        hash_index = self._hash(key)
