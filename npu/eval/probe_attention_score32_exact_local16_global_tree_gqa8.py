#!/usr/bin/env python3
"""Probe the full structural GQA8 local16-to-global exact wrapper against a staged reference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    ExactPartialBeat,
    compose_local16_global_tree_gqa8_exact,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local16_global_tree_gqa8_service_manifest,
    merge_partial_streams,
    partial_stream_from_blocks,
    unpack_final_values,
    unpack_numerators,
)
from npu.sim.perf.attention_online import requantize_score_row

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_score32_exact_local16_global_tree_gqa8"
_CLUSTER_RESULT_RE = re.compile(
    r"CLUSTER_RESULT cluster=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_ROOT_RESULT_RE = re.compile(
    r"ROOT_RESULT cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+) cycle=(\d+)"
)
_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) drain=(\d+) first_root=(-?\d+) last_root=(-?\d+) protocol_error=(\d+) "
    r"global_root_completed=(\d+) global_finalizer_accepted=(\d+) global_tree_root_completed=(\d+) "
    r"global_dispatch_stall=(\d+) global_order_occupancy=(\d+) global_order_high=(\d+) "
    r"global_tree_error=(\d+) global_order_error=(\d+) global_finalizer_error=(\d+)"
)
_CLUSTER_SUMMARY_RE = re.compile(
    r"CLUSTER_SUMMARY cluster=(\d+) cycle=(\d+) wave_accept=(\d+) issue_wait=(\d+) ready_skew=(\d+) emitted=(\d+) "
    r"completed_commands=(\d+) group_error=(\d+) local_tree_error=(\d+) temporal_error=(\d+) reducer_error=(\d+) "
    r"atomic_error=(\d+) protocol_error=(\d+)"
)
_TB_TIMEOUT_RE = re.compile(r"TB_TIMEOUT cycle=(\d+)")

_FAKERAM_MODEL = """
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  initial begin
    addr_q = 0;
    rd_out_q = 0;
    for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0;
  end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) begin
        for (idx = 0; idx < 39; idx = idx + 1) begin
          if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
        end
      end
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _pack(values: list[int], bits: int) -> int:
    mask = (1 << bits) - 1
    return sum((int(value) & mask) << (index * bits) for index, value in enumerate(values))


def compare_full_rows(
    expected_rows: list[dict[str, object]],
    observed_rows: list[dict[str, object]],
) -> dict[str, object]:
    """Compare every structured field; hashes are diagnostic summary only."""
    result: dict[str, object] = {
        "passed": expected_rows == observed_rows,
        "expected_row_count": len(expected_rows),
        "observed_row_count": len(observed_rows),
        "expected_hash": _hash(expected_rows),
        "observed_hash": _hash(observed_rows),
        "first_mismatch": None,
    }
    shared_rows = min(len(expected_rows), len(observed_rows))
    for index in range(shared_rows):
        expected = expected_rows[index]
        observed = observed_rows[index]
        if expected == observed:
            continue
        fields = sorted(set(expected) | set(observed))
        for field in fields:
            if expected.get(field) != observed.get(field):
                result["first_mismatch"] = {
                    "row": index,
                    "field": field,
                    "expected": expected.get(field),
                    "observed": observed.get(field),
                }
                return result
    if len(expected_rows) != len(observed_rows):
        result["first_mismatch"] = {
            "row": shared_rows,
            "field": "__row_count__",
            "expected": len(expected_rows),
            "observed": len(observed_rows),
        }
    return result


def compare_compositional_rows(
    *,
    expected_cluster_rows: list[list[dict[str, object]]],
    observed_cluster_rows: list[list[dict[str, object]]],
    expected_root_rows: list[dict[str, object]],
    observed_root_rows: list[dict[str, object]],
) -> dict[str, object]:
    if len(expected_cluster_rows) != 16 or len(observed_cluster_rows) != 16:
        raise ValueError("compositional audit requires exactly 16 cluster row streams")
    clusters = [
        compare_full_rows(expected_cluster_rows[index], observed_cluster_rows[index])
        for index in range(16)
    ]
    root = compare_full_rows(expected_root_rows, observed_root_rows)
    return {
        "passed": all(bool(result["passed"]) for result in clusters) and bool(root["passed"]),
        "clusters": clusters,
        "root": root,
    }


def _default_config() -> JsonDict:
    cluster_producers = [54] * 8 + [53] * 8
    return {
        "top_name": "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59",
        _CONFIG_KEY: {
            "clusters": 16,
            "cluster_producers": cluster_producers,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "persistent_waves": 8,
            "divider_lanes": 8,
            "finalizer_banks": 59,
        },
        "probe_defaults": {
            "command_count": 1,
            "head_bases": [0],
            "seed": 29,
        },
        "report_links": {
            "proposal_id": "prop_l1_decoder_attention_score32_exact_local16_global_tree_gqa8_v1",
            "proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_exact_local16_global_tree_gqa8_v1/proposal.json",
        },
    }


