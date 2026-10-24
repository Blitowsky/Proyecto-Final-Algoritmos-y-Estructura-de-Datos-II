import warehouse.structures.linkedlist as lk

def enqueue(Q, element):
    lk.add(Q, element)

def dequeue(Q):
    element = Q.head.value
    lk.delete(Q, Q.head.value)
    return element
