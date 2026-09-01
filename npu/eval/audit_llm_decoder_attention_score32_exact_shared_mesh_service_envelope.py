#!/usr/bin/env python3
"""Record the exact shared-mesh standalone RTL service-capacity envelope."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_shared_mesh_service_envelope_v1"
_REPLACEMENT_MODEL = "llm_decoder_attention_score32_exact_shared_mesh_replacement_contract_v1"
_EXACT_REDUCTION_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_EXPECTED_TRAFFIC = {
    "vc0_contexts": 112,
    "vc0_packets": 7616,
    "vc0_flits": 60928,
    "vc1_groups": 4,
    "vc1_rows": 512,
    "vc1_packets": 1260,
    "vc1_flits": 10020,
}


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _positive(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be positive and finite") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return result


def _positive_int(value: Any, label: str) -> int:
    result = _positive(value, label)
    integer = int(result)
    if float(integer) != result:
        raise ValueError(f"{label} must be an integer")
    return integer


def _source_ref(path: Path) -> JsonDict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build_report(
    *,
    replacement: JsonDict,
    exact_reduction: JsonDict,
    observation: JsonDict,
    source_paths: list[Path] | None = None,
) -> JsonDict:
    if replacement.get("model") != _REPLACEMENT_MODEL:
        raise ValueError("unexpected replacement-contract model")
    if exact_reduction.get("model") != _EXACT_REDUCTION_MODEL:
        raise ValueError("unexpected exact-reduction model")
    for field, expected in _EXPECTED_TRAFFIC.items():
        if _positive_int(observation.get(field), field) != expected:
            raise ValueError(f"{field} must be {expected}")
    if _positive_int(observation.get("service_envelope"), "service_envelope") != 1:
        raise ValueError("observation is not the no-artificial-stall service envelope")

    service_cycles = _positive_int(observation.get("service_cycles"), "service_cycles")
    vc0_done_cycle = _positive_int(observation.get("vc0_done_cycle"), "vc0_done_cycle")
    vc1_done_cycle = _positive_int(observation.get("vc1_done_cycle"), "vc1_done_cycle")
    if service_cycles != max(vc0_done_cycle, vc1_done_cycle):
        raise ValueError("service_cycles must equal the later producer completion")
    overlap_valid = _positive_int(observation.get("overlap_valid"), "overlap_valid")
    overlap_arb = _positive_int(observation.get("overlap_arb"), "overlap_arb")
    contention = _positive_int(observation.get("contention"), "contention")

    best = exact_reduction.get("best_requested")
    if not isinstance(best, dict):
        raise ValueError("exact-reduction artifact is missing best_requested")
    layer_cycles = _positive_int(best.get("replica_recost_layer_cycles"), "compute layer cycles")
    compute_clock_ns = _positive(best.get("replica_recost_clock_ns"), "compute clock")
    compute_layer_time_ns = layer_cycles * compute_clock_ns
    maximum_composed_clock_ns = compute_layer_time_ns / service_cycles
    source = replacement.get("source_frontier")
    if not isinstance(source, dict):
        raise ValueError("replacement contract is missing source_frontier")
    if abs(_positive(source.get("compute_clock_ns"), "replacement compute clock") - compute_clock_ns) > 1.0e-9:
        raise ValueError("replacement and exact-reduction compute clocks differ")

    return {
        "version": 1,
        "model": _MODEL,
        "decision": "standalone_exact_shared_mesh_capacity_envelope_recorded",
        "source_refs": [_source_ref(path) for path in source_paths or []],
        "traffic": {**_EXPECTED_TRAFFIC, "total_flits": 70948},
        "rtl_observation": {
            "mode": "eager_producers_no_artificial_consumer_stalls",
            "service_cycles": service_cycles,
            "vc0_done_cycle": vc0_done_cycle,
            "vc1_done_cycle": vc1_done_cycle,
            "overlap_valid_cycles": overlap_valid,
            "overlap_arbitrated_cycles": overlap_arb,
            "contention_cycles": contention,
            "protocol_errors": 0,
            "payload_check": "exact_all_vc0_flits_and_512_vc1_rows",
            "sram_response_contract": "one outstanding read per endpoint with registered response",
        },
        "compute_comparison": {
            "source_compute_layer_cycles": layer_cycles,
            "source_compute_clock_ns": compute_clock_ns,
            "source_compute_layer_time_ns": compute_layer_time_ns,
            "maximum_composed_clock_ns_for_standalone_service_to_fit_compute_window": maximum_composed_clock_ns,
            "capacity_gate_formula": "service_cycles * measured_composed_critical_path_ns <= source_compute_layer_time_ns",
        },
        "interpretation": {
            "proves": [
                "one embodied shared mesh can drain the full exact layer traffic without artificial sink stalls",
                "VC0 and VC1 overlap, arbitrate, contend, and complete with exact payload integrity",
                "the measured physical clock can be compared to a finite standalone capacity threshold",
            ],
            "does_not_prove": [
                "producer-release-coupled layer completion or overlap with compute",
                "workload-annotated physical power or token energy",
                "vendor HBM timing or energy",
            ],
        },
        "next_gate": (
            "Replay the same embodied service with VC0 residency events and VC1 group releases timed by the "
            "actual compute/reducer valid-ready schedule; then compare its final completion to the compute layer window."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    rtl = report["rtl_observation"]
    compute = report["compute_comparison"]
    lines = [
        "# Exact Shared-Mesh Standalone Service Envelope",
        "",
        f"- total exact traffic: `{report['traffic']['total_flits']}` flits",
        f"- joint completion: `{rtl['service_cycles']}` cycles",
        f"- VC0 completion: `{rtl['vc0_done_cycle']}` cycles",
        f"- VC1 completion: `{rtl['vc1_done_cycle']}` cycles",
        f"- source compute layer: `{compute['source_compute_layer_time_ns']:.4f}` ns",
        f"- maximum composed clock for standalone capacity fit: `{compute['maximum_composed_clock_ns_for_standalone_service_to_fit_compute_window']:.9f}` ns",
        "",
        "This is a finite standalone capacity bound, not a producer-coupled throughput result.",
        "",
        "## Proves",
        "",
    ]
    lines.extend(f"- {item}" for item in report["interpretation"]["proves"])
    lines.extend(["", "## Does Not Prove", ""])
    lines.extend(f"- {item}" for item in report["interpretation"]["does_not_prove"])
    lines.extend(["", "## Next Gate", "", report["next_gate"]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-contract", type=Path, required=True)
    parser.add_argument("--exact-reduction-json", type=Path, required=True)
    parser.add_argument("--observation-json", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(
        replacement=_load_json(args.replacement_contract),
        exact_reduction=_load_json(args.exact_reduction_json),
        observation=_load_json(args.observation_json),
        source_paths=args.source,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
