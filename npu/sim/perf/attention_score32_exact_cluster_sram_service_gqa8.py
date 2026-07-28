"""Reference model and manifest helpers for the exact GQA8 cluster SRAM service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

JsonDict = dict[str, Any]

CONFIG_KEY = "attention_score32_exact_cluster_sram_service_gqa8"
MANIFEST_NAME = "attention_score32_exact_cluster_sram_service_gqa8_manifest.json"
HEAD_BASES = (0, 8, 16, 24)
PERSISTENT_WAVES = 8
STREAMS = 2
VALUE_SLICES = 16
BLOCK_SLOTS_PER_STREAM = 64
BUFFERS = 2
BANKS = VALUE_SLICES
ROW_BITS = 512
ROWS_PER_BANK_PER_BUFFER = STREAMS * BLOCK_SLOTS_PER_STREAM
ROWS_PER_BUFFER = BANKS * ROWS_PER_BANK_PER_BUFFER
BUFFER_BYTES = ROWS_PER_BUFFER * ROW_BITS // 8
DOUBLE_BUFFER_BYTES = BUFFERS * BUFFER_BYTES
VALUE_REQ_ADDR_W = 14
VALUE_SLICE_W = 4
COMMAND_WAVE_W = 3
COMMAND_HEAD_BASE_W = 5
TAG_W = 16
COUNTER_W = 32
RESP_FIFO_DEPTH = 1

ARCHITECTURE_METADATA = {
    "topology": "mesh2d",
    "scheduler_policy": "locality_aware",
    "reduction_strategy": "cluster_tree",
    "endpoint_policy": "per_cluster_local",
    "schedule_policy": "prefetch_overlap",
    "bank_arbiter_policy": "locality_first",
    "virtual_channels": 4,
}


def exact_local_cluster_gqa8_extra_producers(*, producers: int, group_index: int) -> tuple[int, ...]:
    producer_count = int(producers)
    resolved_group_index = int(group_index)
    if producer_count == 53:
        group_windows = ((0, 11), (11, 22), (22, 33), (33, 44))
    elif producer_count == 54:
        group_windows = ((0, 10), (10, 20), (20, 30), (30, 40))
    else:
        raise ValueError("producers must be exactly 53 or 54")
    if resolved_group_index not in range(4):
        raise ValueError("group_index must be in [0, 3]")
    start, stop = group_windows[resolved_group_index]
    return tuple(range(start, stop))


def exact_local_cluster_gqa8_command_block_counts(*, producers: int, group_index: int) -> tuple[int, ...]:
    producer_count = int(producers)
    extras = set(exact_local_cluster_gqa8_extra_producers(producers=producer_count, group_index=group_index))
    return tuple(2 if producer_index in extras else 1 for producer_index in range(producer_count))


def exact_local_cluster_gqa8_slot_bases(*, producers: int, group_index: int) -> tuple[int, ...]:
    counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=group_index)
    bases: list[int] = []
    cursor = 0
    for count in counts:
        bases.append(cursor)
        cursor += count
    if cursor != BLOCK_SLOTS_PER_STREAM:
        raise AssertionError("corrected p53/p54 schedule must map exactly 64 slots per stream")
    return tuple(bases)


def build_default_config(*, producers: int = 53) -> JsonDict:
    producer_count = int(producers)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    return {
        "top_name": f"attention_score32_exact_cluster_sram_service_gqa8_p{producer_count}",
        CONFIG_KEY: {"producers": producer_count},
        "probe_defaults": {
            "head_bases": list(HEAD_BASES),
            "waves": PERSISTENT_WAVES,
            "seed": 73,
        },
    }


def cluster_sram_service_manifest(*, producers: int) -> JsonDict:
    producer_count = int(producers)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    schedule = {
        "head_bases": list(HEAD_BASES),
        "per_group_command_block_counts": [
            list(exact_local_cluster_gqa8_command_block_counts(producers=producer_count, group_index=group_index))
            for group_index in range(4)
        ],
        "per_group_block_slot_bases": [
            list(exact_local_cluster_gqa8_slot_bases(producers=producer_count, group_index=group_index))
            for group_index in range(4)
        ],
        "per_group_total_blocks_per_stream": [BLOCK_SLOTS_PER_STREAM] * 4,
    }
    return {
        "architecture_metadata": dict(ARCHITECTURE_METADATA),
        "endpoint_scope": "per_cluster_sram_endpoint_not_mesh_router",
        "producers": producer_count,
        "lanes": producer_count * STREAMS,
        "streams": STREAMS,
        "banks": BANKS,
        "bank_index": "value_slice",
        "bank_reads_per_cycle": 1,
        "row_bits": ROW_BITS,
        "block_slots_per_stream": BLOCK_SLOTS_PER_STREAM,
        "rows_per_bank_per_buffer": ROWS_PER_BANK_PER_BUFFER,
        "rows_per_buffer": ROWS_PER_BUFFER,
        "fill_rows_per_target": ROWS_PER_BUFFER,
        "buffer_bytes": BUFFER_BYTES,
        "buffers": BUFFERS,
        "double_buffer_bytes_per_cluster": DOUBLE_BUFFER_BYTES,
        "response_fifo_depth_per_lane": RESP_FIFO_DEPTH,
        "request_contract": "relative_address_bits_13_3_zero_low3_less_than_internal_corrected_schedule_block_count",
        "block_slot_mapping": "corrected_p53_p54_group_specific_prefix_slot_base_plus_relative_low3",
        "arbitration": "one_grant_per_slice_bank_per_cycle_round_robin_across_producer_stream_lanes",
        "backpressure_contract": "all_ready_valid_inputs_may_hold_valid_without_protocol_error_until_handshake",
        "fill_contract": "target_declares_buffer_command_head_group_wave_then_2048_unique_stream_slot_slice_rows",
        "residence_contract": "command_accept_requires_exact_resident_buffer_command_head_group_wave_tuple",
        "schedule": schedule,
        "counters": [
            "cycle_count",
            "fill_target_accept_count",
            "fill_row_accept_count",
            "fill_stall_cycles",
            "request_accept_count",
            "request_stall_cycles",
            "response_accept_count",
            "response_stall_cycles",
            "bank_conflict_count",
            "command_accept_count",
            "command_release_count",
            "buffer_occupancy_rows",
            "outstanding_response_occupancy",
        ],
        "protocol_errors": [
            "invalid_metadata",
            "invalid_address",
            "residency",
            "overwrite",
            "command",
        ],
        "remaining_abstractions": [
            "mesh_router_not_instantiated_here",
            "external_hbm_fill_stream_only",
            "inferred_memory_not_macro_closed",
        ],
    }


@dataclass(frozen=True)
class Response:
    lane: int
    address: int
    slice_index: int
    data: int
    tag: int


class ClusterSramServiceModel:
    """Cycle-level Python model for the SRAM endpoint handshake and arbitration rules."""

    def __init__(self, *, producers: int) -> None:
        producer_count = int(producers)
        if producer_count not in {53, 54}:
            raise ValueError("producers must be exactly 53 or 54")
        self.producers = producer_count
        self.lanes = producer_count * STREAMS
        self.memory: dict[tuple[int, int, int, int], int] = {}
        self.valid_rows: set[tuple[int, int, int, int]] = set()
        self.target: tuple[int, int, int, int] | None = None
        self.resident: list[tuple[int, int, int] | None] = [None, None]
        self.active: tuple[int, int, int, int] | None = None
        self.responses: list[Response | None] = [None] * self.lanes
        self.bank_rr = [0] * BANKS
        self.counters = {
            "cycle_count": 0,
            "fill_target_accept_count": 0,
            "fill_row_accept_count": 0,
            "fill_stall_cycles": 0,
            "request_accept_count": 0,
            "request_stall_cycles": 0,
            "response_accept_count": 0,
            "response_stall_cycles": 0,
            "bank_conflict_count": 0,
            "command_accept_count": 0,
            "command_release_count": 0,
        }
        self.occupancy = [0, 0]
        self.errors = {
            "invalid_metadata": False,
            "invalid_address": False,
            "residency": False,
            "overwrite": False,
            "command": False,
        }

    @property
    def protocol_error(self) -> bool:
        return any(self.errors.values())

    @property
    def outstanding_response_occupancy(self) -> int:
        return sum(1 for response in self.responses if response is not None)

    @property
    def buffer_occupancy_rows(self) -> tuple[int, int]:
        return tuple(self.occupancy)

    @staticmethod
    def _metadata_valid(*, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> bool:
        return (
            buffer_sel in {0, 1}
            and 0 <= int(command_id) < (1 << 16)
            and int(head_base) in HEAD_BASES
            and 0 <= int(wave_index) < PERSISTENT_WAVES
        )

    def fill_target_ready(self, *, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> bool:
        return self._metadata_valid(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ) and self.target is None and self.resident[buffer_sel] is None and not (
            self.active is not None and self.active[0] == buffer_sel
        )

    def accept_fill_target(self, *, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> bool:
        if not self._metadata_valid(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ):
            self.errors["invalid_metadata"] = True
            return False
        if not self.fill_target_ready(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ):
            return False
        self.valid_rows = {row for row in self.valid_rows if row[0] != buffer_sel}
        self.memory = {key: value for key, value in self.memory.items() if key[0] != buffer_sel}
        self.occupancy[buffer_sel] = 0
        self.target = (buffer_sel, int(command_id), int(head_base), int(wave_index))
        self.counters["fill_target_accept_count"] += 1
        return True

    def note_fill_stall(self, count: int = 1) -> None:
        self.counters["fill_stall_cycles"] += int(count)

    def fill_row(
        self,
        *,
        buffer_sel: int,
        stream: int,
        block_slot: int,
        slice_index: int,
        data: int,
    ) -> bool:
        if self.target is None:
            return False
        if (
            buffer_sel != self.target[0]
            or stream not in range(STREAMS)
            or block_slot not in range(BLOCK_SLOTS_PER_STREAM)
            or slice_index not in range(VALUE_SLICES)
            or not 0 <= int(data) < (1 << ROW_BITS)
        ):
            self.errors["invalid_metadata"] = True
            return False
        key = (buffer_sel, stream, block_slot, slice_index)
        if key in self.valid_rows:
            self.errors["overwrite"] = True
            return False
        self.memory[key] = int(data)
        self.valid_rows.add(key)
        self.occupancy[buffer_sel] += 1
        self.counters["fill_row_accept_count"] += 1
        if self.occupancy[buffer_sel] == ROWS_PER_BUFFER:
            _, command_id, head_base, wave_index = self.target
            self.resident[buffer_sel] = (command_id, head_base, wave_index)
            self.target = None
        return True

    def command_ready(self, *, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> bool:
        return self._metadata_valid(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ) and self.active is None and self.resident[buffer_sel] == (
            int(command_id),
            int(head_base),
            int(wave_index),
        )

    def accept_command(self, *, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> bool:
        if not self._metadata_valid(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ):
            self.errors["invalid_metadata"] = True
            return False
        if not self.command_ready(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ):
            return False
        self.active = (buffer_sel, int(command_id), int(head_base), int(wave_index))
        self.counters["command_accept_count"] += 1
        return True

    def release_command(self, *, buffer_sel: int) -> bool:
        if self.active is None or self.active[0] != int(buffer_sel) or any(self.responses):
            self.errors["command"] = True
            return False
        self.active = None
        self.resident[buffer_sel] = None
        self.occupancy[buffer_sel] = 0
        self.counters["command_release_count"] += 1
        return True

    def _decode(self, lane: int, address: int, slice_index: int) -> tuple[bool, int, int, int]:
        producer = lane // STREAMS
        stream = lane % STREAMS
        assert self.active is not None
        group_index = self.active[2] // 8
        counts = exact_local_cluster_gqa8_command_block_counts(
            producers=self.producers,
            group_index=group_index,
        )
        bases = exact_local_cluster_gqa8_slot_bases(producers=self.producers, group_index=group_index)
        valid = (
            0 <= int(address) < (1 << VALUE_REQ_ADDR_W)
            and (int(address) >> 3) == 0
            and (int(address) & 7) < counts[producer]
            and 0 <= int(slice_index) < VALUE_SLICES
        )
        return valid, stream, bases[producer] + (int(address) & 7), int(slice_index)

    @staticmethod
    def build_tag(*, lane: int, address: int, slice_index: int) -> int:
        return ((int(lane) & 0x7F) << 7) | ((int(address) & 7) << 4) | (int(slice_index) & 0xF)

    def load_buffer(
        self,
        *,
        buffer_sel: int,
        command_id: int,
        head_base: int,
        wave_index: int,
        row_fn,
    ) -> None:
        if not self.accept_fill_target(
            buffer_sel=buffer_sel,
            command_id=command_id,
            head_base=head_base,
            wave_index=wave_index,
        ):
            raise AssertionError("fill target could not be accepted")
        for stream in range(STREAMS):
            for block_slot in range(BLOCK_SLOTS_PER_STREAM):
                for slice_index in range(VALUE_SLICES):
                    if not self.fill_row(
                        buffer_sel=buffer_sel,
                        stream=stream,
                        block_slot=block_slot,
                        slice_index=slice_index,
                        data=int(row_fn(stream, block_slot, slice_index)),
                    ):
                        raise AssertionError("fill row could not be accepted")

    def step(
        self,
        *,
        requests: Iterable[tuple[int, int, int]] = (),
        response_ready: Iterable[int] = (),
    ) -> list[Response]:
        self.counters["cycle_count"] += 1
        ready_set = {int(lane) for lane in response_ready}
        accepted_responses: list[Response] = []
        for lane, response in enumerate(self.responses):
            if response is not None and lane in ready_set:
                accepted_responses.append(response)
                self.responses[lane] = None
                self.counters["response_accept_count"] += 1
            elif response is not None:
                self.counters["response_stall_cycles"] += 1

        request_by_lane = {int(lane): (int(address), int(slice_index)) for lane, address, slice_index in requests}
        if self.active is None:
            self.counters["request_stall_cycles"] += len(request_by_lane)
            return accepted_responses

        candidates: list[list[int]] = [[] for _ in range(BANKS)]
        for lane, (_, slice_index) in request_by_lane.items():
            if lane not in range(self.lanes):
                self.errors["invalid_metadata"] = True
            elif self.responses[lane] is None:
                candidates[slice_index].append(lane)
            else:
                self.counters["request_stall_cycles"] += 1

        for bank, lanes in enumerate(candidates):
            if not lanes:
                continue
            ordered = sorted(lanes, key=lambda lane: (lane - self.bank_rr[bank]) % self.lanes)
            selected = ordered[0]
            loser_count = len(ordered) - 1
            self.counters["request_stall_cycles"] += loser_count
            self.counters["bank_conflict_count"] += loser_count
            address, slice_index = request_by_lane[selected]
            valid, stream, block_slot, _ = self._decode(selected, address, slice_index)
            data = 0
            if valid:
                key = (self.active[0], stream, block_slot, slice_index)
                if key not in self.valid_rows:
                    self.errors["residency"] = True
                else:
                    data = self.memory[key]
            else:
                self.errors["invalid_address"] = True
            self.responses[selected] = Response(
                lane=selected,
                address=address,
                slice_index=slice_index,
                data=data,
                tag=self.build_tag(lane=selected, address=address, slice_index=slice_index),
            )
            self.bank_rr[bank] = (selected + 1) % self.lanes
            self.counters["request_accept_count"] += 1
        return accepted_responses


__all__ = [
    "ARCHITECTURE_METADATA",
    "BANKS",
    "BLOCK_SLOTS_PER_STREAM",
    "BUFFER_BYTES",
    "BUFFERS",
    "COMMAND_HEAD_BASE_W",
    "COMMAND_WAVE_W",
    "CONFIG_KEY",
    "COUNTER_W",
    "ClusterSramServiceModel",
    "DOUBLE_BUFFER_BYTES",
    "HEAD_BASES",
    "MANIFEST_NAME",
    "PERSISTENT_WAVES",
    "RESP_FIFO_DEPTH",
    "ROWS_PER_BANK_PER_BUFFER",
    "ROWS_PER_BUFFER",
    "ROW_BITS",
    "STREAMS",
    "TAG_W",
    "VALUE_REQ_ADDR_W",
    "VALUE_SLICE_W",
    "VALUE_SLICES",
    "Response",
    "build_default_config",
    "cluster_sram_service_manifest",
    "exact_local_cluster_gqa8_command_block_counts",
    "exact_local_cluster_gqa8_extra_producers",
    "exact_local_cluster_gqa8_slot_bases",
]
