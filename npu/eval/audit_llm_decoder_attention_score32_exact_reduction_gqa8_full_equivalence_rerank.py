#!/usr/bin/env python3
"""Rerank the quality-aware score32 frontier with exact reduction and full GQA8 equivalence evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_v1"
_EXPECTED_FRONTIER_MODEL = "llm_decoder_attention_score32_integrated_frontier_ranking_v1"
_EXPECTED_EXACT_REDUCTION_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_EXPECTED_FRONTIER_ITEM_ID = (
    "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_rtl_ppa_recost_frontier_llama7b_v1"
)
_EXPECTED_ONE_GROUP_ITEM_ID = (
    "l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r8"
)
_EXPECTED_FOUR_GROUP_ITEM_ID = (
    "l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r2"
)
_EXPECTED_ONE_GROUP_PROPOSAL_ID = "prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1"
_EXPECTED_ONE_GROUP_PROPOSAL_PATH = (
    "docs/proposals/prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1/proposal.json"
)
_EXPECTED_FOUR_GROUP_PROPOSAL_ID = _EXPECTED_ONE_GROUP_PROPOSAL_ID
_EXPECTED_FOUR_GROUP_PROPOSAL_PATH = _EXPECTED_ONE_GROUP_PROPOSAL_PATH
_EXPECTED_SCORE32_FAMILY = "score32_exp_lut_div"
_EXPECTED_SCORE32_CANDIDATE = "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
_EXPECTED_HEAD_DIMENSION = 128
_EXPECTED_EQUIVALENCE_COUNTS = {
    1: {
        "producer_handshake_count": 1_048_576,
        "fill_target_accept_count": 128,
        "fill_row_accept_count": 262144,
        "sram_request_accept_count": 262144,
        "sram_response_accept_count": 262144,
        "cluster_row_count": 2048,
        "root_row_count": 128,
    },
    4: {
        "producer_handshake_count": 4_194_304,
        "fill_target_accept_count": 512,
        "fill_row_accept_count": 1048576,
        "sram_request_accept_count": 1048576,
        "sram_response_accept_count": 1048576,
        "cluster_row_count": 8192,
        "root_row_count": 512,
    },
}
_EXPECTED_PER_CLUSTER_COUNTS = {
    1: {
        "wave_command_accept_count": 8,
        "completed_command_count": 1,
        "emitted_beat_count": 128,
        "fill_target_accept_count": 8,
        "fill_row_accept_count": 16384,
        "request_accept_count": 16384,
        "response_accept_count": 16384,
        "command_accept_count": 8,
        "command_release_count": 8,
    },
    4: {
        "wave_command_accept_count": 32,
        "completed_command_count": 4,
        "emitted_beat_count": 512,
        "fill_target_accept_count": 32,
        "fill_row_accept_count": 65536,
        "request_accept_count": 65536,
        "response_accept_count": 65536,
        "command_accept_count": 32,
        "command_release_count": 32,
    },
}
_EXPECTED_HEAD_BASES = {
    1: [0],
    4: [0, 8, 16, 24],
}
_EXPECTED_COMMAND_IDS = {
    1: [0x8200],
    4: [0x8200, 0x8201, 0x8202, 0x8203],
}
_GLOBAL_PACKING_CONTRACT = {
    "value_packing": "canonical_pack_numerators",
    "numerator_bits": 41,
    "numerator_lanes": 8,
    "row_bits": 419,
    "value_offset": 91,
}
_CONSERVATIVE_ENERGY_STATUS = "conservative_upper_bound_latency_scaled_non_hbm_energy"
_PROVISIONAL_ENERGY_RANKING_STATUS = (
    "provisional_pending_reducer_and_global_tree_activity_power_measurement"
)


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _as_float(value: Any, *, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not numeric == numeric or numeric in (float("inf"), float("-inf")):
        raise ValueError(f"{label} must be a finite number")
    return numeric


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _require_close(actual: float, expected: float, *, label: str, tolerance: float = 1.0e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise ValueError(f"{label} must be {expected}, got {actual}")


def _validate_exact_reduction(payload: JsonDict) -> JsonDict:
    model = str(payload.get("model") or "")
    decision = str(payload.get("decision") or "")
    _require(model == _EXPECTED_EXACT_REDUCTION_MODEL, f"unexpected exact-reduction model: {model}")
    _require(
        decision == "score32_exact_reduction_schedule_recost_recorded",
        f"unexpected exact-reduction decision: {decision}",
    )
    source_contract = _as_dict(payload.get("source_contract"))
    corrected_contract = _as_dict(payload.get("corrected_contract"))
    best_requested = _as_dict(payload.get("best_requested"))
    delta_vs_source = _as_dict(payload.get("delta_vs_source"))
    _require(source_contract, "exact-reduction artifact is missing source_contract")
    _require(corrected_contract, "exact-reduction artifact is missing corrected_contract")
    _require(best_requested, "exact-reduction artifact is missing best_requested")
    source_latency_us = _as_float(source_contract.get("replica_recost_latency_us"), label="exact reduction source latency")
    corrected_latency_us = _as_float(
        corrected_contract.get("replica_recost_latency_us"),
        label="exact reduction corrected latency",
    )
    source_reduction_cycles = int(_as_float(source_contract.get("cross_tile_reduction_cycles"), label="exact reduction source reduction cycles"))
    corrected_reduction_cycles = int(
        _as_float(corrected_contract.get("cross_tile_reduction_cycles"), label="exact reduction corrected reduction cycles")
    )
    _require(corrected_latency_us > source_latency_us, "exact-reduction corrected latency must exceed source latency")
    _require(
        bool(best_requested.get("exact_reduction_replaces_legacy_component_breakdown")),
        "exact-reduction artifact must mark exact_reduction_replaces_legacy_component_breakdown",
    )
    _require(
        int(_as_float(best_requested.get("cross_tile_reduction_cycles"), label="exact reduction best_requested reduction cycles"))
        == corrected_reduction_cycles,
        "exact-reduction best_requested reduction cycles must match corrected contract",
    )
    return {
        "source_latency_us": source_latency_us,
        "corrected_latency_us": corrected_latency_us,
        "source_reduction_cycles": source_reduction_cycles,
        "corrected_reduction_cycles": corrected_reduction_cycles,
        "source_throughput_per_s": _as_float(
            source_contract.get("token_throughput_per_s"),
            label="exact reduction source throughput",
        ),
        "corrected_throughput_per_s": _as_float(
            corrected_contract.get("token_throughput_per_s"),
            label="exact reduction corrected throughput",
        ),
        "delta_latency_us": _as_float(
            delta_vs_source.get("replica_recost_latency_us"),
            label="exact reduction delta latency",
        ),
        "remaining_abstractions": [str(item) for item in _as_list(payload.get("remaining_abstractions"))],
    }


def _frontier_row_by_candidate(rows: list[JsonDict], candidate_id: str) -> JsonDict | None:
    for row in rows:
        if str(row.get("candidate_id") or "") == candidate_id:
            return dict(row)
    return None


def _frontier_row_by_family(rows: list[JsonDict], family: str) -> JsonDict | None:
    for row in rows:
        if str(row.get("family") or "") == family:
            return dict(row)
    return None


def _validate_frontier(payload: JsonDict, *, exact_reduction: JsonDict) -> JsonDict:
    model = str(payload.get("model") or "")
    decision = str(payload.get("decision") or "")
    _require(model == _EXPECTED_FRONTIER_MODEL, f"unexpected frontier model: {model}")
    _require(decision.startswith("score32_integrated_frontier_"), f"unexpected frontier decision: {decision}")
    rows = [dict(row) for row in _as_list(payload.get("rows")) if isinstance(row, dict)]
    _require(rows, "quality-aware frontier must contain rows")
    diagnosis = _as_dict(payload.get("diagnosis"))
    score32_candidate_id = str(
        diagnosis.get("best_precision_safe_candidate")
        or diagnosis.get("current_recommended_candidate")
        or _EXPECTED_SCORE32_CANDIDATE
    )
    score32_row = _frontier_row_by_candidate(rows, score32_candidate_id) or _frontier_row_by_family(
        rows, _EXPECTED_SCORE32_FAMILY
    )
    _require(score32_row is not None, "quality-aware frontier is missing the score32 precision-safe row")
    _require(
        str(score32_row.get("family") or "") == _EXPECTED_SCORE32_FAMILY,
        "quality-aware frontier score32 row family is mismatched",
    )
    _require(
        str(score32_row.get("candidate_id") or "") == _EXPECTED_SCORE32_CANDIDATE,
        "quality-aware frontier score32 candidate is not the expected schedule-wrapper/controller row",
    )
    _require(bool(score32_row.get("promotable")), "quality-aware frontier score32 row must remain promotable")
    _require(bool(score32_row.get("quality_backed")), "quality-aware frontier score32 row must remain quality-backed")
    _require(
        str(score32_row.get("source_artifact") or "").startswith("score32_schedule_wrapper_hbm_controller_replay"),
        "quality-aware frontier score32 row must come from the HBM controller replay recost path",
    )
    frontier_latency_us = _as_float(score32_row.get("latency_us"), label="frontier score32 latency")
    _require_close(
        frontier_latency_us,
        exact_reduction["source_latency_us"],
        label="frontier score32 latency",
    )
    frontier_throughput = _as_float(
        score32_row.get("token_throughput_per_s"),
        label="frontier score32 throughput",
    )
    _require_close(
        frontier_throughput,
        exact_reduction["source_throughput_per_s"],
        label="frontier score32 throughput",
        tolerance=1.0e-9,
    )
    _require(
        str(diagnosis.get("mixed_int8_quality_status") or "") == "quality_invalidated_low_precision_score_softmax",
        "quality-aware frontier must already invalidate the stale low-precision mixed/int8 row",
    )
    _require(
        str(diagnosis.get("score32_quality_status") or "").endswith("_pass"),
        "quality-aware frontier score32 quality must be passing",
    )
    return {
        "rows": rows,
        "diagnosis": diagnosis,
        "score32_row": score32_row,
    }


def _validate_equivalence(payload: JsonDict, *, label: str, expected_groups: int) -> JsonDict:
    _require(bool(payload.get("passed")), f"{label} equivalence must pass")
    _require(str(payload.get("classification") or "") == "passed", f"{label} equivalence classification must be passed")
    _require(bool(payload.get("counts_passed")), f"{label} equivalence must have counts_passed=true")
    _require(str(payload.get("simulation_status") or "") == "ok", f"{label} simulation_status must be ok")
    _require(
        int(_as_float(payload.get("normalized_returncode"), label=f"{label} normalized_returncode")) == 0,
        f"{label} normalized_returncode must be 0",
    )
    _require(
        int(_as_float(payload.get("logical_head_groups"), label=f"{label} logical_head_groups")) == expected_groups,
        f"{label} equivalence logical_head_groups must be {expected_groups}",
    )
    head_dimension = int(_as_float(payload.get("head_dimension"), label=f"{label} head_dimension"))
    _require(
        head_dimension == _EXPECTED_HEAD_DIMENSION,
        f"{label} head_dimension must be {_EXPECTED_HEAD_DIMENSION}, got {head_dimension}",
    )
    accumulation_beats = int(
        _as_float(
            payload.get("score_accumulation_beats_per_block"),
            label=f"{label} score_accumulation_beats_per_block",
        )
    )
    _require(
        accumulation_beats == _EXPECTED_HEAD_DIMENSION,
        f"{label} score_accumulation_beats_per_block must be {_EXPECTED_HEAD_DIMENSION}, got {accumulation_beats}",
    )
    head_bases = [int(value) for value in _as_list(payload.get("head_bases"))]
    _require(head_bases == _EXPECTED_HEAD_BASES[expected_groups], f"{label} head_bases are mismatched")
    command_ids = [int(value) for value in _as_list(payload.get("command_ids"))]
    _require(command_ids == _EXPECTED_COMMAND_IDS[expected_groups], f"{label} command_ids are mismatched")
    summary = _as_dict(payload.get("summary"))
    expected_counts = _EXPECTED_EQUIVALENCE_COUNTS[expected_groups]
    for key, expected in expected_counts.items():
        actual = int(_as_float(summary.get(key), label=f"{label} summary {key}"))
        _require(actual == expected, f"{label} summary {key} must be {expected}, got {actual}")
    expected_commands = 8 if expected_groups == 1 else 32
    for key in ("command_accept_count", "cadence_command_accept_count"):
        actual = int(_as_float(summary.get(key), label=f"{label} summary {key}"))
        _require(actual == expected_commands, f"{label} summary {key} must be {expected_commands}, got {actual}")
    _require(
        int(_as_float(summary.get("protocol_error"), label=f"{label} summary protocol_error")) == 0,
        f"{label} summary protocol_error must be 0",
    )
    components = _as_dict(payload.get("compositional_components"))
    _require(
        str(components.get("strict_generated_top_guard") or "") == "passed",
        f"{label} strict_generated_top_guard must be passed",
    )
    producer_parallelism = int(
        _as_float(
            components.get("producer_replay_parallelism"),
            label=f"{label} producer_replay_parallelism",
        )
    )
    _require(producer_parallelism == 1, f"{label} producer_replay_parallelism must be 1")
    global_sidecar = _as_dict(components.get("global_sidecar"))
    _require(global_sidecar, f"{label} compositional_components.global_sidecar is required")
    for key, expected in _GLOBAL_PACKING_CONTRACT.items():
        actual = global_sidecar.get(key)
        _require(actual == expected, f"{label} global_sidecar {key} must be {expected!r}, got {actual!r}")
    cluster_summaries = [dict(row) for row in _as_list(payload.get("cluster_summaries")) if isinstance(row, dict)]
    _require(len(cluster_summaries) == 16, f"{label} must contain exactly 16 cluster_summaries")
    expected_per_cluster = _EXPECTED_PER_CLUSTER_COUNTS[expected_groups]
    for cluster_index, cluster_summary in enumerate(cluster_summaries):
        actual_cluster = int(_as_float(cluster_summary.get("cluster"), label=f"{label} cluster summary cluster"))
        _require(actual_cluster == cluster_index, f"{label} cluster summary index {cluster_index} must report cluster {cluster_index}")
        for key, expected in expected_per_cluster.items():
            actual = int(_as_float(cluster_summary.get(key), label=f"{label} cluster {cluster_index} {key}"))
            _require(actual == expected, f"{label} cluster {cluster_index} {key} must be {expected}, got {actual}")
        _require(
            int(_as_float(cluster_summary.get("errors"), label=f"{label} cluster {cluster_index} errors")) == 0,
            f"{label} cluster {cluster_index} errors must be 0",
        )
    full_row_audit = _as_dict(payload.get("full_row_audit"))
    _require(bool(full_row_audit.get("passed")), f"{label} full_row_audit must pass")
    cluster_audits = [dict(row) for row in _as_list(full_row_audit.get("clusters")) if isinstance(row, dict)]
    _require(len(cluster_audits) == 16, f"{label} full_row_audit must contain 16 cluster entries")
    for cluster_index, cluster_audit in enumerate(cluster_audits):
        _require(bool(cluster_audit.get("passed")), f"{label} full_row_audit cluster {cluster_index} must pass")
    root_audit = _as_dict(full_row_audit.get("root"))
    _require(bool(root_audit.get("passed")), f"{label} full_row_audit root must pass")
    source_links = _as_dict(payload.get("source_links"))
    if source_links:
        expected_item_id = _EXPECTED_ONE_GROUP_ITEM_ID if expected_groups == 1 else _EXPECTED_FOUR_GROUP_ITEM_ID
        expected_proposal_id = _EXPECTED_ONE_GROUP_PROPOSAL_ID if expected_groups == 1 else _EXPECTED_FOUR_GROUP_PROPOSAL_ID
        expected_proposal_path = _EXPECTED_ONE_GROUP_PROPOSAL_PATH if expected_groups == 1 else _EXPECTED_FOUR_GROUP_PROPOSAL_PATH
        if "proposal_id" in source_links:
            _require(
                str(source_links.get("proposal_id") or "") == expected_proposal_id,
                f"{label} source_links proposal_id must be {expected_proposal_id}",
            )
        if "proposal_path" in source_links:
            _require(
                str(source_links.get("proposal_path") or "") == expected_proposal_path,
                f"{label} source_links proposal_path must be {expected_proposal_path}",
            )
        for key in ("item_id", "queue_item_id"):
            if key in source_links:
                _require(
                    str(source_links.get(key) or "") == expected_item_id,
                    f"{label} source_links {key} must be {expected_item_id}",
                )
    return {
        "logical_head_groups": expected_groups,
        "head_dimension": head_dimension,
        "score_accumulation_beats_per_block": accumulation_beats,
        "head_bases": head_bases,
        "command_ids": command_ids,
        "summary": {key: expected_counts[key] for key in expected_counts},
        "expected_command_accept_count": expected_commands,
        "expected_cadence_command_accept_count": expected_commands,
        "global_sidecar": {key: global_sidecar[key] for key in _GLOBAL_PACKING_CONTRACT},
        "source_links": source_links,
    }


def _updated_score32_row(frontier_row: JsonDict, *, exact_reduction: JsonDict) -> JsonDict:
    updated = dict(frontier_row)
    source_latency_us = exact_reduction["source_latency_us"]
    corrected_latency_us = exact_reduction["corrected_latency_us"]
    latency_ratio = corrected_latency_us / source_latency_us
    old_compute_energy_mj = _as_float(
        frontier_row.get("compute_energy_mj_per_token"),
        label="frontier score32 compute energy",
    )
    old_hbm_energy_mj = _as_float(
        frontier_row.get("hbm_energy_mj_per_token"),
        label="frontier score32 hbm energy",
    )
    controller_ppa = _as_dict(frontier_row.get("score32_hbm_controller_replay_ppa"))
    old_controller_energy_mj = _as_float(
        controller_ppa.get("controller_energy_mj_per_token", 0.0),
        label="frontier score32 controller energy",
    )
    old_logic_energy_mj = max(0.0, old_compute_energy_mj - old_controller_energy_mj)
    controller_power_mw = controller_ppa.get("controller_power_mw")
    if controller_power_mw is not None:
        upper_controller_energy_mj = round(
            _as_float(controller_power_mw, label="frontier score32 controller power") * corrected_latency_us * 1.0e-6,
            12,
        )
    else:
        upper_controller_energy_mj = round(old_controller_energy_mj * latency_ratio, 12)
    upper_logic_energy_mj = round(old_logic_energy_mj * latency_ratio, 12)
    lower_compute_energy_mj = round(old_compute_energy_mj, 12)
    upper_compute_energy_mj = round(upper_logic_energy_mj + upper_controller_energy_mj, 12)
    lower_total_energy_mj = round(_as_float(frontier_row.get("energy_mj_per_token"), label="frontier score32 total energy"), 12)
    upper_total_energy_mj = round(upper_compute_energy_mj + old_hbm_energy_mj, 12)
    updated["latency_us"] = round(corrected_latency_us, 6)
    updated["token_throughput_per_s"] = round(1_000_000.0 / corrected_latency_us, 12)
    updated["compute_energy_mj_per_token"] = upper_compute_energy_mj
    updated["energy_mj_per_token"] = upper_total_energy_mj
    updated["compute_energy_mj_per_token_lower_bound"] = lower_compute_energy_mj
    updated["compute_energy_mj_per_token_conservative_upper_bound"] = upper_compute_energy_mj
    updated["energy_mj_per_token_lower_bound"] = lower_total_energy_mj
    updated["energy_mj_per_token_conservative_upper_bound"] = upper_total_energy_mj
    updated["energy_estimate_status"] = _CONSERVATIVE_ENERGY_STATUS
    updated["energy_estimate_assumption"] = (
        "Keep HBM energy unchanged and scale the measured non-HBM schedule-wrapper/controller wall-time energy by "
        "the exact-reduction latency ratio as a conservative upper estimate. Exact reducer/global-tree activity "
        "power remains unmeasured."
    )
    updated["energy_ranking_basis"] = "conservative_upper_bound"
    updated["remaining_abstractions"] = sorted(
        {
            *[str(item) for item in _as_list(frontier_row.get("remaining_abstractions"))],
            "Full one- and four-group GQA8 equivalence closes functional composition only; full-array postroute PPA and toggle power remain unmeasured.",
            "Exact reduction latency is now backed by the banked finalized-tree service contract plus one-/four-group RTL equivalence, but dedicated reducer/global-tree activity energy remains unclosed.",
            "Score32 exact-energy ranking remains provisional until reducer/global-tree activity power is measured.",
        }
    )
    updated["source_artifact"] = "score32_exact_reduction_gqa8_full_equivalence_rerank"
    updated["abstraction_status"] = (
        "measured_schedule_wrapper_hbm_controller_replay_ppa_with_exact_reduction_and_full_gqa8_equivalence_provisional_energy_bound"
    )
    updated["exact_reduction_recost"] = {
        "source_latency_us": round(source_latency_us, 6),
        "corrected_latency_us": round(corrected_latency_us, 6),
        "latency_ratio": round(latency_ratio, 12),
        "source_reduction_cycles": exact_reduction["source_reduction_cycles"],
        "corrected_reduction_cycles": exact_reduction["corrected_reduction_cycles"],
        "delta_latency_us": round(exact_reduction["delta_latency_us"], 6),
        "energy_estimate_status": _CONSERVATIVE_ENERGY_STATUS,
        "source_compute_energy_mj_per_token_lower_bound": lower_compute_energy_mj,
        "source_total_energy_mj_per_token_lower_bound": lower_total_energy_mj,
        "scaled_logic_energy_mj_per_token_upper_bound": upper_logic_energy_mj,
        "scaled_controller_energy_mj_per_token_upper_bound": upper_controller_energy_mj,
        "compute_energy_mj_per_token_conservative_upper_bound": upper_compute_energy_mj,
        "total_energy_mj_per_token_conservative_upper_bound": upper_total_energy_mj,
        "hbm_energy_mj_per_token_preserved": round(old_hbm_energy_mj, 12),
        "assumption": updated["energy_estimate_assumption"],
    }
    if controller_ppa:
        updated_controller_ppa = dict(controller_ppa)
        updated_controller_ppa["controller_energy_mj_per_token_lower_bound"] = round(old_controller_energy_mj, 12)
        updated_controller_ppa["controller_energy_mj_per_token_conservative_upper_bound"] = upper_controller_energy_mj
        updated["score32_hbm_controller_replay_ppa"] = updated_controller_ppa
    return updated


def _rank_rows(rows: list[JsonDict], *, metric: str) -> list[JsonDict]:
    return sorted(rows, key=lambda row: _as_float(row.get(metric), label=f"row {row.get('candidate_id')} {metric}"))


def _find_row(rows: list[JsonDict], family: str) -> JsonDict:
    row = _frontier_row_by_family(rows, family)
    if row is None:
        raise ValueError(f"frontier is missing family {family}")
    return row


def build_report(args: argparse.Namespace) -> JsonDict:
    exact_reduction_path = Path(args.exact_reduction_json).resolve()
    quality_aware_frontier_path = Path(args.quality_aware_frontier_json).resolve()
    one_group_path = Path(args.one_group_equivalence_json).resolve()
    four_group_path = Path(args.four_group_equivalence_json).resolve()

    exact_reduction_payload = _load_json(exact_reduction_path)
    quality_aware_frontier_payload = _load_json(quality_aware_frontier_path)
    one_group_payload = _load_json(one_group_path)
    four_group_payload = _load_json(four_group_path)

    exact_reduction = _validate_exact_reduction(exact_reduction_payload)
    frontier = _validate_frontier(quality_aware_frontier_payload, exact_reduction=exact_reduction)
    one_group = _validate_equivalence(one_group_payload, label="one-group", expected_groups=1)
    four_group = _validate_equivalence(four_group_payload, label="four-group", expected_groups=4)

    rows: list[JsonDict] = []
    for row in frontier["rows"]:
        if str(row.get("candidate_id") or "") == str(frontier["score32_row"].get("candidate_id") or ""):
            rows.append(_updated_score32_row(row, exact_reduction=exact_reduction))
        else:
            rows.append(dict(row))

    latency_rank = _rank_rows(rows, metric="latency_us")
    energy_rank = _rank_rows(rows, metric="energy_mj_per_token")
    promotable_rows = [row for row in rows if bool(row.get("promotable"))]
    promotable_latency_rank = _rank_rows(promotable_rows, metric="latency_us")
    promotable_energy_rank = _rank_rows(promotable_rows, metric="energy_mj_per_token")
    score32_row = _find_row(rows, _EXPECTED_SCORE32_FAMILY)
    measured_fp16_row = _find_row(rows, "measured_exact_fp16_gqa8_kv8")
    diagnosis = {
        "decision": "score32_exact_reduction_gqa8_full_equivalence_frontier_recorded",
        "best_latency_candidate": str(latency_rank[0].get("candidate_id") or ""),
        "best_energy_candidate": str(energy_rank[0].get("candidate_id") or ""),
        "best_precision_safe_candidate": str(promotable_latency_rank[0].get("candidate_id") or ""),
        "best_precision_safe_energy_candidate": str(promotable_energy_rank[0].get("candidate_id") or ""),
        "current_recommended_candidate": str(promotable_latency_rank[0].get("candidate_id") or ""),
        "score32_latency_us": round(_as_float(score32_row.get("latency_us"), label="updated score32 latency"), 6),
        "score32_token_throughput_per_s": round(
            _as_float(score32_row.get("token_throughput_per_s"), label="updated score32 throughput"),
            12,
        ),
        "score32_total_energy_mj_per_token": round(
            _as_float(score32_row.get("energy_mj_per_token"), label="updated score32 total energy"),
            12,
        ),
        "score32_total_energy_mj_per_token_lower_bound": round(
            _as_float(score32_row.get("energy_mj_per_token_lower_bound"), label="updated score32 lower-bound energy"),
            12,
        ),
        "score32_energy_estimate_status": str(score32_row.get("energy_estimate_status") or ""),
        "exact_energy_ranking_status": _PROVISIONAL_ENERGY_RANKING_STATUS,
        "score32_die_area_mm2": round(_as_float(score32_row.get("die_area_mm2"), label="updated score32 die area"), 12),
        "score32_quality_status": str(score32_row.get("precision_status") or ""),
        "score32_vs_measured_fp16_throughput_ratio": round(
            _as_float(score32_row.get("token_throughput_per_s"), label="updated score32 throughput")
            / _as_float(measured_fp16_row.get("token_throughput_per_s"), label="fp16 throughput"),
            9,
        ),
        "score32_vs_measured_fp16_energy_ratio": round(
            _as_float(score32_row.get("energy_mj_per_token"), label="updated score32 energy")
            / _as_float(measured_fp16_row.get("energy_mj_per_token"), label="fp16 energy"),
            9,
        ),
        "exact_reduction_source_latency_us": round(exact_reduction["source_latency_us"], 6),
        "exact_reduction_corrected_latency_us": round(exact_reduction["corrected_latency_us"], 6),
        "exact_reduction_delta_latency_us": round(exact_reduction["delta_latency_us"], 6),
        "exact_reduction_source_reduction_cycles": exact_reduction["source_reduction_cycles"],
        "exact_reduction_corrected_reduction_cycles": exact_reduction["corrected_reduction_cycles"],
        "one_group_equivalence_item_id": _EXPECTED_ONE_GROUP_ITEM_ID,
        "four_group_equivalence_item_id": _EXPECTED_FOUR_GROUP_ITEM_ID,
        "one_group_proposal_id": _EXPECTED_ONE_GROUP_PROPOSAL_ID,
        "four_group_proposal_id": _EXPECTED_FOUR_GROUP_PROPOSAL_ID,
        "remaining_abstractions": list(score32_row.get("remaining_abstractions") or []),
    }
    next_step = (
        "Measure reducer/global-tree activity power and full-array postroute PPA so the quality-backed score32 "
        "frontier can replace the current conservative upper-bound energy ranking with measured exact energy."
    )
    return {
        "version": 1,
        "model": _MODEL,
        "decision": diagnosis["decision"],
        "inputs": {
            "exact_reduction_json": str(args.exact_reduction_json),
            "quality_aware_frontier_json": str(args.quality_aware_frontier_json),
            "one_group_equivalence_json": str(args.one_group_equivalence_json),
            "four_group_equivalence_json": str(args.four_group_equivalence_json),
        },
        "source_frontier_contract": {
            "source_item_id": _EXPECTED_FRONTIER_ITEM_ID,
            "source_model": _EXPECTED_FRONTIER_MODEL,
            "score32_candidate_id": _EXPECTED_SCORE32_CANDIDATE,
            "source_score32_latency_us": round(exact_reduction["source_latency_us"], 6),
            "source_score32_throughput_per_s": round(exact_reduction["source_throughput_per_s"], 12),
        },
        "reduction_contract": exact_reduction,
        "equivalence_prerequisites": {
            "one_group": one_group,
            "four_group": four_group,
            "full_path_equivalence_closed": True,
        },
        "latency_rank": latency_rank,
        "energy_rank": energy_rank,
        "promotable_latency_rank": promotable_latency_rank,
        "promotable_energy_rank": promotable_energy_rank,
        "rows": rows,
        "diagnosis": diagnosis,
        "next_step": next_step,
    }


def _render_markdown(report: JsonDict) -> str:
    diagnosis = _as_dict(report.get("diagnosis"))
    lines = [
        "# Score32 Exact Reduction Full-GQA8 Frontier Rerank",
        "",
        f"- decision: `{report['decision']}`",
        f"- score32 latency us: `{diagnosis.get('score32_latency_us')}`",
        f"- score32 token/s: `{diagnosis.get('score32_token_throughput_per_s')}`",
        f"- score32 total energy upper-bound mJ/token: `{diagnosis.get('score32_total_energy_mj_per_token')}`",
        f"- score32 total energy lower-bound mJ/token: `{diagnosis.get('score32_total_energy_mj_per_token_lower_bound')}`",
        f"- energy status: `{diagnosis.get('score32_energy_estimate_status')}`",
        f"- source latency us: `{diagnosis.get('exact_reduction_source_latency_us')}`",
        f"- corrected latency us: `{diagnosis.get('exact_reduction_corrected_latency_us')}`",
        f"- one-group equivalence: `{diagnosis.get('one_group_equivalence_item_id')}`",
        f"- four-group equivalence: `{diagnosis.get('four_group_equivalence_item_id')}`",
        "",
        "## Ranking",
        "",
        f"- best latency candidate: `{diagnosis.get('best_latency_candidate')}`",
        f"- best energy candidate: `{diagnosis.get('best_energy_candidate')}`",
        f"- best precision-safe candidate: `{diagnosis.get('best_precision_safe_candidate')}`",
        f"- best precision-safe energy candidate: `{diagnosis.get('best_precision_safe_energy_candidate')}`",
        f"- exact energy ranking status: `{diagnosis.get('exact_energy_ranking_status')}`",
        "",
        "## Remaining Abstractions",
        "",
    ]
    for item in _as_list(diagnosis.get("remaining_abstractions")):
        lines.append(f"- {item}")
    lines.extend(["", "## Next Step", "", report["next_step"]])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-reduction-json", type=Path, required=True)
    parser.add_argument("--quality-aware-frontier-json", type=Path, required=True)
    parser.add_argument("--one-group-equivalence-json", type=Path, required=True)
    parser.add_argument("--four-group-equivalence-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)

    report = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(_render_markdown(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
