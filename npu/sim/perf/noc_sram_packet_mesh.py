"""Cycle model for the descriptor-driven SRAM packet mesh.

This module models the control boundary of ``noc_sram_packet_mesh4x4``.  The
router and registered-credit behavior are supplied by
``noc_segmented_mesh``; this file adds the endpoint descriptor, SRAM, and
receive-context timing around that mesh.

The model deliberately keeps the packet payload in a deterministic read
function.  It records the same metadata that crosses the RTL boundary, which
is sufficient for scheduling and later full Phase-2 replay without allocating
packet-sized registers.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

from npu.sim.perf.noc_segmented_mesh import (
    ENDPOINTS,
    PORT_EAST,
    PORT_LOCAL,
    PORT_NORTH,
    PORT_SOUTH,
    PORT_WEST,
    VIRTUAL_CHANNELS,
    MeshCycleTrace,
    MeshDelivery,
    MeshLinkTransfer,
    ModelFlit,
    RouterCycleInput,
    RouterSimulationResult,
    _RouterState,
    _neighbor,
    coordinates,
)

TX_DESC_DEPTH = 4
TX_OUTSTANDING = 8
RX_CONTEXTS = 8
MAX_PACKET_FLITS = 8
FLIT_BYTES = 32


@dataclass(frozen=True)
class PacketDescriptor:
    """One paired packet transfer described at both endpoint boundaries."""

    source: int
    destination: int
    vc: int
    tag: int
    flit_count: int
    tx_base_addr: int = 0
    rx_base_addr: int = 0
    release_cycle: int = 0
    schedule_order: int = 0
    data_seed: int = 0
    packet_id: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.source < ENDPOINTS:
            raise ValueError("source must be in [0, 15]")
        if not 0 <= self.destination < ENDPOINTS:
            raise ValueError("destination must be in [0, 15]")
        if not 0 <= self.vc < VIRTUAL_CHANNELS:
            raise ValueError("vc must be in [0, 3]")
        if not 0 <= self.tag < 256:
            raise ValueError("tag must be an 8-bit concrete wire value")
        if not 1 <= self.flit_count <= MAX_PACKET_FLITS:
            raise ValueError("flit_count must be in [1, 8]")
        if self.release_cycle < 0:
            raise ValueError("release_cycle must be non-negative")
        if self.schedule_order < 0:
            raise ValueError("schedule_order must be non-negative")

    @property
    def key(self) -> tuple[int, int, int]:
        """The RX lookup key used by the RTL: ``(source, vc, tag)``."""

        return self.source, self.vc, self.tag


@dataclass(frozen=True)
class DescriptorHandshake:
    cycle: int
    endpoint: int
    direction: str
    packet_index: int
    descriptor: PacketDescriptor


@dataclass(frozen=True)
class SourceMemoryRequest:
    cycle: int
    endpoint: int
    packet_index: int
    address: int
    fragment: int


@dataclass(frozen=True)
class SourceMemoryResponse:
    cycle: int
    endpoint: int
    packet_index: int
    fragment: int
    address: int


@dataclass(frozen=True)
class DestinationMemoryWrite:
    cycle: int
    endpoint: int
    packet_index: int
    address: int
    fragment: int
    data: int


@dataclass(frozen=True)
class CompletionEvent:
    cycle: int
    endpoint: int
    packet_index: int
    source: int
    vc: int
    tag: int


@dataclass(frozen=True)
class CompletionHandshake:
    cycle: int
    endpoint: int
    packet_index: int
    source: int
    vc: int
    tag: int


@dataclass(frozen=True)
class PacketDelivery:
    cycle: int
    packet_index: int
    flit: ModelFlit


@dataclass(frozen=True)
class PacketMeshResult:
    """Observable result of a paired endpoint/mesh simulation."""

    cycles: int
    descriptors: tuple[PacketDescriptor, ...]
    rx_descriptor_handshakes: tuple[DescriptorHandshake, ...]
    tx_descriptor_handshakes: tuple[DescriptorHandshake, ...]
    source_memory_requests: tuple[SourceMemoryRequest, ...]
    source_memory_responses: tuple[SourceMemoryResponse, ...]
    destination_memory_writes: tuple[DestinationMemoryWrite, ...]
    completions: tuple[CompletionEvent, ...]
    completion_handshakes: tuple[CompletionHandshake, ...]
    deliveries: tuple[PacketDelivery, ...]
    link_transfers: tuple[MeshLinkTransfer, ...]
    router_summaries: tuple[RouterSimulationResult, ...]
    protocol_errors: tuple[int, ...]
    max_rx_context_occupancy: int = 0
    mesh_traces: tuple[MeshCycleTrace, ...] = ()

    @property
    def delivered_flits(self) -> tuple[PacketDelivery, ...]:
        return self.deliveries

    @property
    def rx_context_peak(self) -> int:
        return self.max_rx_context_occupancy


@dataclass
class _TxRead:
    due_cycle: int
    packet_index: int
    descriptor: PacketDescriptor
    fragment: int
    address: int


@dataclass
class _RxContext:
    packet_index: int
    descriptor: PacketDescriptor
    expected_fragment: int = 0


@dataclass
class _EndpointState:
    endpoint: int
    tx_fifo_depth: int = TX_DESC_DEPTH
    tx_outstanding_limit: int = TX_OUTSTANDING
    rx_context_limit: int = RX_CONTEXTS
    tx_fifo: deque[tuple[int, PacketDescriptor]] = field(default_factory=deque)
    tx_active: tuple[int, PacketDescriptor] | None = None
    tx_issue_fragment: int = 0
    tx_reads: deque[_TxRead] = field(default_factory=deque)
    tx_output: _TxRead | None = None
    rx_contexts: dict[tuple[int, int, int], _RxContext] = field(default_factory=dict)
    completion: tuple[int, CompletionEvent] | None = None
    protocol_error: bool = False

    def tx_pop_ready(self) -> bool:
        return self.tx_active is None and bool(self.tx_fifo)

    def tx_desc_ready(self) -> bool:
        return len(self.tx_fifo) < self.tx_fifo_depth or self.tx_pop_ready()

    def rx_desc_ready(self, descriptor: PacketDescriptor) -> bool:
        return (
            len(self.rx_contexts) < self.rx_context_limit
            and descriptor.key not in self.rx_contexts
        )

    def source_request_ready(self, ready: bool) -> bool:
        return (
            ready
            and self.tx_active is not None
            and len(self.tx_reads) < self.tx_outstanding_limit
        )

    def source_response_ready(self, tx_flit_fire: bool) -> bool:
        return bool(self.tx_reads) and (self.tx_output is None or tx_flit_fire)

    def rx_ready_for_flit(
        self,
        flit: ModelFlit | None,
        *,
        destination_sram_ready: bool,
        completion_ready: bool,
    ) -> bool:
        if flit is None:
            return True
        context = self.rx_contexts.get((flit.source, flit.vc, flit.tag))
        valid = (
            flit.destination == self.endpoint
            and context is not None
            and flit.fragment == context.expected_fragment
            and flit.last == (flit.fragment + 1 == context.descriptor.flit_count)
        )
        if not valid:
            # The RTL consumes malformed/misrouted input and raises its sticky
            # error; it does not hold the mesh output for an SRAM write.
            return True
        return destination_sram_ready and (
            not flit.last or self.completion is None or completion_ready
        )

    def accept_rx_descriptor(self, packet_index: int, descriptor: PacketDescriptor) -> None:
        if not self.rx_desc_ready(descriptor):
            raise RuntimeError("RX descriptor accepted without a free context")
        self.rx_contexts[descriptor.key] = _RxContext(packet_index, descriptor)

    def accept_rx_flit(
        self,
        cycle: int,
        flit: ModelFlit,
        *,
        destination_sram_ready: bool,
        completion_ready: bool,
    ) -> tuple[DestinationMemoryWrite | None, CompletionEvent | None, bool]:
        context = self.rx_contexts.get((flit.source, flit.vc, flit.tag))
        valid = (
            flit.destination == self.endpoint
            and context is not None
            and flit.fragment == context.expected_fragment
            and flit.last == (flit.fragment + 1 == context.descriptor.flit_count)
        )
        if not valid:
            self.protocol_error = True
            return None, None, True
        if not destination_sram_ready:
            raise RuntimeError("mesh delivered a flit while destination SRAM was not ready")
        if flit.last and self.completion is not None and not completion_ready:
            raise RuntimeError("mesh delivered a final flit while completion was blocked")

        if self.completion is not None and completion_ready:
            self.completion = None
        address = context.descriptor.rx_base_addr + flit.fragment * FLIT_BYTES
        write = DestinationMemoryWrite(
            cycle=cycle,
            endpoint=self.endpoint,
            packet_index=context.packet_index,
            address=address,
            fragment=flit.fragment,
            data=flit.data,
        )
        completion: CompletionEvent | None = None
        if flit.last:
            completion = CompletionEvent(
                cycle=cycle,
                endpoint=self.endpoint,
                packet_index=context.packet_index,
                source=flit.source,
                vc=flit.vc,
                tag=flit.tag,
            )
            del self.rx_contexts[flit.source, flit.vc, flit.tag]
            self.completion = (context.packet_index, completion)
        else:
            context.expected_fragment += 1
        return write, completion, True

    def apply_cycle(
        self,
        *,
        packet_index: int | None,
        tx_descriptor: PacketDescriptor | None,
        tx_pop: bool,
        tx_request: SourceMemoryRequest | None,
        response: SourceMemoryResponse | None,
        tx_flit_fire: bool,
        cycle: int,
    ) -> None:
        if tx_pop:
            if self.tx_active is not None or not self.tx_fifo:
                raise RuntimeError("invalid TX descriptor pop")
            self.tx_active = self.tx_fifo.popleft()
            self.tx_issue_fragment = 0
        if tx_descriptor is not None:
            if packet_index is None:
                raise RuntimeError("TX descriptor lacks packet index")
            if not self.tx_desc_ready():
                raise RuntimeError("TX descriptor accepted without FIFO space")
            self.tx_fifo.append((packet_index, tx_descriptor))

        if tx_flit_fire:
            if self.tx_output is None:
                raise RuntimeError("TX flit handshake without a valid output")
            self.tx_output = None
        if response is not None:
            if not self.tx_reads:
                raise RuntimeError("source response without an outstanding read")
            read = self.tx_reads.popleft()
            if read.packet_index != response.packet_index or read.fragment != response.fragment:
                raise RuntimeError("source response lost in-order metadata")
            self.tx_output = read

        if tx_request is not None:
            if self.tx_active is None:
                raise RuntimeError("source request without an active descriptor")
            descriptor = self.tx_active[1]
            self.tx_reads.append(
                _TxRead(
                    due_cycle=cycle + 1,
                    packet_index=self.tx_active[0],
                    descriptor=descriptor,
                    fragment=tx_request.fragment,
                    address=tx_request.address,
                )
            )
            if tx_request.fragment + 1 == descriptor.flit_count:
                self.tx_active = None
                self.tx_issue_fragment = 0
            else:
                self.tx_issue_fragment += 1


ReadySchedule = (
    Sequence[Sequence[bool]]
    | Mapping[int, Sequence[bool]]
    | Callable[[int, int], bool]
    | None
)


def _ready(schedule: ReadySchedule, cycle: int, endpoint: int) -> bool:
    if schedule is None:
        return True
    if callable(schedule):
        return bool(schedule(cycle, endpoint))
    if isinstance(schedule, Mapping):
        row = schedule.get(cycle)
        return True if row is None else bool(row[endpoint])
    if cycle >= len(schedule):
        return True
    row = schedule[cycle]
    if len(row) != ENDPOINTS:
        raise ValueError("ready schedule rows must contain 16 endpoint values")
    return bool(row[endpoint])


def _flit_for_read(read: _TxRead) -> ModelFlit:
    descriptor = read.descriptor
    return ModelFlit(
        source=descriptor.source,
        destination=descriptor.destination,
        tag=descriptor.tag,
        fragment=read.fragment,
        last=read.fragment + 1 == descriptor.flit_count,
        vc=descriptor.vc,
        data=(descriptor.data_seed << 16) | (read.fragment & 0xFF),
        label=descriptor.packet_id,
    )


def _ordered_indices(descriptors: Sequence[PacketDescriptor]) -> tuple[int, ...]:
    return tuple(sorted(range(len(descriptors)), key=lambda i: (descriptors[i].release_cycle, descriptors[i].schedule_order, i)))


def simulate_packet_mesh(
    descriptors: Iterable[PacketDescriptor],
    *,
    descriptor_scheduler: str = "endpoint_parallel",
    rx_context_limits: Mapping[int, int] | None = None,
    destination_sram_ready_schedule: ReadySchedule = None,
    source_sram_request_ready_schedule: ReadySchedule = None,
    completion_ready_schedule: ReadySchedule = None,
    max_cycles: int = 1_000_000,
    record_mesh_trace: bool = False,
    fast_forward_idle: bool = False,
) -> PacketMeshResult:
    """Simulate paired descriptors and the existing registered-credit mesh.

    ``endpoint_parallel`` schedules one RX per destination and one TX per
    source each cycle, preserving the original abstract scheduler.  The
    synthesizable ``serial_paired`` policy includes the one-cycle SRAM request
    and response buffer. ``serial_generated`` feeds the same scheduler from a
    direct ready/valid command generator. Both hold one global command,
    install its RX descriptor first, and submit its TX descriptor on a later
    edge; steady-state issue cadence is two cycles per command.
    Ready schedules are indexed as ``[cycle][endpoint]``; a callable may be
    used for large replay workloads without materializing a matrix.
    """

    if descriptor_scheduler not in (
        "endpoint_parallel",
        "serial_paired",
        "serial_generated",
    ):
        raise ValueError(
            "descriptor_scheduler must be endpoint_parallel, serial_paired, or "
            "serial_generated"
        )

    serial_scheduler = descriptor_scheduler in ("serial_paired", "serial_generated")

    packet_list = tuple(descriptors)
    if not packet_list:
        return PacketMeshResult(
            cycles=0,
            descriptors=(),
            rx_descriptor_handshakes=(),
            tx_descriptor_handshakes=(),
            source_memory_requests=(),
            source_memory_responses=(),
            destination_memory_writes=(),
            completions=(),
            completion_handshakes=(),
            deliveries=(),
            link_transfers=(),
            router_summaries=(),
            protocol_errors=(),
        )

    context_limits = dict(rx_context_limits or {})
    for endpoint, limit in context_limits.items():
        if not 0 <= int(endpoint) < ENDPOINTS:
            raise ValueError("rx_context_limits keys must be endpoints in [0, 15]")
        if int(limit) < 1:
            raise ValueError("rx_context_limits values must be positive")
    states = [
        _EndpointState(
            endpoint,
            rx_context_limit=int(context_limits.get(endpoint, RX_CONTEXTS)),
        )
        for endpoint in range(ENDPOINTS)
    ]
    routers = [
        _RouterState(
            x_coord=coordinates(endpoint)[0],
            y_coord=coordinates(endpoint)[1],
            fifo_depth=4,
            vc_count=VIRTUAL_CHANNELS,
        )
        for endpoint in range(ENDPOINTS)
    ]
    rx_done: list[int | None] = [None] * len(packet_list)
    tx_done: list[int | None] = [None] * len(packet_list)
    ordered_indices = _ordered_indices(packet_list)
    scheduler_pending = deque(ordered_indices)
    scheduler_active: int | None = None
    scheduler_receive_installed = False
    rx_queues = [deque() for _ in range(ENDPOINTS)]
    tx_queues = [deque() for _ in range(ENDPOINTS)]
    for index in ordered_indices:
        descriptor = packet_list[index]
        rx_queues[descriptor.destination].append(index)
        tx_queues[descriptor.source].append(index)
    rx_done_count = 0
    tx_done_count = 0
    rx_handshakes: list[DescriptorHandshake] = []
    tx_handshakes: list[DescriptorHandshake] = []
    source_requests: list[SourceMemoryRequest] = []
    source_responses: list[SourceMemoryResponse] = []
    destination_writes: list[DestinationMemoryWrite] = []
    completions: list[CompletionEvent] = []
    completion_handshakes: list[CompletionHandshake] = []
    deliveries: list[PacketDelivery] = []
    link_transfers: list[MeshLinkTransfer] = []
    mesh_traces: list[MeshCycleTrace] = []
    router_traces: list[list] = [[] for _ in range(ENDPOINTS)]
    router_forwarded: list[list[tuple[int, ModelFlit]]] = [[] for _ in range(ENDPOINTS)]
    max_rx_context_occupancy = 0

    cycle = 0
    while cycle < max_cycles:
        if fast_forward_idle:
            endpoints_idle = all(
                state.tx_active is None
                and not state.tx_fifo
                and not state.tx_reads
                and state.tx_output is None
                and not state.rx_contexts
                and state.completion is None
                for state in states
            )
            if endpoints_idle and all(router.idle() for router in routers):
                if serial_scheduler:
                    pending_releases = (
                        [packet_list[scheduler_active].release_cycle]
                        if scheduler_active is not None
                        else []
                    )
                else:
                    pending_releases = [
                        packet_list[queue[0]].release_cycle for queue in rx_queues if queue
                    ]
                if pending_releases:
                    next_release = min(pending_releases)
                    if next_release >= max_cycles:
                        break
                    cycle = max(cycle, next_release)

        # Descriptor scheduling is intentionally separate from data movement.
        # An RX handshake at this edge cannot make a same-edge TX release
        # legal, matching the RTL's registered descriptor state.
        rx_push: dict[int, int] = {}
        tx_push: dict[int, int] = {}
        if serial_scheduler:
            if scheduler_active is not None:
                descriptor = packet_list[scheduler_active]
                if descriptor.release_cycle <= cycle:
                    if not scheduler_receive_installed:
                        if states[descriptor.destination].rx_desc_ready(descriptor):
                            rx_push[descriptor.destination] = scheduler_active
                    elif states[descriptor.source].tx_desc_ready():
                        tx_push[descriptor.source] = scheduler_active
        else:
            for endpoint, queue in enumerate(rx_queues):
                if not queue:
                    continue
                index = queue[0]
                descriptor = packet_list[index]
                if (
                    descriptor.release_cycle <= cycle
                    and states[endpoint].rx_desc_ready(descriptor)
                ):
                    rx_push[endpoint] = index

            for endpoint, queue in enumerate(tx_queues):
                if not queue or not states[endpoint].tx_desc_ready():
                    continue
                index = queue[0]
                descriptor = packet_list[index]
                if (
                    rx_done[index] is not None
                    and rx_done[index] < cycle
                    and descriptor.release_cycle <= cycle
                ):
                    tx_push[endpoint] = index

        tx_pop = [state.tx_pop_ready() for state in states]
        tx_requests_by_endpoint: list[SourceMemoryRequest | None] = [None] * ENDPOINTS
        for endpoint, state in enumerate(states):
            if not state.source_request_ready(
                _ready(source_sram_request_ready_schedule, cycle, endpoint)
            ):
                continue
            assert state.tx_active is not None
            packet_index, descriptor = state.tx_active
            fragment = state.tx_issue_fragment
            tx_requests_by_endpoint[endpoint] = SourceMemoryRequest(
                cycle=cycle,
                endpoint=endpoint,
                packet_index=packet_index,
                address=descriptor.tx_base_addr + fragment * FLIT_BYTES,
                fragment=fragment,
            )

        # The endpoint output register and router state are sampled before the
        # edge.  This is the same registered-credit sequencing as the mesh
        # model: local injection is accepted into a router FIFO, while a held
        # local output can be delivered on this edge.
        router_inputs: list[list[RouterCycleInput]] = []
        for endpoint, state in enumerate(states):
            inputs = [RouterCycleInput(False, None) for _ in range(5)]
            if state.tx_output is not None:
                inputs[PORT_LOCAL] = RouterCycleInput(True, _flit_for_read(state.tx_output))
            for port in (PORT_NORTH, PORT_SOUTH, PORT_EAST, PORT_WEST):
                neighbor = _neighbor(endpoint, port)
                if neighbor is None:
                    continue
                upstream, upstream_port = neighbor
                held = routers[upstream].out_holding[upstream_port]
                if held is not None:
                    inputs[port] = RouterCycleInput(True, held)
            router_inputs.append(inputs)

        endpoint_out_ready: list[bool] = []
        for endpoint, state in enumerate(states):
            held = routers[endpoint].out_holding[PORT_LOCAL]
            endpoint_out_ready.append(
                state.rx_ready_for_flit(
                    held,
                    destination_sram_ready=_ready(destination_sram_ready_schedule, cycle, endpoint),
                    completion_ready=_ready(completion_ready_schedule, cycle, endpoint),
                )
            )

        out_ready = [[False] * 5 for _ in range(ENDPOINTS)]
        for endpoint in range(ENDPOINTS):
            out_ready[endpoint][PORT_LOCAL] = endpoint_out_ready[endpoint]
        credit_plans = [
            routers[endpoint].compute_plan(router_inputs[endpoint], [False] * 5)
            for endpoint in range(ENDPOINTS)
        ]
        for endpoint in range(ENDPOINTS):
            for port in (PORT_NORTH, PORT_SOUTH, PORT_EAST, PORT_WEST):
                neighbor = _neighbor(endpoint, port)
                if neighbor is None:
                    out_ready[endpoint][port] = True
                else:
                    downstream, downstream_port = neighbor
                    out_ready[endpoint][port] = credit_plans[downstream].ready[downstream_port]
        plans = [
            routers[endpoint].compute_plan(router_inputs[endpoint], out_ready[endpoint])
            for endpoint in range(ENDPOINTS)
        ]

        cycle_router_traces = []
        cycle_deliveries: list[MeshDelivery] = []
        cycle_links: list[MeshLinkTransfer] = []
        tx_flit_fires = [False] * ENDPOINTS
        rx_flit_events: list[tuple[int, ModelFlit] | None] = [None] * ENDPOINTS
        for endpoint in range(ENDPOINTS):
            trace = routers[endpoint].apply_plan(
                cycle, router_inputs[endpoint], out_ready[endpoint], plans[endpoint]
            )
            cycle_router_traces.append(trace)
            if record_mesh_trace:
                router_traces[endpoint].append(trace)
                router_forwarded[endpoint].extend(trace.forwarded)
            if router_inputs[endpoint][PORT_LOCAL].valid and trace.ready[PORT_LOCAL]:
                tx_flit_fires[endpoint] = True
            for port, flit in trace.forwarded:
                if port == PORT_LOCAL:
                    delivery = MeshDelivery(cycle=cycle, endpoint=endpoint, flit=flit)
                    cycle_deliveries.append(delivery)
                    rx_flit_events[endpoint] = (endpoint, flit)
                else:
                    neighbor = _neighbor(endpoint, port)
                    if neighbor is None:
                        continue
                    destination_node, destination_port = neighbor
                    cycle_links.append(
                        MeshLinkTransfer(
                            cycle=cycle,
                            source_node=endpoint,
                            source_port=port,
                            destination_node=destination_node,
                            destination_port=destination_port,
                            flit=flit,
                        )
                    )

        # A response due this cycle can replace an output flit that was
        # accepted on this same edge, exactly as tx_mem_rsp_ready permits.
        response_by_endpoint: list[SourceMemoryResponse | None] = [None] * ENDPOINTS
        for endpoint, state in enumerate(states):
            if state.tx_reads and state.tx_reads[0].due_cycle <= cycle:
                if state.source_response_ready(tx_flit_fires[endpoint]):
                    read = state.tx_reads[0]
                    response_by_endpoint[endpoint] = SourceMemoryResponse(
                        cycle=cycle,
                        endpoint=endpoint,
                        packet_index=read.packet_index,
                        fragment=read.fragment,
                        address=read.address,
                    )

        for endpoint, state in enumerate(states):
            packet_index = tx_push.get(endpoint)
            descriptor = packet_list[packet_index] if packet_index is not None else None
            request = tx_requests_by_endpoint[endpoint]
            response = response_by_endpoint[endpoint]
            if request is not None:
                source_requests.append(request)
            if response is not None:
                source_responses.append(response)
            state.apply_cycle(
                packet_index=packet_index,
                tx_descriptor=descriptor,
                tx_pop=tx_pop[endpoint],
                tx_request=request,
                response=response,
                tx_flit_fire=tx_flit_fires[endpoint],
                cycle=cycle,
            )
            if endpoint in rx_push:
                index = rx_push[endpoint]
                if not rx_queues[endpoint] or rx_queues[endpoint][0] != index:
                    raise RuntimeError("RX scheduler queue lost packet order")
                rx_queues[endpoint].popleft()
                state.accept_rx_descriptor(index, packet_list[index])
                rx_done[index] = cycle
                rx_done_count += 1
                rx_handshakes.append(
                    DescriptorHandshake(cycle, endpoint, "rx", index, packet_list[index])
                )
                if serial_scheduler:
                    if scheduler_active != index or scheduler_receive_installed:
                        raise RuntimeError("serial RX scheduler state diverged")
                    scheduler_receive_installed = True
            if endpoint in tx_push:
                index = tx_push[endpoint]
                if not tx_queues[endpoint] or tx_queues[endpoint][0] != index:
                    raise RuntimeError("TX scheduler queue lost packet order")
                tx_queues[endpoint].popleft()
                tx_done[index] = cycle
                tx_done_count += 1
                tx_handshakes.append(
                    DescriptorHandshake(cycle, endpoint, "tx", index, packet_list[index])
                )
                if serial_scheduler:
                    if scheduler_active != index or not scheduler_receive_installed:
                        raise RuntimeError("serial TX scheduler state diverged")
                    scheduler_active = None
                    scheduler_receive_installed = False
            if state.completion is not None and _ready(completion_ready_schedule, cycle, endpoint):
                packet_index_completion, completion = state.completion
                completion_handshakes.append(
                    CompletionHandshake(
                        cycle=cycle,
                        endpoint=endpoint,
                        packet_index=packet_index_completion,
                        source=completion.source,
                        vc=completion.vc,
                        tag=completion.tag,
                    )
                )
                # The RTL clears the held completion at this edge.  A new
                # final RX flit in the same edge may install the next event.
                state.completion = None

        # The external command memory can fill an empty scheduler or replace
        # a command whose TX descriptor handshook on this edge.  Its newly
        # accepted command cannot drive endpoint outputs until the next cycle.
        if (
            serial_scheduler
            and scheduler_active is None
            and scheduler_pending
            and cycle >= (2 if descriptor_scheduler == "serial_paired" else 0)
        ):
            scheduler_active = scheduler_pending.popleft()

        for endpoint, event in enumerate(rx_flit_events):
            if event is None:
                continue
            _, flit = event
            context = states[endpoint].rx_contexts.get((flit.source, flit.vc, flit.tag))
            if context is None:
                packet_index = _packet_index_for_flit(flit, packet_list)
            else:
                packet_index = context.packet_index
            delivery = PacketDelivery(cycle, packet_index, flit)
            deliveries.append(delivery)
            write, completion, _ = states[endpoint].accept_rx_flit(
                cycle,
                flit,
                destination_sram_ready=_ready(destination_sram_ready_schedule, cycle, endpoint),
                completion_ready=_ready(completion_ready_schedule, cycle, endpoint),
            )
            if write is not None:
                destination_writes.append(write)
            if completion is not None:
                completions.append(completion)

        # Completion is intentionally generated by accept_rx_flit after the
        # final write, matching the RTL's registered completion output.
        link_transfers.extend(cycle_links)
        if record_mesh_trace:
            mesh_traces.append(
                MeshCycleTrace(
                    cycle=cycle,
                    router_traces=tuple(cycle_router_traces),
                    injected=tuple(
                        (endpoint, router_inputs[endpoint][PORT_LOCAL].flit)
                        for endpoint in range(ENDPOINTS)
                        if tx_flit_fires[endpoint] and router_inputs[endpoint][PORT_LOCAL].flit is not None
                    ),
                    deliveries=tuple(cycle_deliveries),
                    link_transfers=tuple(cycle_links),
                    endpoint_in_ready=tuple(trace.ready[PORT_LOCAL] for trace in cycle_router_traces),
                    endpoint_out_ready=tuple(endpoint_out_ready),
                    endpoint_input_stall=tuple(
                        1 if states[endpoint].tx_output is not None and not tx_flit_fires[endpoint] else 0
                        for endpoint in range(ENDPOINTS)
                    ),
                )
            )
        max_rx_context_occupancy = max(
            max_rx_context_occupancy,
            max(len(state.rx_contexts) for state in states),
        )

        complete = (
            rx_done_count == len(packet_list)
            and tx_done_count == len(packet_list)
            and all(
                state.tx_active is None
                and not state.tx_fifo
                and not state.tx_reads
                and state.tx_output is None
                and not state.rx_contexts
                and state.completion is None
                for state in states
            )
            and all(router.idle() for router in routers)
        )
        if complete:
            return PacketMeshResult(
                cycles=cycle + 1,
                descriptors=packet_list,
                rx_descriptor_handshakes=tuple(rx_handshakes),
                tx_descriptor_handshakes=tuple(tx_handshakes),
                source_memory_requests=tuple(source_requests),
                source_memory_responses=tuple(source_responses),
                destination_memory_writes=tuple(destination_writes),
                completions=tuple(completions),
                completion_handshakes=tuple(completion_handshakes),
                deliveries=tuple(deliveries),
                link_transfers=tuple(link_transfers),
                router_summaries=tuple(
                    state.snapshot(router_traces[endpoint], router_forwarded[endpoint])
                    for endpoint, state in enumerate(routers)
                ),
                protocol_errors=tuple(
                    endpoint for endpoint, state in enumerate(states) if state.protocol_error
                ),
                max_rx_context_occupancy=max_rx_context_occupancy,
                mesh_traces=tuple(mesh_traces),
            )
        cycle += 1

    raise RuntimeError(
        f"packet mesh did not drain within max_cycles={max_cycles}; "
        f"rx={sum(item is not None for item in rx_done)}/{len(packet_list)} "
        f"tx={sum(item is not None for item in tx_done)}/{len(packet_list)}"
    )


def _packet_index_for_flit(flit: ModelFlit, descriptors: Sequence[PacketDescriptor]) -> int:
    matches = [
        index
        for index, descriptor in enumerate(descriptors)
        if descriptor.source == flit.source
        and descriptor.destination == flit.destination
        and descriptor.vc == flit.vc
        and descriptor.tag == flit.tag
    ]
    if not matches:
        raise RuntimeError("delivered flit does not match any packet descriptor")
    # Concrete tags are the wire identity.  Duplicate live keys are rejected
    # at RX descriptor installation, so the first match is unambiguous while a
    # packet is in flight.
    return matches[0]


simulate_noc_sram_packet_mesh = simulate_packet_mesh