def _resolve_workload(
    config: JsonDict,
    *,
    command_count: int | None,
    head_bases: tuple[int, ...] | None,
    seed: int | None,
) -> dict[str, object]:
    defaults = config.get("probe_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    resolved_command_count = int(command_count if command_count is not None else defaults.get("command_count", 2))
    resolved_seed = int(seed if seed is not None else defaults.get("seed", 29))
    resolved_head_bases = head_bases
    if resolved_head_bases is None and isinstance(defaults.get("head_bases"), list):
        resolved_head_bases = tuple(int(value) for value in defaults["head_bases"])
    if resolved_head_bases is None:
        resolved_head_bases = tuple(index * 8 for index in range(resolved_command_count))
    if resolved_command_count < 1 or resolved_command_count > 4:
        raise ValueError("command_count must be in [1, 4]")
    if len(resolved_head_bases) != resolved_command_count:
        raise ValueError("head_bases length must match command_count")
    for head_base in resolved_head_bases:
        if head_base < 0 or head_base > 24 or (head_base % 8):
            raise ValueError("head_bases must be 8-aligned and lie in [0, 24]")
    return {
        "command_count": resolved_command_count,
        "head_bases": tuple(resolved_head_bases),
        "seed": resolved_seed,
    }


def _logical_commands(workload: dict[str, object]) -> tuple[dict[str, int], ...]:
    commands = []
    for index, head_base in enumerate(tuple(int(value) for value in workload["head_bases"])):
        multiplier, shift = _score_params(int(head_base))
        commands.append(
            {
                "logical_index": index,
                "group_index": int(head_base) >> 3,
                "command_id": 0x8200 + index,
                "head_base": int(head_base),
                "multiplier": multiplier,
                "shift": shift,
            }
        )
    return tuple(commands)


def _wave_command_schedule(workload: dict[str, object]) -> tuple[dict[str, int], ...]:
    commands = []
    for logical_command in _logical_commands(workload):
        for wave_index in range(LOCAL_TEMPORAL_WAVES):
            commands.append({**logical_command, "wave_index": wave_index})
    return tuple(commands)


def _stream_block_beats(
    *,
    cluster: int,
    producer: int,
    group_index: int,
    wave_index: int,
    stream: int,
    block_count: int,
    seed: int,
) -> tuple[tuple[tuple[tuple[int, ...], tuple[int, ...]], ...], ...]:
    blocks = []
    for block_index in range(block_count):
        queries = tuple(
            (
                (
                    seed * 17
                    + cluster * 19
                    + producer * 23
                    + group_index * 29
                    + wave_index * 31
                    + stream * 37
                    + block_index * 41
                    + head_lane * 43
                )
                % 127
            )
            - 63
            for head_lane in range(8)
        )
        keys = tuple(
            (
                (
                    seed * 47
                    + cluster * 53
                    + producer * 59
                    + group_index * 61
                    + wave_index * 67
                    + stream * 71
                    + block_index * 73
                    + token_lane * 79
                )
                % 127
            )
            - 63
            for token_lane in range(8)
        )
        blocks.append((((tuple(queries), tuple(keys))),))
    return tuple(blocks)


def _value_blocks(
    *,
    cluster: int,
    producer: int,
    group_index: int,
    wave_index: int,
    stream: int,
    block_count: int,
    seed: int,
) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    (
                        (
                            seed * 83
                            + cluster * 89
                            + producer * 97
                            + group_index * 101
                            + wave_index * 103
                            + stream * 107
                            + block_index * 109
                            + value_slice * 113
                            + row * 127
                            + lane * 131
                        )
                        % 255
                    )
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block_index in range(block_count)
    )


def _raw_scores(block: tuple[tuple[int, ...], tuple[int, ...]], head_lane: int) -> list[int]:
    queries, keys = block
    return [int(queries[head_lane]) * int(keys[token_lane]) for token_lane in range(8)]


def _producer_wave_stream(
    *,
    cluster: int,
    producer: int,
    logical_command: dict[str, int],
    wave_index: int,
    block_count: int,
    seed: int,
) -> tuple[ExactPartialBeat, ...]:
    merged_per_head = []
    for head_lane in range(8):
        stream_partials = []
        for stream in range(2):
            blocks = _stream_block_beats(
                cluster=cluster,
                producer=producer,
                group_index=int(logical_command["group_index"]),
                wave_index=wave_index,
                stream=stream,
                block_count=block_count,
                seed=seed,
            )
            score_rows = [
                list(
                    requantize_score_row(
                        _raw_scores(blocks[block_index][0], head_lane),
                        multiplier=int(logical_command["multiplier"]),
                        shift=int(logical_command["shift"]),
                    )
                )
                for block_index in range(block_count)
            ]
            stream_partials.append(
                partial_stream_from_blocks(
                    command_id=int(logical_command["command_id"]),
                    head_id=int(logical_command["head_base"]) + head_lane,
                    score_rows=score_rows,
                    value_blocks=_value_blocks(
                        cluster=cluster,
                        producer=producer,
                        group_index=int(logical_command["group_index"]),
                        wave_index=wave_index,
                        stream=stream,
                        block_count=block_count,
                        seed=seed,
                    ),
                )
            )
        merged_per_head.append(merge_partial_streams(stream_partials[0], stream_partials[1]))
    return tuple(beat for head_stream in merged_per_head for beat in head_stream)


def _cluster_bases(cluster_producers: tuple[int, ...]) -> tuple[int, ...]:
    bases: list[int] = []
    running = 0
    for producer_count in cluster_producers:
        bases.append(running)
        running += int(producer_count)
    return tuple(bases)


