import warehouse.structures.linkedlist as lk
import math

class Dictionary:
    def __init__(self, m: int) -> None:
        self.m = m
        self.dictionary = [lk.LinkedList() for i in range(m)]

    def hash_func(self, value) -> int:
        def to_key(value) -> int:
            s = str(value)
            return int(s) if s.isdigit() else sum(ord(ch) for ch in s)
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
def insert(D: Dictionary, value, key = None) -> Dictionary:
    key = key if key is not None else value

    def to_key(value) -> int:
        s = str(value)
        return int(s) if s.isdigit() else sum(ord(ch) for ch in s)

    hashed_key = D.hash_func(key)
    lk.add(D.dictionary[hashed_key], (to_key(key), value))
    return D

def search(D: Dictionary, value, key = None):
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

def delete(D: Dictionary, key: int, value = None) -> Dictionary:
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

