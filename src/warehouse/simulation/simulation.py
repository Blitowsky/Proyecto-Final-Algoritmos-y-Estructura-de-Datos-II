from warehouse.domain.picker import Picker
from warehouse.services.assignment_lifecycle import finish_assignment, start_assignment
from warehouse.structures.dictionary import Dictionary, insert

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment

from warehouse.services.wave_assignment import assign_wave, free_pickers

from warehouse.simulation.walker import Walker
from warehouse.simulation.events import Event
from warehouse.simulation.conflicts import Move, resolve
from warehouse.simulation.rerouting import free_neighbor, reroute_around
from warehouse.structures.linkedlist import length

class Record:
    def __init__(self, walker: Walker, end_tick: int, steps: int) -> None:
        assignment: Assignment = walker.assignment
        self.picker: str = walker.picker.id
        self.wave: str = assignment.wave.id
        self.start_tick: int = walker.start_tick if walker.start_tick else -1
        self.end_tick: int = end_tick
        
        self.planned_distance: float = assignment.route.distance if assignment.route else -1
        self.steps: int = steps
        self.waits: int = walker.waits
        self.reroutes: int = walker.reroutes
        self.side_steps: int = walker.side_steps

    @property
    def ticks(self) -> int:
        return self.end_tick - self.start_tick + 1 if self.start_tick >= 0 else -1

