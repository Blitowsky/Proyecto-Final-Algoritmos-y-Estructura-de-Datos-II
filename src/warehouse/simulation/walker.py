from warehouse.algorithms.pathfinding import find_path
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.picker import Picker
from warehouse.domain.route import Leg
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment

from warehouse.services.route_runner import perform_leg_action


class Walker:
    def __init__(self, warehouse: WareHouse, assignment: Assignment, algorithm: str = "bfs") -> None:
        self.warehouse: WareHouse = warehouse
        self.assignment: Assignment = assignment
        self.picker: Picker = assignment.picker
        self.algorithm: str = algorithm

        self.legs: list[Leg] = []
        leg = assignment.route.legs.head if assignment.route else None
        while leg is not None:
            if leg.value is not None:
                self.legs.append(leg.value)
            leg = leg.nextNode

        self.leg_index: int = -1
        self.leg: Leg|None = None
        self.path: list[int] = []
        self.index: int = 0
        self.done: bool = False

        self.start_tick: int|None = None
        self.distance_at_start: int = self.picker.distance
        self.waited: int = 0
        self.waiting_for: int|None = None

        self.moves: int = 0
        self.waits: int = 0
        self.reroutes: int = 0
        self.side_steps: int = 0
        self.replans: int = 0
        self.actions: int = 0

        self._enter_next_leg()

    def peek(self) -> tuple[str, int|None]:
        while not self.done:
            self._sync()
            if self.index < len(self.path) - 1:
                return "move", self.path[self.index + 1]
            if self.leg is not None and self.leg.kind in ("pick", "return"):
                return "act", None
            self._enter_next_leg()
        return "done", None

    def goal_cells(self) -> LinkedList|None:
        if self.leg is None:
            return None
        if self.leg.kind == "pick" and self.leg.stop:
            return self.leg.stop.cells
        if self.leg.kind in ("approach", "return"):
            return self.assignment.zone.access
        return None

    def step_to(self, cell: int) -> None:
        if self.path[self.index + 1] != cell:
            raise ValueError(f"El picker {self.picker.id} no debía ir a la celda {cell}.")
        self.picker.move_to(cell, self.warehouse)
        self.index += 1
        self.moves += 1
        self.waited = 0
        self.waiting_for = None

    def act(self) -> Leg|None:
        leg = self.leg
        if leg is None:
            return None
        perform_leg_action(self.picker, self.warehouse, leg)
        self.actions += 1
        self.waited = 0
        self.waiting_for = None
        self._enter_next_leg()
        return leg

    def refused(self, blocker: int) -> None:
        self.waits += 1
        self.waited += 1
        self.waiting_for = blocker

    def reroute(self, path: list[int]) -> None:
        self.path = path
        self.index = 0
        self.reroutes += 1
        self.waited = 0

    def _enter_next_leg(self) -> None:
        self.leg_index += 1
        if self.leg_index >= len(self.legs):
            self.done = True
            self.leg = None
            self.path = []
            self.index = 0
            return
        self.leg = self.legs[self.leg_index]
        self.path = []
        cell = self.leg.path.head
        while cell is not None:
            if cell.value is not None:
                self.path.append(cell.value)
            cell = cell.nextNode
        self.index = 0

    def _sync(self) -> None:
        if self.path[self.index] == self.picker.node:
            return
        goal = self.goal_cells()
        if goal is None:
            goal = LinkedList()
            if self.leg:
                add(goal, self.leg.end)
            else:
                raise ValueError(f"El picker {self.picker.id} no tiene un camino con el cual sincronizarse.")
        found = find_path(self.warehouse, self.picker.node, goal, self.algorithm)
        if found is None:
            raise ValueError(f"El picker {self.picker.id} no puede alcanzar su objetivo desde la celda {self.picker.node}.")
        self.path = []
        cell = found.path.head
        while cell is not None:
            if cell.value is not None:
                self.path.append(cell.value)
            cell = cell.nextNode
        self.index = 0
        self.replans += 1

    @property
    def remaining_steps(self) -> int:
        return len(self.path) - 1 - self.index