def _hierarchy_driver_data(cluster_producers: tuple[int, ...], workload: dict[str, object]) -> dict[str, object]:
    wave_commands = _wave_command_schedule(workload)
    total_producers = sum(cluster_producers)
    cluster_bases = _cluster_bases(cluster_producers)
    query_mem: list[list[int]] = [[] for _ in range(total_producers)]
    key_mem: list[list[int]] = [[] for _ in range(total_producers)]
    last_mem: list[list[int]] = [[] for _ in range(total_producers)]
    value_mem: list[list[int]] = [[] for _ in range(total_producers * 2)]
    beat_limits = [[0 for _ in range(total_producers)] for _ in range(len(wave_commands))]
    block_offsets = [[0 for _ in range(total_producers)] for _ in range(len(wave_commands))]
    command_block_counts = [[0 for _ in range(total_producers)] for _ in range(len(wave_commands))]
    max_beats_per_producer = 0
    max_blocks_per_producer = 0

    for cluster, producer_count in enumerate(cluster_producers):
        producer_base = cluster_bases[cluster]
        for producer in range(producer_count):
            global_index = producer_base + producer
            cumulative_beats = 0
            cumulative_blocks = 0
            stream_values: list[list[int]] = [[], []]
            for command_index, wave_command in enumerate(wave_commands):
                block_count = int(
                    exact_local_cluster_gqa8_command_block_counts(
                        producers=int(producer_count),
                        group_index=int(wave_command["group_index"]),
                    )[producer]
                )
                command_block_counts[command_index][global_index] = block_count
                block_offsets[command_index][global_index] = cumulative_blocks
                blocks0 = _stream_block_beats(
                    cluster=cluster,
                    producer=producer,
                    group_index=int(wave_command["group_index"]),
                    wave_index=int(wave_command["wave_index"]),
                    stream=0,
                    block_count=block_count,
                    seed=int(workload["seed"]),
                )
                blocks1 = _stream_block_beats(
                    cluster=cluster,
                    producer=producer,
                    group_index=int(wave_command["group_index"]),
                    wave_index=int(wave_command["wave_index"]),
                    stream=1,
                    block_count=block_count,
                    seed=int(workload["seed"]),
                )
                values0 = _value_blocks(
                    cluster=cluster,
                    producer=producer,
                    group_index=int(wave_command["group_index"]),
                    wave_index=int(wave_command["wave_index"]),
                    stream=0,
                    block_count=block_count,
                    seed=int(workload["seed"]),
                )
                values1 = _value_blocks(
                    cluster=cluster,
                    producer=producer,
                    group_index=int(wave_command["group_index"]),
                    wave_index=int(wave_command["wave_index"]),
                    stream=1,
                    block_count=block_count,
                    seed=int(workload["seed"]),
                )
                for block_index in range(block_count):
                    queries0, keys0 = blocks0[block_index][0]
                    queries1, keys1 = blocks1[block_index][0]
                    query_mem[global_index].append(_pack(list(queries0), 8) | (_pack(list(queries1), 8) << 64))
                    key_mem[global_index].append(_pack(list(keys0), 8) | (_pack(list(keys1), 8) << 64))
                    last_mem[global_index].append(1)
                    for value_slice in range(16):
                        stream_values[0].append(_pack([lane for row in values0[block_index][value_slice] for lane in row], 8))
                        stream_values[1].append(_pack([lane for row in values1[block_index][value_slice] for lane in row], 8))
                cumulative_beats += block_count
                cumulative_blocks += block_count
                beat_limits[command_index][global_index] = cumulative_beats
            value_mem[global_index * 2] = stream_values[0]
            value_mem[(global_index * 2) + 1] = stream_values[1]
            max_beats_per_producer = max(max_beats_per_producer, cumulative_beats)
            max_blocks_per_producer = max(max_blocks_per_producer, cumulative_blocks)

    return {
        "wave_commands": wave_commands,
        "cluster_bases": cluster_bases,
        "query_mem": query_mem,
        "key_mem": key_mem,
        "last_mem": last_mem,
        "value_mem": value_mem,
        "beat_limits": beat_limits,
        "block_offsets": block_offsets,
        "command_block_counts": command_block_counts,
        "max_beats_per_producer": max_beats_per_producer,
        "max_blocks_per_producer": max_blocks_per_producer,
    }


def _reference(config: JsonDict, workload: dict[str, object]) -> dict[str, object]:
    body = config.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise ValueError(f"config must contain {_CONFIG_KEY}")
    cluster_producers = tuple(int(value) for value in body["cluster_producers"])
    expected_cluster_rows: list[list[dict[str, object]]] = [[] for _ in range(16)]
    expected_root_rows: list[dict[str, object]] = []

    for logical_command in _logical_commands(workload):
        composition = compose_local16_global_tree_gqa8_exact(
            tuple(
                tuple(
                    tuple(
                        _producer_wave_stream(
                            cluster=cluster,
                            producer=producer,
                            logical_command=logical_command,
                            wave_index=wave_index,
                            block_count=int(
                                exact_local_cluster_gqa8_command_block_counts(
                                    producers=int(cluster_producers[cluster]),
                                    group_index=int(logical_command["group_index"]),
                                )[producer]
                            ),
                            seed=int(workload["seed"]),
                        )
                        for producer in range(cluster_producers[cluster])
                    )
                    for wave_index in range(LOCAL_TEMPORAL_WAVES)
                )
                for cluster in range(16)
            )
        )
        for cluster in range(16):
            expected_cluster_rows[cluster].extend(
                {
                    "cluster": cluster,
                    "command_id": beat.command_id,
                    "head_id": beat.head_id,
                    "slice": beat.slice_index,
                    "last": beat.last,
                    "global_max": beat.max_score,
                    "exp_sum": beat.exp_sum,
                    "value": list(beat.numerators),
                }
                for beat in composition.cluster_compositions[cluster].temporal_aggregate
            )
        expected_root_rows.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "value": list(beat.values),
            }
            for beat in composition.finalized_beats
        )

    return {
        "cluster_rows": expected_cluster_rows,
        "root_rows": expected_root_rows,
        "cluster_hashes": [_hash(rows) for rows in expected_cluster_rows],
        "root_hash": _hash(expected_root_rows),
    }


def _ready_init(pattern: tuple[bool, ...]) -> str:
    return "\n".join(f"    root_ready_mem[{index}] = 1'b{1 if value else 0};" for index, value in enumerate(pattern))


def _score_params(head_base: int) -> tuple[int, int]:
    group_index = int(head_base) >> 3
    if group_index == 0:
        return (1 << 20), 0
    if group_index == 1:
        return 13, 1
    if group_index == 2:
        return 29, 2
    return 37, 1


def _expected_cluster_summary_counts(workload: dict[str, object]) -> dict[str, int]:
    return {
        "wave_command_accept_count": int(workload["command_count"]) * LOCAL_TEMPORAL_WAVES,
        "emitted_beat_count": int(workload["command_count"]) * 128,
        "completed_command_count": int(workload["command_count"]),
    }


def _command_init(command_data: dict[str, object]) -> str:
    lines = []
    for index, command in enumerate(tuple(command_data["wave_commands"])):
        lines.append(
            f"    command_id_mem[{index}] = 16'h{int(command['command_id']):04x}; "
            f"head_base_mem[{index}] = 5'd{int(command['head_base'])}; "
            f"multiplier_mem[{index}] = 32'd{int(command['multiplier'])}; "
            f"shift_mem[{index}] = 6'd{int(command['shift'])};"
        )
    return "\n".join(lines)


def _cluster_result_logging() -> str:
    lines: list[str] = []
    for cluster in range(16):
        lines.extend(
            [
                f"      if (dut.cluster_out_valid_w[{cluster}] && dut.cluster_out_ready_w[{cluster}]) begin",
                f'        $display("CLUSTER_RESULT cluster={cluster} cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x cycle=%0d",',
                f"                 dut.cluster_out_command_id_w[{cluster * 16} +: 16],",
                f"                 dut.cluster_out_head_id_w[{cluster * 5} +: 5],",
                f"                 dut.cluster_out_slice_w[{cluster * 4} +: 4],",
                f"                 dut.cluster_out_last_w[{cluster}],",
                f"                 $signed(dut.cluster_out_global_max_w[{cluster * 32} +: 32]),",
                f"                 dut.cluster_out_exp_sum_w[{cluster * 33} +: 33],",
                f"                 dut.cluster_out_value_w[{cluster * 328} +: 328],",
                "                 cycle);",
                "      end",
            ]
        )
    return "\n".join(lines)


