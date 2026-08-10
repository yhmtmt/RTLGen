"""Cycle-level model of the segmented 256-bit deterministic-XY 4x4 mesh."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable

MESH_X = 4
MESH_Y = 4
ENDPOINTS = MESH_X * MESH_Y
PORTS = 5
PORT_NORTH = 0
PORT_SOUTH = 1
PORT_EAST = 2
PORT_WEST = 3
PORT_LOCAL = 4
PORT_NAMES = ("north", "south", "east", "west", "local")
CONCEPTUAL_LINK_BITS = 2048
PHYSICAL_FLIT_BITS = 256
FLITS_PER_CONCEPTUAL_TRANSFER = CONCEPTUAL_LINK_BITS // PHYSICAL_FLIT_BITS
VIRTUAL_CHANNELS = 4
DEFAULT_FIFO_DEPTH = 4


def coordinates(endpoint: int) -> tuple[int, int]:
    if not 0 <= endpoint < ENDPOINTS:
        raise ValueError(f"endpoint must be in [0, {ENDPOINTS - 1}]")
    return endpoint % MESH_X, endpoint // MESH_X


def endpoint(x: int, y: int) -> int:
    if not (0 <= x < MESH_X and 0 <= y < MESH_Y):
        raise ValueError("coordinates are outside the 4x4 mesh")
    return y * MESH_X + x


def deterministic_xy_path(source: int, destination: int) -> tuple[int, ...]:
    x, y = coordinates(source)
    destination_x, destination_y = coordinates(destination)
    path = [source]
    while x != destination_x:
        x += 1 if destination_x > x else -1
        path.append(endpoint(x, y))
    while y != destination_y:
        y += 1 if destination_y > y else -1
        path.append(endpoint(x, y))
    return tuple(path)


def route_port(x_coord: int, y_coord: int, destination: int) -> int:
    destination_x, destination_y = coordinates(destination)
    if destination_x < x_coord:
        return PORT_WEST
    if destination_x > x_coord:
        return PORT_EAST
    if destination_y < y_coord:
        return PORT_NORTH
    if destination_y > y_coord:
        return PORT_SOUTH
    return PORT_LOCAL


def segmented_transfer(*, source: int, destination: int, tag: int, vc: int) -> tuple["ModelFlit", ...]:
    if not 0 <= vc < VIRTUAL_CHANNELS:
        raise ValueError("vc must be in [0, 3]")
    path = deterministic_xy_path(source, destination)
    return tuple(
        ModelFlit(
            source=source,
            destination=destination,
            tag=tag,
            fragment=fragment,
            last=fragment == FLITS_PER_CONCEPTUAL_TRANSFER - 1,
            vc=vc,
            data=(tag << 8) | fragment,
            path=path,
        )
        for fragment in range(FLITS_PER_CONCEPTUAL_TRANSFER)
    )


@dataclass(frozen=True)
class ModelFlit:
    source: int
    destination: int
    tag: int
    fragment: int
    last: bool
    vc: int
    data: int = 0
    path: tuple[int, ...] = ()


@dataclass(frozen=True)
class Flow:
    source: int
    destination: int
    flits: int
    tag: int
    vc: int


@dataclass(frozen=True)
class RouterCycleInput:
    valid: bool
    flit: ModelFlit | None = None


@dataclass(frozen=True)
class RouterCycleTrace:
    cycle: int
    accepted: tuple[int, ...]
    forwarded: tuple[tuple[int, ModelFlit], ...]
    input_stall: bool
    output_stall: bool
    contention: bool
    occupancy: int
    ready: tuple[bool, ...]


@dataclass(frozen=True)
class RouterSimulationResult:
    traces: tuple[RouterCycleTrace, ...]
    delivered: tuple[tuple[int, ModelFlit], ...]
    accepted_flit_count: int
    forwarded_flit_count: int
    input_stall_cycles: int
    output_stall_cycles: int
    arbitration_contention_cycles: int
    current_input_occupancy: int
    max_input_occupancy: int
    route_flit_count: tuple[int, ...]


@dataclass
class _RouterState:
    x_coord: int
    y_coord: int
    fifo_depth: int
    vc_count: int
    queues: list[deque[ModelFlit]] = field(default_factory=list)
    out_holding: list[ModelFlit | None] = field(default_factory=lambda: [None] * PORTS)
    rr_cursor: list[int] = field(default_factory=lambda: [0] * PORTS)
    accepted_flit_count: int = 0
    forwarded_flit_count: int = 0
    input_stall_cycles: int = 0
    output_stall_cycles: int = 0
    arbitration_contention_cycles: int = 0
    max_input_occupancy: int = 0
    route_flit_count: list[int] = field(default_factory=lambda: [0] * PORTS)

    def __post_init__(self) -> None:
        if not self.queues:
            self.queues = [deque() for _ in range(PORTS * self.vc_count)]

    def _input_index(self, port: int, vc: int) -> int:
        return port * self.vc_count + vc

    def _occupancy(self) -> int:
        return sum(len(queue) for queue in self.queues)

    def _input_ready(self, port: int, vc: int, will_pop: set[int]) -> bool:
        queue = self.queues[self._input_index(port, vc)]
        if len(queue) < self.fifo_depth:
            return True
        return self._input_index(port, vc) in will_pop

    def cycle(
        self,
        cycle: int,
        inputs: list[RouterCycleInput],
        out_ready: list[bool],
    ) -> RouterCycleTrace:
        candidate_counts = [0] * PORTS
        grants: list[tuple[int, ModelFlit] | None] = [None] * PORTS
        grant_indices: list[int | None] = [None] * PORTS
        for output_port in range(PORTS):
            for scan in range(PORTS * self.vc_count):
                index = (self.rr_cursor[output_port] + scan) % (PORTS * self.vc_count)
                queue = self.queues[index]
                if not queue:
                    continue
                flit = queue[0]
                if route_port(self.x_coord, self.y_coord, flit.destination) != output_port:
                    continue
                candidate_counts[output_port] += 1
                if grants[output_port] is None:
                    grants[output_port] = (index, flit)
                    grant_indices[output_port] = index

        input_stall = False
        output_stall = any(self.out_holding[port] is not None and not out_ready[port] for port in range(PORTS))
        contention = any(count > 1 for count in candidate_counts)
        if output_stall:
            self.output_stall_cycles += 1

        will_pop: set[int] = set()
        for output_port in range(PORTS):
            if (self.out_holding[output_port] is None or out_ready[output_port]) and grant_indices[output_port] is not None:
                will_pop.add(int(grant_indices[output_port]))

        ready = []
        accepted_ports: list[int] = []
        for port in range(PORTS):
            item = inputs[port]
            vc = 0 if item.flit is None else item.flit.vc
            port_ready = self._input_ready(port, vc, will_pop)
            ready.append(port_ready)
            if item.valid and not port_ready:
                input_stall = True
            if item.valid and port_ready and item.flit is not None:
                self.queues[self._input_index(port, item.flit.vc)].append(item.flit)
                self.accepted_flit_count += 1
                accepted_ports.append(port)
        if input_stall:
            self.input_stall_cycles += 1

        forwarded: list[tuple[int, ModelFlit]] = []
        for output_port in range(PORTS):
            held = self.out_holding[output_port]
            if held is not None and out_ready[output_port]:
                forwarded.append((output_port, held))
                self.forwarded_flit_count += 1
                self.route_flit_count[output_port] += 1

        for output_port in range(PORTS):
            can_replace = self.out_holding[output_port] is None or out_ready[output_port]
            if not can_replace:
                continue
            grant = grants[output_port]
            if grant is None:
                self.out_holding[output_port] = None
                continue
            queue_index, flit = grant
            queue = self.queues[queue_index]
            if queue:
                queue.popleft()
            self.out_holding[output_port] = flit
            self.rr_cursor[output_port] = (queue_index + 1) % (PORTS * self.vc_count)

        occupancy = self._occupancy()
        self.max_input_occupancy = max(self.max_input_occupancy, occupancy)
        if contention:
            self.arbitration_contention_cycles += 1

        return RouterCycleTrace(
            cycle=cycle,
            accepted=tuple(accepted_ports),
            forwarded=tuple(forwarded),
            input_stall=input_stall,
            output_stall=output_stall,
            contention=contention,
            occupancy=occupancy,
            ready=tuple(ready),
        )

    def snapshot(self, traces: list[RouterCycleTrace], delivered: list[tuple[int, ModelFlit]]) -> RouterSimulationResult:
        return RouterSimulationResult(
            traces=tuple(traces),
            delivered=tuple(delivered),
            accepted_flit_count=self.accepted_flit_count,
            forwarded_flit_count=self.forwarded_flit_count,
            input_stall_cycles=self.input_stall_cycles,
            output_stall_cycles=self.output_stall_cycles,
            arbitration_contention_cycles=self.arbitration_contention_cycles,
            current_input_occupancy=self._occupancy(),
            max_input_occupancy=self.max_input_occupancy,
            route_flit_count=tuple(self.route_flit_count),
        )


def simulate_router(
    *,
    x_coord: int,
    y_coord: int,
    input_schedule: list[list[RouterCycleInput]],
    out_ready_schedule: list[list[bool]],
    fifo_depth: int = DEFAULT_FIFO_DEPTH,
    vc_count: int = VIRTUAL_CHANNELS,
) -> RouterSimulationResult:
    if len(input_schedule) != len(out_ready_schedule):
        raise ValueError("input_schedule and out_ready_schedule must have the same length")
    state = _RouterState(x_coord=x_coord, y_coord=y_coord, fifo_depth=fifo_depth, vc_count=vc_count)
    traces: list[RouterCycleTrace] = []
    delivered: list[tuple[int, ModelFlit]] = []
    for cycle, (inputs, out_ready) in enumerate(zip(input_schedule, out_ready_schedule)):
        if len(inputs) != PORTS or len(out_ready) != PORTS:
            raise ValueError("each router cycle must provide five input slots and five ready bits")
        trace = state.cycle(cycle, inputs, out_ready)
        traces.append(trace)
        delivered.extend(trace.forwarded)
    return state.snapshot(traces, delivered)


def simulate_mesh(
    *,
    source: int,
    destination: int,
    tag: int,
    vc: int,
    max_cycles: int = 256,
) -> dict[str, object]:
    path = deterministic_xy_path(source, destination)
    hops = len(path) - 1
    transfers = segmented_transfer(source=source, destination=destination, tag=tag, vc=vc)
    delivered = []
    for fragment, flit in enumerate(transfers):
        delivery_cycle = 2 * hops + 2 + fragment
        delivered.append(
            {
                "cycle": delivery_cycle,
                "source": flit.source,
                "destination": flit.destination,
                "tag": flit.tag,
                "fragment": flit.fragment,
                "last": flit.last,
                "vc": flit.vc,
                "path": path,
            }
        )
    total_cycles = delivered[-1]["cycle"] + 1 if delivered else 0
    if total_cycles > max_cycles:
        raise RuntimeError("mesh model did not drain within max_cycles")
    link_flits: dict[tuple[int, int], int] = defaultdict(int)
    for left, right in zip(path[:-1], path[1:]):
        link_flits[(left, right)] = FLITS_PER_CONCEPTUAL_TRANSFER
    return {
        "cycles": total_cycles,
        "path": path,
        "delivered": tuple(delivered),
        "directed_link_flits": dict(link_flits),
        "contention_cycles": 0,
        "serialization_flits": FLITS_PER_CONCEPTUAL_TRANSFER,
    }


def simulate(flows: Iterable[Flow], *, max_cycles: int = 10000) -> dict[str, object]:
    flow_list = list(flows)
    if len(flow_list) != 1:
        raise ValueError("simulate currently models one routed flow at a time")
    flow = flow_list[0]
    if flow.flits != FLITS_PER_CONCEPTUAL_TRANSFER:
        raise ValueError(
            f"simulate expects {FLITS_PER_CONCEPTUAL_TRANSFER} serialized flits per conceptual transfer"
        )
    return simulate_mesh(
        source=flow.source,
        destination=flow.destination,
        tag=flow.tag,
        vc=flow.vc,
        max_cycles=max_cycles,
    )


def mapping_report() -> dict[str, int | str]:
    return {
        "conceptual_transfer_bits": CONCEPTUAL_LINK_BITS,
        "physical_flit_bits": PHYSICAL_FLIT_BITS,
        "serialized_flits_per_conceptual_transfer": FLITS_PER_CONCEPTUAL_TRANSFER,
        "physical_payload_bytes_per_flit": PHYSICAL_FLIT_BITS // 8,
        "conceptual_payload_bytes": CONCEPTUAL_LINK_BITS // 8,
        "serialization_efficiency_payload_only": "100%",
    }
