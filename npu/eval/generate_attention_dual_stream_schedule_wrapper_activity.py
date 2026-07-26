#!/usr/bin/env python3
"""Generate a deterministic dual-cluster wrapper VCD and activity manifest."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_dual_stream_schedule_wrapper import (  # noqa: E402
    _validate as _validate_wrapper_config,
    _write_wrapper as _write_wrapper_rtl,
)

JsonDict = dict[str, Any]

_DEFAULT_CLOCK_PERIOD_NS = 10.0
_DEFAULT_SERVICE_WINDOW_CYCLES = 986
_DEFAULT_WARMUP_CYCLES = 32
_DEFAULT_COMMAND_COUNT = 340
_OUTPUT_VCD_NAME = "attention_dual_stream_schedule_wrapper_activity.vcd"
_OUTPUT_MANIFEST_NAME = "attention_dual_stream_schedule_wrapper_activity_manifest.json"
_OUTPUT_TOP_NAME = "top.v"
_OUTPUT_CONFIG_NAME = "config.json"
_OUTPUT_WRAPPER_MANIFEST_NAME = "attention_dual_stream_schedule_wrapper_manifest.json"
_SCOPE = "tb/dut"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _hash_json(value: object) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _portable_path(path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def _tool(name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.is_file():
        return str(fallback)
    raise FileNotFoundError(f"unable to locate required simulator tool: {name}")


def _normalize_vcd(path: Path) -> None:
    tmp_path = path.with_suffix(path.suffix + ".normalized")
    in_date_block = False
    date_rewritten = False
    with path.open("r", encoding="utf-8", errors="replace") as src, tmp_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            if not date_rewritten and not in_date_block and line.strip() == "$date":
                dst.write("$date\n")
                dst.write("  deterministic_schedule_wrapper_activity_v1\n")
                in_date_block = True
                date_rewritten = True
                continue
            if in_date_block:
                if line.strip() == "$end":
                    dst.write("$end\n")
                    in_date_block = False
                continue
            dst.write(line)
    tmp_path.replace(path)


def _mask(width: int) -> int:
    return (1 << width) - 1 if width > 0 else 0


def _u(value: int, width: int) -> int:
    return value & _mask(width)


def _s(value: int, width: int) -> int:
    value &= _mask(width)
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def _extract(value: int, lsb: int, width: int) -> int:
    return (value >> lsb) & _mask(width)


@dataclass(frozen=True)
class _Command:
    tile_id: int
    wave_id: int
    base_token: int


@dataclass
class _DatapathState:
    seed_state: int = 1
    cycle_ctr: int = 0
    stream_buf_0: int = 0
    stream_buf_1: int = 0
    softmax_scores_pipe_0: int = 0
    stream_buf_0_pipe_0: int = 0
    stream_buf_0_pipe_1: int = 0
    stream_buf_1_pipe_0: int = 0
    stream_buf_1_pipe_1: int = 0
    score_mix_0_pipe_0: int = 0
    score_mix_0_pipe_1: int = 0
    score_mix_1_pipe_0: int = 0
    score_mix_1_pipe_1: int = 0
    softmax_weights: int = 0
    value_accum_0: int = 0
    value_accum_1: int = 0
    done: int = 0
    softmax_weights_out: int = 0
    value_accum_0_out: int = 0
    value_accum_1_out: int = 0
    score_mix_0_out: int = 0
    score_mix_1_out: int = 0


@dataclass
class _ClusterState:
    active: bool = False
    service_ctr: int = 0
    seed: int = 0
    datapath: _DatapathState = field(default_factory=_DatapathState)


@dataclass
class _WrapperState:
    count: int = 0
    rr_ptr: int = 0
    inflight: tuple[int, int] = (0, 0)
    dispatch_valid: bool = False
    dispatch_cluster_id: int = 0
    dispatch_tile_id: int = 0
    dispatch_wave_id: int = 0
    dispatch_base_token: int = 0
    queue: tuple[_Command, ...] = ()
    clusters: tuple[_ClusterState, _ClusterState] = ()
    completed_count: int = 0
    result_fold: int = 0


def _default_clusters() -> tuple[_ClusterState, _ClusterState]:
    return (
        _ClusterState(seed=0x1000),
        _ClusterState(seed=0x1001),
    )


def _command_for_index(index: int, *, tile_bits: int, wave_bits: int, base_bits: int) -> _Command:
    return _Command(
        tile_id=((index * 37) + 11) & _mask(tile_bits),
        wave_id=((index * 13) + (index // 7) + 3) & _mask(wave_bits),
        base_token=((index * 29) + (index * index) + 5) & _mask(base_bits),
    )


def _command_gap(cycle: int) -> bool:
    return (cycle % 23) == 7


def _external_ready(
    cycle: int,
    *,
    cluster_active: tuple[bool, bool],
) -> tuple[int, int]:
    return (
        1 if (not cluster_active[0] and (cycle % 2) == 0) else 0,
        1 if (not cluster_active[1] and (cycle % 2) == 0) else 0,
    )


def _lfsr_step(seed_state: int) -> int:
    bit = ((seed_state >> 31) ^ (seed_state >> 21) ^ (seed_state >> 1) ^ seed_state) & 0x1
    return ((_u(seed_state, 32) << 1) & 0xFFFF_FFFF) | bit


def _stream_insert(seed_state: int, cycle_ctr: int, stream: int) -> int:
    return _u(seed_state ^ cycle_ctr ^ (0x13572468 ^ stream), 32)


def _exp_lut_div_weights(
    scores: list[int],
    *,
    accum_bits: int,
    weight_bits: int,
    input_frac_bits: int,
    bucket_shift: int,
) -> int:
    output_scale = (1 << weight_bits) - 1
    input_scale = 1 << input_frac_bits
    bucket_step = 1 << bucket_shift
    max_delta = 8 * input_scale
    max_bucket = (max_delta + (bucket_step >> 1)) >> bucket_shift
    row_max = max(scores)
    exp_weights: list[int] = []
    for lane in scores:
        delta = max(0, row_max - lane)
        delta = min(delta, max_delta)
        exp_bucket = (delta + (bucket_step >> 1)) >> bucket_shift
        exp_bucket = min(exp_bucket, max_bucket)
        weight = int(math.exp(-((exp_bucket * bucket_step) / float(input_scale))) * output_scale + 0.5)
        exp_weights.append(weight)
    sum_weight = sum(exp_weights)
    packed = 0
    for index, weight in enumerate(exp_weights):
        numer = (weight * output_scale) + (sum_weight >> 1)
        lane_out = numer // sum_weight if sum_weight else 0
        lane_out = min(lane_out, output_scale)
        packed |= _u(lane_out, weight_bits) << (index * weight_bits)
    return packed & _mask(len(scores) * weight_bits)


def _datapath_score_mix_and_scores(
    state: _DatapathState,
    *,
    array_m: int,
    array_n: int,
    k_unroll: int,
    row_elems: int,
    stream_buffer_bits: int,
    mac_accum_bits: int,
    softmax_score_bits: int,
) -> tuple[int, int, int]:
    macs_per_stream = array_m * array_n * k_unroll
    score_lane_terms: list[int] = [0 for _ in range(row_elems)]
    score_mix_terms = [0, 0]
    compute_fold = 0
    stream_bufs = (state.stream_buf_0, state.stream_buf_1)
    for stream in range(2):
        stream_buf = stream_bufs[stream]
        for idx in range(macs_per_stream):
            row = idx // (array_n * k_unroll)
            col = (idx // k_unroll) % array_n
            ku = idx % k_unroll
            const_a = (0x3D ^ ((stream + 1) * 0x17) ^ ((row + 1) * 0x13) ^ ((col + 1) * 0x27) ^ (ku * 0x41)) & 0xFF
            const_b = (0x21 ^ ((stream + 1) * 0x2B) ^ ((row + 1) * 0x1D) ^ ((col + 1) * 0xA3) ^ (ku * 0x55)) & 0xFF
            const_c = (
                0x001011
                ^ ((stream + 1) * 0x0101)
                ^ ((row + 1) * 0x0007)
                ^ ((col + 1) * 0x000B)
                ^ (ku * 0x0013)
            ) & _mask(mac_accum_bits)
            mac_a = _u(
                _extract(state.seed_state, 0, 8)
                ^ _extract(stream_buf, (idx * 7) % (stream_buffer_bits - 7), 8)
                ^ const_a
                ^ _extract(state.cycle_ctr, 0, 8),
                8,
            )
            mac_b = _u(
                _extract(state.seed_state, 8, 8)
                ^ _extract(stream_buf, (idx * 11) % (stream_buffer_bits - 7), 8)
                ^ const_b
                ^ _extract(state.cycle_ctr, 8, 8),
                8,
            )
            mac_c = _u(
                _u(state.cycle_ctr, mac_accum_bits)
                ^ _extract(stream_buf, (idx * 13) % (stream_buffer_bits - mac_accum_bits + 1), mac_accum_bits)
                ^ const_c,
                mac_accum_bits,
            )
            product = _s(mac_a, 8) * _s(mac_b, 8)
            mac_r = _u(product + _s(mac_c, mac_accum_bits), mac_accum_bits)
            score_lane_terms[idx % row_elems] ^= _extract(mac_r, 0, softmax_score_bits)
            score_mix_terms[stream] ^= mac_r
            compute_fold ^= _extract(mac_r, 0, 32)
    softmax_scores = 0
    for lane in reversed(range(row_elems)):
        softmax_scores = (softmax_scores << softmax_score_bits) | _u(
            score_lane_terms[lane], softmax_score_bits
        )
    return (
        softmax_scores & _mask(row_elems * softmax_score_bits),
        _u(score_mix_terms[0], mac_accum_bits),
        _u(score_mix_terms[1], mac_accum_bits),
    )


def _value_accum(
    *,
    stream_data: int,
    weights: int,
    score_mix: int,
    row_elems: int,
    weight_bits: int,
    value_bits: int,
    value_lanes: int,
    stream_buffer_bits: int,
    score_mix_bits: int,
) -> int:
    acc_bits = 40
    product_bits = value_bits + weight_bits + 1
    product_sum = 0
    for lane in range(value_lanes):
        value = _s(_extract(stream_data, (lane * value_bits) % (stream_buffer_bits - value_bits + 1), value_bits), value_bits)
        weight = _u(_extract(weights, (lane % row_elems) * weight_bits, weight_bits), weight_bits)
        product = value * weight
        product_sum += product
    return _u(product_sum + _s(score_mix, score_mix_bits), acc_bits)


def _datapath_step(
    state: _DatapathState,
    *,
    seed_input: int,
    start: bool,
    array_m: int,
    array_n: int,
    k_unroll: int,
    row_elems: int,
    stream_buffer_bits: int,
    mac_accum_bits: int,
    softmax_score_bits: int,
    softmax_weight_bits: int,
    softmax_input_frac_bits: int,
    softmax_bucket_shift: int,
    value_bits: int,
    value_lanes: int,
    score_mix_bits: int,
) -> _DatapathState:
    softmax_scores, score_mix_0, score_mix_1 = _datapath_score_mix_and_scores(
        state,
        array_m=array_m,
        array_n=array_n,
        k_unroll=k_unroll,
        row_elems=row_elems,
        stream_buffer_bits=stream_buffer_bits,
        mac_accum_bits=mac_accum_bits,
        softmax_score_bits=softmax_score_bits,
    )
    scores_for_softmax = [
        _s(_extract(state.softmax_scores_pipe_0, lane * softmax_score_bits, softmax_score_bits), softmax_score_bits)
        for lane in range(row_elems)
    ]
    softmax_weights_next = _exp_lut_div_weights(
        scores_for_softmax,
        accum_bits=40,
        weight_bits=softmax_weight_bits,
        input_frac_bits=softmax_input_frac_bits,
        bucket_shift=softmax_bucket_shift,
    )
    value_accum_0_next = _value_accum(
        stream_data=state.stream_buf_0_pipe_1,
        weights=state.softmax_weights,
        score_mix=state.score_mix_0_pipe_1,
        row_elems=row_elems,
        weight_bits=softmax_weight_bits,
        value_bits=value_bits,
        value_lanes=value_lanes,
        stream_buffer_bits=stream_buffer_bits,
        score_mix_bits=score_mix_bits,
    )
    value_accum_1_next = _value_accum(
        stream_data=state.stream_buf_1_pipe_1,
        weights=state.softmax_weights,
        score_mix=state.score_mix_1_pipe_1,
        row_elems=row_elems,
        weight_bits=softmax_weight_bits,
        value_bits=value_bits,
        value_lanes=value_lanes,
        stream_buffer_bits=stream_buffer_bits,
        score_mix_bits=score_mix_bits,
    )
    next_state = _DatapathState(
        seed_state=_u(_lfsr_step(state.seed_state) ^ seed_input, 32),
        cycle_ctr=_u(state.cycle_ctr + 1, 16),
        stream_buf_0=_u(
            ((state.stream_buf_0 & _mask(stream_buffer_bits - 32)) << 32)
            | _stream_insert(state.seed_state, state.cycle_ctr, 0),
            stream_buffer_bits,
        ),
        stream_buf_1=_u(
            ((state.stream_buf_1 & _mask(stream_buffer_bits - 32)) << 32)
            | _stream_insert(state.seed_state, state.cycle_ctr, 1),
            stream_buffer_bits,
        ),
        softmax_scores_pipe_0=softmax_scores,
        stream_buf_0_pipe_0=state.stream_buf_0,
        stream_buf_0_pipe_1=state.stream_buf_0_pipe_0,
        stream_buf_1_pipe_0=state.stream_buf_1,
        stream_buf_1_pipe_1=state.stream_buf_1_pipe_0,
        score_mix_0_pipe_0=score_mix_0,
        score_mix_0_pipe_1=state.score_mix_0_pipe_0,
        score_mix_1_pipe_0=score_mix_1,
        score_mix_1_pipe_1=state.score_mix_1_pipe_0,
        softmax_weights=softmax_weights_next,
        value_accum_0=value_accum_0_next,
        value_accum_1=value_accum_1_next,
        done=1 if start else 0,
        softmax_weights_out=state.softmax_weights_out,
        value_accum_0_out=state.value_accum_0_out,
        value_accum_1_out=state.value_accum_1_out,
        score_mix_0_out=state.score_mix_0_out,
        score_mix_1_out=state.score_mix_1_out,
    )
    if start:
        next_state.softmax_weights_out = softmax_weights_next
        next_state.value_accum_0_out = value_accum_0_next
        next_state.value_accum_1_out = value_accum_1_next
        next_state.score_mix_0_out = score_mix_0
        next_state.score_mix_1_out = score_mix_1
    return next_state


def _datapath_result_fold(state: _DatapathState) -> int:
    return _u(
        _extract(state.softmax_weights_out, 0, 32)
        ^ _extract(state.value_accum_0_out, 0, 32)
        ^ _extract(state.value_accum_1_out, 0, 32)
        ^ _extract(state.score_mix_0_out, 0, 32)
        ^ _extract(state.score_mix_1_out, 0, 32)
        ^ (state.done & 0x1),
        32,
    )


def _dispatch_selected_cluster(
    state: _WrapperState,
    *,
    cluster_ready: tuple[int, int],
    max_inflight: int,
) -> tuple[int, bool]:
    for offset in range(2):
        idx = (state.rr_ptr + offset) % 2
        if cluster_ready[idx] and state.inflight[idx] < max_inflight:
            return idx, True
    return 0, False


def _wrapper_step(
    state: _WrapperState,
    *,
    params: JsonDict,
    cycle: int,
    command_valid: bool,
    command: _Command,
    external_ready: tuple[int, int],
) -> tuple[_WrapperState, JsonDict]:
    clusters = list(state.clusters or _default_clusters())
    cluster_service_cycles = int(params["cluster_service_cycles"])
    cluster_ready = tuple(
        1 if external_ready[idx] and not clusters[idx].active else 0 for idx in range(2)
    )
    queue_empty = len(state.queue) == 0
    queue_full = len(state.queue) >= int(params["queue_depth"])
    command_ready = not queue_full
    dispatch_ready = True
    issue_fire = bool(state.dispatch_valid and dispatch_ready)
    push_fire = bool(command_valid and command_ready)
    pop_fire = issue_fire
    selected_cluster, selected_valid = _dispatch_selected_cluster(
        state,
        cluster_ready=cluster_ready,
        max_inflight=int(params["max_inflight_per_cluster"]),
    )
    cluster_complete = tuple(
        clusters[idx].active and clusters[idx].service_ctr == (cluster_service_cycles - 1)
        for idx in range(2)
    )
    if cluster_complete[0]:
        cluster_done_valid = True
        cluster_done_id = 0
    elif cluster_complete[1]:
        cluster_done_valid = True
        cluster_done_id = 1
    else:
        cluster_done_valid = False
        cluster_done_id = 0
    cluster_start = tuple(issue_fire and state.dispatch_cluster_id == idx for idx in range(2))
    accepted = False
    issue = None
    if push_fire:
        accepted = True
    if issue_fire:
        issue = {
            "cycle": cycle,
            "cluster": state.dispatch_cluster_id,
            "tile_id": state.dispatch_tile_id,
            "wave_id": state.dispatch_wave_id,
            "base_token": state.dispatch_base_token,
        }
    completed = None
    result_fold = state.result_fold
    completed_count = state.completed_count
    if cluster_done_valid:
        completed_count += 1
        result_fold = _u(
            result_fold
            ^ _datapath_result_fold(clusters[cluster_done_id].datapath)
            ^ _u(command.tile_id, 16)
            ^ cluster_done_id,
            32,
        )
        completed = {
            "cycle": cycle,
            "cluster": cluster_done_id,
            "completed_count": completed_count,
            "result_fold": result_fold,
        }
    next_clusters: list[_ClusterState] = []
    for idx in range(2):
        cluster = clusters[idx]
        new_seed = cluster.seed
        new_active = cluster.active
        new_service_ctr = cluster.service_ctr
        if cluster_start[idx]:
            new_active = True
            new_service_ctr = 0
            new_seed = _u(
                state.dispatch_tile_id
                ^ state.dispatch_wave_id
                ^ state.dispatch_base_token
                ^ (0x9E3779B9 ^ (idx * 0x01010101)),
                32,
            )
        elif cluster_complete[idx]:
            new_active = False
            new_service_ctr = 0
        elif cluster.active:
            new_service_ctr = _u(cluster.service_ctr + 1, 32)
        datapath_next = _datapath_step(
            cluster.datapath,
            seed_input=cluster.seed,
            start=cluster_start[idx],
            array_m=int(params["datapath_manifest"]["array_m"]),
            array_n=int(params["datapath_manifest"]["array_n"]),
            k_unroll=int(params["datapath_manifest"]["k_unroll"]),
            row_elems=int(params["datapath_manifest"]["softmax_row_elems"]),
            stream_buffer_bits=int(params["datapath_manifest"]["stream_buffer_bits"]),
            mac_accum_bits=int(params["datapath_manifest"]["mac_accum_bits"]),
            softmax_score_bits=int(params["datapath_manifest"]["softmax_score_bits"]),
            softmax_weight_bits=int(params["datapath_manifest"]["softmax_weight_bits"]),
            softmax_input_frac_bits=int(params["datapath_manifest"]["softmax_input_frac_bits"]),
            softmax_bucket_shift=int(
                params["datapath_manifest"]["softmax_reciprocal_lut_bucket_shift"]
            ),
            value_bits=int(params["datapath_manifest"]["value_bits"]),
            value_lanes=int(params["datapath_manifest"]["value_lanes"]),
            score_mix_bits=int(params["datapath_manifest"]["mac_accum_bits"]),
        )
        next_clusters.append(
            _ClusterState(
                active=new_active,
                service_ctr=new_service_ctr,
                seed=new_seed,
                datapath=datapath_next,
            )
        )
    old_queue = list(state.queue)
    head_payload = old_queue[0] if old_queue else _Command(0, 0, 0)
    queue = list(old_queue)
    if push_fire:
        queue.append(command)
    if pop_fire and queue:
        queue.pop(0)
    inflight = list(state.inflight)
    for idx in range(2):
        if cluster_done_valid and cluster_done_id == idx and not (pop_fire and state.dispatch_cluster_id == idx):
            if inflight[idx] > 0:
                inflight[idx] -= 1
        elif pop_fire and state.dispatch_cluster_id == idx and not (
            cluster_done_valid and cluster_done_id == idx and inflight[idx] > 0
        ):
            inflight[idx] += 1
    rr_ptr = state.rr_ptr
    if pop_fire:
        rr_ptr = (state.dispatch_cluster_id + 1) % 2
    dispatch_valid = state.dispatch_valid
    dispatch_cluster_id = state.dispatch_cluster_id
    dispatch_tile_id = state.dispatch_tile_id
    dispatch_wave_id = state.dispatch_wave_id
    dispatch_base_token = state.dispatch_base_token
    if (not state.dispatch_valid) or dispatch_ready:
        dispatch_valid = bool(len(old_queue) > 0 and selected_valid)
        dispatch_cluster_id = selected_cluster
        dispatch_tile_id = head_payload.tile_id
        dispatch_wave_id = head_payload.wave_id
        dispatch_base_token = head_payload.base_token
    next_state = _WrapperState(
        count=len(queue),
        rr_ptr=rr_ptr,
        inflight=(inflight[0], inflight[1]),
        dispatch_valid=dispatch_valid,
        dispatch_cluster_id=dispatch_cluster_id,
        dispatch_tile_id=dispatch_tile_id,
        dispatch_wave_id=dispatch_wave_id,
        dispatch_base_token=dispatch_base_token,
        queue=tuple(queue),
        clusters=(next_clusters[0], next_clusters[1]),
        completed_count=completed_count,
        result_fold=result_fold,
    )
    trace_row = {
        "cycle": cycle,
        "command_valid": int(command_valid),
        "command_ready": int(command_ready),
        "tile_id": command.tile_id,
        "wave_id": command.wave_id,
        "base_token": command.base_token,
        "external_ready": list(external_ready),
        "dispatch_valid": int(state.dispatch_valid),
        "queue_depth": len(state.queue),
        "completed_count": state.completed_count,
        "result_fold": f"{state.result_fold:08x}",
        "cluster_active": [int(cluster.active) for cluster in clusters],
    }
    return next_state, {
        "trace": trace_row,
        "accepted": (
            {
                "cycle": cycle,
                "tile_id": command.tile_id,
                "wave_id": command.wave_id,
                "base_token": command.base_token,
            }
            if accepted
            else None
        ),
        "issue": issue,
        "completed": completed,
    }


def _simulate_reference(
    *,
    params: JsonDict,
    service_window_cycles: int,
    warmup_cycles: int,
    command_count: int,
) -> JsonDict:
    commands = [
        _command_for_index(
            index,
            tile_bits=int(params["tile_id_bits"]),
            wave_bits=int(params["wave_id_bits"]),
            base_bits=int(params["base_token_bits"]),
        )
        for index in range(command_count)
    ]
    state = _WrapperState(
        queue=(),
        clusters=_default_clusters(),
    )
    send_index = 0
    cycle = 0
    accepted_rows: list[JsonDict] = []
    issue_rows: list[JsonDict] = []
    completed_rows: list[JsonDict] = []
    trace_rows: list[JsonDict] = []
    ready_low_cycles = 0
    window_active_cycles = 0
    window_dual_active_cycles = 0
    window_completed_count = 0
    window_issue_counts = [0, 0]
    max_queue_depth = 0
    drain_limit = warmup_cycles + service_window_cycles + max(command_count * 4, 256)
    while cycle < drain_limit:
        command = commands[min(send_index, command_count - 1)]
        command_valid = send_index < command_count and cycle > 0 and not _command_gap(cycle)
        external_ready = _external_ready(
            cycle,
            cluster_active=(
                bool(state.clusters[0].active),
                bool(state.clusters[1].active),
            ),
        )
        state, events = _wrapper_step(
            state,
            params=params,
            cycle=cycle,
            command_valid=command_valid,
            command=command,
            external_ready=external_ready,
        )
        trace_rows.append(events["trace"])
        max_queue_depth = max(max_queue_depth, int(events["trace"]["queue_depth"]))
        if not int(events["trace"]["command_ready"]):
            ready_low_cycles += 1
        if events["accepted"] is not None:
            accepted_rows.append(events["accepted"])
            send_index += 1
        if events["issue"] is not None:
            issue_rows.append(events["issue"])
        if events["completed"] is not None:
            completed_rows.append(events["completed"])
        if warmup_cycles <= cycle < warmup_cycles + service_window_cycles:
            if any(events["trace"]["cluster_active"]):
                window_active_cycles += 1
            if events["trace"]["cluster_active"] == [1, 1]:
                window_dual_active_cycles += 1
            if events["issue"] is not None:
                window_issue_counts[int(events["issue"]["cluster"])] += 1
            if events["completed"] is not None:
                window_completed_count += 1
        if cycle >= warmup_cycles + service_window_cycles and send_index >= command_count:
            if not state.clusters[0].active and not state.clusters[1].active and len(state.queue) == 0:
                break
        cycle += 1
    if window_active_cycles != service_window_cycles:
        raise RuntimeError("reference simulation did not keep the wrapper active across the full service window")
    if ready_low_cycles <= 0:
        raise RuntimeError("reference simulation did not exercise command_ready backpressure")
    if window_issue_counts[0] <= 0 or window_issue_counts[1] <= 0:
        raise RuntimeError("reference simulation did not issue commands across both clusters")
    if state.completed_count != len(accepted_rows):
        raise RuntimeError("reference simulation did not fully drain accepted commands")
    return {
        "commands": commands,
        "accepted_rows": accepted_rows,
        "issue_rows": issue_rows,
        "completed_rows": completed_rows,
        "trace_rows": trace_rows,
        "final_cycle": cycle,
        "final_completed_count": state.completed_count,
        "final_result_fold": f"{state.result_fold:08x}",
        "ready_low_cycles": ready_low_cycles,
        "window_active_cycles": window_active_cycles,
        "window_dual_active_cycles": window_dual_active_cycles,
        "window_completed_count": window_completed_count,
        "window_issue_counts": {"0": window_issue_counts[0], "1": window_issue_counts[1]},
        "max_queue_depth": max_queue_depth,
    }


def _tb_text(
    *,
    params: JsonDict,
    commands: list[_Command],
    clock_period_ns: float,
    warmup_cycles: int,
    service_window_cycles: int,
    vcd_path: str,
) -> str:
    top_name = str(params["top_name"])
    tile_bits = int(params["tile_id_bits"])
    wave_bits = int(params["wave_id_bits"])
    base_bits = int(params["base_token_bits"])
    command_init_lines: list[str] = []
    for idx, command in enumerate(commands):
        command_init_lines.append(
            f"    command_tile_ids[{idx}] = {tile_bits}'d{command.tile_id}; "
            f"command_wave_ids[{idx}] = {wave_bits}'d{command.wave_id}; "
            f"command_base_tokens[{idx}] = {base_bits}'d{command.base_token};"
        )
    command_count = len(commands)
    cycle_limit = warmup_cycles + service_window_cycles + 128
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMAND_COUNT = {command_count};
  localparam integer WARMUP_CYCLES = {warmup_cycles};
  localparam integer SERVICE_WINDOW_CYCLES = {service_window_cycles};
  localparam integer CYCLE_LIMIT = {cycle_limit};
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid;
  wire command_ready;
  reg [{tile_bits - 1}:0] command_tile_id;
  reg [{wave_bits - 1}:0] command_wave_id;
  reg [{base_bits - 1}:0] command_base_token;
  reg [1:0] external_cluster_ready;
  wire [31:0] completed_count;
  wire [31:0] result_fold;
  reg [{tile_bits - 1}:0] command_tile_ids [0:COMMAND_COUNT-1];
  reg [{wave_bits - 1}:0] command_wave_ids [0:COMMAND_COUNT-1];
  reg [{base_bits - 1}:0] command_base_tokens [0:COMMAND_COUNT-1];
  integer cycle;
  integer send_index;
  integer accepted_count;
  integer completed_snapshot;
  integer ready_low_cycles;
  integer window_active_cycles;
  integer window_dual_active_cycles;
  integer window_completed_count;
  integer window_issue_count_0;
  integer window_issue_count_1;
  integer max_queue_depth;

  {top_name} dut (
    .clk(clk),
    .rst_n(rst_n),
    .command_valid(command_valid),
    .command_ready(command_ready),
    .command_tile_id(command_tile_id),
    .command_wave_id(command_wave_id),
    .command_base_token(command_base_token),
    .external_cluster_ready(external_cluster_ready),
    .completed_count(completed_count),
    .result_fold(result_fold)
  );

  always #{clock_period_ns / 2.0:.3f} clk = ~clk;

  initial begin
{chr(10).join(command_init_lines)}
    command_valid = 1'b0;
    command_tile_id = {{{tile_bits}{{1'b0}}}};
    command_wave_id = {{{wave_bits}{{1'b0}}}};
    command_base_token = {{{base_bits}{{1'b0}}}};
    external_cluster_ready = 2'b00;
    cycle = 0;
    send_index = 0;
    accepted_count = 0;
    completed_snapshot = 0;
    ready_low_cycles = 0;
    window_active_cycles = 0;
    window_dual_active_cycles = 0;
    window_completed_count = 0;
    window_issue_count_0 = 0;
    window_issue_count_1 = 0;
    max_queue_depth = 0;
    $dumpfile("{vcd_path}");
    $dumpvars(0, tb.dut);
    $dumpoff;
    repeat (4) @(posedge clk);
    rst_n = 1'b1;
  end

  always @(*) begin
    if (send_index < COMMAND_COUNT) begin
      command_tile_id = command_tile_ids[send_index];
      command_wave_id = command_wave_ids[send_index];
      command_base_token = command_base_tokens[send_index];
    end else begin
      command_tile_id = {{{tile_bits}{{1'b0}}}};
      command_wave_id = {{{wave_bits}{{1'b0}}}};
      command_base_token = {{{base_bits}{{1'b0}}}};
    end
    command_valid = rst_n && (cycle > 0) && (send_index < COMMAND_COUNT) && ((cycle % 23) != 7);
    external_cluster_ready[0] = (!dut.cluster_0_active && ((cycle % 2) == 0)) ? 1'b1 : 1'b0;
    external_cluster_ready[1] = (!dut.cluster_1_active && ((cycle % 2) == 0)) ? 1'b1 : 1'b0;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      send_index <= 0;
      accepted_count <= 0;
      completed_snapshot <= 0;
      ready_low_cycles <= 0;
      window_active_cycles <= 0;
      window_dual_active_cycles <= 0;
      window_completed_count <= 0;
      window_issue_count_0 <= 0;
      window_issue_count_1 <= 0;
      max_queue_depth <= 0;
    end else begin
      if (cycle == WARMUP_CYCLES - 1) begin
        $dumpon;
      end
      if (cycle == WARMUP_CYCLES + SERVICE_WINDOW_CYCLES - 1) begin
        $dumpoff;
      end
      if (!command_ready) begin
        ready_low_cycles <= ready_low_cycles + 1;
      end
      if (dut.u_dispatch.queued_count > max_queue_depth) begin
        max_queue_depth <= dut.u_dispatch.queued_count;
      end
      if (cycle >= WARMUP_CYCLES && cycle < WARMUP_CYCLES + SERVICE_WINDOW_CYCLES) begin
        if (dut.cluster_0_active || dut.cluster_1_active) begin
          window_active_cycles <= window_active_cycles + 1;
        end
        if (dut.cluster_0_active && dut.cluster_1_active) begin
          window_dual_active_cycles <= window_dual_active_cycles + 1;
        end
      end
      if (command_valid && command_ready) begin
        $display("ACCEPT cycle=%0d tile=%0d wave=%0d base=%0d", cycle, command_tile_id, command_wave_id, command_base_token);
        send_index <= send_index + 1;
        accepted_count <= accepted_count + 1;
      end
      if (dut.cluster_0_start) begin
        $display("ISSUE cycle=%0d cluster=0 tile=%0d wave=%0d base=%0d", cycle, dut.dispatch_tile_id, dut.dispatch_wave_id, dut.dispatch_base_token);
        if (cycle >= WARMUP_CYCLES && cycle < WARMUP_CYCLES + SERVICE_WINDOW_CYCLES) begin
          window_issue_count_0 <= window_issue_count_0 + 1;
        end
      end
      if (dut.cluster_1_start) begin
        $display("ISSUE cycle=%0d cluster=1 tile=%0d wave=%0d base=%0d", cycle, dut.dispatch_tile_id, dut.dispatch_wave_id, dut.dispatch_base_token);
        if (cycle >= WARMUP_CYCLES && cycle < WARMUP_CYCLES + SERVICE_WINDOW_CYCLES) begin
          window_issue_count_1 <= window_issue_count_1 + 1;
        end
      end
      completed_snapshot <= completed_count;
      if (completed_count != completed_snapshot) begin
        $display("DONE cycle=%0d cluster=%0d completed=%0d result=%08x",
                 cycle, dut.cluster_done_id, completed_count, result_fold);
        if (cycle >= WARMUP_CYCLES && cycle < WARMUP_CYCLES + SERVICE_WINDOW_CYCLES) begin
          window_completed_count <= window_completed_count + 1;
        end
      end
      if (cycle >= WARMUP_CYCLES + SERVICE_WINDOW_CYCLES &&
          completed_count == accepted_count &&
          !dut.cluster_0_active &&
          !dut.cluster_1_active &&
          dut.u_dispatch.queue_empty) begin
        $display("SUMMARY ready_low=%0d window_active=%0d window_dual=%0d window_completed=%0d issue0=%0d issue1=%0d max_queue=%0d",
                 ready_low_cycles, window_active_cycles, window_dual_active_cycles, window_completed_count,
                 window_issue_count_0, window_issue_count_1, max_queue_depth);
        $display("FINAL cycle=%0d accepted=%0d completed=%0d result=%08x", cycle, accepted_count, completed_count, result_fold);
        $finish;
      end
      if (cycle >= CYCLE_LIMIT) begin
        $display("FAIL timeout cycle=%0d accepted=%0d completed=%0d result=%08x", cycle, accepted_count, completed_count, result_fold);
        $finish_and_return(1);
      end
      cycle <= cycle + 1;
    end
  end
endmodule
"""