def _cluster_summary_logging() -> str:
    lines: list[str] = []
    for cluster in range(16):
        lines.extend(
            [
                f'        $display("CLUSTER_SUMMARY cluster={cluster} cycle=%0d wave_accept=%0d issue_wait=%0d ready_skew=%0d emitted=%0d completed_commands=%0d group_error=%0d local_tree_error=%0d temporal_error=%0d reducer_error=%0d atomic_error=%0d protocol_error=%0d",',
                f"                 cluster_cycle_count[{cluster * 32} +: 32],",
                f"                 cluster_wave_command_accept_count[{cluster * 32} +: 32],",
                f"                 cluster_wave_command_issue_wait_cycles[{cluster * 32} +: 32],",
                f"                 cluster_producer_ready_skew_cycles[{cluster * 32} +: 32],",
                f"                 cluster_emitted_beat_count[{cluster * 32} +: 32],",
                f"                 cluster_completed_command_count[{cluster * 32} +: 32],",
                f"                 cluster_group_contract_error[{cluster}],",
                f"                 cluster_local_tree_protocol_error[{cluster}],",
                f"                 cluster_temporal_merge_protocol_error[{cluster}],",
                f"                 cluster_reducer_protocol_error[{cluster}],",
                f"                 cluster_atomic_command_protocol_error[{cluster}],",
                f"                 cluster_protocol_error[{cluster}]);",
            ]
        )
    return "\n".join(lines)


