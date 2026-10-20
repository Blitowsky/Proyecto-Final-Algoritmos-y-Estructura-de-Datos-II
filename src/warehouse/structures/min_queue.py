class MinQueue:
    def __init__(self) -> None:
        self._heap: list = []
        self._counter: int = 0

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def push(self, priority: int, item) -> None:
        self._heap.append((priority, self._counter, item))
        self._counter += 1
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> tuple:
        if not self._heap:
            raise IndexError("pop from an empty min-queue")
        top = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return top[0], top[2]

    @staticmethod
    def _less(a, b):
        return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1])

    def _sift_up(self, i):
        heap = self._heap
        while i > 0:
            parent = (i - 1) // 2
            if not self._less(heap[i], heap[parent]):
                break
            heap[i], heap[parent] = heap[parent], heap[i]
            i = parent

    def _sift_down(self, i):
        heap = self._heap
        n = len(heap)
        while True:
            left = 2 * i + 1
            right = left + 1
            smallest = i
            if left < n and self._less(heap[left], heap[smallest]):
                smallest = left
            if right < n and self._less(heap[right], heap[smallest]):
                smallest = right
            if smallest == i:
                break
            heap[i], heap[smallest] = heap[smallest], heap[i]
            i = smallest
