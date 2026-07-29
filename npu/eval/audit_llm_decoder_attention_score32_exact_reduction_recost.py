#!/usr/bin/env python3
"""Recost the score32 schedule-wrapper row with the exact banked reduction schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.sim.perf.attention_exact_partial import exact_banked_finalized_tree_full_wave_saturated_service

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_EXPECTED_SOURCE_ITEM_ID = "l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1"
_EXPECTED_REDUCTION_CYCLES = 141
_EXPECTED_LAYER_CYCLES = 8231
_EXPECTED_TOTAL_CYCLES = 263392
_EXPECTED_HEADS = 32
_EXPECTED_LAYERS = 32
_EXPECTED_TILE_WAVES = 8
_EXPECTED_TILE_SERVICE_CYCLES = 986
_EXPECTED_QKV_CYCLES = 192
_EXPECTED_KV_WRITE_CYCLES = 10
_EXPECTED_CLOCK_NS = 48.6509
_RECORDED_FULL_WAVE_OUTPUT_HASH = "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"
_RECORDED_B59_PROBE_COMMAND = (
    "python npu/eval/probe_attention_score32_exact_banked_finalized_tree.py "
    "--clusters 16 --heads 32 --divider-lanes 8 --finalizer-banks 59 --saturated --root-ready-pattern 1 --json"
)
_EXPECTED_CONFIG = {
    "clusters": 16,
    "radix": 2,
    "divider_lanes": 8,
    "finalizer_banks": 59,
    "value_slices": 16,
    "head_id_bits": 5,
}


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


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
        return path.resolve().relative_to(Path(__file__).resolve().parents[2].resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must be {expected!r}, got {actual!r}")


def _as_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be a finite number")
    return numeric


def _validate_source_contract(payload: JsonDict) -> JsonDict:
    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, dict):
        raise ValueError("source recost payload missing diagnosis")
    _require_equal(diagnosis.get("decision"), "dual_stream_feasible", "source diagnosis.decision")
    row = payload.get("best_requested")
    if not isinstance(row, dict):
        raise ValueError("source recost payload missing best_requested")
    _require_equal(row.get("cross_tile_reduction_cycles"), _EXPECTED_REDUCTION_CYCLES, "source reduction cycles")
    _require_equal(row.get("replica_recost_layer_cycles"), _EXPECTED_LAYER_CYCLES, "source layer cycles")
    _require_equal(row.get("replica_recost_total_cycles"), _EXPECTED_TOTAL_CYCLES, "source total cycles")
    _require_equal(row.get("total_cycles"), _EXPECTED_TOTAL_CYCLES, "source total_cycles")
    _require_equal(row.get("layers"), _EXPECTED_LAYERS, "source layers")
    _require_equal(row.get("tile_waves"), _EXPECTED_TILE_WAVES, "source tile_waves")
    _require_equal(
        row.get("replica_recost_tile_service_cycles"),
        _EXPECTED_TILE_SERVICE_CYCLES,
        "source tile service cycles",
    )
    _require_equal(row.get("tile_service_cycles"), _EXPECTED_TILE_SERVICE_CYCLES, "source tile_service_cycles")
    _require_equal(row.get("replica_recost_qkv_cycles"), _EXPECTED_QKV_CYCLES, "source qkv cycles")
    _require_equal(row.get("kv_write_cycles"), _EXPECTED_KV_WRITE_CYCLES, "source kv_write_cycles")
    clock_ns = _as_float(row.get("replica_recost_clock_ns"), "source replica_recost_clock_ns")
    _require_equal(clock_ns, _EXPECTED_CLOCK_NS, "source replica_recost_clock_ns")
    source_latency_us = _as_float(row.get("replica_recost_latency_us"), "source replica_recost_latency_us")
    source_throughput = 1_000_000.0 / source_latency_us
    return {
        "source_best_requested_original": dict(row),
        "source_path_decision": diagnosis.get("decision"),
        "source_best_requested_contract": {
            "cross_tile_reduction_cycles": _EXPECTED_REDUCTION_CYCLES,
            "replica_recost_layer_cycles": _EXPECTED_LAYER_CYCLES,
            "replica_recost_total_cycles": _EXPECTED_TOTAL_CYCLES,
            "total_cycles": _EXPECTED_TOTAL_CYCLES,
            "layers": _EXPECTED_LAYERS,
            "tile_waves": _EXPECTED_TILE_WAVES,
            "replica_recost_tile_service_cycles": _EXPECTED_TILE_SERVICE_CYCLES,
            "tile_service_cycles": _EXPECTED_TILE_SERVICE_CYCLES,
            "replica_recost_qkv_cycles": _EXPECTED_QKV_CYCLES,
            "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
            "replica_recost_clock_ns": clock_ns,
            "replica_recost_latency_us": source_latency_us,
            "token_throughput_per_s": round(source_throughput, 12),
        },
    }


def _validate_banked_config(path: Path) -> JsonDict:
    payload = _load_json(path)
    body = payload.get("attention_score32_exact_banked_finalized_tree")
    if not isinstance(body, dict):
        raise ValueError("banked config missing attention_score32_exact_banked_finalized_tree")
    for key, expected in _EXPECTED_CONFIG.items():
        _require_equal(body.get(key), expected, f"banked config {key}")
    top_name = str(payload.get("top_name") or "").strip()
    if top_name != "attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59":
        raise ValueError("banked config top_name must be attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59")
    return payload


def build_report(args: argparse.Namespace) -> JsonDict:
    source_path = Path(args.source_recost_json).resolve()
    config_path = Path(args.banked_config).resolve()
    source_payload = _load_json(source_path)
    source_contract = _validate_source_contract(source_payload)
    config_payload = _validate_banked_config(config_path)
    source_best_requested_original = dict(source_contract["source_best_requested_original"])

    service = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=_EXPECTED_CONFIG["clusters"],
        heads=_EXPECTED_HEADS,
        divider_lanes=_EXPECTED_CONFIG["divider_lanes"],
        finalizer_banks=_EXPECTED_CONFIG["finalizer_banks"],
    )
    _require_equal(service["exact_no_stall_full_wave_service"], True, "exact no-stall full-wave service")
    _require_equal(service["first_output_cycle"], 62, "bank59 first_output_cycle")
    _require_equal(service["last_output_cycle"], 573, "bank59 last_output_cycle")
    _require_equal(service["drain_cycles"], 574, "bank59 drain_cycles")
    corrected_reduction_cycles = int(service["drain_cycles"])
    corrected_layer_cycles = (
        _EXPECTED_TILE_WAVES * _EXPECTED_TILE_SERVICE_CYCLES
    ) + _EXPECTED_QKV_CYCLES + _EXPECTED_KV_WRITE_CYCLES + corrected_reduction_cycles
    corrected_total_cycles = _EXPECTED_LAYERS * corrected_layer_cycles
    corrected_latency_us = round((corrected_total_cycles * _EXPECTED_CLOCK_NS) / 1000.0, 6)
    corrected_throughput = round(1_000_000.0 / corrected_latency_us, 12)
    source_latency_us = _as_float(source_best_requested_original.get("latency_us"), "source latency_us")
    source_schedule_latency_us = _as_float(
        source_best_requested_original.get("source_latency_us"),
        "source source_latency_us",
    )
    source_base_cross_tile_reduction_cycles = source_best_requested_original.get("base_cross_tile_reduction_cycles")
    if source_base_cross_tile_reduction_cycles is not None:
        source_base_cross_tile_reduction_cycles = int(
            _as_float(source_base_cross_tile_reduction_cycles, "source base_cross_tile_reduction_cycles")
        )
    corrected_replica_recost_latency_slowdown_vs_source = round(corrected_latency_us / source_latency_us, 12)
    corrected_adjusted_speedup_if_feasible = round(source_schedule_latency_us / corrected_latency_us, 12)
    corrected_best_requested = dict(source_best_requested_original)
    corrected_field_updates: JsonDict = {
        "cross_tile_reduction_cycles": corrected_reduction_cycles,
        "replica_recost_layer_cycles": corrected_layer_cycles,
        "layer_cycles": corrected_layer_cycles,
        "replica_recost_total_cycles": corrected_total_cycles,
        "total_cycles": corrected_total_cycles,
        "replica_recost_latency_us": corrected_latency_us,
        "adjusted_latency_us_if_feasible": corrected_latency_us,
        "replica_recost_latency_slowdown_vs_source": corrected_replica_recost_latency_slowdown_vs_source,
        "adjusted_speedup_if_feasible": corrected_adjusted_speedup_if_feasible,
        "token_throughput_per_s": corrected_throughput,
        "exact_reduction_replaces_legacy_component_breakdown": True,
    }
    if source_base_cross_tile_reduction_cycles is not None:
        corrected_field_updates["base_cross_tile_reduction_cycles"] = corrected_reduction_cycles
    corrected_best_requested.update(corrected_field_updates)
    source_best_requested = source_contract["source_best_requested_contract"]
    overridden_fields = [
        field for field in corrected_field_updates if field in source_best_requested_original
    ]
    added_fields = [
        field for field in corrected_field_updates if field not in source_best_requested_original
    ]
    return {
        "version": 1,
        "model": _MODEL,
        "decision": "score32_exact_reduction_schedule_recost_recorded",
        "source_revision": {
            "source_item_id": _EXPECTED_SOURCE_ITEM_ID,
            "source_best_requested_preserved": True,
            "source_best_requested_field_count": len(source_best_requested_original),
            "source_path_decision": source_contract["source_path_decision"],
            "source_only_latency_fields_preserved": [
                field
                for field in ("latency_us", "source_latency_us", "unconstrained_latency_us")
                if field in source_best_requested_original
            ],
            "overridden_best_requested_fields": overridden_fields,
            "added_best_requested_fields": added_fields,
            "legacy_component_breakdown_revision": {
                "source_base_cross_tile_reduction_cycles": source_base_cross_tile_reduction_cycles,
                "replacement_base_cross_tile_reduction_cycles": corrected_reduction_cycles
                if source_base_cross_tile_reduction_cycles is not None
                else None,
                "historical_source_diagnostics": {
                    field: source_best_requested_original[field]
                    for field in (
                        "base_cross_tile_local_cycles",
                        "base_cross_tile_noc_cycles",
                        "base_cross_tile_vector_cycles",
                    )
                    if field in source_best_requested_original
                },
            },
            "obsolete_schedule_assumption": {
                "cross_tile_reduction_cycles": _EXPECTED_REDUCTION_CYCLES,
                "replica_recost_layer_cycles": _EXPECTED_LAYER_CYCLES,
                "replica_recost_total_cycles": _EXPECTED_TOTAL_CYCLES,
            },
            "replacement_schedule_contract": {
                "cross_tile_reduction_cycles": corrected_reduction_cycles,
                "replica_recost_layer_cycles": corrected_layer_cycles,
                "replica_recost_total_cycles": corrected_total_cycles,
            },
        },
        "source_artifacts": {
            "schedule_wrapper_recost_json": {
                "path": _portable_path(source_path),
                "file_sha256": _sha256_file(source_path),
                "canonical_json_sha256": _canonical_json_sha256(source_payload),
            },
            "banked_config_json": {
                "path": _portable_path(config_path),
                "file_sha256": _sha256_file(config_path),
                "canonical_json_sha256": _canonical_json_sha256(config_payload),
            },
        },
        "source_contract": source_best_requested,
        "service_contract_provenance": {
            "analytical_function": (
                "npu.sim.perf.attention_exact_partial.exact_banked_finalized_tree_full_wave_saturated_service"
            ),
            "checked_in_contract_md": "npu/docs/attention_score32_exact_banked_finalized_tree_contract.md",
            "validated_config": {
                "top_name": config_payload["top_name"],
                **_EXPECTED_CONFIG,
            },
            "recorded_exact_output_hash": _RECORDED_FULL_WAVE_OUTPUT_HASH,
            "recorded_probe_command": _RECORDED_B59_PROBE_COMMAND,
            "recorded_rtl_evidence": {
                "bank1": {"first_output_cycle": 62, "last_output_cycle": 30211, "drain_cycles": 30212},
                "bank57": {"first_output_cycle": 62, "last_output_cycle": 589, "drain_cycles": 590},
                "bank58": {"first_output_cycle": 62, "last_output_cycle": 581, "drain_cycles": 582},
                "bank59": {"first_output_cycle": 62, "last_output_cycle": 573, "drain_cycles": 574},
                "bank64": {"first_output_cycle": 62, "last_output_cycle": 573, "drain_cycles": 574},
            },
            "service": service,
        },
        "source_best_requested": source_best_requested_original,
        "corrected_contract": {
            "cross_tile_reduction_cycles": corrected_reduction_cycles,
            "base_cross_tile_reduction_cycles": corrected_reduction_cycles
            if source_base_cross_tile_reduction_cycles is not None
            else None,
            "replica_recost_layer_cycles": corrected_layer_cycles,
            "replica_recost_total_cycles": corrected_total_cycles,
            "total_cycles": corrected_total_cycles,
            "heads": _EXPECTED_HEADS,
            "layers": _EXPECTED_LAYERS,
            "tile_waves": _EXPECTED_TILE_WAVES,
            "replica_recost_tile_service_cycles": _EXPECTED_TILE_SERVICE_CYCLES,
            "tile_service_cycles": _EXPECTED_TILE_SERVICE_CYCLES,
            "replica_recost_qkv_cycles": _EXPECTED_QKV_CYCLES,
            "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
            "replica_recost_clock_ns": _EXPECTED_CLOCK_NS,
            "replica_recost_latency_us": corrected_latency_us,
            "adjusted_latency_us_if_feasible": corrected_latency_us,
            "replica_recost_latency_slowdown_vs_source": corrected_replica_recost_latency_slowdown_vs_source,
            "adjusted_speedup_if_feasible": corrected_adjusted_speedup_if_feasible,
            "token_throughput_per_s": corrected_throughput,
            "exact_reduction_replaces_legacy_component_breakdown": True,
        },
        "best_requested": corrected_best_requested,
        "delta_vs_source": {
            "cross_tile_reduction_cycles": corrected_reduction_cycles - int(source_best_requested["cross_tile_reduction_cycles"]),
            "base_cross_tile_reduction_cycles": (
                corrected_reduction_cycles - source_base_cross_tile_reduction_cycles
                if source_base_cross_tile_reduction_cycles is not None
                else None
            ),
            "replica_recost_layer_cycles": corrected_layer_cycles - int(source_best_requested["replica_recost_layer_cycles"]),
            "replica_recost_total_cycles": corrected_total_cycles - int(source_best_requested["replica_recost_total_cycles"]),
            "replica_recost_latency_us": round(
                corrected_latency_us - _as_float(source_best_requested["replica_recost_latency_us"], "source contract latency"),
                12,
            ),
            "adjusted_latency_us_if_feasible": round(
                corrected_latency_us
                - _as_float(
                    source_best_requested_original.get("adjusted_latency_us_if_feasible"),
                    "source adjusted_latency_us_if_feasible",
                ),
                12,
            ),
            "replica_recost_latency_slowdown_vs_source": round(
                corrected_replica_recost_latency_slowdown_vs_source
                - _as_float(
                    source_best_requested_original.get("replica_recost_latency_slowdown_vs_source"),
                    "source replica_recost_latency_slowdown_vs_source",
                ),
                12,
            ),
            "adjusted_speedup_if_feasible": round(
                corrected_adjusted_speedup_if_feasible
                - _as_float(
                    source_best_requested_original.get("adjusted_speedup_if_feasible"),
                    "source adjusted_speedup_if_feasible",
                ),
                12,
            ),
            "token_throughput_per_s": round(
                corrected_throughput
                - _as_float(
                    source_best_requested_original.get(
                        "token_throughput_per_s",
                        source_best_requested["token_throughput_per_s"],
                    ),
                    "source token_throughput_per_s",
                ),
                12,
            ),
        },
        "remaining_abstractions": [
            "Exact reducer PPA remains unclosed; this recost changes schedule cycles only.",
            "Exact reducer activity energy remains unclosed; no reduction toggle-energy closure is claimed here.",
            "328-bit exact transport, NoC, and SRAM composition remain unclosed.",
            "Producer arrival timing and overlap with the reducer are not embodied here; adding the 574-cycle drain after tile waves is a conservative serialized-stage schedule.",
        ],
        "summary": {
            "source_reduction_cycles": int(source_best_requested["cross_tile_reduction_cycles"]),
            "corrected_reduction_cycles": corrected_reduction_cycles,
            "source_layer_cycles": int(source_best_requested["replica_recost_layer_cycles"]),
            "corrected_layer_cycles": corrected_layer_cycles,
            "source_total_cycles": int(source_best_requested["replica_recost_total_cycles"]),
            "corrected_total_cycles": corrected_total_cycles,
            "source_latency_us": _as_float(source_best_requested["replica_recost_latency_us"], "source summary latency"),
            "corrected_latency_us": corrected_latency_us,
            "source_adjusted_latency_us_if_feasible": _as_float(
                source_best_requested_original.get("adjusted_latency_us_if_feasible"),
                "source summary adjusted latency",
            ),
            "corrected_adjusted_latency_us_if_feasible": corrected_latency_us,
            "source_adjusted_speedup_if_feasible": _as_float(
                source_best_requested_original.get("adjusted_speedup_if_feasible"),
                "source summary adjusted speedup",
            ),
            "corrected_adjusted_speedup_if_feasible": corrected_adjusted_speedup_if_feasible,
            "source_token_throughput_per_s": _as_float(
                source_best_requested_original.get(
                    "token_throughput_per_s",
                    source_best_requested["token_throughput_per_s"],
                ),
                "source summary token throughput",
            ),
            "corrected_token_throughput_per_s": corrected_throughput,
        },
    }


def _build_markdown(report: JsonDict) -> str:
    source = report["source_contract"]
    corrected = report["corrected_contract"]
    service = report["service_contract_provenance"]["service"]
    lines = [
        "# Score32 Exact Reduction Recost",
        "",
        f"- decision: `{report['decision']}`",
        f"- source recost: `{report['source_artifacts']['schedule_wrapper_recost_json']['path']}`",
        f"- banked config: `{report['source_artifacts']['banked_config_json']['path']}`",
        f"- analytical service: `{report['service_contract_provenance']['analytical_function']}`",
        f"- source item: `{report['source_revision']['source_item_id']}`",
        f"- recorded exact output hash: `{report['service_contract_provenance']['recorded_exact_output_hash']}`",
        f"- recorded probe command: `{report['service_contract_provenance']['recorded_probe_command']}`",
        "",
        "| metric | source | corrected |",
        "| --- | ---: | ---: |",
        f"| reduction cycles | {source['cross_tile_reduction_cycles']} | {corrected['cross_tile_reduction_cycles']} |",
        f"| layer cycles | {source['replica_recost_layer_cycles']} | {corrected['replica_recost_layer_cycles']} |",
        f"| total cycles | {source['replica_recost_total_cycles']} | {corrected['replica_recost_total_cycles']} |",
        f"| latency us | {source['replica_recost_latency_us']:.6f} | {corrected['replica_recost_latency_us']:.6f} |",
        (
            f"| adjusted latency us if feasible | "
            f"{report['source_best_requested']['adjusted_latency_us_if_feasible']:.6f} | "
            f"{corrected['adjusted_latency_us_if_feasible']:.6f} |"
        ),
        f"| token/s | {source['token_throughput_per_s']:.5f} | {corrected['token_throughput_per_s']:.5f} |",
        "",
        "## Full-Wave Service",
        "",
        f"- config: `c16/r2/l8/b59`",
        (
            f"- no-stall full-wave root service: first `{service['first_output_cycle']}`, "
            f"last `{service['last_output_cycle']}`, drain `{service['drain_cycles']}`, "
            f"interval `{service['interval_cycles']}`, cycles/beat `{service['cycles_per_beat']:.6f}`, "
            f"dispatch stall `{service['dispatch_stall_cycles']}`"
        ),
        (
            f"- divider contract stays distinct: iterations `{service['divider_iterations_per_group']}`, "
            f"output latency `{service['per_bank_output_latency_cycles']}`, "
            f"reaccept `{service['per_bank_accept_interval_cycles']}`"
        ),
        (
            "- schedule interpretation: producer arrival timing and overlap with the reducer are not "
            "embodied here; the 574-cycle drain is applied after tile waves as a conservative "
            "serialized-stage schedule"
        ),
        "",
        "## Remaining Abstractions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["remaining_abstractions"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-recost-json", type=Path, required=True)
    parser.add_argument("--banked-config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)

    report = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
