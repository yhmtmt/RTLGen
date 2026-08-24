"""Cycle model for the shared-SRAM read-group adapter service."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdapterServiceResult:
    beat_width: int
    group_slots: int
    groups: int
    segments_per_macro_read: int
    cycle_count: int
    beat_request_count: int
    macro_read_count: int
    beat_response_count: int
    beat_request_stall_count: int
    beat_response_stall_count: int
    macro_request_stall_count: int
    macro_response_stall_count: int
    folded_result: int
    protocol_error: bool
    access_reduction_proven: bool

    def to_dict(self) -> dict[str, int | bool]:
        return asdict(self)


def simulate_shared_sram_read_group_adapter(
    *,
    beat_width: int,
    group_slots: int,
    groups: int = 64,
    seed: int = 0x12345678,
    response_ready_pattern: tuple[bool, ...] = (True, True, True, True, True, False, True, True),
) -> AdapterServiceResult:
    if beat_width not in (256, 512):
        raise ValueError("beat_width must be 256 or 512")
    if group_slots < 1:
        raise ValueError("group_slots must be positive")
    if groups < 1:
        raise ValueError("groups must be positive")
    if not response_ready_pattern:
        raise ValueError("response_ready_pattern must not be empty")

    macro_width = 1024
    macro_bytes = macro_width // 8
    beat_bytes = beat_width // 8
    segments = macro_width // beat_width
    total_beats = groups * segments
    empty, collect, ready, inflight, emit = range(5)

    state = [empty] * group_slots
    base_addr = [0] * group_slots
    next_addr = [0] * group_slots
    collect_slot = 0
    issue_slot = 0
    emit_slot = 0
    macro_slot = 0
    macro_addr = 0
    macro_inflight = False
    emit_index = 0

    macro_rsp_valid = False
    macro_rsp_addr = 0
    macro_rsp_slot = 0
    cycle_count = 0
    issued = 0
    received = 0
    macro_reads = 0
    request_stalls = 0
    response_stalls = 0
    macro_request_stalls = 0
    macro_response_stalls = 0
    folded_result = 0
    protocol_error = False

    while received < total_beats:
        if cycle_count > total_beats * 16 + 1024:
            raise RuntimeError("adapter cycle model did not converge")

        req_valid = issued < total_beats
        req_addr = 0x00100000 + issued * beat_bytes
        collect_empty = state[collect_slot] == empty
        collect_active = state[collect_slot] == collect
        first_valid = req_addr % beat_bytes == 0 and req_addr % macro_bytes == 0
        continuing_valid = req_addr == next_addr[collect_slot]
        metadata_valid = first_valid if collect_empty else continuing_valid if collect_active else False
        request_slot_available = collect_empty or collect_active
        req_ready = not protocol_error and request_slot_available and metadata_valid
        request_fire = req_valid and req_ready

        macro_response_valid_for_request = macro_rsp_valid and macro_inflight
        macro_response_metadata_valid = macro_rsp_slot == macro_slot and macro_rsp_addr == macro_addr
        macro_response_accept = (
            macro_response_valid_for_request and macro_response_metadata_valid and not protocol_error
        )
        macro_request_valid = (
            not protocol_error
            and (not macro_inflight or macro_response_accept)
            and state[issue_slot] == ready
        )
        macro_request_fire = macro_request_valid

        response_valid = not protocol_error and state[emit_slot] == emit
        response_ready = response_ready_pattern[cycle_count % len(response_ready_pattern)]
        response_fire = response_valid and response_ready
        response_addr = base_addr[emit_slot] + emit_index * beat_bytes

        if req_valid and not req_ready:
            request_stalls += 1
        if response_valid and not response_ready:
            response_stalls += 1
        if macro_request_valid and not macro_request_fire:
            macro_request_stalls += 1
        if macro_rsp_valid and not macro_inflight:
            macro_response_stalls += 1

        new_state = list(state)
        new_base_addr = list(base_addr)
        new_next_addr = list(next_addr)
        new_collect_slot = collect_slot
        new_issue_slot = issue_slot
        new_emit_slot = emit_slot
        new_macro_slot = macro_slot
        new_macro_addr = macro_addr
        new_macro_inflight = macro_inflight
        new_emit_index = emit_index

        if request_fire:
            issued += 1
            if collect_empty:
                new_base_addr[collect_slot] = req_addr
                new_next_addr[collect_slot] = req_addr + beat_bytes
                new_state[collect_slot] = collect
            else:
                new_next_addr[collect_slot] = req_addr + beat_bytes
                if next_addr[collect_slot] + beat_bytes == base_addr[collect_slot] + macro_bytes:
                    new_state[collect_slot] = ready
                    new_collect_slot = (collect_slot + 1) % group_slots

        if macro_response_accept:
            new_macro_inflight = False
            new_state[macro_slot] = emit

        if macro_request_fire:
            new_macro_inflight = True
            new_macro_slot = issue_slot
            new_macro_addr = base_addr[issue_slot]
            new_state[issue_slot] = inflight
            new_issue_slot = (issue_slot + 1) % group_slots
            macro_reads += 1

        if response_fire:
            received += 1
            folded_result ^= response_addr
            if emit_index == segments - 1:
                new_state[emit_slot] = empty
                new_emit_slot = (emit_slot + 1) % group_slots
                new_emit_index = 0
            else:
                new_emit_index = emit_index + 1

        new_macro_rsp_valid = macro_rsp_valid
        if macro_rsp_valid and macro_inflight:
            new_macro_rsp_valid = False
        if macro_request_fire:
            new_macro_rsp_valid = True
            macro_rsp_addr = base_addr[issue_slot]
            macro_rsp_slot = issue_slot

        state = new_state
        base_addr = new_base_addr
        next_addr = new_next_addr
        collect_slot = new_collect_slot
        issue_slot = new_issue_slot
        emit_slot = new_emit_slot
        macro_slot = new_macro_slot
        macro_addr = new_macro_addr
        macro_inflight = new_macro_inflight
        emit_index = new_emit_index
        macro_rsp_valid = new_macro_rsp_valid
        cycle_count += 1

    return AdapterServiceResult(
        beat_width=beat_width,
        group_slots=group_slots,
        groups=groups,
        segments_per_macro_read=segments,
        cycle_count=cycle_count,
        beat_request_count=issued,
        macro_read_count=macro_reads,
        beat_response_count=received,
        beat_request_stall_count=request_stalls,
        beat_response_stall_count=response_stalls,
        macro_request_stall_count=macro_request_stalls,
        macro_response_stall_count=macro_response_stalls,
        folded_result=folded_result & 0xFFFFFFFF,
        protocol_error=protocol_error,
        access_reduction_proven=(macro_reads > 0 and issued == macro_reads * segments and received == issued),
    )


__all__ = ["AdapterServiceResult", "simulate_shared_sram_read_group_adapter"]
