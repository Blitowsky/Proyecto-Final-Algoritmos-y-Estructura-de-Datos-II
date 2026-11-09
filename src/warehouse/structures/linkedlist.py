class LinkedList:
    def __init__(self):
        self.head: Node|None = None
        self.tail: Node|None = None
    
    def __getstate__(self):
        valores = []
        actual = self.head

        while actual is not None:
            valores.append(actual.value)
            actual = actual.nextNode

        return valores

    def __setstate__(self, valores):
        self.head = None
        self.tail = None

        for valor in valores:
            add(self, valor)


    def __iter__(self):
        current = self.head
        while current is not None:
            yield current.value
            current = current.nextNode

    def print_list(self):
        current = self.head
        while current is not None:
            print(current.value, end=" -> ")
            current = current.nextNode
        print("None")
    


class Node:
    def __init__(self, value=None):
        self.value = value
        self.nextNode: Node|None = None

def add(L: LinkedList, element) -> None:
    currentNode = Node()
    currentNode.value = element

    if L.head is None:
        L.head = currentNode
        L.tail = currentNode
    else:
        L.tail.nextNode = currentNode
        L.tail = currentNode



def search(L: LinkedList,element):
    currentNode = L.head
    position = 0

    while currentNode:
        if currentNode.value == element:
            return position
        
        currentNode = currentNode.nextNode
        position +=1

    return None


def insert(L:LinkedList, element, position: int):
    if position <= length(L) and position > 0:
        currentNode = L.head
        k = 0
        while currentNode != None and  k < position - 1:
            currentNode = currentNode.nextNode
            k+=1
        nodo = Node()
        nodo.value = element
        nodo.nextNode = currentNode.nextNode
        currentNode.nextNode = nodo
        return position  
    elif position == 0:
        add(L, element)
        return 0
    else:
        return None
    
def delete(L: LinkedList, element) -> int | None:
    position = 0
    currentNode = L.head
    for i in range(length(L)):
        if element == currentNode.value:
            currentNode.value = None
            if i == 0:
                L.head = currentNode.nextNode
            elif (i == length(L)-1):
                lNode.nextNode = None
            else:
                lNode.nextNode = currentNode.nextNode
            return position
        else:
            position += 1
            lNode = currentNode
            currentNode = currentNode.nextNode
    return None
    

def length(L: LinkedList) -> int:
    currentNode = L.head
    len = 0
    while currentNode:
        len += 1
        currentNode = currentNode.nextNode
    return len


def access(L: LinkedList, position: int):
    currentNode = L.head
    element = None
    counter = 0
    while currentNode != None:
        if counter == position:
            element = currentNode.value
            break
        currentNode = currentNode.nextNode
        counter += 1
    return element


def update(L: LinkedList, element, position: int) -> int | None:
    currentNode = L.head
    if position >= length(L):
        return None
    else:
        for i in range(0, position):
            currentNode = currentNode.nextNode
        currentNode.value = element
        return position


def print_list(L):
    currentNode = L.head
    while currentNode:
        print(currentNode.value, end = " ")
        currentNode = currentNode.nextNode
    print("")
    return