def _testbench(*, top_name: str, cluster_producers: tuple[int, ...], workload: dict[str, object], output_ready_pattern: tuple[bool, ...]) -> str:
    total_producers = sum(cluster_producers)
    value_lanes = total_producers * 2
    command_data = _hierarchy_driver_data(cluster_producers, workload)
    wave_commands = tuple(command_data["wave_commands"])
    query_mem = command_data["query_mem"]
    key_mem = command_data["key_mem"]
    last_mem = command_data["last_mem"]
    value_mem = command_data["value_mem"]
    beat_limits = command_data["beat_limits"]
    block_offsets = command_data["block_offsets"]
    max_beats_per_producer = int(command_data["max_beats_per_producer"])
    max_blocks_per_producer = int(command_data["max_blocks_per_producer"])

    beat_limit_init = []
    for command_index in range(len(wave_commands)):
        for producer in range(total_producers):
            beat_limit_init.append(
                f"    cmd_beat_limit_mem[{command_index}][{producer}] = 32'd{int(beat_limits[command_index][producer])}; "
                f"cmd_block_offset_mem[{command_index}][{producer}] = 32'd{int(block_offsets[command_index][producer])};"
            )
    beat_init = []
    for producer in range(total_producers):
        for beat_index, packed_query in enumerate(query_mem[producer]):
            flat_index = (producer * max_beats_per_producer) + beat_index
            beat_init.append(
                f"    query_mem[{flat_index}] = 128'h{int(packed_query):032x}; "
                f"key_mem[{flat_index}] = 128'h{int(key_mem[producer][beat_index]):032x}; "
                f"last_mem[{flat_index}] = 1'b{int(last_mem[producer][beat_index])};"
            )
    value_init = []
    for lane_index in range(value_lanes):
        for slice_index, packed_matrix in enumerate(value_mem[lane_index]):
            flat_index = (lane_index * max_blocks_per_producer * 16) + slice_index
            value_init.append(f"    value_mem[{flat_index}] = 512'h{int(packed_matrix):0128x};")

    return f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMANDS = {int(workload["command_count"])};
  localparam integer WAVE_COMMANDS = {len(wave_commands)};
  localparam integer TOTAL_PRODUCERS = {total_producers};
  localparam integer VALUE_LANES = {value_lanes};
  localparam integer MAX_BEATS_PER_PRODUCER = {max_beats_per_producer};
  localparam integer MAX_BLOCKS_PER_PRODUCER = {max_blocks_per_producer};
  localparam integer TOTAL_RESULTS = COMMANDS * 128;
  localparam integer ROOT_READY_PATTERN_LEN = {len(output_ready_pattern)};
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer issued_commands = 0;
  integer active_command_index = -1;
  integer root_seen = 0;
  integer first_root_cycle = -1;
  integer last_root_cycle = -1;
  reg pending_summary = 0;

  reg [15:0] command_id_mem [0:WAVE_COMMANDS-1];
  reg [4:0] head_base_mem [0:WAVE_COMMANDS-1];
  reg [31:0] multiplier_mem [0:WAVE_COMMANDS-1];
  reg [5:0] shift_mem [0:WAVE_COMMANDS-1];
  reg [31:0] cmd_beat_limit_mem [0:WAVE_COMMANDS-1][0:TOTAL_PRODUCERS-1];
  reg [31:0] cmd_block_offset_mem [0:WAVE_COMMANDS-1][0:TOTAL_PRODUCERS-1];
  reg [127:0] query_mem [0:(TOTAL_PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [127:0] key_mem [0:(TOTAL_PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg last_mem [0:(TOTAL_PRODUCERS*MAX_BEATS_PER_PRODUCER)-1];
  reg [511:0] value_mem [0:(VALUE_LANES*MAX_BLOCKS_PER_PRODUCER*16)-1];
  reg root_ready_mem [0:ROOT_READY_PATTERN_LEN-1];

  reg command_valid;
  wire command_ready;
  reg [15:0] command_id;
  reg [4:0] command_head_base;
  reg [31:0] command_score_multiplier;
  reg [5:0] command_score_shift;
  reg [TOTAL_PRODUCERS-1:0] input_valid;
  wire [TOTAL_PRODUCERS-1:0] input_ready;
  reg [TOTAL_PRODUCERS-1:0] input_last;
  reg signed [(TOTAL_PRODUCERS*128)-1:0] input_query;
  reg signed [(TOTAL_PRODUCERS*128)-1:0] input_key;
  wire [VALUE_LANES-1:0] value_read_req_valid;
  reg [VALUE_LANES-1:0] value_read_req_ready;
  wire [(VALUE_LANES*14)-1:0] value_read_req_address;
  wire [(VALUE_LANES*4)-1:0] value_read_req_slice;
  reg [VALUE_LANES-1:0] value_response_valid;
  wire [VALUE_LANES-1:0] value_response_ready;
  reg [(VALUE_LANES*14)-1:0] value_response_address;
  reg [(VALUE_LANES*4)-1:0] value_response_slice;
  reg [(VALUE_LANES*512)-1:0] value_response_matrix;
  wire root_valid;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire root_last;
  wire [319:0] root_value;
  wire [(16 * 32) - 1:0] cluster_cycle_count;
  wire [(16 * 32) - 1:0] cluster_wave_command_accept_count;
  wire [(16 * 32) - 1:0] cluster_wave_command_issue_wait_cycles;
  wire [(16 * 32) - 1:0] cluster_producer_ready_skew_cycles;
  wire [(16 * 32) - 1:0] cluster_emitted_beat_count;
  wire [(16 * 32) - 1:0] cluster_completed_command_count;
  wire [15:0] cluster_group_contract_error;
  wire [15:0] cluster_local_tree_protocol_error;
  wire [15:0] cluster_temporal_merge_protocol_error;
  wire [15:0] cluster_reducer_protocol_error;
  wire [15:0] cluster_atomic_command_protocol_error;
  wire [15:0] cluster_protocol_error;
  wire [31:0] global_cycle_count;
  wire [31:0] global_root_completed_count;
  wire [31:0] global_finalizer_accepted_count;
  wire [31:0] global_tree_root_completed_count;
  wire [31:0] global_order_fifo_occupancy;
  wire [31:0] global_order_fifo_high_watermark;
  wire [31:0] global_order_enqueued_count;
  wire [31:0] global_order_dequeued_count;
  wire [31:0] global_dispatch_stall_cycles;
  wire [31:0] global_dispatch_bank_id;
  wire [31:0] global_head_bank_id;
  wire [(15 * 32) - 1:0] global_node_completed_count;
  wire [(4 * 32) - 1:0] global_stage_completed_count;
  wire [14:0] global_node_protocol_error;
  wire [3:0] global_stage_protocol_error;
  wire [58:0] global_bank_protocol_error;
  wire [58:0] global_bank_outstanding;
  wire global_tree_protocol_error;
  wire global_order_protocol_error;
  wire global_finalizer_protocol_error;
  wire global_protocol_error;
  wire protocol_error;

  integer beat_issue [0:TOTAL_PRODUCERS-1];
  reg pending_valid [0:VALUE_LANES-1];
  reg [13:0] pending_addr [0:VALUE_LANES-1];
  reg [3:0] pending_slice [0:VALUE_LANES-1];
  integer pending_delay [0:VALUE_LANES-1];
  integer producer_index;
  integer lane_index;
  integer flat_index;
  integer response_index;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .command_id(command_id),
      .command_head_base(command_head_base),
      .command_score_multiplier(command_score_multiplier),
      .command_score_shift(command_score_shift),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_query(input_query),
      .input_key(input_key),
      .value_read_req_valid(value_read_req_valid),
      .value_read_req_ready(value_read_req_ready),
      .value_read_req_address(value_read_req_address),
      .value_read_req_slice(value_read_req_slice),
      .value_response_valid(value_response_valid),
      .value_response_ready(value_response_ready),
      .value_response_address(value_response_address),
      .value_response_slice(value_response_slice),
      .value_response_matrix(value_response_matrix),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cluster_cycle_count(cluster_cycle_count),
      .cluster_wave_command_accept_count(cluster_wave_command_accept_count),
      .cluster_wave_command_issue_wait_cycles(cluster_wave_command_issue_wait_cycles),
      .cluster_producer_ready_skew_cycles(cluster_producer_ready_skew_cycles),
      .cluster_emitted_beat_count(cluster_emitted_beat_count),
      .cluster_completed_command_count(cluster_completed_command_count),
      .cluster_group_contract_error(cluster_group_contract_error),
      .cluster_local_tree_protocol_error(cluster_local_tree_protocol_error),
      .cluster_temporal_merge_protocol_error(cluster_temporal_merge_protocol_error),
      .cluster_reducer_protocol_error(cluster_reducer_protocol_error),
      .cluster_atomic_command_protocol_error(cluster_atomic_command_protocol_error),
      .cluster_protocol_error(cluster_protocol_error),
      .global_cycle_count(global_cycle_count),
      .global_root_completed_count(global_root_completed_count),
      .global_finalizer_accepted_count(global_finalizer_accepted_count),
      .global_tree_root_completed_count(global_tree_root_completed_count),
      .global_order_fifo_occupancy(global_order_fifo_occupancy),
      .global_order_fifo_high_watermark(global_order_fifo_high_watermark),
      .global_order_enqueued_count(global_order_enqueued_count),
      .global_order_dequeued_count(global_order_dequeued_count),
      .global_dispatch_stall_cycles(global_dispatch_stall_cycles),
      .global_dispatch_bank_id(global_dispatch_bank_id),
      .global_head_bank_id(global_head_bank_id),
      .global_node_completed_count(global_node_completed_count),
      .global_stage_completed_count(global_stage_completed_count),
      .global_node_protocol_error(global_node_protocol_error),
      .global_stage_protocol_error(global_stage_protocol_error),
      .global_bank_protocol_error(global_bank_protocol_error),
      .global_bank_outstanding(global_bank_outstanding),
      .global_tree_protocol_error(global_tree_protocol_error),
      .global_order_protocol_error(global_order_protocol_error),
      .global_finalizer_protocol_error(global_finalizer_protocol_error),
      .global_protocol_error(global_protocol_error),
      .protocol_error(protocol_error)
  );

  always #5 clk = ~clk;

  always @* begin
    command_valid = rst_n && (issued_commands < WAVE_COMMANDS);
    command_id = command_valid ? command_id_mem[issued_commands] : 16'd0;
    command_head_base = command_valid ? head_base_mem[issued_commands] : 5'd0;
    command_score_multiplier = command_valid ? multiplier_mem[issued_commands] : 32'd0;
    command_score_shift = command_valid ? shift_mem[issued_commands] : 6'd0;
    input_valid = {{TOTAL_PRODUCERS{{1'b0}}}};
    input_last = {{TOTAL_PRODUCERS{{1'b0}}}};
    input_query = {{(TOTAL_PRODUCERS*128){{1'b0}}}};
    input_key = {{(TOTAL_PRODUCERS*128){{1'b0}}}};
    value_read_req_ready = {{VALUE_LANES{{1'b1}}}};
    root_ready = root_ready_mem[cycle % ROOT_READY_PATTERN_LEN];
    for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1) begin
      if (rst_n && (active_command_index >= 0) && (beat_issue[producer_index] < cmd_beat_limit_mem[active_command_index][producer_index])) begin
        flat_index = (producer_index * MAX_BEATS_PER_PRODUCER) + beat_issue[producer_index];
        input_valid[producer_index] = 1'b1;
        input_last[producer_index] = last_mem[flat_index];
        input_query[(producer_index * 128) +: 128] = query_mem[flat_index];
        input_key[(producer_index * 128) +: 128] = key_mem[flat_index];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issued_commands <= 0;
      active_command_index <= -1;
      root_seen <= 0;
      first_root_cycle <= -1;
      last_root_cycle <= -1;
      pending_summary <= 0;
      value_response_valid <= {{VALUE_LANES{{1'b0}}}};
      value_response_address <= {{(VALUE_LANES*14){{1'b0}}}};
      value_response_slice <= {{(VALUE_LANES*4){{1'b0}}}};
      value_response_matrix <= {{(VALUE_LANES*512){{1'b0}}}};
      for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1) begin
        beat_issue[producer_index] <= 0;
      end
      for (lane_index = 0; lane_index < VALUE_LANES; lane_index = lane_index + 1) begin
        pending_valid[lane_index] <= 1'b0;
        pending_addr[lane_index] <= 14'd0;
        pending_slice[lane_index] <= 4'd0;
        pending_delay[lane_index] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      if (command_valid && command_ready) begin
        active_command_index <= issued_commands;
        $display("COMMAND_ACCEPT idx=%0d cmd=%0d head_base=%0d logical=%0d wave=%0d cycle=%0d",
                 issued_commands,
                 command_id_mem[issued_commands],
                 head_base_mem[issued_commands],
                 issued_commands / {LOCAL_TEMPORAL_WAVES},
                 issued_commands % {LOCAL_TEMPORAL_WAVES},
                 global_cycle_count);
        issued_commands <= issued_commands + 1;
      end
      for (producer_index = 0; producer_index < TOTAL_PRODUCERS; producer_index = producer_index + 1) begin
        if (input_valid[producer_index] && input_ready[producer_index]) begin
          beat_issue[producer_index] <= beat_issue[producer_index] + 1;
        end
      end
      for (lane_index = 0; lane_index < VALUE_LANES; lane_index = lane_index + 1) begin
        if (value_response_valid[lane_index] && value_response_ready[lane_index]) begin
          value_response_valid[lane_index] <= 1'b0;
        end
        if (value_read_req_valid[lane_index] && value_read_req_ready[lane_index]) begin
          if (pending_valid[lane_index]) $fatal(1, "value lane %0d multiple outstanding request", lane_index);
          pending_valid[lane_index] <= 1'b1;
          pending_addr[lane_index] <= value_read_req_address[(lane_index * 14) +: 14];
          pending_slice[lane_index] <= value_read_req_slice[(lane_index * 4) +: 4];
          pending_delay[lane_index] <= 0;
        end
        if (pending_valid[lane_index]) begin
          if (pending_delay[lane_index] == 0) begin
            if (!value_response_valid[lane_index]) begin
              producer_index = lane_index / 2;
              response_index =
                  ((lane_index * MAX_BLOCKS_PER_PRODUCER)
                   + cmd_block_offset_mem[active_command_index][producer_index]
                   + pending_addr[lane_index]) * 16
                  + pending_slice[lane_index];
              pending_valid[lane_index] <= 1'b0;
              value_response_valid[lane_index] <= 1'b1;
              value_response_address[(lane_index * 14) +: 14] <= pending_addr[lane_index];
              value_response_slice[(lane_index * 4) +: 4] <= pending_slice[lane_index];
              value_response_matrix[(lane_index * 512) +: 512] <= value_mem[response_index];
            end
          end else begin
            pending_delay[lane_index] <= pending_delay[lane_index] - 1;
          end
        end
      end
{_cluster_result_logging()}
      if (root_valid && root_ready) begin
        $display("ROOT_RESULT cmd=%0d head=%0d slice=%0d last=%0d value=%080x cycle=%0d",
                 root_command_id, root_head_id, root_slice, root_last, root_value, cycle);
        if (first_root_cycle < 0) first_root_cycle <= cycle;
        last_root_cycle <= cycle;
        root_seen <= root_seen + 1;
        if (root_seen + 1 == TOTAL_RESULTS) pending_summary <= 1'b1;
      end
      if (pending_summary) begin
        $display("SUMMARY outputs=%0d drain=%0d first_root=%0d last_root=%0d protocol_error=%0d global_root_completed=%0d global_finalizer_accepted=%0d global_tree_root_completed=%0d global_dispatch_stall=%0d global_order_occupancy=%0d global_order_high=%0d global_tree_error=%0d global_order_error=%0d global_finalizer_error=%0d",
                 root_seen, cycle + 1, first_root_cycle, last_root_cycle, protocol_error,
                 global_root_completed_count, global_finalizer_accepted_count, global_tree_root_completed_count,
                 global_dispatch_stall_cycles, global_order_fifo_occupancy, global_order_fifo_high_watermark,
                 global_tree_protocol_error, global_order_protocol_error, global_finalizer_protocol_error);
        {_cluster_summary_logging()}
        #1 $finish;
      end
      if (cycle > {max(160000, len(wave_commands) * 16000)}) begin
        $display("TB_TIMEOUT cycle=%0d", cycle);
        #1 $finish;
      end
    end
  end

  initial begin
{_command_init(command_data)}
{chr(10).join(beat_limit_init)}
{chr(10).join(beat_init)}
{chr(10).join(value_init)}
{_ready_init(output_ready_pattern)}
    clk = 1'b0;
    rst_n = 1'b0;
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
"""


def _parse_summary(stdout: str) -> tuple[dict[str, int], list[dict[str, int]], list[dict[str, object]], list[dict[str, object]], int | None]:
    summary: dict[str, int] | None = None
    cluster_summaries: list[dict[str, int]] = []
    observed_cluster_rows: list[dict[str, object]] = []
    observed_root_rows: list[dict[str, object]] = []
    timeout_cycle: int | None = None

    for line in stdout.splitlines():
        if match := _CLUSTER_RESULT_RE.search(line):
            observed_cluster_rows.append(
                {
                    "cluster": int(match.group(1)),
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": list(unpack_numerators(int(match.group(8), 16))),
                    "cycle": int(match.group(9)),
                }
            )
            continue
        if match := _ROOT_RESULT_RE.search(line):
            observed_root_rows.append(
                {
                    "command_id": int(match.group(1)),
                    "head_id": int(match.group(2)),
                    "slice": int(match.group(3)),
                    "last": bool(int(match.group(4))),
                    "value": list(unpack_final_values(int(match.group(5), 16))),
                    "cycle": int(match.group(6)),
                }
            )
            continue
        if match := _SUMMARY_RE.search(line):
            summary = {
                "outputs": int(match.group(1)),
                "drain_cycles": int(match.group(2)),
                "first_root_cycle": int(match.group(3)),
                "last_root_cycle": int(match.group(4)),
                "protocol_error": int(match.group(5)),
                "global_root_completed_count": int(match.group(6)),
                "global_finalizer_accepted_count": int(match.group(7)),
                "global_tree_root_completed_count": int(match.group(8)),
                "global_dispatch_stall_cycles": int(match.group(9)),
                "global_order_fifo_occupancy": int(match.group(10)),
                "global_order_fifo_high_watermark": int(match.group(11)),
                "global_tree_protocol_error": int(match.group(12)),
                "global_order_protocol_error": int(match.group(13)),
                "global_finalizer_protocol_error": int(match.group(14)),
            }
            continue
        if match := _CLUSTER_SUMMARY_RE.search(line):
            cluster_summaries.append(
                {
                    "cluster": int(match.group(1)),
                    "cycle_count": int(match.group(2)),
                    "wave_command_accept_count": int(match.group(3)),
                    "wave_command_issue_wait_cycles": int(match.group(4)),
                    "producer_ready_skew_cycles": int(match.group(5)),
                    "emitted_beat_count": int(match.group(6)),
                    "completed_command_count": int(match.group(7)),
                    "group_contract_error": int(match.group(8)),
                    "local_tree_protocol_error": int(match.group(9)),
                    "temporal_merge_protocol_error": int(match.group(10)),
                    "reducer_protocol_error": int(match.group(11)),
                    "atomic_command_protocol_error": int(match.group(12)),
                    "protocol_error": int(match.group(13)),
                }
            )
            continue
        if match := _TB_TIMEOUT_RE.search(line):
            timeout_cycle = int(match.group(1))

    if summary is None:
        summary = {}
    cluster_summaries.sort(key=lambda row: row["cluster"])
    return summary, cluster_summaries, observed_cluster_rows, observed_root_rows, timeout_cycle


def build_report(
    *,
    config: JsonDict | None = None,
    command_count: int | None = None,
    head_bases: tuple[int, ...] | None = None,
    seed: int | None = None,
    output_ready_pattern: tuple[bool, ...] = (True,),
    timeout_sec: int = 300,
    proposal_id: str | None = None,
    proposal_path: str | None = None,
) -> JsonDict:
    resolved_config = json.loads(json.dumps(config if config is not None else _default_config()))
    workload = _resolve_workload(
        resolved_config,
        command_count=command_count,
        head_bases=head_bases,
        seed=seed,
    )
    reference = _reference(resolved_config, workload)
    body = resolved_config.get(_CONFIG_KEY)
    if not isinstance(body, dict):
        raise ValueError(f"config must contain {_CONFIG_KEY}")
    cluster_producers = tuple(int(value) for value in body["cluster_producers"])
    service_model = exact_local16_global_tree_gqa8_service_manifest(
        cluster_producers=cluster_producers,
        head_groups=int(workload["command_count"]),
    )

    with tempfile.TemporaryDirectory(prefix="score32_exact_local16_global_probe_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        rtl_dir = temp_dir / "rtl"
        generate(resolved_config, rtl_dir)
        testbench_path = temp_dir / "tb.v"
        fakeram_path = temp_dir / "fakeram45_2048x39.v"
        testbench_path.write_text(
            _testbench(
                top_name=str(resolved_config["top_name"]),
                cluster_producers=cluster_producers,
                workload=workload,
                output_ready_pattern=tuple(bool(value) for value in output_ready_pattern),
            ),
            encoding="utf-8",
        )
        fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")
        sim_path = temp_dir / "sim.out"
        try:
            subprocess.run(
                [
                    _tool("iverilog"),
                    "-g2012",
                    "-s",
                    "tb",
                    "-o",
                    str(sim_path),
                    str(rtl_dir / "top.v"),
                    str(fakeram_path),
                    str(testbench_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            run_result = subprocess.run(
                [_tool("vvp"), str(sim_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            simulation_status = "ok"
            stdout = run_result.stdout
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            simulation_status = "subprocess_timeout"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")

    summary, cluster_summaries, observed_cluster_rows, observed_root_rows, tb_timeout_cycle = _parse_summary(stdout)
    normalized_cluster_rows = [{key: value for key, value in row.items() if key != "cycle"} for row in observed_cluster_rows]
    normalized_root_rows = [{key: value for key, value in row.items() if key != "cycle"} for row in observed_root_rows]
    observed_cluster_rows_by_cluster = [
        [row for row in normalized_cluster_rows if int(row["cluster"]) == cluster] for cluster in range(16)
    ]
    expected_cluster_rows = [row for rows in reference["cluster_rows"] for row in rows]
    expected_counts = _expected_cluster_summary_counts(workload)
    expected_cluster_summaries = [{"cluster": cluster, **expected_counts} for cluster in range(16)]
    cluster_summaries_ok = len(cluster_summaries) == 16 and all(
        cluster_summaries[index]["cluster"] == expected_cluster_summaries[index]["cluster"]
        and cluster_summaries[index]["wave_command_accept_count"] == expected_cluster_summaries[index]["wave_command_accept_count"]
        and cluster_summaries[index]["emitted_beat_count"] == expected_cluster_summaries[index]["emitted_beat_count"]
        and cluster_summaries[index]["completed_command_count"] == expected_cluster_summaries[index]["completed_command_count"]
        and cluster_summaries[index]["group_contract_error"] == 0
        and cluster_summaries[index]["local_tree_protocol_error"] == 0
        and cluster_summaries[index]["temporal_merge_protocol_error"] == 0
        and cluster_summaries[index]["reducer_protocol_error"] == 0
        and cluster_summaries[index]["atomic_command_protocol_error"] == 0
        and cluster_summaries[index]["protocol_error"] == 0
        for index in range(16)
    )
    summary_ok = (
        bool(summary)
        and summary.get("protocol_error", 1) == 0
        and summary.get("global_tree_protocol_error", 1) == 0
        and summary.get("global_order_protocol_error", 1) == 0
        and summary.get("global_finalizer_protocol_error", 1) == 0
    )
    row_audit = compare_compositional_rows(
        expected_cluster_rows=reference["cluster_rows"],
        observed_cluster_rows=observed_cluster_rows_by_cluster,
        expected_root_rows=reference["root_rows"],
        observed_root_rows=normalized_root_rows,
    )
    timed_out = simulation_status != "ok" or tb_timeout_cycle is not None
    passed = (
        simulation_status == "ok"
        and tb_timeout_cycle is None
        and summary_ok
        and cluster_summaries_ok
        and bool(row_audit["passed"])
        and summary.get("outputs") == len(reference["root_rows"])
        and summary.get("global_root_completed_count") == len(reference["root_rows"])
        and summary.get("global_finalizer_accepted_count") == len(reference["root_rows"])
        and summary.get("global_tree_root_completed_count") == len(reference["root_rows"])
    )

    report: JsonDict = {
        "passed": passed,
        "simulation_status": "testbench_timeout" if tb_timeout_cycle is not None else simulation_status,
        "timed_out": timed_out,
        "timeout_classification": "failed_inconclusive" if timed_out else None,
        "interface_mode": "stress" if tuple(output_ready_pattern) != (True,) else "ideal",
        "clusters": 16,
        "cluster_producers": list(cluster_producers),
        "total_local_producers": sum(cluster_producers),
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "command_count": int(workload["command_count"]),
        "wave_command_count": int(workload["command_count"]) * LOCAL_TEMPORAL_WAVES,
        "head_bases": list(int(value) for value in workload["head_bases"]),
        "seed": int(workload["seed"]),
        "outputs": int(summary.get("outputs", len(observed_root_rows))),
        "expected_outputs": len(reference["root_rows"]),
        "cluster_aggregate_outputs": len(normalized_cluster_rows),
        "expected_cluster_aggregate_outputs": len(expected_cluster_rows),
        "observed_root_hash": _hash(normalized_root_rows),
        "expected_root_hash": reference["root_hash"],
        "observed_cluster_hashes": [
            _hash([row for row in normalized_cluster_rows if int(row["cluster"]) == cluster]) for cluster in range(16)
        ],
        "expected_cluster_hashes": reference["cluster_hashes"],
        "observed_root_rows": normalized_root_rows,
        "expected_root_rows": reference["root_rows"],
        "observed_cluster_rows": normalized_cluster_rows,
        "expected_cluster_rows": expected_cluster_rows,
        "observed_root_cycles": [int(row["cycle"]) for row in observed_root_rows],
        "observed_cluster_cycles": [int(row["cycle"]) for row in observed_cluster_rows],
        "summary": summary,
        "cluster_summaries": cluster_summaries,
        "timeout_sec": int(timeout_sec),
        "tb_timeout_cycle": tb_timeout_cycle,
        "full_row_audit": row_audit,
        "service_model": service_model,
    }
    linkage = dict(resolved_config.get("report_links") or {})
    if proposal_id:
        linkage["proposal_id"] = proposal_id
    if proposal_path:
        linkage["proposal_path"] = proposal_path
    if linkage:
        report["source_links"] = linkage
    return report


def _render_text(report: JsonDict) -> str:
    lines = [
        "# attention_score32_exact_local16_global_tree_gqa8_probe",
        "",
        f"- passed: `{report['passed']}`",
        f"- simulation_status: `{report['simulation_status']}`",
        f"- interface_mode: `{report['interface_mode']}`",
        f"- total_local_producers: `{report['total_local_producers']}`",
        f"- outputs: `{report['outputs']}`",
        f"- expected_outputs: `{report['expected_outputs']}`",
        f"- observed_root_hash: `{report['observed_root_hash']}`",
        f"- expected_root_hash: `{report['expected_root_hash']}`",
    ]
    if "summary" in report and isinstance(report["summary"], dict):
        summary = report["summary"]
        lines.extend(
            [
                f"- drain_cycles: `{summary.get('drain_cycles')}`",
                f"- first_root_cycle: `{summary.get('first_root_cycle')}`",
                f"- last_root_cycle: `{summary.get('last_root_cycle')}`",
                f"- global_dispatch_stall_cycles: `{summary.get('global_dispatch_stall_cycles')}`",
            ]
        )
    linkage = dict(report.get("source_links") or {})
    if linkage.get("proposal_id"):
        lines.append(f"- proposal_id: `{linkage['proposal_id']}`")
    if linkage.get("proposal_path"):
        lines.append(f"- proposal_path: `{linkage['proposal_path']}`")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--command-count", type=int, default=None)
    parser.add_argument("--head-bases", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--root-ready-pattern", type=str, default="1")
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument("--proposal-id", type=str, default=None)
    parser.add_argument("--proposal-path", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    config = _default_config() if args.config is None else json.loads(args.config.read_text(encoding="utf-8"))
    head_bases = None if args.head_bases is None else tuple(int(value) for value in args.head_bases.split(",") if value.strip())
    ready_pattern = tuple(value.strip() == "1" for value in args.root_ready_pattern.split(",") if value.strip())
    report = build_report(
        config=config,
        command_count=args.command_count,
        head_bases=head_bases,
        seed=args.seed,
        output_ready_pattern=ready_pattern or (True,),
        timeout_sec=args.timeout_sec,
        proposal_id=str(args.proposal_id or "").strip() or None,
        proposal_path=str(args.proposal_path or "").strip() or None,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