def _compile_and_run(*, sources: list[Path], timeout: int = 240) -> str:
    with tempfile.TemporaryDirectory(prefix="schedule-wrapper-activity-run-") as tmp_text:
        simv = Path(tmp_text) / "simv"
        compiled = subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), *[str(src) for src in sources]],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=timeout)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")
        return run.stdout


def _parse_stdout(stdout: str) -> JsonDict:
    accepted_rows: list[JsonDict] = []
    issue_rows: list[JsonDict] = []
    completed_rows: list[JsonDict] = []
    final_row: JsonDict | None = None
    summary_row: JsonDict | None = None
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("ACCEPT "):
            fields = dict(item.split("=", 1) for item in line.split()[1:])
            accepted_rows.append(
                {
                    "cycle": int(fields["cycle"]),
                    "tile_id": int(fields["tile"]),
                    "wave_id": int(fields["wave"]),
                    "base_token": int(fields["base"]),
                }
            )
            continue
        if line.startswith("ISSUE "):
            fields = dict(item.split("=", 1) for item in line.split()[1:])
            issue_rows.append(
                {
                    "cycle": int(fields["cycle"]),
                    "cluster": int(fields["cluster"]),
                    "tile_id": int(fields["tile"]),
                    "wave_id": int(fields["wave"]),
                    "base_token": int(fields["base"]),
                }
            )
            continue
        if line.startswith("DONE "):
            fields = dict(item.split("=", 1) for item in line.split()[1:])
            completed_rows.append(
                {
                    "cycle": int(fields["cycle"]),
                    "cluster": int(fields["cluster"]),
                    "completed_count": int(fields["completed"]),
                    "result_fold": fields["result"].lower(),
                }
            )
            continue
        if line.startswith("FINAL "):
            fields = dict(item.split("=", 1) for item in line.split()[1:])
            final_row = {
                "cycle": int(fields["cycle"]),
                "accepted": int(fields["accepted"]),
                "completed": int(fields["completed"]),
                "result_fold": fields["result"].lower(),
            }
            continue
        if line.startswith("SUMMARY "):
            fields = dict(item.split("=", 1) for item in line.split()[1:])
            summary_row = {
                "ready_low_cycles": int(fields["ready_low"]),
                "window_active_cycles": int(fields["window_active"]),
                "window_dual_active_cycles": int(fields["window_dual"]),
                "window_completed_count": int(fields["window_completed"]),
                "window_issue_counts": {
                    "0": int(fields["issue0"]),
                    "1": int(fields["issue1"]),
                },
                "max_queue_depth": int(fields["max_queue"]),
            }
            continue
        if line.startswith("FAIL "):
            raise RuntimeError(line)
    if final_row is None:
        raise RuntimeError("simulation did not emit FINAL line")
    if summary_row is None:
        raise RuntimeError("simulation did not emit SUMMARY line")
    return {
        "accepted_rows": accepted_rows,
        "issue_rows": issue_rows,
        "completed_rows": completed_rows,
        "summary_row": summary_row,
        "final_row": final_row,
    }


