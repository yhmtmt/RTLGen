#!/usr/bin/env python3
"""Model decoder logit-rank streaming hierarchy throughput and latency."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

DEFAULT_RANK_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
)
DEFAULT_SCALE_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
)
DEFAULT_CANDIDATE_MERGE_PPA = Path(
    "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator + denominator - 1) // denominator


def _byte_width(bits: int) -> int:
    return _ceil_div(bits, 8)


def _parse_csv_point(path: str) -> JsonDict:
    match = re.search(r"logit_rank_r(?P<lanes>\d+)_l(?P<bits>\d+)_k(?P<topk>\d+)", path)
    if not match:
        return {"lanes": None, "logit_bits": None, "top_k": None}
    return {
        "lanes": int(match.group("lanes")),
        "logit_bits": int(match.group("bits")),
        "top_k": int(match.group("topk")),
    }


def _parse_candidate_merge_csv_point(path: str) -> JsonDict:
    match = re.search(
        r"candidate_stream_merge_fifo_k(?P<topk>\d+)_l(?P<logit_bits>\d+)_t"
        r"(?P<token_id_bits>\d+)_d(?P<fifo_depth_groups>\d+)",
        path,
    )
    if not match:
        return {
            "top_k": None,
            "logit_bits": None,
            "token_id_bits": None,
            "fifo_depth_groups": None,
        }
    return {
        "top_k": int(match.group("topk")),
        "logit_bits": int(match.group("logit_bits")),
        "token_id_bits": int(match.group("token_id_bits")),
        "fifo_depth_groups": int(match.group("fifo_depth_groups")),
    }


def _load_json(path: Path) -> JsonDict:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return payload


def load_ranker_points(path: Path | None) -> list[JsonDict]:
    if path is None or not path.exists():
        return []
    payload = _load_json(path)
    rows: list[JsonDict] = []
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        ref = proposal.get("metrics_ref")
        metrics = proposal.get("metric_summary")
        if not isinstance(ref, dict) or not isinstance(metrics, dict):
            continue
        if str(ref.get("status") or "") != "ok":
            continue
        metrics_csv = str(ref.get("metrics_csv") or "")
        point = _parse_csv_point(metrics_csv)
        rows.append(
            {
                "source": str(path),
                "artifact_item_id": payload.get("item_id"),
                "metrics_csv": metrics_csv,
                "lanes": point["lanes"],
                "logit_bits": point["logit_bits"],
                "top_k": point["top_k"],
                "metrics": {
                    "critical_path_ns": _as_float(metrics.get("critical_path_ns")),
                    "die_area": _as_float(metrics.get("die_area")),
                    "total_power_mw": _as_float(metrics.get("total_power_mw")),
                },
            }
        )
    rows.sort(
        key=lambda row: (
            _as_int(row.get("lanes"), 10**9),
            _as_int(row.get("top_k"), 10**9),
            row["metrics"]["critical_path_ns"],
        )
    )
    return rows


def load_ranker_points_from_paths(paths: list[Path | None]) -> list[JsonDict]:
    points: list[JsonDict] = []
    seen: set[tuple[str | None, int, int]] = set()
    for path in paths:
        for point in load_ranker_points(path):
            key = (
                point.get("metrics_csv"),
                _as_int(point.get("lanes")),
                _as_int(point.get("top_k")),
            )
            if key in seen:
                continue
            seen.add(key)
            points.append(point)
    points.sort(
        key=lambda row: (
            _as_int(row.get("lanes"), 10**9),
            _as_int(row.get("top_k"), 10**9),
            row["metrics"]["critical_path_ns"],
        )
    )
    return points


def load_candidate_merge_points(path: Path | None) -> list[JsonDict]:
    if path is None or not path.exists():
        return []
    payload = _load_json(path)
    rows: list[JsonDict] = []
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        ref = proposal.get("metrics_ref")
        metrics = proposal.get("metric_summary")
        if not isinstance(ref, dict) or not isinstance(metrics, dict):
            continue
        if str(ref.get("status") or "") != "ok":
            continue
        metrics_csv = str(ref.get("metrics_csv") or "")
        point = _parse_candidate_merge_csv_point(metrics_csv)
        rows.append(
            {
                "source": str(path),
                "artifact_item_id": payload.get("item_id"),
                "metrics_csv": metrics_csv,
                "top_k": point["top_k"],
                "logit_bits": point["logit_bits"],
                "token_id_bits": point["token_id_bits"],
                "fifo_depth_groups": point["fifo_depth_groups"],
                "metrics": {
                    "critical_path_ns": _as_float(metrics.get("critical_path_ns")),
                    "die_area": _as_float(metrics.get("die_area")),
                    "total_power_mw": _as_float(metrics.get("total_power_mw")),
                },
            }
        )
    rows.sort(
        key=lambda row: (
            _as_int(row.get("top_k"), 10**9),
            _as_int(row.get("logit_bits"), 10**9),
            _as_int(row.get("token_id_bits"), 10**9),
            _as_int(row.get("fifo_depth_groups"), 10**9),
            row["metrics"]["critical_path_ns"],
            row["metrics"]["die_area"],
            row["metrics"]["total_power_mw"],
        )
    )
    return rows


def _fallback_ranker_point(*, lanes: int, top_k: int, critical_path_ns: float) -> JsonDict:
    return {
        "source": "cli_default",
        "metrics_csv": None,
        "lanes": lanes,
        "logit_bits": 16,
        "top_k": top_k,
        "metrics": {
            "critical_path_ns": critical_path_ns,
            "die_area": None,
            "total_power_mw": None,
        },
    }


def _select_ranker_point(
    points: list[JsonDict], *, lanes: int, top_k: int, default_critical_path_ns: float
) -> JsonDict:
    exact = [
        row
        for row in points
        if _as_int(row.get("lanes")) == lanes and _as_int(row.get("top_k")) == top_k
    ]
    if exact:
        return exact[0]
    same_k = [row for row in points if _as_int(row.get("top_k")) == top_k and _as_int(row.get("lanes")) > 0]
    if same_k:
        nearest = min(same_k, key=lambda row: abs(_as_int(row.get("lanes")) - lanes))
        scale = math.log2(max(2, lanes)) / math.log2(max(2, _as_int(nearest.get("lanes"), lanes)))
        clone = json.loads(json.dumps(nearest))
        clone["source"] = f"{nearest['source']}#scaled_nearest_lane"
        clone["lanes"] = lanes
        clone["metrics"]["critical_path_ns"] = round(nearest["metrics"]["critical_path_ns"] * scale, 6)
        clone["model_note"] = (
            f"critical_path_ns scaled from measured r{nearest['lanes']} k{nearest['top_k']} "
            f"by log2(lanes) ratio"
        )
        return clone
    return _fallback_ranker_point(
        lanes=lanes, top_k=top_k, critical_path_ns=default_critical_path_ns
    )


def _fallback_candidate_merge_point(
    *,
    top_k: int,
    logit_bits: int,
    token_id_bits: int,
    fifo_depth_groups: int,
    critical_path_ns: float,
) -> JsonDict:
    return {
        "source": "fallback_ranker_merge_proxy",
        "metrics_csv": None,
        "top_k": top_k,
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "fifo_depth_groups": fifo_depth_groups,
        "metrics": {
            "critical_path_ns": critical_path_ns,
            "die_area": None,
            "total_power_mw": None,
        },
        "model_note": "candidate-stream merge/FIFO PPA artifact missing; using ranker clock proxy",
    }


def _select_candidate_merge_point(
    points: list[JsonDict],
    *,
    top_k: int,
    logit_bits: int,
    token_id_bits: int,
    fifo_depth_groups: int,
    default_critical_path_ns: float,
) -> JsonDict:
    exact = [
        row
        for row in points
        if _as_int(row.get("top_k")) == top_k
        and _as_int(row.get("logit_bits")) == logit_bits
        and _as_int(row.get("token_id_bits")) == token_id_bits
        and _as_int(row.get("fifo_depth_groups")) == fifo_depth_groups
    ]
    if exact:
        return exact[0]
    same_k = [
        row
        for row in points
        if _as_int(row.get("top_k")) == top_k
        and _as_int(row.get("logit_bits")) == logit_bits
        and _as_int(row.get("token_id_bits")) == token_id_bits
    ]
    if same_k:
        nearest = min(
            same_k,
            key=lambda row: (
                abs(_as_int(row.get("fifo_depth_groups")) - fifo_depth_groups),
                row["metrics"]["critical_path_ns"],
            ),
        )
        clone = json.loads(json.dumps(nearest))
        clone["source"] = f"{nearest['source']}#nearest_fifo_depth"
        clone["fifo_depth_groups"] = fifo_depth_groups
        clone["model_note"] = (
            f"candidate-stream merge/FIFO metrics taken from nearest measured depth "
            f"d{nearest['fifo_depth_groups']}"
        )
        return clone
    return _fallback_candidate_merge_point(
        top_k=top_k,
        logit_bits=logit_bits,
        token_id_bits=token_id_bits,
        fifo_depth_groups=fifo_depth_groups,
        critical_path_ns=default_critical_path_ns,
    )


def simulate_streaming_hierarchy(
    *,
    vocab_size: int,
    producer_lanes: int,
    producer_latency_cycles: int,
    producer_ii_cycles: int,
    local_ranker_latency_cycles: int,
    local_ranker_ii_cycles: int,
    local_top_k: int,
    global_merge_latency_cycles: int,
    global_merge_ii_cycles: int,
    candidate_fifo_depth_groups: int,
) -> JsonDict:
    tile_count = _ceil_div(vocab_size, producer_lanes)
    local_done_times: list[int] = []
    local_available = 0
    for tile in range(tile_count):
        producer_ready = producer_latency_cycles + tile * producer_ii_cycles
        local_start = max(producer_ready, local_available)
        local_done_times.append(local_start + local_ranker_latency_cycles)
        local_available = local_start + local_ranker_ii_cycles

    merge_start_times: list[int] = []
    merge_done_times: list[int] = []
    merge_available = 0
    for local_done in local_done_times:
        merge_start = max(local_done, merge_available)
        merge_start_times.append(merge_start)
        merge_done_times.append(merge_start + global_merge_latency_cycles)
        merge_available = merge_start + global_merge_ii_cycles

    events: list[tuple[int, int]] = []
    for t in local_done_times:
        events.append((t, 1))
    for t in merge_start_times:
        events.append((t, -1))
    events.sort(key=lambda item: (item[0], -item[1]))
    occupancy = 0
    max_occupancy = 0
    for _, delta in events:
        occupancy += delta
        max_occupancy = max(max_occupancy, occupancy)

    total_candidates = tile_count * local_top_k
    total_cycles = max(merge_done_times) if merge_done_times else 0
    return {
        "tile_count": tile_count,
        "producer_lanes": producer_lanes,
        "local_top_k": local_top_k,
        "total_candidates_emitted": total_candidates,
        "total_cycles": total_cycles,
        "producer_last_tile_ready_cycle": producer_latency_cycles + max(0, tile_count - 1) * producer_ii_cycles,
        "local_last_done_cycle": max(local_done_times) if local_done_times else 0,
        "global_last_done_cycle": total_cycles,
        "required_fifo_depth_groups": max_occupancy,
        "candidate_fifo_depth_groups": candidate_fifo_depth_groups,
        "fifo_capacity_ok": max_occupancy <= candidate_fifo_depth_groups,
        "producer_ii_cycles": producer_ii_cycles,
        "local_ranker_latency_cycles": local_ranker_latency_cycles,
        "local_ranker_ii_cycles": local_ranker_ii_cycles,
        "global_merge_latency_cycles": global_merge_latency_cycles,
        "global_merge_ii_cycles": global_merge_ii_cycles,
    }


def _time_summary(*, cycles: int, clock_ns: float, vocab_size: int) -> JsonDict:
    latency_ns = cycles * clock_ns
    latency_us = latency_ns / 1000.0
    tokens_per_s = 1_000_000_000.0 / latency_ns if latency_ns > 0 else 0.0
    logits_per_s = vocab_size * tokens_per_s
    return {
        "clock_ns": round(clock_ns, 6),
        "latency_cycles": cycles,
        "latency_us_per_token": round(latency_us, 6),
        "tokens_per_s": round(tokens_per_s, 3),
        "logits_per_s": round(logits_per_s, 3),
    }


def _flat_point_report(
    *,
    point: JsonDict,
    vocab_size: int,
    ranker_latency_cycles: int,
    ranker_ii_cycles: int,
) -> JsonDict:
    lanes = _as_int(point.get("lanes"), 1) or 1
    tiles = _ceil_div(vocab_size, lanes)
    cycles = ranker_latency_cycles + max(0, tiles - 1) * ranker_ii_cycles
    metrics = point["metrics"]
    return {
        "architecture": "flat_measured_ranker_scan",
        "lanes": lanes,
        "top_k": point.get("top_k"),
        "tile_count": tiles,
        "ranker_latency_cycles": ranker_latency_cycles,
        "ranker_ii_cycles": ranker_ii_cycles,
        "total_cycles": cycles,
        "timing": _time_summary(
            cycles=cycles,
            clock_ns=_as_float(metrics.get("critical_path_ns"), 1.0),
            vocab_size=vocab_size,
        ),
        "metrics": metrics,
        "source": point.get("source"),
        "metrics_csv": point.get("metrics_csv"),
    }


def _traffic_summary(
    *,
    vocab_size: int,
    tile_count: int,
    producer_lanes: int,
    top_k: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    logit_bytes = _byte_width(logit_bits)
    token_bytes = _byte_width(token_id_bits)
    materialized_logit_bytes = vocab_size * logit_bytes
    candidate_bytes_per_entry = logit_bytes + token_bytes
    candidate_entries = tile_count * top_k
    candidate_payload_bytes = candidate_entries * candidate_bytes_per_entry
    candidate_fifo_round_trip_bytes = candidate_payload_bytes * 2
    final_topk_bytes = top_k * candidate_bytes_per_entry
    materialized_rank_memory_bytes = materialized_logit_bytes * 2
    streaming_memory_bytes = candidate_fifo_round_trip_bytes + final_topk_bytes
    reduction = 0.0
    if materialized_rank_memory_bytes > 0:
        reduction = 1.0 - (streaming_memory_bytes / materialized_rank_memory_bytes)
    return {
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "producer_lanes": producer_lanes,
        "top_k": top_k,
        "materialized_rank_memory_bytes": materialized_rank_memory_bytes,
        "streaming_candidate_memory_bytes": streaming_memory_bytes,
        "candidate_payload_bytes": candidate_payload_bytes,
        "candidate_fifo_round_trip_bytes": candidate_fifo_round_trip_bytes,
        "final_topk_bytes": final_topk_bytes,
        "candidate_entries": candidate_entries,
        "traffic_reduction_vs_materialized": round(reduction, 6),
    }


def _memory_service_summary(
    *,
    read_bytes: int,
    write_bytes: int,
    compute_cycles: int,
    clock_ns: float,
    memory_bandwidth_bytes_per_cycle: float,
    sram_read_energy_pj_per_byte: float,
    sram_write_energy_pj_per_byte: float,
    noc_hops: int,
    noc_energy_pj_per_byte_hop: float,
) -> JsonDict:
    if memory_bandwidth_bytes_per_cycle <= 0.0:
        raise ValueError("memory_bandwidth_bytes_per_cycle must be positive")
    if min(sram_read_energy_pj_per_byte, sram_write_energy_pj_per_byte, noc_energy_pj_per_byte_hop) < 0.0:
        raise ValueError("memory energy parameters must be non-negative")
    if noc_hops < 0:
        raise ValueError("noc_hops must be non-negative")

    total_bytes = read_bytes + write_bytes
    service_cycles = math.ceil(total_bytes / memory_bandwidth_bytes_per_cycle)
    memory_bound_cycles = max(compute_cycles, service_cycles)
    sram_energy_pj = (
        read_bytes * sram_read_energy_pj_per_byte
        + write_bytes * sram_write_energy_pj_per_byte
    )
    noc_energy_pj = total_bytes * noc_hops * noc_energy_pj_per_byte_hop
    total_energy_pj = sram_energy_pj + noc_energy_pj
    return {
        "source": "planning_default_not_literature_backed",
        "unit": "bytes_cycles_and_pj",
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
        "total_bytes": total_bytes,
        "bandwidth_bytes_per_cycle": memory_bandwidth_bytes_per_cycle,
        "service_cycles": service_cycles,
        "compute_cycles": compute_cycles,
        "memory_bound_cycles": memory_bound_cycles,
        "is_memory_bound": service_cycles > compute_cycles,
        "memory_bound_latency_us": round(memory_bound_cycles * clock_ns / 1000.0, 6),
        "sram_energy_nj": round(sram_energy_pj / 1000.0, 6),
        "noc_energy_nj": round(noc_energy_pj / 1000.0, 6),
        "total_memory_energy_nj": round(total_energy_pj / 1000.0, 6),
        "noc_hops": noc_hops,
    }


def _streaming_overlap_candidate(
    *,
    measured_points: list[JsonDict],
    candidate_merge_points: list[JsonDict],
    vocab_size: int,
    producer_lanes: int,
    top_k: int,
    producer_latency_cycles: int,
    producer_ii_cycles: int,
    local_ranker_latency_cycles: int,
    local_ranker_ii_cycles: int,
    global_merge_latency_cycles: int,
    global_merge_ii_cycles: int,
    candidate_fifo_depth_groups: int,
    fallback_critical_path_ns: float,
    token_id_bits: int,
    memory_bandwidth_bytes_per_cycle: float,
    sram_read_energy_pj_per_byte: float,
    sram_write_energy_pj_per_byte: float,
    noc_hops: int,
    noc_energy_pj_per_byte_hop: float,
) -> JsonDict:
    local_point = _select_ranker_point(
        measured_points,
        lanes=producer_lanes,
        top_k=top_k,
        default_critical_path_ns=fallback_critical_path_ns,
    )
    merge_lanes = max(producer_lanes, top_k)
    global_point = _select_ranker_point(
        measured_points,
        lanes=merge_lanes,
        top_k=top_k,
        default_critical_path_ns=fallback_critical_path_ns,
    )
    local_clock = _as_float(local_point["metrics"].get("critical_path_ns"), fallback_critical_path_ns)
    global_clock = _as_float(global_point["metrics"].get("critical_path_ns"), fallback_critical_path_ns)
    logit_bits = _as_int(local_point.get("logit_bits"), 16) or 16
    merge_fifo_point = _select_candidate_merge_point(
        candidate_merge_points,
        top_k=top_k,
        logit_bits=logit_bits,
        token_id_bits=token_id_bits,
        fifo_depth_groups=candidate_fifo_depth_groups,
        default_critical_path_ns=global_clock,
    )
    merge_fifo_clock = _as_float(
        merge_fifo_point["metrics"].get("critical_path_ns"), global_clock
    )
    hierarchy_clock_ns = max(local_clock, merge_fifo_clock)
    sim = simulate_streaming_hierarchy(
        vocab_size=vocab_size,
        producer_lanes=producer_lanes,
        producer_latency_cycles=producer_latency_cycles,
        producer_ii_cycles=producer_ii_cycles,
        local_ranker_latency_cycles=local_ranker_latency_cycles,
        local_ranker_ii_cycles=local_ranker_ii_cycles,
        local_top_k=top_k,
        global_merge_latency_cycles=global_merge_latency_cycles,
        global_merge_ii_cycles=global_merge_ii_cycles,
        candidate_fifo_depth_groups=candidate_fifo_depth_groups,
    )
    rank_scan_cycles = local_ranker_latency_cycles + max(0, sim["tile_count"] - 1) * local_ranker_ii_cycles
    buffered_e2e_cycles = sim["producer_last_tile_ready_cycle"] + rank_scan_cycles + global_merge_latency_cycles
    overlap_recovered_cycles = max(0, buffered_e2e_cycles - sim["total_cycles"])
    candidate = {
        "architecture": "hierarchical_streaming_local_rank_global_merge",
        "merge_variant": f"merge_ii_{global_merge_ii_cycles}",
        "sweep_key": (
            f"w{producer_lanes}_k{top_k}_prodii{producer_ii_cycles}_"
            f"mergeii{global_merge_ii_cycles}_fifo{candidate_fifo_depth_groups}"
        ),
        **sim,
        "timing": _time_summary(
            cycles=sim["total_cycles"],
            clock_ns=hierarchy_clock_ns,
            vocab_size=vocab_size,
        ),
        "buffered_baseline": {
            "rank_after_materialization_cycles": buffered_e2e_cycles,
            "streaming_cycles": sim["total_cycles"],
            "overlap_recovered_cycles": overlap_recovered_cycles,
            "overlap_recovered_fraction": (
                round(overlap_recovered_cycles / buffered_e2e_cycles, 6)
                if buffered_e2e_cycles > 0
                else 0.0
            ),
        },
        "traffic": _traffic_summary(
            vocab_size=vocab_size,
            tile_count=sim["tile_count"],
            producer_lanes=producer_lanes,
            top_k=top_k,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        ),
        "local_ranker_point": local_point,
        "global_merge_point": global_point,
        "candidate_merge_fifo_point": merge_fifo_point,
        "component_ppa_metrics": {
            "local_ranker": local_point["metrics"],
            "candidate_merge_fifo": merge_fifo_point["metrics"],
            "global_merge_ranker_proxy": global_point["metrics"],
            "estimated_total_die_area": (
                round(
                    _as_float(local_point["metrics"].get("die_area"))
                    + _as_float(merge_fifo_point["metrics"].get("die_area")),
                    6,
                )
                if local_point["metrics"].get("die_area") is not None
                and merge_fifo_point["metrics"].get("die_area") is not None
                else None
            ),
            "estimated_total_power_mw": (
                round(
                    _as_float(local_point["metrics"].get("total_power_mw"))
                    + _as_float(merge_fifo_point["metrics"].get("total_power_mw")),
                    6,
                )
                if local_point["metrics"].get("total_power_mw") is not None
                and merge_fifo_point["metrics"].get("total_power_mw") is not None
                else None
            ),
            "clock_source": "max(local_ranker, candidate_merge_fifo)",
        },
        "equivalence_contract": {
            "stream_contract": "LogitTileStream/CandidateStream ready-valid v1",
            "ordering": "accepted tile_id order, lower token_id tie-break",
            "perf_sim_observables": [
                "accepted LogitTileStream beat count",
                "accepted CandidateStream group count",
                "producer stall cycles",
                "candidate FIFO max occupancy",
                "final last-beat completion cycle",
            ],
            "rtl_equivalence_requirement": (
                "A future RTL merge block must match the same candidate ordering, "
                "valid masking, backpressure, and last-beat completion observables "
                "before PPA numbers are used in rankings."
            ),
        },
    }
    traffic = candidate["traffic"]
    candidate_payload_bytes = _as_int(traffic.get("candidate_payload_bytes"))
    final_topk_bytes = _as_int(traffic.get("final_topk_bytes"))
    candidate["memory_hierarchy"] = _memory_service_summary(
        read_bytes=candidate_payload_bytes,
        write_bytes=candidate_payload_bytes + final_topk_bytes,
        compute_cycles=sim["total_cycles"],
        clock_ns=hierarchy_clock_ns,
        memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
        sram_read_energy_pj_per_byte=sram_read_energy_pj_per_byte,
        sram_write_energy_pj_per_byte=sram_write_energy_pj_per_byte,
        noc_hops=noc_hops,
        noc_energy_pj_per_byte_hop=noc_energy_pj_per_byte_hop,
    )
    return candidate


def build_report(
    *,
    rank_ppa_path: Path | None = DEFAULT_RANK_PPA,
    scale_ppa_path: Path | None = DEFAULT_SCALE_PPA,
    candidate_merge_ppa_path: Path | None = DEFAULT_CANDIDATE_MERGE_PPA,
    prompt_stress_path: Path | None = None,
    logit_rank_bypass_path: Path | None = None,
    vocab_size: int = 50257,
    producer_lanes: int = 8,
    top_k: int = 4,
    producer_latency_cycles: int = 1,
    producer_ii_cycles: int = 1,
    local_ranker_latency_cycles: int = 4,
    local_ranker_ii_cycles: int = 1,
    global_merge_latency_cycles: int = 3,
    global_merge_ii_cycles_list: list[int] | None = None,
    candidate_fifo_depth_groups: int = 16,
    producer_lanes_list: list[int] | None = None,
    top_k_list: list[int] | None = None,
    producer_ii_cycles_list: list[int] | None = None,
    candidate_fifo_depth_groups_list: list[int] | None = None,
    token_id_bits: int = 16,
    fallback_critical_path_ns: float = 3.6,
    memory_bandwidth_bytes_per_cycle: float = 64.0,
    sram_read_energy_pj_per_byte: float = 0.05,
    sram_write_energy_pj_per_byte: float = 0.07,
    noc_hops: int = 0,
    noc_energy_pj_per_byte_hop: float = 0.02,
) -> JsonDict:
    if vocab_size <= 0:
        raise ValueError("vocab_size must be positive")
    if producer_lanes <= 0:
        raise ValueError("producer_lanes must be positive")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if token_id_bits <= 0:
        raise ValueError("token_id_bits must be positive")
    if memory_bandwidth_bytes_per_cycle <= 0.0:
        raise ValueError("memory_bandwidth_bytes_per_cycle must be positive")
    if noc_hops < 0:
        raise ValueError("noc_hops must be non-negative")
    merge_iis = global_merge_ii_cycles_list or [1, 2, 4]
    lane_options = producer_lanes_list or [producer_lanes]
    top_k_options = top_k_list or [top_k]
    producer_ii_options = producer_ii_cycles_list or [producer_ii_cycles]
    fifo_options = candidate_fifo_depth_groups_list or [candidate_fifo_depth_groups]
    for name, values in (
        ("producer_lanes_list", lane_options),
        ("top_k_list", top_k_options),
        ("producer_ii_cycles_list", producer_ii_options),
        ("candidate_fifo_depth_groups_list", fifo_options),
    ):
        if any(item <= 0 for item in values):
            raise ValueError(f"{name} values must be positive")
    measured_points = load_ranker_points_from_paths([rank_ppa_path, scale_ppa_path])
    candidate_merge_points = load_candidate_merge_points(candidate_merge_ppa_path)
    if not measured_points:
        measured_points = [
            _fallback_ranker_point(
                lanes=producer_lanes, top_k=1, critical_path_ns=fallback_critical_path_ns
            ),
            _fallback_ranker_point(
                lanes=producer_lanes, top_k=top_k, critical_path_ns=fallback_critical_path_ns
            ),
        ]

    flat = [
        _flat_point_report(
            point=point,
            vocab_size=vocab_size,
            ranker_latency_cycles=local_ranker_latency_cycles,
            ranker_ii_cycles=local_ranker_ii_cycles,
        )
        for point in measured_points
        if _as_int(point.get("lanes")) > 0
    ]
    for row in flat:
        logit_bits = _as_int(row.get("metrics", {}).get("logit_bits"), 0)
        if logit_bits <= 0:
            matching_point = next(
                (
                    point
                    for point in measured_points
                    if point.get("metrics_csv") == row.get("metrics_csv")
                ),
                {},
            )
            logit_bits = _as_int(matching_point.get("logit_bits"), 16) or 16
        materialized_logit_bytes = vocab_size * _byte_width(logit_bits)
        row["memory_hierarchy"] = _memory_service_summary(
            read_bytes=materialized_logit_bytes,
            write_bytes=materialized_logit_bytes,
            compute_cycles=row["total_cycles"],
            clock_ns=row["timing"]["clock_ns"],
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            sram_read_energy_pj_per_byte=sram_read_energy_pj_per_byte,
            sram_write_energy_pj_per_byte=sram_write_energy_pj_per_byte,
            noc_hops=noc_hops,
            noc_energy_pj_per_byte_hop=noc_energy_pj_per_byte_hop,
        )

    alternatives: list[JsonDict] = []
    for merge_ii in merge_iis:
        alternatives.append(
            _streaming_overlap_candidate(
                measured_points=measured_points,
                candidate_merge_points=candidate_merge_points,
                vocab_size=vocab_size,
                producer_lanes=producer_lanes,
                top_k=top_k,
                producer_latency_cycles=producer_latency_cycles,
                producer_ii_cycles=producer_ii_cycles,
                local_ranker_latency_cycles=local_ranker_latency_cycles,
                local_ranker_ii_cycles=local_ranker_ii_cycles,
                global_merge_latency_cycles=global_merge_latency_cycles,
                global_merge_ii_cycles=merge_ii,
                candidate_fifo_depth_groups=candidate_fifo_depth_groups,
                fallback_critical_path_ns=fallback_critical_path_ns,
                token_id_bits=token_id_bits,
                memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
                sram_read_energy_pj_per_byte=sram_read_energy_pj_per_byte,
                sram_write_energy_pj_per_byte=sram_write_energy_pj_per_byte,
                noc_hops=noc_hops,
                noc_energy_pj_per_byte_hop=noc_energy_pj_per_byte_hop,
            )
        )

    overlap_sweep: list[JsonDict] = []
    seen_sweep_keys: set[str] = set()
    for lanes in lane_options:
        for local_k in top_k_options:
            for prod_ii in producer_ii_options:
                for merge_ii in merge_iis:
                    for fifo_depth in fifo_options:
                        candidate = _streaming_overlap_candidate(
                            measured_points=measured_points,
                            candidate_merge_points=candidate_merge_points,
                            vocab_size=vocab_size,
                            producer_lanes=lanes,
                            top_k=local_k,
                            producer_latency_cycles=producer_latency_cycles,
                            producer_ii_cycles=prod_ii,
                            local_ranker_latency_cycles=local_ranker_latency_cycles,
                            local_ranker_ii_cycles=local_ranker_ii_cycles,
                            global_merge_latency_cycles=global_merge_latency_cycles,
                            global_merge_ii_cycles=merge_ii,
                            candidate_fifo_depth_groups=fifo_depth,
                            fallback_critical_path_ns=fallback_critical_path_ns,
                            token_id_bits=token_id_bits,
                            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
                            sram_read_energy_pj_per_byte=sram_read_energy_pj_per_byte,
                            sram_write_energy_pj_per_byte=sram_write_energy_pj_per_byte,
                            noc_hops=noc_hops,
                            noc_energy_pj_per_byte_hop=noc_energy_pj_per_byte_hop,
                        )
                        if candidate["sweep_key"] in seen_sweep_keys:
                            continue
                        seen_sweep_keys.add(candidate["sweep_key"])
                        overlap_sweep.append(candidate)

    all_candidates = flat + alternatives
    best = min(
        all_candidates,
        key=lambda row: (
            not bool(row.get("fifo_capacity_ok", True)),
            row["timing"]["latency_us_per_token"],
            str(row["architecture"]),
        ),
    )
    baseline = min(flat, key=lambda row: row["timing"]["latency_us_per_token"]) if flat else None
    for row in alternatives:
        if baseline is None:
            row["speedup_vs_best_flat"] = None
        else:
            row["speedup_vs_best_flat"] = round(
                baseline["timing"]["latency_us_per_token"] / row["timing"]["latency_us_per_token"], 6
            )
    for row in overlap_sweep:
        if baseline is None:
            row["speedup_vs_best_flat"] = None
        else:
            row["speedup_vs_best_flat"] = round(
                baseline["timing"]["latency_us_per_token"] / row["timing"]["latency_us_per_token"], 6
            )
    best_overlap = min(
        overlap_sweep,
        key=lambda row: (
            not bool(row.get("fifo_capacity_ok", True)),
            -row["buffered_baseline"]["overlap_recovered_fraction"],
            row["timing"]["latency_us_per_token"],
            row["traffic"]["streaming_candidate_memory_bytes"],
        ),
    ) if overlap_sweep else None
    best_memory_traffic = min(
        overlap_sweep,
        key=lambda row: (
            not bool(row.get("fifo_capacity_ok", True)),
            row["memory_hierarchy"]["total_bytes"],
            row["memory_hierarchy"]["memory_bound_latency_us"],
            row["timing"]["latency_us_per_token"],
        ),
    ) if overlap_sweep else None

    return {
        "version": 0.1,
        "model": "decoder_logit_rank_streaming_hierarchy_v1",
        "rank_ppa_path": str(rank_ppa_path) if rank_ppa_path is not None else None,
        "rank_ppa_paths": [
            str(path)
            for path in [rank_ppa_path, scale_ppa_path, candidate_merge_ppa_path]
            if path is not None
        ],
        "inputs": {
            "rank_ppa_path": str(rank_ppa_path) if rank_ppa_path is not None else None,
            "scale_ppa_path": str(scale_ppa_path) if scale_ppa_path is not None else None,
            "candidate_merge_ppa_path": (
                str(candidate_merge_ppa_path) if candidate_merge_ppa_path is not None else None
            ),
            "prompt_stress_path": str(prompt_stress_path) if prompt_stress_path is not None else None,
            "logit_rank_bypass_path": str(logit_rank_bypass_path) if logit_rank_bypass_path is not None else None,
            "vocab_size": vocab_size,
            "producer_lanes": producer_lanes,
            "top_k": top_k,
            "producer_latency_cycles": producer_latency_cycles,
            "producer_ii_cycles": producer_ii_cycles,
            "local_ranker_latency_cycles": local_ranker_latency_cycles,
            "local_ranker_ii_cycles": local_ranker_ii_cycles,
            "global_merge_latency_cycles": global_merge_latency_cycles,
            "global_merge_ii_cycles_list": merge_iis,
            "candidate_fifo_depth_groups": candidate_fifo_depth_groups,
            "producer_lanes_list": lane_options,
            "top_k_list": top_k_options,
            "producer_ii_cycles_list": producer_ii_options,
            "candidate_fifo_depth_groups_list": fifo_options,
            "token_id_bits": token_id_bits,
            "fallback_critical_path_ns": fallback_critical_path_ns,
            "memory_bandwidth_bytes_per_cycle": memory_bandwidth_bytes_per_cycle,
            "sram_read_energy_pj_per_byte": sram_read_energy_pj_per_byte,
            "sram_write_energy_pj_per_byte": sram_write_energy_pj_per_byte,
            "noc_hops": noc_hops,
            "noc_energy_pj_per_byte_hop": noc_energy_pj_per_byte_hop,
        },
        "memory_hierarchy_model": {
            "source": "planning_default_not_literature_backed",
            "unit": "bytes_cycles_and_pj",
            "scope": (
                "First-order SRAM/NoC service estimate layered on existing compute cycles. "
                "This is not a measured Nangate45 memory macro or NoC PPA result."
            ),
        },
        "assumptions": [
            "Producer emits one W-lane logit tile after producer latency and then every producer II cycles.",
            "Local ranker accepts one producer tile per local ranker II and emits one candidate group after local ranker latency.",
            "Candidate FIFO depth is reported in local candidate groups; overflow is reported as capacity evidence, not hidden by backpressure.",
            "Global merge consumes one local candidate group per merge II and produces the final token rank after the last merge latency.",
            "Buffered baseline waits for the producer to materialize all logits before rank reduction starts.",
            "Traffic model counts materialized-logit write+read bytes versus candidate FIFO write+read bytes.",
            "Measured row-8 datapath and row-16/row-32 scale critical_path_ns values are used as ranker clock proxies.",
            "Measured candidate-stream merge/FIFO PPA is used for global merge buffering when an exact or nearest-depth point is available.",
            "Memory hierarchy estimates use explicit planning parameters and are reported separately from measured cell PPA.",
            "Missing lane points are explicit defaults or log2-lane scaled proxies.",
            "Perf-sim and future RTL equivalence is defined at accepted ready-valid stream beats, FIFO occupancy, valid masks, last-beat completion, and tie-breaking.",
        ],
        "measured_ranker_points": measured_points,
        "measured_candidate_merge_fifo_points": candidate_merge_points,
        "flat_measured_ranker_points": flat,
        "hierarchical_streaming_alternatives": alternatives,
        "overlap_traffic_sweep": overlap_sweep,
        "recommendation": {
            "architecture": best["architecture"],
            "merge_variant": best.get("merge_variant"),
            "latency_us_per_token": best["timing"]["latency_us_per_token"],
            "tokens_per_s": best["timing"]["tokens_per_s"],
            "fifo_capacity_ok": best.get("fifo_capacity_ok", True),
            "reason": (
                "Lowest modelled latency per token among FIFO-valid measured flat scans and "
                "hierarchical streaming alternatives."
            ),
        },
        "overlap_recommendation": (
            {
                "sweep_key": best_overlap["sweep_key"],
                "latency_us_per_token": best_overlap["timing"]["latency_us_per_token"],
                "tokens_per_s": best_overlap["timing"]["tokens_per_s"],
                "fifo_capacity_ok": best_overlap["fifo_capacity_ok"],
                "overlap_recovered_fraction": best_overlap["buffered_baseline"]["overlap_recovered_fraction"],
                "traffic_reduction_vs_materialized": best_overlap["traffic"]["traffic_reduction_vs_materialized"],
                "reason": (
                    "Best FIFO-valid overlap candidate by recovered buffered-baseline cycles, "
                    "then latency and candidate memory traffic."
                ),
            }
            if best_overlap is not None
            else None
        ),
        "memory_traffic_recommendation": (
            {
                "sweep_key": best_memory_traffic["sweep_key"],
                "latency_us_per_token": best_memory_traffic["timing"]["latency_us_per_token"],
                "memory_bound_latency_us": best_memory_traffic["memory_hierarchy"]["memory_bound_latency_us"],
                "memory_total_bytes": best_memory_traffic["memory_hierarchy"]["total_bytes"],
                "total_memory_energy_nj": best_memory_traffic["memory_hierarchy"]["total_memory_energy_nj"],
                "traffic_reduction_vs_materialized": best_memory_traffic["traffic"]["traffic_reduction_vs_materialized"],
                "fifo_capacity_ok": best_memory_traffic["fifo_capacity_ok"],
                "reason": (
                    "Best FIFO-valid streaming candidate by modeled memory bytes, then "
                    "memory-bound latency and compute latency."
                ),
            }
            if best_memory_traffic is not None
            else None
        ),
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    overlap = payload.get("overlap_recommendation") or {}
    memory = payload.get("memory_traffic_recommendation") or {}
    lines = [
        "# Decoder Logit-Rank Streaming Hierarchy",
        "",
        f"- model: `{payload['model']}`",
        f"- rank_ppa_paths: `{', '.join(payload.get('rank_ppa_paths') or [])}`",
        f"- recommendation: `{rec['architecture']}`",
        f"- merge_variant: `{rec['merge_variant'] or ''}`",
        f"- latency_us_per_token: `{rec['latency_us_per_token']}`",
        f"- tokens_per_s: `{rec['tokens_per_s']}`",
        f"- fifo_capacity_ok: `{rec['fifo_capacity_ok']}`",
        f"- reason: {rec['reason']}",
        f"- overlap_sweep_best: `{overlap.get('sweep_key', '')}`",
        f"- overlap_recovered_fraction: `{overlap.get('overlap_recovered_fraction', '')}`",
        f"- traffic_reduction_vs_materialized: `{overlap.get('traffic_reduction_vs_materialized', '')}`",
        f"- memory_traffic_best: `{memory.get('sweep_key', '')}`",
        f"- memory_total_bytes: `{memory.get('memory_total_bytes', '')}`",
        f"- memory_bound_latency_us: `{memory.get('memory_bound_latency_us', '')}`",
        "",
        "## Inputs",
        "",
        "| input | value |",
        "|---|---:|",
    ]
    for key, value in payload["inputs"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Flat Measured Ranker Points",
            "",
            "| lanes | top_k | cycles | latency_us | memory_bytes | memory_bound_us | tokens_per_s | critical_path_ns | source |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["flat_measured_ranker_points"]:
        mem = row.get("memory_hierarchy") or {}
        lines.append(
            "| {lanes} | {topk} | {cycles} | {latency} | {mem_bytes} | {mem_lat} | {tps} | {cp} | `{source}` |".format(
                lanes=row["lanes"],
                topk=row["top_k"],
                cycles=row["total_cycles"],
                latency=row["timing"]["latency_us_per_token"],
                mem_bytes=mem.get("total_bytes"),
                mem_lat=mem.get("memory_bound_latency_us"),
                tps=row["timing"]["tokens_per_s"],
                cp=row["timing"]["clock_ns"],
                source=row.get("metrics_csv") or row.get("source") or "",
            )
        )
    lines.extend(
        [
            "",
            "## Hierarchical Streaming Alternatives",
            "",
            "| variant | W | top_k | cycles | latency_us | memory_bytes | memory_bound_us | tokens_per_s | merge_fifo_cp_ns | est_area | fifo required/capacity | fifo ok | speedup vs flat |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        ]
    )
    for row in payload["hierarchical_streaming_alternatives"]:
        component_ppa = row.get("component_ppa_metrics") or {}
        merge_fifo = row.get("candidate_merge_fifo_point") or {}
        merge_metrics = merge_fifo.get("metrics") or {}
        mem = row.get("memory_hierarchy") or {}
        lines.append(
            "| `{variant}` | {lanes} | {topk} | {cycles} | {latency} | {mem_bytes} | {mem_lat} | {tps} | {merge_cp} | {area} | {fifo}/{cap} | `{ok}` | {speedup} |".format(
                variant=row["merge_variant"],
                lanes=row["producer_lanes"],
                topk=row["local_top_k"],
                cycles=row["total_cycles"],
                latency=row["timing"]["latency_us_per_token"],
                mem_bytes=mem.get("total_bytes"),
                mem_lat=mem.get("memory_bound_latency_us"),
                tps=row["timing"]["tokens_per_s"],
                merge_cp=merge_metrics.get("critical_path_ns"),
                area=component_ppa.get("estimated_total_die_area"),
                fifo=row["required_fifo_depth_groups"],
                cap=row["candidate_fifo_depth_groups"],
                ok=row["fifo_capacity_ok"],
                speedup=row["speedup_vs_best_flat"],
            )
        )
    lines.extend(
        [
            "",
            "## Overlap And Traffic Sweep",
            "",
            "| key | cycles | latency_us | memory_bytes | memory_energy_nj | fifo required/capacity | overlap recovered | traffic reduction | speedup vs flat |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["overlap_traffic_sweep"][:24]:
        mem = row.get("memory_hierarchy") or {}
        lines.append(
            "| `{key}` | {cycles} | {latency} | {mem_bytes} | {mem_energy} | {fifo}/{cap} | {overlap} | {traffic} | {speedup} |".format(
                key=row["sweep_key"],
                cycles=row["total_cycles"],
                latency=row["timing"]["latency_us_per_token"],
                mem_bytes=mem.get("total_bytes"),
                mem_energy=mem.get("total_memory_energy_nj"),
                fifo=row["required_fifo_depth_groups"],
                cap=row["candidate_fifo_depth_groups"],
                overlap=row["buffered_baseline"]["overlap_recovered_fraction"],
                traffic=row["traffic"]["traffic_reduction_vs_materialized"],
                speedup=row["speedup_vs_best_flat"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _int_list(value: str) -> list[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integer list")
    parsed = [int(item) for item in items]
    if any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def main() -> int:
    ap = argparse.ArgumentParser(description="Model decoder logit-rank streaming hierarchy")
    ap.add_argument("--prompt-stress", help="prompt-stress evidence JSON path")
    ap.add_argument("--logit-rank-bypass", help="logit-rank bypass evidence JSON path")
    ap.add_argument("--rank-ppa", default=str(DEFAULT_RANK_PPA), help="rank datapath PPA JSON")
    ap.add_argument("--scale-ppa", default=str(DEFAULT_SCALE_PPA), help="rank scale PPA JSON")
    ap.add_argument(
        "--candidate-merge-ppa",
        default=str(DEFAULT_CANDIDATE_MERGE_PPA),
        help="candidate-stream merge/FIFO PPA JSON",
    )
    ap.add_argument("--vocab-size", type=int, default=50257, help="decoder vocabulary size")
    ap.add_argument("--producer-lanes", type=int, default=8, help="W-lane producer tile width")
    ap.add_argument("--top-k", type=int, default=4, help="local candidates per tile")
    ap.add_argument("--producer-latency-cycles", type=int, default=1)
    ap.add_argument("--producer-ii-cycles", type=int, default=1)
    ap.add_argument("--local-ranker-latency-cycles", type=int, default=4)
    ap.add_argument("--local-ranker-ii-cycles", type=int, default=1)
    ap.add_argument("--global-merge-latency-cycles", type=int, default=3)
    ap.add_argument("--global-merge-ii-cycles", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--candidate-fifo-depth-groups", type=int, default=16)
    ap.add_argument("--producer-lanes-list", type=_int_list, help="comma-separated producer lane sweep")
    ap.add_argument("--top-k-list", type=_int_list, help="comma-separated local top-k sweep")
    ap.add_argument("--producer-ii-cycles-list", type=_int_list, help="comma-separated producer II sweep")
    ap.add_argument("--candidate-fifo-depth-groups-list", type=_int_list, help="comma-separated FIFO depth sweep")
    ap.add_argument("--token-id-bits", type=int, default=16)
    ap.add_argument("--fallback-critical-path-ns", type=float, default=3.6)
    ap.add_argument("--memory-bandwidth-bytes-per-cycle", type=float, default=64.0)
    ap.add_argument("--sram-read-energy-pj-per-byte", type=float, default=0.05)
    ap.add_argument("--sram-write-energy-pj-per-byte", type=float, default=0.07)
    ap.add_argument("--noc-hops", type=int, default=0)
    ap.add_argument("--noc-energy-pj-per-byte-hop", type=float, default=0.02)
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--out-md", required=True, help="output Markdown path")
    args = ap.parse_args()

    payload = build_report(
        rank_ppa_path=Path(args.rank_ppa) if args.rank_ppa else None,
        scale_ppa_path=Path(args.scale_ppa) if args.scale_ppa else None,
        candidate_merge_ppa_path=Path(args.candidate_merge_ppa) if args.candidate_merge_ppa else None,
        prompt_stress_path=Path(args.prompt_stress) if args.prompt_stress else None,
        logit_rank_bypass_path=Path(args.logit_rank_bypass) if args.logit_rank_bypass else None,
        vocab_size=args.vocab_size,
        producer_lanes=args.producer_lanes,
        top_k=args.top_k,
        producer_latency_cycles=args.producer_latency_cycles,
        producer_ii_cycles=args.producer_ii_cycles,
        local_ranker_latency_cycles=args.local_ranker_latency_cycles,
        local_ranker_ii_cycles=args.local_ranker_ii_cycles,
        global_merge_latency_cycles=args.global_merge_latency_cycles,
        global_merge_ii_cycles_list=args.global_merge_ii_cycles,
        candidate_fifo_depth_groups=args.candidate_fifo_depth_groups,
        producer_lanes_list=args.producer_lanes_list,
        top_k_list=args.top_k_list,
        producer_ii_cycles_list=args.producer_ii_cycles_list,
        candidate_fifo_depth_groups_list=args.candidate_fifo_depth_groups_list,
        token_id_bits=args.token_id_bits,
        fallback_critical_path_ns=args.fallback_critical_path_ns,
        memory_bandwidth_bytes_per_cycle=args.memory_bandwidth_bytes_per_cycle,
        sram_read_energy_pj_per_byte=args.sram_read_energy_pj_per_byte,
        sram_write_energy_pj_per_byte=args.sram_write_energy_pj_per_byte,
        noc_hops=args.noc_hops,
        noc_energy_pj_per_byte_hop=args.noc_energy_pj_per_byte_hop,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(
        json.dumps(
            {
                "ok": True,
                "out": str(out),
                "out_md": str(out_md),
                "recommendation": payload["recommendation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
