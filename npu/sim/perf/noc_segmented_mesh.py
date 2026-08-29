"""Cycle-level model of the segmented 256-bit deterministic-XY 4x4 mesh."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator

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
    label: str = ""


@dataclass(frozen=True)
class Flow:
    source: int
    destination: int
    flits: int
    tag: int
    vc: int
    release_cycle: int = 0


@dataclass(frozen=True)
class ScheduledFlit:
    release_cycle: int
    flit: ModelFlit
    schedule_order: int = 0
    packet_order: int = 0


@dataclass(frozen=True)
class TrafficFlow:
    name: str
    source: int
    destination: int
    payload_bytes: int
    vc: int
    release_cycle: int = 0
    packet_payload_bytes: int = CONCEPTUAL_LINK_BITS // 8
    tag_base: int = 0
    data_seed: int = 0
    schedule_order: int = 0


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
    inputs: tuple[RouterCycleInput, ...] = ()
    out_ready: tuple[bool, ...] = ()


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


@dataclass(frozen=True)
class RouterReplayVerification:
    cycle_count: int
    accepted_flit_count: int
    forwarded_flit_count: int
    input_stall_cycles: int
    output_stall_cycles: int
    arbitration_contention_cycles: int
    current_input_occupancy: int
    max_input_occupancy: int
    route_flit_count: tuple[int, ...]


@dataclass(frozen=True)
class RouterPlan:
    grants: tuple[tuple[int, ModelFlit] | None, ...]
    grant_indices: tuple[int | None, ...]
    will_pop: tuple[int, ...]
    ready: tuple[bool, ...]
    input_stall: bool
    output_stall: bool
    contention: bool


@dataclass(frozen=True)
class MeshLinkTransfer:
    cycle: int
    source_node: int
    source_port: int
    destination_node: int
    destination_port: int
    flit: ModelFlit


@dataclass(frozen=True)
class MeshDelivery:
    cycle: int
    endpoint: int
    flit: ModelFlit


@dataclass(frozen=True)
class MeshCycleTrace:
    cycle: int
    router_traces: tuple[RouterCycleTrace, ...]
    injected: tuple[tuple[int, ModelFlit], ...]
    deliveries: tuple[MeshDelivery, ...]
    link_transfers: tuple[MeshLinkTransfer, ...]
    endpoint_in_ready: tuple[bool, ...]
    endpoint_out_ready: tuple[bool, ...]
    endpoint_input_stall: tuple[int, ...]


@dataclass(frozen=True)
class MeshSimulationResult:
    cycles: int
    traces: tuple[MeshCycleTrace, ...]
    deliveries: tuple[MeshDelivery, ...]
    link_transfers: tuple[MeshLinkTransfer, ...]
    router_summaries: tuple[RouterSimulationResult, ...]
    endpoint_injected_flit_count: int
    endpoint_input_stall_cycles: tuple[int, ...]
    max_endpoint_input_occupancy: int = 0
    max_endpoint_vc_occupancy: tuple[int, ...] = ()
    mesh_contention_cycles: int = 0


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

    def _input_ready(self, port: int, vc: int) -> bool:
        queue = self.queues[self._input_index(port, vc)]
        # Match the RTL's registered-occupancy credit boundary. A full FIFO
        # does not expose a combinational path from downstream ready to its
        # upstream sender, even when one entry will be popped this cycle.
        return len(queue) < self.fifo_depth

    def idle(self) -> bool:
        return self._occupancy() == 0 and all(flit is None for flit in self.out_holding)

    def compute_plan(
        self,
        inputs: list[RouterCycleInput],
        out_ready: list[bool],
    ) -> RouterPlan:
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

        output_stall = any(self.out_holding[port] is not None and not out_ready[port] for port in range(PORTS))
        contention = any(count > 1 for count in candidate_counts)

        will_pop: set[int] = set()
        for output_port in range(PORTS):
            if (self.out_holding[output_port] is None or out_ready[output_port]) and grant_indices[output_port] is not None:
                will_pop.add(int(grant_indices[output_port]))

        ready = []
        input_stall = False
        for port in range(PORTS):
            item = inputs[port]
            vc = 0 if item.flit is None else item.flit.vc
            port_ready = self._input_ready(port, vc)
            ready.append(port_ready)
            if item.valid and not port_ready:
                input_stall = True

        return RouterPlan(
            grants=tuple(grants),
            grant_indices=tuple(grant_indices),
            will_pop=tuple(sorted(will_pop)),
            ready=tuple(ready),
            input_stall=input_stall,
            output_stall=output_stall,
            contention=contention,
        )

    def apply_plan(
        self,
        cycle: int,
        inputs: list[RouterCycleInput],
        out_ready: list[bool],
        plan: RouterPlan,
        *,
        capture_replay_signals: bool = True,
    ) -> RouterCycleTrace:
        accepted_ports: list[int] = []
        for port in range(PORTS):
            item = inputs[port]
            if item.valid and plan.ready[port] and item.flit is not None:
                self.queues[self._input_index(port, item.flit.vc)].append(item.flit)
                self.accepted_flit_count += 1
                accepted_ports.append(port)

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
            grant = plan.grants[output_port]
            if grant is None:
                self.out_holding[output_port] = None
                continue
            queue_index, flit = grant
            queue = self.queues[queue_index]
            if queue:
                queue.popleft()
            self.out_holding[output_port] = flit
            self.rr_cursor[output_port] = (queue_index + 1) % (PORTS * self.vc_count)

        if plan.input_stall:
            self.input_stall_cycles += 1
        if plan.output_stall:
            self.output_stall_cycles += 1
        if plan.contention:
            self.arbitration_contention_cycles += 1

        occupancy = self._occupancy()
        self.max_input_occupancy = max(self.max_input_occupancy, occupancy)

        return RouterCycleTrace(
            cycle=cycle,
            accepted=tuple(accepted_ports),
            forwarded=tuple(forwarded),
            input_stall=plan.input_stall,
            output_stall=plan.output_stall,
            contention=plan.contention,
            occupancy=occupancy,
            ready=plan.ready,
            inputs=tuple(inputs) if capture_replay_signals else (),
            out_ready=tuple(out_ready) if capture_replay_signals else (),
        )

    def cycle(
        self,
        cycle: int,
        inputs: list[RouterCycleInput],
        out_ready: list[bool],
    ) -> RouterCycleTrace:
        plan = self.compute_plan(inputs, out_ready)
        return self.apply_plan(cycle, inputs, out_ready, plan)

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


def extract_router_replay_schedules(
    mesh_result: MeshSimulationResult,
    *,
    node: int,
) -> tuple[list[list[RouterCycleInput]], list[list[bool]]]:
    if not 0 <= node < ENDPOINTS:
        raise ValueError(f"node must be in [0, {ENDPOINTS - 1}]")
    traces_by_cycle: dict[int, RouterCycleTrace] = {}
    for mesh_trace in mesh_result.traces:
        if not 0 <= mesh_trace.cycle < mesh_result.cycles:
            raise ValueError("mesh trace cycle is outside the recorded simulation interval")
        if mesh_trace.cycle in traces_by_cycle:
            raise ValueError("mesh result contains duplicate cycle traces")
        traces_by_cycle[mesh_trace.cycle] = mesh_trace.router_traces[node]

    idle_inputs = [RouterCycleInput(False, None) for _ in range(PORTS)]
    ready_outputs = [True for _ in range(PORTS)]
    input_schedule: list[list[RouterCycleInput]] = []
    out_ready_schedule: list[list[bool]] = []
    for cycle in range(mesh_result.cycles):
        trace = traces_by_cycle.get(cycle)
        if trace is None:
            input_schedule.append(list(idle_inputs))
            out_ready_schedule.append(list(ready_outputs))
            continue
        if not trace.inputs or not trace.out_ready:
            raise ValueError(f"router replay signals were not captured for node {node}")
        if trace.cycle != cycle or len(trace.inputs) != PORTS or len(trace.out_ready) != PORTS:
            raise ValueError("router cycle trace is malformed")
        input_schedule.append(list(trace.inputs))
        out_ready_schedule.append(list(trace.out_ready))
    return input_schedule, out_ready_schedule


def iter_router_replay_cycles(
    mesh_result: MeshSimulationResult,
    *,
    node: int,
) -> Iterator[tuple[int, tuple[RouterCycleInput, ...], tuple[bool, ...], RouterCycleTrace | None]]:
    """Yield a complete replay stream without expanding fast-forwarded idle cycles in memory."""
    if not 0 <= node < ENDPOINTS:
        raise ValueError(f"node must be in [0, {ENDPOINTS - 1}]")
    recorded = iter(mesh_result.traces)
    mesh_trace = next(recorded, None)
    prior_cycle = -1
    idle_inputs = tuple(RouterCycleInput(False, None) for _ in range(PORTS))
    ready_outputs = tuple(True for _ in range(PORTS))
    for cycle in range(mesh_result.cycles):
        if mesh_trace is not None and mesh_trace.cycle < cycle:
            raise ValueError("mesh result contains duplicate or unordered cycle traces")
        if mesh_trace is None or mesh_trace.cycle != cycle:
            yield cycle, idle_inputs, ready_outputs, None
            continue
        if mesh_trace.cycle <= prior_cycle or not 0 <= mesh_trace.cycle < mesh_result.cycles:
            raise ValueError("mesh result contains duplicate, unordered, or out-of-range cycle traces")
        trace = mesh_trace.router_traces[node]
        if not trace.inputs or not trace.out_ready:
            raise ValueError(f"router replay signals were not captured for node {node}")
        if trace.cycle != cycle or len(trace.inputs) != PORTS or len(trace.out_ready) != PORTS:
            raise ValueError("router cycle trace is malformed")
        yield cycle, trace.inputs, trace.out_ready, trace
        prior_cycle = cycle
        mesh_trace = next(recorded, None)
    if mesh_trace is not None:
        raise ValueError("mesh trace cycle is outside the recorded simulation interval")


def verify_router_replay(mesh_result: MeshSimulationResult, *, node: int) -> RouterReplayVerification:
    """Replay one captured router cycle-by-cycle while retaining counters only."""
    x_coord, y_coord = coordinates(node)
    state = _RouterState(
        x_coord=x_coord,
        y_coord=y_coord,
        fifo_depth=DEFAULT_FIFO_DEPTH,
        vc_count=VIRTUAL_CHANNELS,
    )
    cycle_count = 0
    for cycle, inputs, out_ready, expected_trace in iter_router_replay_cycles(
        mesh_result,
        node=node,
    ):
        actual_trace = state.cycle(cycle, list(inputs), list(out_ready))
        if expected_trace is not None and actual_trace != expected_trace:
            raise ValueError(f"router replay diverged at node {node} cycle {cycle}")
        cycle_count += 1
    expected = mesh_result.router_summaries[node]
    observed = RouterReplayVerification(
        cycle_count=cycle_count,
        accepted_flit_count=state.accepted_flit_count,
        forwarded_flit_count=state.forwarded_flit_count,
        input_stall_cycles=state.input_stall_cycles,
        output_stall_cycles=state.output_stall_cycles,
        arbitration_contention_cycles=state.arbitration_contention_cycles,
        current_input_occupancy=state._occupancy(),
        max_input_occupancy=state.max_input_occupancy,
        route_flit_count=tuple(state.route_flit_count),
    )
    expected_values = (
        expected.accepted_flit_count,
        expected.forwarded_flit_count,
        expected.input_stall_cycles,
        expected.output_stall_cycles,
        expected.arbitration_contention_cycles,
        expected.current_input_occupancy,
        expected.max_input_occupancy,
        expected.route_flit_count,
    )
    observed_values = (
        observed.accepted_flit_count,
        observed.forwarded_flit_count,
        observed.input_stall_cycles,
        observed.output_stall_cycles,
        observed.arbitration_contention_cycles,
        observed.current_input_occupancy,
        observed.max_input_occupancy,
        observed.route_flit_count,
    )
    if observed_values != expected_values:
        raise ValueError(f"router replay summary diverged for node {node}")
    return observed


def _opposite_port(port: int) -> int:
    if port == PORT_NORTH:
        return PORT_SOUTH
    if port == PORT_SOUTH:
        return PORT_NORTH
    if port == PORT_EAST:
        return PORT_WEST
    if port == PORT_WEST:
        return PORT_EAST
    return PORT_LOCAL


def _neighbor(endpoint_id: int, port: int) -> tuple[int, int] | None:
    x_coord, y_coord = coordinates(endpoint_id)
    if port == PORT_NORTH and y_coord > 0:
        node = endpoint(x_coord, y_coord - 1)
    elif port == PORT_SOUTH and y_coord < MESH_Y - 1:
        node = endpoint(x_coord, y_coord + 1)
    elif port == PORT_EAST and x_coord < MESH_X - 1:
        node = endpoint(x_coord + 1, y_coord)
    elif port == PORT_WEST and x_coord > 0:
        node = endpoint(x_coord - 1, y_coord)
    elif port == PORT_LOCAL:
        node = endpoint_id
    else:
        return None
    return node, _opposite_port(port)


def _conceptual_payload_bytes() -> int:
    return CONCEPTUAL_LINK_BITS // 8


def _flit_payload_bytes() -> int:
    return PHYSICAL_FLIT_BITS // 8


def packetize_traffic_flow(flow: TrafficFlow) -> tuple[ScheduledFlit, ...]:
    if flow.payload_bytes <= 0:
        raise ValueError("traffic flow payload_bytes must be positive")
    if not 0 <= flow.vc < VIRTUAL_CHANNELS:
        raise ValueError("traffic flow vc must be in [0, 3]")
    if flow.packet_payload_bytes <= 0 or flow.packet_payload_bytes > _conceptual_payload_bytes():
        raise ValueError(
            f"traffic flow packet_payload_bytes must be in [1, {_conceptual_payload_bytes()}]"
        )
    packet_count = int(math.ceil(flow.payload_bytes / flow.packet_payload_bytes))
    remainder = flow.payload_bytes
    scheduled: list[ScheduledFlit] = []
    path = deterministic_xy_path(flow.source, flow.destination)
    for packet_index in range(packet_count):
        packet_bytes = min(flow.packet_payload_bytes, remainder)
        remainder -= packet_bytes
        flit_count = int(math.ceil(packet_bytes / _flit_payload_bytes()))
        if flit_count > FLITS_PER_CONCEPTUAL_TRANSFER:
            raise ValueError(
                "traffic flow packetization exceeds the eight-fragment tagged packet envelope"
            )
        # Producer order is simulator metadata, independent of the concrete
        # eight-bit tag carried by the modeled wire protocol.
        tag = (flow.tag_base + packet_index) & 0xFF
        for fragment in range(flit_count):
            scheduled.append(
                ScheduledFlit(
                    release_cycle=flow.release_cycle,
                    schedule_order=flow.schedule_order,
                    packet_order=packet_index,
                    flit=ModelFlit(
                        source=flow.source,
                        destination=flow.destination,
                        tag=tag,
                        fragment=fragment,
                        last=fragment == flit_count - 1,
                        vc=flow.vc,
                        data=(flow.data_seed << 16) | (packet_index << 8) | fragment,
                        path=path,
                        label=flow.name,
                    ),
                )
            )
    return tuple(scheduled)


def _resolve_endpoint_out_ready(
    endpoint_out_ready_schedule: list[list[bool]] | None,
    cycle: int,
) -> list[bool]:
    if endpoint_out_ready_schedule is None or cycle >= len(endpoint_out_ready_schedule):
        return [True] * ENDPOINTS
    ready = endpoint_out_ready_schedule[cycle]
    if len(ready) != ENDPOINTS:
        raise ValueError("endpoint_out_ready_schedule rows must have 16 ready bits")
    return list(ready)


def simulate_scheduled_flits(
    scheduled_flits: Iterable[ScheduledFlit],
    *,
    endpoint_out_ready_schedule: list[list[bool]] | None = None,
    endpoint_out_ready: Callable[[int, int, ModelFlit | None], bool] | None = None,
    endpoint_injection_policy: str = "fifo",
    fifo_depth: int = DEFAULT_FIFO_DEPTH,
    vc_count: int = VIRTUAL_CHANNELS,
    max_cycles: int = 100000,
    fast_forward_idle: bool = False,
    capture_router_replay_nodes: Iterable[int] | None = None,
    record_mesh_trace: bool = True,
    record_link_transfers: bool = True,
) -> MeshSimulationResult:
    if endpoint_injection_policy not in ("fifo", "vc_round_robin"):
        raise ValueError("endpoint_injection_policy must be fifo or vc_round_robin")
    if endpoint_out_ready_schedule is not None and endpoint_out_ready is not None:
        raise ValueError(
            "endpoint_out_ready_schedule and endpoint_out_ready are mutually exclusive"
        )
    replay_nodes = set(capture_router_replay_nodes or ())
    if any(not 0 <= node < ENDPOINTS for node in replay_nodes):
        raise ValueError(f"capture_router_replay_nodes entries must be in [0, {ENDPOINTS - 1}]")
    if replay_nodes and not record_mesh_trace:
        raise ValueError("router replay capture requires record_mesh_trace=True")
    ordered = sorted(
        scheduled_flits,
        key=lambda item: (
            item.release_cycle,
            item.flit.source,
            item.schedule_order,
            item.packet_order,
            item.flit.fragment,
        ),
    )
    release_queues: list[deque[ScheduledFlit]] = [deque() for _ in range(ENDPOINTS)]
    vc_release_queues: list[list[deque[ScheduledFlit]]] = [
        [deque() for _ in range(vc_count)] for _ in range(ENDPOINTS)
    ]
    fifo_vc_occupancies = [[0] * vc_count for _ in range(ENDPOINTS)]
    endpoint_vc_rr = [0] * ENDPOINTS
    future = deque(ordered)
    states = [
        _RouterState(
            x_coord=coordinates(node)[0],
            y_coord=coordinates(node)[1],
            fifo_depth=fifo_depth,
            vc_count=vc_count,
        )
        for node in range(ENDPOINTS)
    ]
    router_traces: list[list[RouterCycleTrace]] = [[] for _ in range(ENDPOINTS)]
    router_forwarded: list[list[tuple[int, ModelFlit]]] = [[] for _ in range(ENDPOINTS)]
    deliveries: list[MeshDelivery] = []
    link_transfers: list[MeshLinkTransfer] = []
    cycle_traces: list[MeshCycleTrace] = []
    endpoint_input_stall_cycles = [0] * ENDPOINTS
    endpoint_injected_flit_count = 0
    max_endpoint_input_occupancy = 0
    max_endpoint_vc_occupancy = [0] * vc_count
    mesh_contention_cycles = 0

    def queues_empty() -> bool:
        if endpoint_injection_policy == "fifo":
            return all(not queue for queue in release_queues)
        return all(
            not queue
            for endpoint_queues in vc_release_queues
            for queue in endpoint_queues
        )

    def selected_local_queue(node: int) -> tuple[deque[ScheduledFlit] | None, int | None]:
        if endpoint_injection_policy == "fifo":
            queue = release_queues[node]
            return (queue if queue else None), None
        queues = vc_release_queues[node]
        for offset in range(vc_count):
            vc = (endpoint_vc_rr[node] + offset) % vc_count
            if queues[vc]:
                return queues[vc], vc
        return None, None

    cycle = 0
    while cycle < max_cycles:
        if (
            fast_forward_idle
            and future
            and future[0].release_cycle > cycle
            and queues_empty()
            and all(state.idle() for state in states)
        ):
            cycle = future[0].release_cycle

        while future and future[0].release_cycle <= cycle:
            released = future.popleft()
            if not 0 <= released.flit.vc < vc_count:
                raise ValueError(
                    f"scheduled flit VC {released.flit.vc} is outside configured vc_count={vc_count}"
                )
            if endpoint_injection_policy == "fifo":
                release_queues[released.flit.source].append(released)
                fifo_vc_occupancies[released.flit.source][released.flit.vc] += 1
            else:
                vc_release_queues[released.flit.source][released.flit.vc].append(
                    released
                )

        if endpoint_injection_policy == "fifo":
            occupancies = [len(queue) for queue in release_queues]
            max_endpoint_input_occupancy = max(
                max_endpoint_input_occupancy, max(occupancies, default=0)
            )
            for vc in range(vc_count):
                max_endpoint_vc_occupancy[vc] = max(
                    max_endpoint_vc_occupancy[vc],
                    max(
                        (row[vc] for row in fifo_vc_occupancies),
                        default=0,
                    ),
                )
        else:
            occupancies = [
                sum(len(queue) for queue in endpoint_queues)
                for endpoint_queues in vc_release_queues
            ]
            max_endpoint_input_occupancy = max(
                max_endpoint_input_occupancy, max(occupancies, default=0)
            )
            for vc in range(vc_count):
                max_endpoint_vc_occupancy[vc] = max(
                    max_endpoint_vc_occupancy[vc],
                    max(
                        (len(endpoint_queues[vc]) for endpoint_queues in vc_release_queues),
                        default=0,
                    ),
                )

        router_inputs: list[list[RouterCycleInput]] = []
        selected_local_queues: list[deque[ScheduledFlit] | None] = []
        selected_local_vcs: list[int | None] = []
        for node in range(ENDPOINTS):
            inputs = [RouterCycleInput(False, None) for _ in range(PORTS)]
            local_queue, selected_vc = selected_local_queue(node)
            selected_local_queues.append(local_queue)
            selected_local_vcs.append(selected_vc)
            if local_queue:
                inputs[PORT_LOCAL] = RouterCycleInput(True, local_queue[0].flit)
            for port in (PORT_NORTH, PORT_SOUTH, PORT_EAST, PORT_WEST):
                neighbor = _neighbor(node, port)
                if neighbor is None:
                    continue
                upstream_node, upstream_port = neighbor
                flit = states[upstream_node].out_holding[upstream_port]
                if flit is not None:
                    inputs[port] = RouterCycleInput(True, flit)
            router_inputs.append(inputs)

        if endpoint_out_ready is None:
            resolved_endpoint_out_ready = _resolve_endpoint_out_ready(
                endpoint_out_ready_schedule, cycle
            )
        else:
            resolved_endpoint_out_ready = [
                bool(
                    endpoint_out_ready(
                        cycle,
                        node,
                        states[node].out_holding[PORT_LOCAL],
                    )
                )
                for node in range(ENDPOINTS)
            ]
        out_ready = [[False] * PORTS for _ in range(ENDPOINTS)]
        for node in range(ENDPOINTS):
            out_ready[node][PORT_LOCAL] = resolved_endpoint_out_ready[node]

        # Input credit is a function of registered FIFO occupancy only. First
        # sample those credits, then calculate link readiness and the final
        # arbitration plan. No network-wide combinational fixpoint is needed.
        credit_plans = [
            states[node].compute_plan(router_inputs[node], [False] * PORTS)
            for node in range(ENDPOINTS)
        ]
        for node in range(ENDPOINTS):
            out_ready[node][PORT_LOCAL] = resolved_endpoint_out_ready[node]
            for port in (PORT_NORTH, PORT_SOUTH, PORT_EAST, PORT_WEST):
                neighbor = _neighbor(node, port)
                if neighbor is None:
                    out_ready[node][port] = True
                    continue
                downstream_node, downstream_port = neighbor
                out_ready[node][port] = credit_plans[downstream_node].ready[downstream_port]
        plans = [
            states[node].compute_plan(router_inputs[node], out_ready[node])
            for node in range(ENDPOINTS)
        ]

        cycle_router_traces: list[RouterCycleTrace] = []
        cycle_injected: list[tuple[int, ModelFlit]] = []
        cycle_deliveries: list[MeshDelivery] = []
        cycle_links: list[MeshLinkTransfer] = []
        cycle_endpoint_stall: list[int] = []

        for node in range(ENDPOINTS):
            trace = states[node].apply_plan(
                cycle,
                router_inputs[node],
                out_ready[node],
                plans[node],
                capture_replay_signals=node in replay_nodes,
            )
            cycle_router_traces.append(trace)
            if record_mesh_trace:
                router_traces[node].append(trace)
                router_forwarded[node].extend(trace.forwarded)
            local_queue = selected_local_queues[node]
            if local_queue and trace.ready[PORT_LOCAL]:
                injected = local_queue.popleft().flit
                cycle_injected.append((node, injected))
                endpoint_injected_flit_count += 1
                selected_vc = selected_local_vcs[node]
                if selected_vc is not None:
                    endpoint_vc_rr[node] = (selected_vc + 1) % vc_count
                else:
                    fifo_vc_occupancies[node][injected.vc] -= 1
                cycle_endpoint_stall.append(0)
            else:
                if endpoint_injection_policy == "fifo":
                    has_queued = bool(release_queues[node])
                else:
                    has_queued = any(vc_release_queues[node])
                stalled = 1 if has_queued else 0
                cycle_endpoint_stall.append(stalled)
                endpoint_input_stall_cycles[node] += stalled
            for port, flit in trace.forwarded:
                if port == PORT_LOCAL:
                    delivery = MeshDelivery(cycle=cycle, endpoint=node, flit=flit)
                    deliveries.append(delivery)
                    cycle_deliveries.append(delivery)
                    continue
                neighbor = _neighbor(node, port)
                if neighbor is None:
                    continue
                destination_node, destination_port = neighbor
                transfer = MeshLinkTransfer(
                    cycle=cycle,
                    source_node=node,
                    source_port=port,
                    destination_node=destination_node,
                    destination_port=destination_port,
                    flit=flit,
                )
                if record_link_transfers:
                    link_transfers.append(transfer)
                    cycle_links.append(transfer)

        if any(trace.contention for trace in cycle_router_traces):
            mesh_contention_cycles += 1
        if record_mesh_trace:
            cycle_traces.append(
                MeshCycleTrace(
                    cycle=cycle,
                    router_traces=tuple(cycle_router_traces),
                    injected=tuple(cycle_injected),
                    deliveries=tuple(cycle_deliveries),
                    link_transfers=tuple(cycle_links),
                    endpoint_in_ready=tuple(
                        trace.ready[PORT_LOCAL] for trace in cycle_router_traces
                    ),
                    endpoint_out_ready=tuple(resolved_endpoint_out_ready),
                    endpoint_input_stall=tuple(cycle_endpoint_stall),
                )
            )

        if not future and queues_empty() and all(state.idle() for state in states):
            return MeshSimulationResult(
                cycles=cycle + 1,
                traces=tuple(cycle_traces),
                deliveries=tuple(deliveries),
                link_transfers=tuple(link_transfers),
                router_summaries=tuple(
                    state.snapshot(router_traces[node], router_forwarded[node])
                    for node, state in enumerate(states)
                ),
                endpoint_injected_flit_count=endpoint_injected_flit_count,
                endpoint_input_stall_cycles=tuple(endpoint_input_stall_cycles),
                max_endpoint_input_occupancy=max_endpoint_input_occupancy,
                max_endpoint_vc_occupancy=tuple(max_endpoint_vc_occupancy),
                mesh_contention_cycles=mesh_contention_cycles,
            )

        cycle += 1

    raise RuntimeError("mesh model did not drain within max_cycles")


def simulate_mesh(
    *,
    source: int,
    destination: int,
    tag: int,
    vc: int,
    max_cycles: int = 256,
) -> dict[str, object]:
    path = deterministic_xy_path(source, destination)
    scheduled = [
        ScheduledFlit(release_cycle=0, flit=flit)
        for flit in segmented_transfer(source=source, destination=destination, tag=tag, vc=vc)
    ]
    result = simulate_scheduled_flits(scheduled, max_cycles=max_cycles)
    delivered = [
        {
            "cycle": delivery.cycle,
            "source": delivery.flit.source,
            "destination": delivery.flit.destination,
            "tag": delivery.flit.tag,
            "fragment": delivery.flit.fragment,
            "last": delivery.flit.last,
            "vc": delivery.flit.vc,
            "path": path,
        }
        for delivery in result.deliveries
    ]
    link_flits: dict[tuple[int, int], int] = defaultdict(int)
    for transfer in result.link_transfers:
        link_flits[(transfer.source_node, transfer.destination_node)] += 1
    return {
        "cycles": result.cycles,
        "path": path,
        "delivered": tuple(delivered),
        "directed_link_flits": dict(link_flits),
        "contention_cycles": sum(
            1
            for trace in result.traces
            if any(router_trace.contention for router_trace in trace.router_traces)
        ),
        "serialization_flits": FLITS_PER_CONCEPTUAL_TRANSFER,
    }


def simulate(flows: Iterable[Flow], *, max_cycles: int = 10000) -> dict[str, object]:
    flow_list = list(flows)
    scheduled: list[ScheduledFlit] = []
    for flow_order, flow in enumerate(flow_list):
        if flow.flits <= 0:
            raise ValueError("flow flits must be positive")
        if flow.flits % FLITS_PER_CONCEPTUAL_TRANSFER != 0:
            raise ValueError(
                f"flow flits must be a multiple of {FLITS_PER_CONCEPTUAL_TRANSFER}"
            )
        path = deterministic_xy_path(flow.source, flow.destination)
        packet_count = flow.flits // FLITS_PER_CONCEPTUAL_TRANSFER
        for packet_index in range(packet_count):
            tag = (flow.tag + packet_index) & 0xFF
            for fragment in range(FLITS_PER_CONCEPTUAL_TRANSFER):
                scheduled.append(
                    ScheduledFlit(
                        release_cycle=flow.release_cycle,
                        schedule_order=flow_order,
                        packet_order=packet_index,
                        flit=ModelFlit(
                            source=flow.source,
                            destination=flow.destination,
                            tag=tag,
                            fragment=fragment,
                            last=fragment == FLITS_PER_CONCEPTUAL_TRANSFER - 1,
                            vc=flow.vc,
                            data=(packet_index << 8) | fragment,
                            path=path,
                        ),
                    )
                )
    result = simulate_scheduled_flits(scheduled, max_cycles=max_cycles)
    link_flits: dict[tuple[int, int], int] = defaultdict(int)
    for transfer in result.link_transfers:
        link_flits[(transfer.source_node, transfer.destination_node)] += 1
    return {
        "cycles": result.cycles,
        "delivered": tuple(
            {
                "cycle": delivery.cycle,
                "source": delivery.flit.source,
                "destination": delivery.flit.destination,
                "tag": delivery.flit.tag,
                "fragment": delivery.flit.fragment,
                "last": delivery.flit.last,
                "vc": delivery.flit.vc,
                "path": delivery.flit.path,
                "label": delivery.flit.label,
            }
            for delivery in result.deliveries
        ),
        "directed_link_flits": dict(link_flits),
        "contention_cycles": sum(
            1
            for trace in result.traces
            if any(router_trace.contention for router_trace in trace.router_traces)
        ),
        "serialization_flits": len(scheduled),
    }


def mapping_report() -> dict[str, int | str]:
    return {
        "conceptual_transfer_bits": CONCEPTUAL_LINK_BITS,
        "physical_flit_bits": PHYSICAL_FLIT_BITS,
        "serialized_flits_per_conceptual_transfer": FLITS_PER_CONCEPTUAL_TRANSFER,
        "physical_payload_bytes_per_flit": PHYSICAL_FLIT_BITS // 8,
        "conceptual_payload_bytes": CONCEPTUAL_LINK_BITS // 8,
        "serialization_efficiency_payload_only": "100%",
    }