class Simulation:
    def __init__(
        self,
        warehouse: WareHouse,
        algorithm: str = "bfs",
        stop_orderer = None,
        patience: int = 3,
        max_ticks: int = 100000,
        auto_assign: bool = False
    ) -> None:
        if patience < 1:
            raise ValueError("La paciencia debe ser al menos 1.")
        self.warehouse: WareHouse = warehouse
        self.algorithm: str = algorithm
        self.stop_orderer = stop_orderer
        self.patience: int = patience
        self.max_ticks: int = max_ticks
        self.auto_assign: bool = auto_assign

        self.tick: int = 0
        self.events: list[Event] = []
        self.walkers: list[Walker] = []
        self.records: list[Record] = []
        self._asked_to_step_aside: list[tuple[str|None, str|None]] = []

    @property
    def finished(self) -> bool:
        if len(self.walkers) > 0:
            return False
        picker = self.warehouse.pickers.head
        while picker is not None:
            if (picker.value is not None and
                picker.value.assignment is not None and
                picker.value.assignment.status == "assigned"):
                return False
            picker = picker.nextNode
        if self.auto_assign:
            wave = self.warehouse.waves.head
            while wave is not None:
                if wave.value is not None and wave.value.status == "created":
                    return False
                wave = wave.nextNode
        return True

    def run(self) -> list[Event]:
        while not self.finished:
            if self.tick >= self.max_ticks:
                raise Exception(self._stuck_message())
            self.step()
        return self.events

    def step(self) -> list[Event]:
        self.tick += 1
        out = []
        warehouse = self.warehouse

        if self.auto_assign:
            self._assign_created_waves()
        self._start_assigned(out)

        size = warehouse.width * warehouse.height
        occupied = Dictionary(size)
        standing = []
        picker = self.warehouse.pickers.head
        while picker is not None:
            if picker.value is not None:
                insert(occupied, picker.value.id, picker.value.node)
                standing.append((picker.value.id, picker.value.node))
            picker = picker.nextNode

        moves = []
        acting = []
        claimed = Dictionary(size)
        for walker in self.walkers:
            kind, cell = walker.peek()
            cell = cell if cell is not None else walker.picker.node
            if kind == "move":
                moves.append(Move(
                    walker.picker.id,
                    walker.picker.node,
                    cell,
                    self._rank(walker.picker.id)
                ))
                insert(claimed, True, cell)
            elif kind == "act":
                acting.append(walker)

        stepping_aside = []
        for picker_id, in_the_way_of in self._asked_to_step_aside:
            if picker_id is None or in_the_way_of is None:
                continue

            picker = self._picker(picker_id)
            cell = free_neighbor(
                warehouse,
                picker.node,
                occupied,
                claimed,
                self._path_cells(in_the_way_of)
            )
            if cell is None:
                continue

            moves = [m for m in moves if m.picker != picker_id]
            acting = [w for w in acting if w.picker.id != picker_id]
            moves.append(Move(
                picker_id,
                picker.node,
                cell,
                (2, 0, str(picker_id))
            ))
            insert(claimed, True, cell)
            stepping_aside.append(picker_id)
        self._asked_to_step_aside = []

        resolve(size, standing, moves)

        for move in moves:
            walker = self._walker(move.picker)
            if move.picker in stepping_aside:
                if move.granted:
                    self._picker(move.picker).move_to(move.dst, self.warehouse)
                    if walker is not None:
                        walker.side_steps += 1
                    out.append(Event(
                        self.tick,
                        move.picker,
                        "side_step",
                        move.src,
                        move.dst,
                        "dio un paso a un lado"
                    ))
                continue

            if walker and move.granted:
                walker.step_to(move.dst)
                out.append(Event(
                    self.tick,
                    move.picker,
                    "move",
                    move.src,
                    move.dst
                ))

        for walker in acting:
            self._do_action(walker, out)

        rerouting = []
        for first_pass in (True, False):
            for move in moves:
                if (move.granted or
                    move.picker in stepping_aside or
                    (move.reason == "head_on") != first_pass
                ):
                    continue
                refused_walker = self._walker(move.picker)
                if refused_walker:
                    self._refused(refused_walker, move, out, rerouting)

        for walker in list(self.walkers):
            if walker.done:
                self._finish(walker, out)

        self.events.extend(out)
        return out

    def _assign_created_waves(self) -> None:
        wave = self.warehouse.waves.head
        while wave is not None:
            if wave.value is None or wave.value.status != "created":
                wave = wave.nextNode
                continue
            free_picks = free_pickers(self.warehouse)
            if len(free_picks) == 0:
                return
            try:
                assign_wave(self.warehouse, wave.value, None, self.algorithm)
            except ValueError:
                if len(self.walkers) == 0 and len(free_picks) == length(self.warehouse.pickers):
                    raise
            wave = wave.nextNode

    def _start_assigned(self, out: list[Event]) -> None:
        p = self.warehouse.pickers.head
        while p is not None:
            if p.value is None:
                p = p.nextNode
                continue
            picker = p.value
            assignment = picker.assignment
            if assignment is None or assignment.status != "assigned":
                p = p.nextNode
                continue
            route = start_assignment(
                self.warehouse,
                assignment,
                self.stop_orderer,
                self.algorithm
            )
            walker = Walker(self.warehouse, assignment, self.algorithm)
            walker.start_tick = self.tick
            self.walkers.append(walker)
            stops = 0
            leg = route.legs.head
            while leg is not None:
                if leg.value is not None and leg.value.kind == "pick":
                    stops += 1
                leg = leg.nextNode
            out.append(Event(
                self.tick,
                picker.id,
                "start",
                picker.node,
                None,
                f"Wave {assignment.wave.id}; {stops} paradas; distancia planeada {route.distance}; zona {assignment.zone.id}."
            ))
            p = p.nextNode

    def _do_action(self, walker: Walker, out: list[Event]) -> None:
        picker = walker.picker
        current = picker.node
        leg = walker.act()
        if leg is None:
            return
        if leg.kind == "pick":
            parts = []
            item = leg.items.head
            while item is not None:
                if item.value is not None:
                    parts.append(f"{item.value.product.id} x{item.value.qty}")
                item = item.nextNode
            out.append(Event(
                self.tick,
                picker.id,
                "pick",
                current,
                None,
                ", ".join(parts)
            ))
        else:
            weight = 0.0
            count = 0
            item = leg.items.head
            while item is not None:
                if item.value is not None:
                    weight += item.value.weight
                    count += 1
                item = item.nextNode
            out.append(Event(
                self.tick,
                picker.id,
                "drop",
                current,
                None,
                f"{count} productos, {round(weight, 3)}kg"
            ))

    def _refused(
        self,
        walker: Walker,
        move: Move,
        out: list[Event],
        rerouting: list[str]
    ) -> None:
        warehouse = self.warehouse
        walker.refused(move.blocker)
        out.append(Event(
            self.tick,
            move.picker,
            "wait",
            move.src,
            None,
            f"bloqueado por {move.blocker} ({move.reason})"
        ))
        
        if move.reason == "head_on":
            extra = reroute_around(
                    warehouse,
                    walker,
                    move.dst,
                    self._cells_of_others(move.picker),
                )
            if extra is not None:
                rerouting.append(move.picker)
                out.append(Event(
                    self.tick,
                    move.picker,
                    "reroute",
                    move.src,
                    None,
                    f"se topa con {move.blocker}, alrededor de {_xy(warehouse, move.dst)} ({_signed(extra)} pasos)."
                ))
            else:
                self._ask_to_step_aside(move.picker, move.blocker)
            return

        limit = self.patience
        if move.blocker and self._walker(move.blocker) is None:
            self._ask_to_step_aside(move.blocker, move.picker)
            limit = max(self.patience, 2)

        if walker.waited >= limit and move.blocker not in rerouting:
            extra = reroute_around(
                    warehouse,
                    walker,
                    move.dst,
                    self._cells_of_others(move.picker)
                )
            if extra is not None:
                rerouting.append(move.picker)
                out.append(Event(
                    self.tick,
                    move.picker,
                    "reroute",
                    move.src,
                    None,
                    f"esperó {self.patience} ticks, alrededor de {_xy(warehouse, move.dst)} ({_signed(extra)} pasos)."
                ))
            else:
                walker.waited = 0

    def _finish(self, walker: Walker, out: list[Event]) -> None:
        picker = walker.picker
        assignment = walker.assignment
        record = Record(
                walker,
                self.tick,
                picker.distance - walker.distance_at_start
            )
        finish_assignment(assignment)
        self.walkers.remove(walker)
        self.records.append(record)
        out.append(Event(
            self.tick,
            picker.id,
            "finish",
            picker.node,
            None,
            f"Wave {assignment.wave.id}: " +
            f"{record.steps} pasos dados ({record.planned_distance} planeados), " +
            f"{record.waits} esperas, {record.reroutes} reenrutamientos, {record.side_steps} pasos al costado."
        ))

    def _ask_to_step_aside(self, picker_id: str|None, in_the_way_of: str|None):
        for asked, _ in self._asked_to_step_aside:
            if asked == picker_id:
                return
        self._asked_to_step_aside.append((picker_id, in_the_way_of))

    def _path_cells(self, picker_id: str) -> Dictionary:
        cells = Dictionary(self.warehouse.width * self.warehouse.height)
        walker = self._walker(picker_id)
        if walker is not None:
            for i in range(walker.index, len(walker.path)):
                insert(cells, True, walker.path[i])
            for leg in walker.legs[walker.leg_index +1:]:
                cell = leg.path.head
                while cell is not None:
                    if cell.value is not None:
                        insert(cells, True, cell.value)
                    cell = cell.nextNode
        return cells

    def _cells_of_others(self, picker_id: str) -> list[int]:
        cells = []
        picker = self.warehouse.pickers.head
        while picker is not None:
            if picker.value is not None and picker.value.id != picker_id:
                cells.append(picker.value.node)
            picker = picker.nextNode
        return cells

    def _picker(self, picker_id: str) -> Picker:
        picker = self.warehouse.pickers.head
        while picker is not None:
            if picker.value is not None and picker.value.id == picker_id:
                return picker.value
            picker = picker.nextNode
        raise ValueError(f"No existe el picker {picker_id}.")
        
    def _walker(self, picker_id: str) -> Walker|None:
        for walker in self.walkers:
            if walker.picker.id == picker_id:
                return walker
        return None
        
    def _rank(self, picker_id: str) -> tuple[int, int, str]:
        walker = self._walker(picker_id)
        if walker is None:
            return (1, 0, str(picker_id))
        return (0, -walker.assignment.wave.top_priority, str(picker_id))

    def _stuck_message(self) -> str:
        text = f"La simulación no terminó después de {self.tick} ticks."
        for walker in self.walkers:
            text += f" {walker.picker.id} en {_xy(self.warehouse, walker.picker.node)}"
            if walker.waiting_for is not None:
                text += f" está esperando por {walker.waiting_for} (hace {walker.waited} ticks)."
        return text

    def summary(self) -> dict:
        total = {
            "ticks": self.tick,
            "assignments": 0,
            "planned_distance": 0.0,
            "steps": 0,
            "waits": 0,
            "reroutes": 0,
            "side_steps": 0
        }

        for record in self.records:
            total["assignments"] += 1
            total["planned_distance"] += record.planned_distance
            total["steps"] += record.steps
        for event in self.events:
            if event.kind == "wait":
                total["waits"] += 1
            elif event.kind == "reroute":
                total["reroutes"] += 1
            elif event.kind == "side_step":
                total["side_steps"] += 1
        return total


def _xy(warehouse: WareHouse, cell: int) -> str:
    x, y = warehouse.node_xy(cell)
    return f"<{x}, {y}>"

def _signed(number: int) -> str:
    return ("+" if number > 0 else "") + str(number)