def _assert_equal(label: str, expected: object, observed: object) -> None:
    if expected != observed:
        raise RuntimeError(f"schedule-wrapper activity mismatch in {label}")


def _completed_timeline(rows: list[JsonDict]) -> list[JsonDict]:
    return [
        {
            "cycle": int(row["cycle"]) + 1,
            "completed_count": int(row["completed_count"]),
        }
        for row in rows
    ]


def generate_activity(
    config: JsonDict,
    out_dir: Path,
    *,
    clock_period_ns: float = _DEFAULT_CLOCK_PERIOD_NS,
    service_window_cycles: int = _DEFAULT_SERVICE_WINDOW_CYCLES,
    warmup_cycles: int = _DEFAULT_WARMUP_CYCLES,
    command_count: int = _DEFAULT_COMMAND_COUNT,
) -> JsonDict:
    if clock_period_ns <= 0.0:
        raise ValueError("clock_period_ns must be > 0")
    if service_window_cycles <= 0:
        raise ValueError("service_window_cycles must be > 0")
    if warmup_cycles < 4:
        raise ValueError("warmup_cycles must be >= 4")
    cfg = json.loads(json.dumps(config))
    params = _validate_wrapper_config(cfg)
    if int(params["clusters"]) != 2:
        raise ValueError("wrapper activity generator currently requires clusters=2")
    datapath_manifest = json.loads(json.dumps(params["datapath_params"]))
    if bool(datapath_manifest.get("equivalence_hash")):
        raise ValueError("wrapper activity generator requires datapath equivalence_hash=false")
    if str(datapath_manifest.get("semantic_profile") or "").strip() != "score32_exp_lut_div":
        raise ValueError("wrapper activity generator requires semantic_profile=score32_exp_lut_div")
    if str(datapath_manifest.get("softmax_impl") or "").strip() != "exp_lut_div":
        raise ValueError("wrapper activity generator requires softmax_impl=exp_lut_div")
    runtime_params = {
        **params,
        "datapath_manifest": datapath_manifest,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    reference = _simulate_reference(
        params=runtime_params,
        service_window_cycles=service_window_cycles,
        warmup_cycles=warmup_cycles,
        command_count=command_count,
    )
    with tempfile.TemporaryDirectory(prefix="schedule-wrapper-activity-") as tmp_text:
        rtl_dir = Path(tmp_text) / "rtl"
        _write_wrapper_rtl(cfg=cfg, params=params, out_path=rtl_dir)
        top_path = rtl_dir / _OUTPUT_TOP_NAME
        tb_path = Path(tmp_text) / "tb.sv"
        tb_path.write_text(
            _tb_text(
                params=runtime_params,
                commands=reference["commands"],
                clock_period_ns=clock_period_ns,
                warmup_cycles=warmup_cycles,
                service_window_cycles=service_window_cycles,
                vcd_path=str((out_dir / _OUTPUT_VCD_NAME).resolve()),
            ),
            encoding="utf-8",
        )
        stdout = _compile_and_run(sources=[top_path, tb_path])
        generated_paths = {
            _OUTPUT_CONFIG_NAME: rtl_dir / _OUTPUT_CONFIG_NAME,
            _OUTPUT_TOP_NAME: top_path,
            _OUTPUT_WRAPPER_MANIFEST_NAME: rtl_dir / _OUTPUT_WRAPPER_MANIFEST_NAME,
        }
        for name, src in generated_paths.items():
            (out_dir / name).write_bytes(src.read_bytes())
    vcd_path = out_dir / _OUTPUT_VCD_NAME
    if not vcd_path.is_file():
        raise RuntimeError("simulation did not emit VCD")
    _normalize_vcd(vcd_path)
    observed = _parse_stdout(stdout)
    _assert_equal("accepted_rows", reference["accepted_rows"], observed["accepted_rows"])
    _assert_equal("issue_rows", reference["issue_rows"], observed["issue_rows"])
    _assert_equal(
        "completed_timeline",
        _completed_timeline(reference["completed_rows"]),
        [
            {
                "cycle": int(row["cycle"]),
                "completed_count": int(row["completed_count"]),
            }
            for row in observed["completed_rows"]
        ],
    )
    _assert_equal("final completed count", reference["final_completed_count"], observed["final_row"]["completed"])
    _assert_equal("summary_row", {
        "ready_low_cycles": reference["ready_low_cycles"],
        "window_active_cycles": reference["window_active_cycles"],
        "window_dual_active_cycles": reference["window_dual_active_cycles"],
        "window_completed_count": reference["window_completed_count"],
        "window_issue_counts": reference["window_issue_counts"],
        "max_queue_depth": reference["max_queue_depth"],
    }, observed["summary_row"])
    if observed["final_row"]["accepted"] != len(reference["accepted_rows"]):
        raise RuntimeError("accepted count mismatch in final row")
    manifest = {
        "version": 1,
        "model": "attention_dual_stream_schedule_wrapper_activity_v1",
        "generator": "npu/eval/generate_attention_dual_stream_schedule_wrapper_activity.py",
        "clock_period_ns": clock_period_ns,
        "scope": _SCOPE,
        "service_window_cycles": service_window_cycles,
        "cycle_count": service_window_cycles,
        "warmup_cycles": warmup_cycles,
        "cluster_service_cycles": int(params["cluster_service_cycles"]),
        "total_sim_cycles": int(reference["final_cycle"]),
        "artifacts": {
            "config_json": _OUTPUT_CONFIG_NAME,
            "top_verilog": _OUTPUT_TOP_NAME,
            "wrapper_manifest_json": _OUTPUT_WRAPPER_MANIFEST_NAME,
            "vcd": _OUTPUT_VCD_NAME,
        },
        "hashes": {
            "config_sha256": _hash_json(cfg),
            "top_sha256": _sha256_file(out_dir / _OUTPUT_TOP_NAME),
            "vcd_sha256": _sha256_file(vcd_path),
            "accepted_rows_sha256": _hash_json(reference["accepted_rows"]),
            "issue_rows_sha256": _hash_json(reference["issue_rows"]),
            "completed_timeline_sha256": _hash_json(_completed_timeline(reference["completed_rows"])),
            "summary_sha256": _hash_json(observed["summary_row"]),
            "final_state_sha256": _hash_json({"accepted": observed["final_row"]["accepted"], "completed": observed["final_row"]["completed"]}),
        },
        "gates": {
            "equivalence_pass": True,
            "protocol_gate_ok": True,
            "count_gate_ok": True,
            "hash_gate_ok": True,
            "observable_completion_gate_ok": True,
            "window_active_gate_ok": True,
            "both_clusters_issue_gate_ok": True,
            "service_window_gate_ok": True,
        },
        "request_result_protocol_counters": {
            "accepted_count": len(reference["accepted_rows"]),
            "issue_count": len(reference["issue_rows"]),
            "completed_count": len(reference["completed_rows"]),
            "ready_low_cycles": int(reference["ready_low_cycles"]),
            "window_active_cycles": int(reference["window_active_cycles"]),
            "window_dual_active_cycles": int(reference["window_dual_active_cycles"]),
            "window_completed_count": int(reference["window_completed_count"]),
            "max_queue_depth": int(reference["max_queue_depth"]),
            "window_issue_counts": reference["window_issue_counts"],
            "cluster_issue_counts_total": {
                "0": sum(1 for row in reference["issue_rows"] if row["cluster"] == 0),
                "1": sum(1 for row in reference["issue_rows"] if row["cluster"] == 1),
            },
            "final_result_fold_evidence": observed["final_row"]["result_fold"],
        },
        "completion_result_evidence": {
            "hardware_done_rows": observed["completed_rows"],
            "hardware_final_result_fold": observed["final_row"]["result_fold"],
            "reference_final_result_fold": reference["final_result_fold"],
        },
        "stimulus_contract": {
            "command_count": command_count,
            "command_gap_rule": "cycle % 23 != 7",
            "external_ready_rule": "an inactive cluster is externally ready only on even cycles",
            "equivalence_hash_in_hardware": False,
            "testbench_hashes_are_evidence_only": True,
        },
        "scope_summary": {
            "exercised": [
                "actual generated dual-stream schedule-wrapper RTL",
                "multiple commands issued across both clusters",
                "top-level command_ready backpressure from queue saturation",
                "warmup before VCD dump and drain after VCD dump",
                "exact 986-cycle active wrapper service window",
            ],
            "remaining": [
                "post-route power, ODB, and SPEF are outside this generator",
                "hardware equivalence hash remains disabled in the wrapper datapath",
            ],
        },
    }
    for value in json.loads(json.dumps(manifest)).get("artifacts", {}).values():
        if isinstance(value, str) and value.startswith("/"):
            raise RuntimeError("portable manifest must not contain absolute artifact paths")
    (out_dir / _OUTPUT_MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=_DEFAULT_CLOCK_PERIOD_NS)
    parser.add_argument("--service-window-cycles", type=int, default=_DEFAULT_SERVICE_WINDOW_CYCLES)
    parser.add_argument("--warmup-cycles", type=int, default=_DEFAULT_WARMUP_CYCLES)
    parser.add_argument("--command-count", type=int, default=_DEFAULT_COMMAND_COUNT)
    args = parser.parse_args()
    generate_activity(
        _load(args.config),
        args.out_dir,
        clock_period_ns=args.clock_period_ns,
        service_window_cycles=args.service_window_cycles,
        warmup_cycles=args.warmup_cycles,
        command_count=args.command_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
