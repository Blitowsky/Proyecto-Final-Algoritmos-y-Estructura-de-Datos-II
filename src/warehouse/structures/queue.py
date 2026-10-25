class _Node:
    def __init__(self, value) -> None:
        self.value = value
        self.nextNode: _Node|None = None

class Queue:
    def __init__(self) -> None:
        self.head: _Node|None = None
        self.tail: _Node|None = None
        self.size: int = 0

    def is_empty(self) -> bool:
        return self.head is None

    def enqueue(self, value) -> None:
        node = _Node(value)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            self.tail.nextNode = node
            self.tail = node
        self.size += 1

    def dequeue(self):
        if self.head is None:
            raise IndexError("dequeue from an empty queue")
        node = self.head
        self.head = node.nextNode
        if self.head is None:
            self.tail = None
        self.size -= 1
        return node.value
