#!/usr/bin/env python3
"""Audit the score32 schedule-wrapper cadence point against exact hierarchy evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree_c16 import generate as generate_exact_c16
from npu.sim.perf.attention_online import ROW_ELEMS

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_hierarchy_cadence_audit_v1"
_DECISION = "score32_schedule_wrapper_cadence_arithmetically_reproducible_but_exact_hierarchy_unclosed"
_EXPECTED_SOURCE_ITEM_ID = "l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1"
_EXPECTED_WRAPPER_TOP = "attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2"
_EXPECTED_EXACT_TOP = "attention_score32_exact_partial_producer_tree_c16_r2_l8_b59"
_EXPECTED_SEQUENCE_LENGTH = 131072
_EXPECTED_TILE_TOKENS = 1024
_EXPECTED_TILE_COUNT = 128
_EXPECTED_ACTIVE_GLOBAL_CLUSTERS = 16
_EXPECTED_TILE_WAVES = 8
_EXPECTED_WRAPPER_COUNT = 428
_EXPECTED_WRAPPER_CLUSTER_DATAPATHS = 856
_EXPECTED_WRAPPER_CLUSTER_MACS = 128
_EXPECTED_WRAPPER_TOTAL_MACS = 256
_EXPECTED_FRONTIER_MACS = 109568
_EXPECTED_PER_CLUSTER_FLOOR = 53
_EXPECTED_PER_CLUSTER_CEIL = 54
_EXPECTED_CONSERVATIVE_CLUSTER_MACS = 6784
_EXPECTED_TILE_WORK_MACS = 4194304
_EXPECTED_TILE_STAGE_CYCLES = 619
_EXPECTED_TILE_STATS_CYCLES = 116
_EXPECTED_SUBTILE_COUNT = 8
_EXPECTED_SUBTILE_QK = 78
_EXPECTED_SUBTILE_VALUE = 78
_EXPECTED_SUBTILE_STATS = 15
_EXPECTED_SUBTILE_HBM = 163
_EXPECTED_SUBTILE_AUX = 86
_EXPECTED_PREFETCH_DISTANCE = 3
_EXPECTED_PIPELINE_CYCLES = 986
_EXPECTED_QKV_CYCLES = 192
_EXPECTED_KV_WRITE_CYCLES = 10
_EXPECTED_CROSS_TILE_REDUCTION_CYCLES = 141
_EXPECTED_LAYERS = 32
_EXPECTED_TOTAL_CYCLES = 263392
_EXPECTED_CLOCK_NS = 48.6509
_EXPECTED_SUPPORTED_MIN_MAX_BLOCKS = 8
_EXPECTED_STREAMS_PER_FUNCTIONAL_PRODUCER = 2
_EXPECTED_STREAMS_PER_53_DATAPATH_CLUSTER = 106
_EXPECTED_STREAMS_PER_54_DATAPATH_CLUSTER = 108
_EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_53 = 22
_EXPECTED_STREAMS_WITH_1_BLOCK_FOR_53 = 84
_EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_54 = 20
_EXPECTED_STREAMS_WITH_1_BLOCK_FOR_54 = 88
_EXPECTED_MAX_BLOCKS_PER_STREAM_PER_WAVE = 2
_EXPECTED_STRUCTURAL_STIMULUS_NOTE = (
    "local datapath stimulus is deterministic PPA/equivalence stimulus, not full token data replay"
)
_EXPECTED_PPA_GUARD_NOTE = (
    "PPA mode exposes softmax weights, value accumulators, and score mixes directly; equivalence hash disabled"
)
_EXPECTED_CONTROL_NOTE = "control\": \"start/done, seed LFSR, per-stream buffer registers\""
_EXPECTED_MAX_BLOCKS_RANGE_NOTE = "max_blocks must be a power of two in [8, 16384]"


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"expected at least one CSV row: {path}")
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must be {expected!r}, got {actual!r}")


def _require_contains(text: str, token: str, label: str) -> None:
    if token not in text:
        raise ValueError(f"{label} missing token: {token}")


def _as_int(value: Any, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    return parsed


def _as_float(value: Any, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{label} must be finite")
    return parsed


def _find_wrapper_metric_row(rows: list[dict[str, str]], expected_top_name: str) -> tuple[int, dict[str, str]]:
    matching = [(index, row) for index, row in enumerate(rows) if row.get("design") == expected_top_name]
    if not matching:
        raise ValueError(f"wrapper metrics CSV has no design={expected_top_name}")
    matching.sort(key=lambda item: (_as_float(item[1].get("critical_path_ns"), "wrapper metrics critical_path_ns"), item[0]))
    return matching[0]


def _validate_wrapper_config(payload: JsonDict) -> JsonDict:
    _require_equal(payload.get("top_name"), _EXPECTED_WRAPPER_TOP, "wrapper config top_name")
    body = payload.get("attention_dual_stream_schedule_wrapper")
    if not isinstance(body, dict):
        raise ValueError("wrapper config missing attention_dual_stream_schedule_wrapper")
    datapath = body.get("datapath")
    if not isinstance(datapath, dict):
        raise ValueError("wrapper config missing datapath")
    _require_equal(int(body.get("clusters", 0)), 2, "wrapper config clusters")
    _require_equal(int(datapath.get("streams", 0)), 2, "wrapper datapath streams")
    _require_equal(int(datapath.get("array_m", 0)), 8, "wrapper datapath array_m")
    _require_equal(int(datapath.get("array_n", 0)), 8, "wrapper datapath array_n")
    _require_equal(int(datapath.get("k_unroll", 0)), 1, "wrapper datapath k_unroll")
    wrapper_cluster_macs = int(datapath["streams"]) * int(datapath["array_m"]) * int(datapath["array_n"]) * int(datapath["k_unroll"])
    wrapper_total_macs = int(body["clusters"]) * wrapper_cluster_macs
    _require_equal(wrapper_cluster_macs, _EXPECTED_WRAPPER_CLUSTER_MACS, "wrapper cluster datapath MACs/cycle")
    _require_equal(wrapper_total_macs, _EXPECTED_WRAPPER_TOTAL_MACS, "wrapper total MACs/cycle")
    return {
        "clusters": int(body["clusters"]),
        "streams": int(datapath["streams"]),
        "array_m": int(datapath["array_m"]),
        "array_n": int(datapath["array_n"]),
        "k_unroll": int(datapath["k_unroll"]),
        "wrapper_cluster_macs_per_cycle": wrapper_cluster_macs,
        "wrapper_total_macs_per_cycle": wrapper_total_macs,
        "semantic_profile": str(datapath.get("semantic_profile")),
    }


def _validate_source_recost(payload: JsonDict, *, wrapper_metrics_path: Path, wrapper_config: JsonDict) -> JsonDict:
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict):
        raise ValueError("source recost JSON missing diagnosis")
    _require_equal(diagnosis.get("decision"), "dual_stream_feasible", "source diagnosis.decision")
    best = payload.get("best_requested")
    if not isinstance(best, dict):
        raise ValueError("source recost JSON missing best_requested")
    _require_equal(best.get("sequence_length"), _EXPECTED_SEQUENCE_LENGTH, "source sequence_length")
    _require_equal(best.get("tile_tokens"), _EXPECTED_TILE_TOKENS, "source tile_tokens")
    _require_equal(best.get("tile_count"), _EXPECTED_TILE_COUNT, "source tile_count")
    _require_equal(best.get("active_clusters"), _EXPECTED_ACTIVE_GLOBAL_CLUSTERS, "source active_clusters")
    _require_equal(best.get("tile_waves"), _EXPECTED_TILE_WAVES, "source tile_waves")
    _require_equal(best.get("replica_recost_area_fit_replica_count"), _EXPECTED_WRAPPER_COUNT, "source wrapper count")
    _require_equal(best.get("replica_recost_macs_per_cycle"), _EXPECTED_FRONTIER_MACS, "source replica_recost_macs_per_cycle")
    _require_equal(best.get("measured_dual_stream_composed_precision_profile"), _EXPECTED_WRAPPER_TOP, "source measured wrapper top")
    _require_equal(
        best.get("measured_dual_stream_composed_metrics_csv"),
        _portable_path(wrapper_metrics_path),
        "source measured wrapper metrics path",
    )
    _require_equal(best.get("compute_mode"), "dual_mac", "source compute_mode")
    _require_equal(best.get("tile_qk_cycles"), _EXPECTED_TILE_STAGE_CYCLES, "source tile_qk_cycles")
    _require_equal(best.get("tile_value_cycles"), _EXPECTED_TILE_STAGE_CYCLES, "source tile_value_cycles")
    _require_equal(best.get("tile_stats_cycles"), _EXPECTED_TILE_STATS_CYCLES, "source tile_stats_cycles")
    _require_equal(best.get("pipeline_attention_cycles"), _EXPECTED_PIPELINE_CYCLES, "source pipeline_attention_cycles")
    _require_equal(best.get("tile_service_cycles"), _EXPECTED_PIPELINE_CYCLES, "source tile_service_cycles")
    _require_equal(best.get("qkv_cycles"), _EXPECTED_QKV_CYCLES, "source qkv_cycles")
    _require_equal(best.get("cross_tile_reduction_cycles"), _EXPECTED_CROSS_TILE_REDUCTION_CYCLES, "source cross_tile_reduction_cycles")
    _require_equal(best.get("kv_write_cycles"), _EXPECTED_KV_WRITE_CYCLES, "source kv_write_cycles")
    _require_equal(best.get("layers"), _EXPECTED_LAYERS, "source layers")
    _require_equal(best.get("total_cycles"), _EXPECTED_TOTAL_CYCLES, "source total_cycles")
    _require_equal(round(_as_float(best.get("measured_dual_stream_composed_clock_ns"), "source wrapper clock_ns"), 4), _EXPECTED_CLOCK_NS, "source measured wrapper clock_ns")
    _require_equal(round(_as_float(best.get("measured_dual_stream_composed_power_mw"), "source wrapper power_mw"), 1), 60.7, "source measured wrapper power_mw")
    _require_equal(best.get("subtile_pipeline_json"), None, "source best_requested subtile_pipeline_json")
    _require_equal(best.get("measured_dual_stream_composed_semantic_profile"), wrapper_config["semantic_profile"], "source wrapper semantic_profile")
    return best


def _reconstruct_pipeline_schedule(*, subtile_count: int, qk_sub: int, stats_sub: int, value_sub: int, hbm_sub: int, aux_sub: int, prefetch_distance: int) -> JsonDict:
    qk_free = 0
    stats_free = 0
    value_free = 0
    trace: list[JsonDict] = []
    hbm_end: list[int] = []
    for index in range(subtile_count):
        hbm_ready = max(0, index + 1 - prefetch_distance) * hbm_sub
        qk_start = max(qk_free, hbm_ready, index * aux_sub)
        qk_done = qk_start + qk_sub
        stats_start = max(stats_free, qk_done)
        stats_done = stats_start + stats_sub
        value_start = max(value_free, stats_done, hbm_ready)
        value_done = value_start + value_sub
        qk_free = qk_done
        stats_free = stats_done
        value_free = value_done
        hbm_end.append(hbm_ready)
        trace.append(
            {
                "subtile": index,
                "hbm_ready_cycle": hbm_ready,
                "aux_release_cycle": index * aux_sub,
                "qk_start_cycle": qk_start,
                "qk_done_cycle": qk_done,
                "stats_start_cycle": stats_start,
                "stats_done_cycle": stats_done,
                "value_start_cycle": value_start,
                "value_done_cycle": value_done,
            }
        )
    pipeline_cycles = max(value_free, hbm_end[-1], subtile_count * aux_sub)
    return {
        "trace": trace,
        "hbm_exposed_cycles": hbm_end[-1],
        "aux_memory_span_cycles": subtile_count * aux_sub,
        "pipeline_cycles": pipeline_cycles,
    }


def _generate_exact_c16_manifest(config_payload: JsonDict) -> JsonDict:
    with tempfile.TemporaryDirectory(prefix="score32_exact_hierarchy_c16_") as temp_dir_name:
        out_dir = Path(temp_dir_name)
        generate_exact_c16(config_payload, out_dir)
        return _load_json(out_dir / "attention_score32_exact_partial_producer_tree_c16_manifest.json")


def _build_report(args: argparse.Namespace) -> JsonDict:
    source_recost_path = Path(args.source_recost_json).resolve()
    wrapper_config_path = Path(args.wrapper_config).resolve()
    wrapper_metrics_path = Path(args.wrapper_metrics).resolve()
    exact_c16_config_path = Path(args.exact_c16_config).resolve()
    subtile_generator_path = Path(args.subtile_pipeline_generator).resolve()
    schedule_wrapper_generator_path = Path(args.schedule_wrapper_generator).resolve()
    composed_generator_path = Path(args.composed_generator).resolve()
    exact_c16_generator_path = Path(args.exact_c16_generator).resolve()
    producer_cluster_generator_path = Path(args.producer_cluster_generator).resolve()
    attention_online_path = Path(args.attention_online_source).resolve()

    source_recost = _load_json(source_recost_path)
    wrapper_config_payload = _load_json(wrapper_config_path)
    wrapper_metrics_rows = _load_csv_rows(wrapper_metrics_path)
    exact_c16_config_payload = _load_json(exact_c16_config_path)

    wrapper_contract = _validate_wrapper_config(wrapper_config_payload)
    source_best = _validate_source_recost(
        source_recost,
        wrapper_metrics_path=wrapper_metrics_path,
        wrapper_config=wrapper_contract,
    )

    subtile_pipeline_path = REPO_ROOT / str(source_recost.get("subtile_pipeline_json", "")).strip()
    if not subtile_pipeline_path.is_file():
        raise ValueError("source recost JSON points to a missing subtile_pipeline_json")
    subtile_pipeline = _load_json(subtile_pipeline_path)
    subtile_best = subtile_pipeline.get("best")
    if not isinstance(subtile_best, dict):
        raise ValueError("subtile pipeline JSON missing best row")
    _require_equal(subtile_best.get("sequence_length"), _EXPECTED_SEQUENCE_LENGTH, "subtile best sequence_length")
    _require_equal(subtile_best.get("tile_tokens"), _EXPECTED_TILE_TOKENS, "subtile best tile_tokens")
    _require_equal(subtile_best.get("tile_count"), _EXPECTED_TILE_COUNT, "subtile best tile_count")
    _require_equal(subtile_best.get("tile_waves"), _EXPECTED_TILE_WAVES, "subtile best tile_waves")
    _require_equal(subtile_best.get("compute_mode"), "dual_mac", "subtile best compute_mode")
    _require_equal(subtile_best.get("normalize_strategy"), "online_correction", "subtile best normalize_strategy")
    _require_equal(subtile_best.get("subtile_count"), _EXPECTED_SUBTILE_COUNT, "subtile best subtile_count")
    _require_equal(subtile_best.get("prefetch_distance"), _EXPECTED_PREFETCH_DISTANCE, "subtile best prefetch_distance")
    _require_equal(subtile_best.get("subtile_qk_cycles"), _EXPECTED_SUBTILE_QK, "subtile best subtile_qk_cycles")
    _require_equal(subtile_best.get("subtile_value_cycles"), _EXPECTED_SUBTILE_VALUE, "subtile best subtile_value_cycles")
    _require_equal(subtile_best.get("subtile_stats_cycles"), _EXPECTED_SUBTILE_STATS, "subtile best subtile_stats_cycles")
    _require_equal(subtile_best.get("subtile_hbm_cycles"), _EXPECTED_SUBTILE_HBM, "subtile best subtile_hbm_cycles")
    _require_equal(subtile_best.get("subtile_aux_memory_cycles"), _EXPECTED_SUBTILE_AUX, "subtile best subtile_aux_memory_cycles")
    _require_equal(subtile_best.get("pipeline_attention_cycles"), _EXPECTED_PIPELINE_CYCLES, "subtile best pipeline_attention_cycles")
    _require_equal(subtile_best.get("pipeline_residual_memory_cycles"), 688, "subtile best pipeline_residual_memory_cycles")
    _require_equal(subtile_best.get("hbm_exposed_cycles"), 815, "subtile best hbm_exposed_cycles")
    _require_equal(subtile_best.get("tile_service_cycles"), _EXPECTED_PIPELINE_CYCLES, "subtile best tile_service_cycles")

    wrapper_metric_row_index, wrapper_metric_row = _find_wrapper_metric_row(wrapper_metrics_rows, _EXPECTED_WRAPPER_TOP)
    wrapper_best_clock_ns = round(_as_float(wrapper_metric_row.get("critical_path_ns"), "wrapper metrics critical_path_ns"), 4)
    wrapper_best_power_mw = round(_as_float(wrapper_metric_row.get("total_power_mw"), "wrapper metrics total_power_mw"), 1)
    wrapper_best_area_um2 = round(_as_float(wrapper_metric_row.get("stdcell_area_um2"), "wrapper metrics stdcell_area_um2"), 1)
    _require_equal(wrapper_best_clock_ns, _EXPECTED_CLOCK_NS, "wrapper metrics best critical_path_ns")
    _require_equal(wrapper_best_power_mw, 60.7, "wrapper metrics best total_power_mw")
    _require_equal(wrapper_best_area_um2, 693452.0, "wrapper metrics best stdcell_area_um2")
    _require_equal(int(source_best.get("measured_dual_stream_composed_required_replicas", 0)), _EXPECTED_WRAPPER_COUNT, "source measured wrapper replica count")
    _require_equal(int(source_best.get("measured_block_macs_per_cycle", 0)), _EXPECTED_WRAPPER_CLUSTER_MACS, "source measured block MACs/cycle")

    tile_count = math.ceil(_EXPECTED_SEQUENCE_LENGTH / _EXPECTED_TILE_TOKENS)
    tile_waves = math.ceil(tile_count / _EXPECTED_ACTIVE_GLOBAL_CLUSTERS)
    _require_equal(tile_count, _EXPECTED_TILE_COUNT, "derived tile_count")
    _require_equal(tile_waves, _EXPECTED_TILE_WAVES, "derived tile_waves")

    wrapper_cluster_datapaths = _EXPECTED_WRAPPER_COUNT * wrapper_contract["clusters"]
    frontier_macs = _EXPECTED_WRAPPER_COUNT * wrapper_contract["wrapper_total_macs_per_cycle"]
    _require_equal(wrapper_cluster_datapaths, _EXPECTED_WRAPPER_CLUSTER_DATAPATHS, "derived wrapper cluster datapaths")
    _require_equal(frontier_macs, _EXPECTED_FRONTIER_MACS, "derived frontier MACs/cycle")

    replicas_per_cluster_floor = wrapper_cluster_datapaths // _EXPECTED_ACTIVE_GLOBAL_CLUSTERS
    replicas_per_cluster_remainder = wrapper_cluster_datapaths % _EXPECTED_ACTIVE_GLOBAL_CLUSTERS
    replicas_per_cluster_ceil = math.ceil(wrapper_cluster_datapaths / _EXPECTED_ACTIVE_GLOBAL_CLUSTERS)
    _require_equal(replicas_per_cluster_floor, _EXPECTED_PER_CLUSTER_FLOOR, "derived replicas_per_cluster_floor")
    _require_equal(replicas_per_cluster_ceil, _EXPECTED_PER_CLUSTER_CEIL, "derived replicas_per_cluster_ceil")
    _require_equal(replicas_per_cluster_remainder, 8, "derived replicas_per_cluster_remainder")
    conservative_per_cluster_macs = replicas_per_cluster_floor * wrapper_contract["wrapper_cluster_macs_per_cycle"]
    _require_equal(conservative_per_cluster_macs, _EXPECTED_CONSERVATIVE_CLUSTER_MACS, "derived conservative per-cluster MACs/cycle")
    _require_equal(int(subtile_best.get("per_cluster_macs_per_cycle", 0)), _EXPECTED_CONSERVATIVE_CLUSTER_MACS, "subtile best per_cluster_macs_per_cycle")

    tile_work_macs = _EXPECTED_TILE_TOKENS * int(source_best["hidden_size"])
    _require_equal(tile_work_macs, _EXPECTED_TILE_WORK_MACS, "derived tile work MACs")
    tile_qk_cycles = math.ceil(tile_work_macs / conservative_per_cluster_macs)
    tile_value_cycles = math.ceil(tile_work_macs / conservative_per_cluster_macs)
    _require_equal(tile_qk_cycles, _EXPECTED_TILE_STAGE_CYCLES, "derived tile_qk_cycles")
    _require_equal(tile_value_cycles, _EXPECTED_TILE_STAGE_CYCLES, "derived tile_value_cycles")
    _require_equal(int(subtile_best.get("tile_qk_cycles", 0)), _EXPECTED_TILE_STAGE_CYCLES, "subtile best tile_qk_cycles")
    _require_equal(int(subtile_best.get("tile_value_cycles", 0)), _EXPECTED_TILE_STAGE_CYCLES, "subtile best tile_value_cycles")

    tile_stats_cycles = math.ceil((3 * int(source_best["attention_heads"]) * _EXPECTED_TILE_TOKENS) / int(subtile_best["per_cluster_vector_ops_per_cycle"]))
    _require_equal(tile_stats_cycles, _EXPECTED_TILE_STATS_CYCLES, "derived tile_stats_cycles")
    _require_equal(int(subtile_best.get("tile_stats_cycles", 0)), _EXPECTED_TILE_STATS_CYCLES, "subtile best tile_stats_cycles")

    qk_sub = math.ceil(tile_qk_cycles / _EXPECTED_SUBTILE_COUNT)
    value_sub = math.ceil(tile_value_cycles / _EXPECTED_SUBTILE_COUNT)
    stats_sub = math.ceil(tile_stats_cycles / _EXPECTED_SUBTILE_COUNT)
    hbm_sub = math.ceil(int(subtile_best["tile_hbm_cycles"]) / _EXPECTED_SUBTILE_COUNT)
    aux_sub = max(
        math.ceil(int(subtile_best["tile_local_sram_cycles"]) / _EXPECTED_SUBTILE_COUNT),
        math.ceil(int(subtile_best["tile_shared_path_cycles"]) / _EXPECTED_SUBTILE_COUNT),
    )
    _require_equal(qk_sub, _EXPECTED_SUBTILE_QK, "derived subtile_qk_cycles")
    _require_equal(value_sub, _EXPECTED_SUBTILE_VALUE, "derived subtile_value_cycles")
    _require_equal(stats_sub, _EXPECTED_SUBTILE_STATS, "derived subtile_stats_cycles")
    _require_equal(hbm_sub, _EXPECTED_SUBTILE_HBM, "derived subtile_hbm_cycles")
    _require_equal(aux_sub, _EXPECTED_SUBTILE_AUX, "derived subtile_aux_memory_cycles")

    schedule = _reconstruct_pipeline_schedule(
        subtile_count=_EXPECTED_SUBTILE_COUNT,
        qk_sub=qk_sub,
        stats_sub=stats_sub,
        value_sub=value_sub,
        hbm_sub=hbm_sub,
        aux_sub=aux_sub,
        prefetch_distance=_EXPECTED_PREFETCH_DISTANCE,
    )
    _require_equal(schedule["pipeline_cycles"], _EXPECTED_PIPELINE_CYCLES, "reconstructed pipeline cycles")
    _require_equal(schedule["hbm_exposed_cycles"], 815, "reconstructed hbm_exposed_cycles")
    _require_equal(schedule["aux_memory_span_cycles"], 688, "reconstructed aux_memory_span_cycles")

    exact_manifest = _generate_exact_c16_manifest(exact_c16_config_payload)
    _require_equal(exact_manifest.get("top_name"), _EXPECTED_EXACT_TOP, "exact c16 manifest top_name")
    _require_equal(exact_manifest.get("max_blocks"), 16, "exact c16 manifest max_blocks")
    _require_equal(exact_manifest.get("producers"), 16, "exact c16 manifest producers")
    _require_equal(exact_manifest.get("clusters"), 16, "exact c16 manifest clusters")
    _require_equal(exact_manifest.get("producer_result_mode"), "exact_partial", "exact c16 manifest producer_result_mode")
    producer_manifest = exact_manifest.get("submodule_manifests", {}).get("producer")
    if not isinstance(producer_manifest, dict):
        raise ValueError("exact c16 manifest missing producer submodule manifest")
    score_tile_manifest = producer_manifest.get("submodule_manifests", {}).get("score_tile")
    reducer_manifest = producer_manifest.get("submodule_manifests", {}).get("multivalue_reducer")
    if not isinstance(score_tile_manifest, dict) or not isinstance(reducer_manifest, dict):
        raise ValueError("producer manifest missing score_tile or multivalue_reducer manifest")
    _require_equal(score_tile_manifest.get("array_m"), 1, "exact producer score_tile array_m")
    _require_equal(score_tile_manifest.get("array_n"), 8, "exact producer score_tile array_n")
    _require_equal(producer_manifest.get("semantic_profile"), "decode_m1x8_shared_score_16x8d_value_exact_partial_v1", "exact producer semantic_profile")
    _require_equal(reducer_manifest.get("max_blocks"), 16, "exact producer reducer max_blocks")
    _require_equal(reducer_manifest.get("max_context_tokens"), 128, "exact producer reducer max_context_tokens")
    _require_equal(int(ROW_ELEMS), 8, "attention_online ROW_ELEMS")

    exact_slice_macs = int(exact_manifest["producers"]) * int(score_tile_manifest["array_m"]) * int(score_tile_manifest["array_n"])
    _require_equal(exact_slice_macs, 128, "exact c16 slice MACs/cycle")
    _require_equal(frontier_macs // exact_slice_macs, _EXPECTED_WRAPPER_CLUSTER_DATAPATHS, "frontier/exact slice MAC ratio")
    if frontier_macs % exact_slice_macs:
        raise ValueError("frontier MACs/cycle must be an integer multiple of the exact c16 slice MACs/cycle")

    tile_blocks = _EXPECTED_TILE_TOKENS // int(ROW_ELEMS)
    per_head_eight_wave_blocks = tile_blocks * _EXPECTED_TILE_WAVES
    _require_equal(tile_blocks, 128, "derived tile block count")
    _require_equal(per_head_eight_wave_blocks, 1024, "derived per-head eight-wave block count")

    max_blocks = int(exact_manifest["max_blocks"])
    streams_per_53_datapath_cluster = _EXPECTED_PER_CLUSTER_FLOOR * _EXPECTED_STREAMS_PER_FUNCTIONAL_PRODUCER
    streams_per_54_datapath_cluster = _EXPECTED_PER_CLUSTER_CEIL * _EXPECTED_STREAMS_PER_FUNCTIONAL_PRODUCER
    _require_equal(
        streams_per_53_datapath_cluster,
        _EXPECTED_STREAMS_PER_53_DATAPATH_CLUSTER,
        "derived streams_per_53_datapath_cluster",
    )
    _require_equal(
        streams_per_54_datapath_cluster,
        _EXPECTED_STREAMS_PER_54_DATAPATH_CLUSTER,
        "derived streams_per_54_datapath_cluster",
    )
    streams_with_2_blocks_for_53 = tile_blocks - streams_per_53_datapath_cluster
    streams_with_1_block_for_53 = streams_per_53_datapath_cluster - streams_with_2_blocks_for_53
    streams_with_2_blocks_for_54 = tile_blocks - streams_per_54_datapath_cluster
    streams_with_1_block_for_54 = streams_per_54_datapath_cluster - streams_with_2_blocks_for_54
    _require_equal(streams_with_2_blocks_for_53, _EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_53, "derived streams_with_2_blocks_for_53")
    _require_equal(streams_with_1_block_for_53, _EXPECTED_STREAMS_WITH_1_BLOCK_FOR_53, "derived streams_with_1_block_for_53")
    _require_equal(streams_with_2_blocks_for_54, _EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_54, "derived streams_with_2_blocks_for_54")
    _require_equal(streams_with_1_block_for_54, _EXPECTED_STREAMS_WITH_1_BLOCK_FOR_54, "derived streams_with_1_block_for_54")
    max_blocks_per_stream_per_wave = math.ceil(tile_blocks / streams_per_53_datapath_cluster)
    _require_equal(
        max_blocks_per_stream_per_wave,
        _EXPECTED_MAX_BLOCKS_PER_STREAM_PER_WAVE,
        "derived max_blocks_per_stream_per_wave",
    )

    local_merge_counts = {
        "clusters_with_54_datapaths": 8,
        "clusters_with_53_datapaths": 8,
        "merges_per_54_datapath_cluster": 53,
        "merges_per_53_datapath_cluster": 52,
        "total_local_merges_per_beat": wrapper_cluster_datapaths - _EXPECTED_ACTIVE_GLOBAL_CLUSTERS,
        "global_merges_per_beat": _EXPECTED_ACTIVE_GLOBAL_CLUSTERS - 1,
    }
    _require_equal(local_merge_counts["total_local_merges_per_beat"], 840, "derived local merges per beat")
    _require_equal(local_merge_counts["global_merges_per_beat"], 15, "derived global merges per beat")

    schedule_wrapper_source_text = schedule_wrapper_generator_path.read_text(encoding="utf-8")
    composed_source_text = composed_generator_path.read_text(encoding="utf-8")
    exact_c16_generator_source_text = exact_c16_generator_path.read_text(encoding="utf-8")
    producer_cluster_generator_source_text = producer_cluster_generator_path.read_text(encoding="utf-8")
    _require_contains(schedule_wrapper_source_text, _EXPECTED_STRUCTURAL_STIMULUS_NOTE, "schedule wrapper generator")
    _require_contains(composed_source_text, _EXPECTED_PPA_GUARD_NOTE, "composed generator")
    _require_contains(composed_source_text, _EXPECTED_CONTROL_NOTE, "composed generator")
    _require_contains(exact_c16_generator_source_text, _EXPECTED_MAX_BLOCKS_RANGE_NOTE, "exact c16 generator")
    _require_contains(producer_cluster_generator_source_text, _EXPECTED_MAX_BLOCKS_RANGE_NOTE, "producer cluster generator")

    wrapper_structural_only = {
        "deterministic_stimulus_not_full_token_replay": True,
        "seed_lfsr_and_stream_buffers_present": True,
        "ppa_outputs_exposed_directly": True,
        "functional_exact_partial_protocol_present": False,
        "structural_density_anchor_only": True,
    }

    report = {
        "version": 1,
        "model": _MODEL,
        "decision": _DECISION,
        "source_contract": {
            "source_item_id": _EXPECTED_SOURCE_ITEM_ID,
            "source_decision": source_recost["diagnosis"]["decision"],
            "sequence_length": _EXPECTED_SEQUENCE_LENGTH,
            "tile_tokens": _EXPECTED_TILE_TOKENS,
            "tile_count": tile_count,
            "active_global_clusters": _EXPECTED_ACTIVE_GLOBAL_CLUSTERS,
            "tile_waves": tile_waves,
            "wrapper_count": _EXPECTED_WRAPPER_COUNT,
            "wrapper_cluster_datapaths": wrapper_cluster_datapaths,
            "frontier_macs_per_cycle": frontier_macs,
            "tile_service_cycles": _EXPECTED_PIPELINE_CYCLES,
            "cross_tile_reduction_cycles": _EXPECTED_CROSS_TILE_REDUCTION_CYCLES,
            "qkv_cycles": _EXPECTED_QKV_CYCLES,
            "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
            "total_cycles": _EXPECTED_TOTAL_CYCLES,
        },
        "arithmetically_reproduced_frontier": {
            "wrapper_config": wrapper_contract,
            "measured_wrapper_best_row": {
                "row_index": wrapper_metric_row_index,
                "critical_path_ns": wrapper_best_clock_ns,
                "total_power_mw": wrapper_best_power_mw,
                "stdcell_area_um2": wrapper_best_area_um2,
                "param_hash": wrapper_metric_row.get("param_hash"),
                "tag": wrapper_metric_row.get("tag"),
            },
            "global_distribution": {
                "clusters_with_54_datapaths": 8,
                "clusters_with_53_datapaths": 8,
                "conservative_per_cluster_macs_per_cycle": conservative_per_cluster_macs,
            },
            "tile_work": {
                "qk_macs": tile_work_macs,
                "value_macs": tile_work_macs,
                "qk_cycles": tile_qk_cycles,
                "value_cycles": tile_value_cycles,
                "stats_cycles": tile_stats_cycles,
            },
            "subtile_pipeline_reconstruction": {
                "subtile_count": _EXPECTED_SUBTILE_COUNT,
                "prefetch_distance": _EXPECTED_PREFETCH_DISTANCE,
                "compute_mode": "dual_mac",
                "normalize_strategy": "online_correction",
                "subtile_qk_cycles": qk_sub,
                "subtile_value_cycles": value_sub,
                "subtile_stats_cycles": stats_sub,
                "subtile_hbm_cycles": hbm_sub,
                "subtile_aux_memory_cycles": aux_sub,
                "trace": schedule["trace"],
                "hbm_exposed_cycles": schedule["hbm_exposed_cycles"],
                "aux_memory_span_cycles": schedule["aux_memory_span_cycles"],
                "pipeline_attention_cycles": schedule["pipeline_cycles"],
            },
        },
        "exact_hierarchy_gap": {
            "exact_c16_slice": {
                "producers": int(exact_manifest["producers"]),
                "producer_score_tile_array_m": int(score_tile_manifest["array_m"]),
                "producer_score_tile_array_n": int(score_tile_manifest["array_n"]),
                "slice_macs_per_cycle": exact_slice_macs,
                "frontier_ratio": _EXPECTED_WRAPPER_CLUSTER_DATAPATHS,
                "semantics_only_not_frontier_cadence": True,
            },
            "block_protocol": {
                "tokens_per_block": int(ROW_ELEMS),
                "placeholder_c16_config_max_blocks": max_blocks,
                "placeholder_per_wave_blocks_per_head": tile_blocks,
                "placeholder_eight_wave_blocks_per_head_if_one_command": per_head_eight_wave_blocks,
                "placeholder_per_wave_shortfall_blocks": tile_blocks - max_blocks,
                "placeholder_eight_wave_shortfall_blocks": per_head_eight_wave_blocks - max_blocks,
                "placeholder_shortfall_is_diagnostic_only": True,
            },
            "required_exact_hierarchy": {
                "real_partial_producers": wrapper_cluster_datapaths,
                "local_grouping": "53_or_54_real_128mac_wrapper_cluster_partial_producers_per_global_cluster",
                "functional_producer_block_distribution_per_wave": {
                    "blocks_per_tile": tile_blocks,
                    "streams_per_functional_producer": _EXPECTED_STREAMS_PER_FUNCTIONAL_PRODUCER,
                    "streams_per_53_datapath_cluster": streams_per_53_datapath_cluster,
                    "streams_per_54_datapath_cluster": streams_per_54_datapath_cluster,
                    "distribution_for_53_datapaths": {
                        "streams_with_2_blocks": streams_with_2_blocks_for_53,
                        "streams_with_1_block": streams_with_1_block_for_53,
                    },
                    "distribution_for_54_datapaths": {
                        "streams_with_2_blocks": streams_with_2_blocks_for_54,
                        "streams_with_1_block": streams_with_1_block_for_54,
                    },
                    "max_blocks_per_stream_per_wave": max_blocks_per_stream_per_wave,
                    "supported_generator_min_max_blocks": _EXPECTED_SUPPORTED_MIN_MAX_BLOCKS,
                    "supported_generator_min_max_blocks_suffices": True,
                },
                "selected_temporal_accumulation_boundary": (
                    "per_wave_producer_emission_then_local_53_54_way_reduction_then_"
                    "persistent_local_state_across_8_waves_then_one_c16_global_exact_reduction"
                ),
                "single_c16_global_exact_reduction_after_local_aggregation": True,
                "local_merge_counts": local_merge_counts,
                "next_unmeasured_block": "local_exact_partial_reducer_and_temporal_state_across_8_waves",
            },
            "measured_wrapper_classification": wrapper_structural_only,
        },
        "next_l1_contract": {
            "proposal_id": "prop_l1_decoder_attention_score32_exact_partial_dual_stream_producer_v1",
            "required_functional_block": "functional_2stream_m8x8_exact_partial_producer_before_53_54_way_local_aggregation",
            "required_macs_per_cycle_per_functional_block": _EXPECTED_WRAPPER_CLUSTER_MACS,
            "producer_streams": _EXPECTED_STREAMS_PER_FUNCTIONAL_PRODUCER,
            "per_wave_blocks_per_tile": tile_blocks,
            "max_blocks_per_stream_per_wave": max_blocks_per_stream_per_wave,
            "minimum_supported_max_blocks_for_functional_block": _EXPECTED_SUPPORTED_MIN_MAX_BLOCKS,
            "temporal_accumulation_boundary": (
                "local_reducer_persistent_across_8_waves_before_one_c16_global_exact_reduction"
            ),
            "placeholder_c16_max_blocks_shortfall_is_diagnostic_only": True,
            "structural_wrapper_density_is_insufficient_for_functional_closure": True,
        },
        "non_claims": [
            "Do not revise frontier throughput or latency yet.",
            "The 986-cycle tile service point is arithmetically reproducible from checked-in sources, but hardware-equivalence closure remains open.",
            "The native c16 exact slice proves protocol semantics only; it does not validate the 109568-MAC/cycle frontier cadence.",
            "The next unmeasured block is the local 53/54-way reducer plus temporal exact-partial state across 8 waves.",
        ],
        "source_artifacts": {
            "schedule_wrapper_recost_json": {
                "path": _portable_path(source_recost_path),
                "file_sha256": _sha256_file(source_recost_path),
                "canonical_json_sha256": _canonical_json_sha256(source_recost),
            },
            "subtile_pipeline_json": {
                "path": _portable_path(subtile_pipeline_path),
                "file_sha256": _sha256_file(subtile_pipeline_path),
                "canonical_json_sha256": _canonical_json_sha256(subtile_pipeline),
            },
            "wrapper_config_json": {
                "path": _portable_path(wrapper_config_path),
                "file_sha256": _sha256_file(wrapper_config_path),
                "canonical_json_sha256": _canonical_json_sha256(wrapper_config_payload),
            },
            "wrapper_metrics_csv": {
                "path": _portable_path(wrapper_metrics_path),
                "file_sha256": _sha256_file(wrapper_metrics_path),
                "selected_row_index": wrapper_metric_row_index,
                "selected_row_sha256": hashlib.sha256(
                    json.dumps(wrapper_metric_row, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            },
            "exact_c16_config_json": {
                "path": _portable_path(exact_c16_config_path),
                "file_sha256": _sha256_file(exact_c16_config_path),
                "canonical_json_sha256": _canonical_json_sha256(exact_c16_config_payload),
            },
            "subtile_pipeline_generator_py": {
                "path": _portable_path(subtile_generator_path),
                "file_sha256": _sha256_file(subtile_generator_path),
            },
            "schedule_wrapper_generator_py": {
                "path": _portable_path(schedule_wrapper_generator_path),
                "file_sha256": _sha256_file(schedule_wrapper_generator_path),
            },
            "composed_generator_py": {
                "path": _portable_path(composed_generator_path),
                "file_sha256": _sha256_file(composed_generator_path),
            },
            "exact_c16_generator_py": {
                "path": _portable_path(exact_c16_generator_path),
                "file_sha256": _sha256_file(exact_c16_generator_path),
            },
            "producer_cluster_generator_py": {
                "path": _portable_path(producer_cluster_generator_path),
                "file_sha256": _sha256_file(producer_cluster_generator_path),
            },
            "attention_online_source_py": {
                "path": _portable_path(attention_online_path),
                "file_sha256": _sha256_file(attention_online_path),
            },
        },
    }
    return report


def _build_markdown(report: JsonDict) -> str:
    frontier = report["arithmetically_reproduced_frontier"]
    exact_gap = report["exact_hierarchy_gap"]
    contract = report["next_l1_contract"]
    block_protocol = exact_gap["block_protocol"]
    lines = [
        "# Score32 Exact Hierarchy Cadence Audit",
        "",
        f"- decision: `{report['decision']}`",
        f"- source recost: `{report['source_artifacts']['schedule_wrapper_recost_json']['path']}`",
        f"- subtile pipeline: `{report['source_artifacts']['subtile_pipeline_json']['path']}`",
        f"- wrapper config: `{report['source_artifacts']['wrapper_config_json']['path']}`",
        f"- wrapper metrics: `{report['source_artifacts']['wrapper_metrics_csv']['path']}`",
        f"- exact c16 config: `{report['source_artifacts']['exact_c16_config_json']['path']}`",
        "",
        "## Reproduced Frontier Arithmetic",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| seq | {report['source_contract']['sequence_length']} |",
        f"| tile tokens | {report['source_contract']['tile_tokens']} |",
        f"| tile count | {report['source_contract']['tile_count']} |",
        f"| active global clusters | {report['source_contract']['active_global_clusters']} |",
        f"| tile waves | {report['source_contract']['tile_waves']} |",
        f"| wrapper total MAC/cycle | {frontier['wrapper_config']['wrapper_total_macs_per_cycle']} |",
        f"| wrapper-cluster datapath MAC/cycle | {frontier['wrapper_config']['wrapper_cluster_macs_per_cycle']} |",
        f"| wrapper count | {report['source_contract']['wrapper_count']} |",
        f"| wrapper-cluster datapaths | {report['source_contract']['wrapper_cluster_datapaths']} |",
        f"| frontier MAC/cycle | {report['source_contract']['frontier_macs_per_cycle']} |",
        "",
        f"Eight global clusters carry `{_EXPECTED_PER_CLUSTER_CEIL}` datapaths and eight carry `{_EXPECTED_PER_CLUSTER_FLOOR}`.",
        f"The conservative per-cluster capacity is `{_EXPECTED_PER_CLUSTER_FLOOR} x {_EXPECTED_WRAPPER_CLUSTER_MACS} = {_EXPECTED_CONSERVATIVE_CLUSTER_MACS}` MAC/cycle.",
        "",
        f"Each tile does `{_EXPECTED_TILE_TOKENS} x 4096 = {_EXPECTED_TILE_WORK_MACS}` QK MACs and the same value MACs, so each barrier stage takes `ceil({_EXPECTED_TILE_WORK_MACS}/{_EXPECTED_CONSERVATIVE_CLUSTER_MACS}) = {_EXPECTED_TILE_STAGE_CYCLES}` cycles.",
        "",
        "## 986-Cycle Reconstruction",
        "",
        f"- subtiles: `{_EXPECTED_SUBTILE_COUNT}`",
        f"- qk/value per subtile: `{_EXPECTED_SUBTILE_QK}` / `{_EXPECTED_SUBTILE_VALUE}` cycles",
        f"- stats per subtile: `{_EXPECTED_SUBTILE_STATS}` cycles",
        f"- HBM per subtile: `{_EXPECTED_SUBTILE_HBM}` cycles",
        f"- aux memory release per subtile: `{_EXPECTED_SUBTILE_AUX}` cycles",
        f"- prefetch distance: `{_EXPECTED_PREFETCH_DISTANCE}`",
        f"- reconstructed pipeline cycles: `{frontier['subtile_pipeline_reconstruction']['pipeline_attention_cycles']}`",
        "",
        "| subtile | hbm_ready | aux_release | qk_start | qk_done | stats_done | value_start | value_done |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in frontier["subtile_pipeline_reconstruction"]["trace"]:
        lines.append(
            f"| {row['subtile']} | {row['hbm_ready_cycle']} | {row['aux_release_cycle']} | {row['qk_start_cycle']} | "
            f"{row['qk_done_cycle']} | {row['stats_done_cycle']} | {row['value_start_cycle']} | {row['value_done_cycle']} |"
        )
    lines.extend(
        [
            "",
            "## Exact Hierarchy Gap",
            "",
            f"- merged native c16 exact slice: `{exact_gap['exact_c16_slice']['slice_macs_per_cycle']}` MAC/cycle "
            f"(`16 x m1x8` producers)",
            f"- frontier ratio: `{exact_gap['exact_c16_slice']['frontier_ratio']}x` below the `{report['source_contract']['frontier_macs_per_cycle']}`-MAC/cycle frontier",
            f"- placeholder config max_blocks: `{block_protocol['placeholder_c16_config_max_blocks']}`",
            f"- tokens per exact block: `{block_protocol['tokens_per_block']}`",
            f"- placeholder blocks per 1024-token tile: `{block_protocol['placeholder_per_wave_blocks_per_head']}`",
            f"- placeholder blocks per head for one-command eight-wave persistence: `{block_protocol['placeholder_eight_wave_blocks_per_head_if_one_command']}`",
            f"- local merges per beat: `{exact_gap['required_exact_hierarchy']['local_merge_counts']['total_local_merges_per_beat']}`",
            f"- global merges per beat: `{exact_gap['required_exact_hierarchy']['local_merge_counts']['global_merges_per_beat']}`",
            "",
            "The current c16 placeholder is therefore not enough: it is too small in MAC density and its `max_blocks=16` only diagnoses the placeholder path, not the required producer contract.",
            "",
            f"In the required hierarchy, a `{_EXPECTED_PER_CLUSTER_FLOOR}`-datapath cluster spreads `128` tile blocks across `{_EXPECTED_STREAMS_PER_53_DATAPATH_CLUSTER}` streams, so `{_EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_53}` streams carry `2` blocks and `{_EXPECTED_STREAMS_WITH_1_BLOCK_FOR_53}` carry `1`. A `{_EXPECTED_PER_CLUSTER_CEIL}`-datapath cluster spreads them across `{_EXPECTED_STREAMS_PER_54_DATAPATH_CLUSTER}` streams, so `{_EXPECTED_STREAMS_WITH_2_BLOCKS_FOR_54}` streams carry `2` blocks and `{_EXPECTED_STREAMS_WITH_1_BLOCK_FOR_54}` carry `1`.",
            f"That fixes per-wave producer demand at `2` blocks/stream, and the checked-in generator floor `max_blocks >= {_EXPECTED_SUPPORTED_MIN_MAX_BLOCKS}` is already sufficient.",
            "",
            "## Wrapper Classification",
            "",
            "- The measured dual-stream wrapper is a structural PPA anchor, not a functional exact-partial producer.",
            "- Its generator uses deterministic seed/stream-buffer stimulus and exposes PPA outputs directly.",
            "- It supports density estimates, but it does not establish functional equivalence or exact partial-state cadence.",
            "",
            "## Next L1 Contract",
            "",
            f"- proposal: `{contract['proposal_id']}`",
            f"- required block: `{contract['required_functional_block']}`",
            f"- producer streams: `{contract['producer_streams']}`",
            f"- per-wave blocks per tile: `{contract['per_wave_blocks_per_tile']}`",
            f"- max blocks per stream per wave: `{contract['max_blocks_per_stream_per_wave']}`",
            f"- minimum supported producer `max_blocks`: `{contract['minimum_supported_max_blocks_for_functional_block']}`",
            "- temporal accumulation boundary: per-wave producer emission, local 53/54-way reduction, then persistent local aggregate state across 8 waves before one c16 global exact reduction",
            "",
            "## Non-Claims",
            "",
        ]
    )
    for claim in report["non_claims"]:
        lines.append(f"- {claim}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-recost-json", type=Path, required=True)
    parser.add_argument("--wrapper-config", type=Path, required=True)
    parser.add_argument("--wrapper-metrics", type=Path, required=True)
    parser.add_argument("--exact-c16-config", type=Path, required=True)
    parser.add_argument(
        "--subtile-pipeline-generator",
        type=Path,
        default=REPO_ROOT / "npu/eval/estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py",
    )
    parser.add_argument(
        "--schedule-wrapper-generator",
        type=Path,
        default=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
    )
    parser.add_argument(
        "--composed-generator",
        type=Path,
        default=REPO_ROOT / "npu/rtlgen/gen_attention_dual_stream_composed.py",
    )
    parser.add_argument(
        "--exact-c16-generator",
        type=Path,
        default=REPO_ROOT / "npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py",
    )
    parser.add_argument(
        "--producer-cluster-generator",
        type=Path,
        default=REPO_ROOT / "npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py",
    )
    parser.add_argument(
        "--attention-online-source",
        type=Path,
        default=REPO_ROOT / "npu/sim/perf/attention_online.py",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)

    report = _build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
