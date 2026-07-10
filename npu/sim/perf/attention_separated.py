"""Exact functional and cycle reference for the separated attention cluster."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

ROW_ELEMS = 8
HEAD_DIM = 8
VALUE_DIM = 8
SCORE_BITS = 32
WEIGHT_BITS = 16
VALUE_BITS = 8
VALUE_ACCUM_BITS = 40
INPUT_FRAC_BITS = 28
EXP_BUCKET_SHIFT = 20
MAX_EXP_BUCKET = 8 << (INPUT_FRAC_BITS - EXP_BUCKET_SHIFT)
WEIGHT_SCALE = (1 << WEIGHT_BITS) - 1

JsonDict = dict[str, Any]


@dataclass(frozen=True)
class AttentionSeparatedCommand:
    command_id: int
    seed: int

    def normalized(self) -> "AttentionSeparatedCommand":
        return AttentionSeparatedCommand(self.command_id & 0xFFFF, self.seed & 0xFFFFFFFF)


def default_commands(count: int = 8) -> list[AttentionSeparatedCommand]:
    return [
        AttentionSeparatedCommand(
            command_id=(0x120 + index * 0x17) & 0xFFFF,
            seed=(0x13579BDF * (index + 1) + 0x2468ACE0) & 0xFFFFFFFF,
        )
        for index in range(count)
    ]


def _u32(value: int) -> int:
    return value & 0xFFFFFFFF


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def derive_q8(command: AttentionSeparatedCommand, *, tag: int, lane_a: int, lane_b: int) -> int:
    command = command.normalized()
    mixed = _u32(command.seed ^ command.command_id)
    mixed = _u32(mixed ^ _u32(tag * 0x119DE1F3))
    mixed = _u32(mixed ^ _u32(lane_a * 0x344B5409))
    mixed = _u32(mixed ^ _u32(lane_b * 0x27D4EB2D))
    mixed = _u32(mixed ^ (mixed >> 16))
    mixed = _u32(mixed ^ (mixed >> 8))
    return _signed(mixed & 0xF, 4)


def command_tensors(command: AttentionSeparatedCommand) -> JsonDict:
    q = [derive_q8(command, tag=17, lane_a=0, lane_b=dim) for dim in range(HEAD_DIM)]
    keys = [
        [derive_q8(command, tag=51, lane_a=row, lane_b=dim) for dim in range(HEAD_DIM)]
        for row in range(ROW_ELEMS)
    ]
    values = [
        [derive_q8(command, tag=85, lane_a=row, lane_b=dim) for dim in range(VALUE_DIM)]
        for row in range(ROW_ELEMS)
    ]
    return {"q": q, "k": keys, "v": values}


def producer_result(command: AttentionSeparatedCommand) -> JsonDict:
    command = command.normalized()
    tensors = command_tensors(command)
    scores = [
        _signed(sum(q * k for q, k in zip(tensors["q"], key_row)) << EXP_BUCKET_SHIFT, SCORE_BITS)
        for key_row in tensors["k"]
    ]
    return {
        "command_id": command.command_id,
        "seed": command.seed,
        "score_row": scores,
        "value_matrix": tensors["v"],
    }


def _exp_lut(bucket: int) -> int:
    bucket = min(max(0, int(bucket)), MAX_EXP_BUCKET)
    scale = float(1 << EXP_BUCKET_SHIFT) / float(1 << INPUT_FRAC_BITS)
    return max(1, int(math.exp(-(bucket * scale)) * WEIGHT_SCALE + 0.5))


def consumer_result(payload: JsonDict) -> JsonDict:
    scores = [int(value) for value in payload["score_row"]]
    row_max = max(scores)
    exp_values = [
        _exp_lut(((row_max - score) + (1 << (EXP_BUCKET_SHIFT - 1))) >> EXP_BUCKET_SHIFT)
        for score in scores
    ]
    exp_sum = sum(exp_values)
    weights = [(value * WEIGHT_SCALE + (exp_sum >> 1)) // exp_sum for value in exp_values]
    value_matrix = payload["value_matrix"]
    values = [
        _signed(sum(weights[row] * int(value_matrix[row][dim]) for row in range(ROW_ELEMS)), VALUE_ACCUM_BITS)
        for dim in range(VALUE_DIM)
    ]
    return {
        "command_id": int(payload["command_id"]),
        "score_row": scores,
        "weights": weights,
        "value": values,
    }


def exact_reference(command: AttentionSeparatedCommand) -> JsonDict:
    producer = producer_result(command)
    return {"producer": producer, "consumer": consumer_result(producer)}


def scenario_names() -> tuple[str, ...]:
    return (
        "always_ready",
        "intermittent_consumer_stall",
        "all_consumers_blocked_temporarily",
        "result_backpressure",
    )


def consumer_enable_mask(scenario: str, *, cycle: int, consumer_count: int) -> int:
    full = (1 << consumer_count) - 1
    if scenario in {"always_ready", "result_backpressure"}:
        return full
    if scenario == "intermittent_consumer_stall":
        return sum(1 << idx for idx in range(consumer_count) if (cycle + idx) % 4 != 1)
    if scenario == "all_consumers_blocked_temporarily":
        return 0 if 6 <= cycle < 10 else full
    raise ValueError(f"unknown scenario: {scenario}")


def result_ready(scenario: str, *, cycle: int) -> bool:
    if scenario in {"always_ready", "intermittent_consumer_stall", "all_consumers_blocked_temporarily"}:
        return True
    if scenario == "result_backpressure":
        return not (9 <= cycle < 13 or cycle % 6 == 4)
    raise ValueError(f"unknown scenario: {scenario}")


def _first_rr(valid: list[bool], start: int) -> int | None:
    for offset in range(len(valid)):
        index = (start + offset) % len(valid)
        if valid[index]:
            return index
    return None


def simulate(
    commands: list[AttentionSeparatedCommand],
    *,
    producer_count: int,
    consumer_count: int,
    scenario: str,
    max_cycles: int = 1000,
) -> JsonDict:
    if not 1 <= producer_count <= 8:
        raise ValueError("producer_count must be in [1, 8]")
    if not 1 <= consumer_count <= producer_count:
        raise ValueError("consumer_count must be in [1, producer_count]")
    if scenario not in scenario_names():
        raise ValueError(f"unknown scenario: {scenario}")

    producer_slots: list[JsonDict | None] = [None] * producer_count
    consumer_slots: list[JsonDict | None] = [None] * consumer_count
    issue_rr = dispatch_producer_rr = dispatch_consumer_rr = result_rr = 0
    command_index = accepted = completed = 0
    accept_events: list[JsonDict] = []
    dispatch_events: list[JsonDict] = []
    result_events: list[JsonDict] = []

    for cycle in range(max_cycles):
        if completed == len(commands):
            break
        enable = consumer_enable_mask(scenario, cycle=cycle, consumer_count=consumer_count)
        ready = result_ready(scenario, cycle=cycle)
        issue_index = _first_rr([slot is None for slot in producer_slots], issue_rr)
        producer_index = _first_rr([slot is not None for slot in producer_slots], dispatch_producer_rr)
        consumer_index = _first_rr(
            [slot is None and bool(enable & (1 << idx)) for idx, slot in enumerate(consumer_slots)],
            dispatch_consumer_rr,
        )
        result_index = _first_rr([slot is not None for slot in consumer_slots], result_rr)

        command_fire = command_index < len(commands) and issue_index is not None
        dispatch_fire = producer_index is not None and consumer_index is not None
        result_fire = result_index is not None and ready

        if result_fire:
            assert result_index is not None
            result = consumer_slots[result_index]
            assert result is not None
            result_events.append({"cycle": cycle, "consumer": result_index, **result})
            consumer_slots[result_index] = None
            completed += 1
            result_rr = (result_index + 1) % consumer_count

        if dispatch_fire:
            assert producer_index is not None and consumer_index is not None
            payload = producer_slots[producer_index]
            assert payload is not None
            result = consumer_result(payload)
            dispatch_events.append(
                {
                    "cycle": cycle,
                    "producer": producer_index,
                    "consumer": consumer_index,
                    "command_id": payload["command_id"],
                }
            )
            producer_slots[producer_index] = None
            consumer_slots[consumer_index] = result
            dispatch_producer_rr = (producer_index + 1) % producer_count
            dispatch_consumer_rr = (consumer_index + 1) % consumer_count

        if command_fire:
            assert issue_index is not None
            command = commands[command_index].normalized()
            producer_slots[issue_index] = producer_result(command)
            accept_events.append(
                {"cycle": cycle, "producer": issue_index, "command_id": command.command_id, "seed": command.seed}
            )
            accepted += 1
            command_index += 1
            issue_rr = (issue_index + 1) % producer_count
    else:
        raise RuntimeError(f"scenario {scenario} exceeded {max_cycles} cycles")

    summary = {
        "scenario": scenario,
        "producer_count": producer_count,
        "consumer_count": consumer_count,
        "accepted_count": accepted,
        "completed_count": completed,
        "accept_events": accept_events,
        "dispatch_events": dispatch_events,
        "result_events": result_events,
        "accepted_order": [event["command_id"] for event in accept_events],
        "completed_order": [event["command_id"] for event in result_events],
        "final_cycle": result_events[-1]["cycle"] if result_events else -1,
    }
    summary["sha256"] = hashlib.sha256(
        json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return summary


def unpack_signed(packed: int, *, lanes: int, bits: int) -> list[int]:
    return [_signed(packed >> (lane * bits), bits) for lane in range(lanes)]


def unpack_unsigned(packed: int, *, lanes: int, bits: int) -> list[int]:
    mask = (1 << bits) - 1
    return [(packed >> (lane * bits)) & mask for lane in range(lanes)]


__all__ = [
    "AttentionSeparatedCommand",
    "consumer_enable_mask",
    "consumer_result",
    "default_commands",
    "derive_q8",
    "exact_reference",
    "producer_result",
    "result_ready",
    "scenario_names",
    "simulate",
    "unpack_signed",
    "unpack_unsigned",
]
