#!/usr/bin/env python3
"""Fail-closed checker for the exact Phase-2 shared-stream artifact contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.sim.perf.attention_phase2_shared_stream_transport import (
    CONTEXT_BYTES,
    CONTEXT_COUNT,
    DESTINATION_SPACE_BASE,
    FLITS_PER_PACKET,
    MAPPING_SHIFTS,
    PACKETS_PER_CONTEXT,
    PACKET_BYTES,
    TOTAL_FLITS,
    TOTAL_PACKETS,
    TOTAL_SHARED_BYTES,
    REMOTE_WAVES,
    TransportContractError,
)


DEFAULT_ARTIFACT = REPO_ROOT / (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)

JsonDict = dict[str, Any]


class ArtifactContractError(TransportContractError):
    """Raised when a checked artifact cannot prove shared-stream consistency."""


def _mapping(payload: JsonDict, key: str) -> Any:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ArtifactContractError(f"artifact missing object {key!r}")
    return value


def _require(mapping: JsonDict, key: str, expected: Any, label: str) -> None:
    if key not in mapping:
        raise ArtifactContractError(f"{label} is missing required shared field {key!r}")
    if mapping[key] != expected:
        raise ArtifactContractError(
            f"{label}.{key}={mapping[key]!r}; expected independent shared value {expected!r}"
        )


def _load(path: Path) -> JsonDict:
    if not path.is_file():
        raise ArtifactContractError(f"missing Phase-2 artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactContractError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ArtifactContractError("Phase-2 artifact root must be a JSON object")
    return payload


def validate_artifact(path: str | Path = DEFAULT_ARTIFACT) -> JsonDict:
    """Validate only shared transport evidence from the historical artifact.

    The artifact also contains historical reduction fields.  They are
    intentionally not used to satisfy any shared check.  Missing shared
    fields fail closed even when similarly named reduction fields are present.
    """

    artifact_path = Path(path).resolve()
    payload = _load(artifact_path)
    flow_summary = _mapping(payload, "flow_summary")
    traffic = _mapping(payload, "traffic_quantities")
    mapping = _mapping(payload, "mapping")
    schedule = _mapping(payload, "schedule_parameters")
    simulation = _mapping(payload, "simulation")
    delivered_by_class = _mapping(simulation, "delivery_flit_count_by_class")

    # These are the only fields allowed to establish shared-stream totals.
    _require(flow_summary, "remote_shared_flow_count", CONTEXT_COUNT, "flow_summary")
    _require(flow_summary, "remote_shared_packet_count", TOTAL_PACKETS, "flow_summary")
    _require(flow_summary, "remote_shared_bytes", TOTAL_SHARED_BYTES, "flow_summary")
    _require(traffic, "shared_tile_payload_bytes", CONTEXT_BYTES, "traffic_quantities")
    _require(traffic, "simulated_tiles", 128, "traffic_quantities")
    _require(schedule, "packet_payload_bytes", PACKET_BYTES, "schedule_parameters")
    _require(schedule, "shared_vc", 0, "schedule_parameters")
    _require(delivered_by_class, "shared", TOTAL_FLITS, "simulation.delivery_flit_count_by_class")
    _require(simulation, "remote_shared_worst_hops_observed", 6, "simulation")
    _require(simulation, "remote_shared_average_hops_observed", 3.0, "simulation")

    _require(mapping, "cluster_endpoints", list(range(16)), "mapping")
    _require(mapping, "shared_sram_home_offset", 1, "mapping")
    _require(mapping, "shared_sram_home_stride", 3, "mapping")
    _require(mapping, "shared_sram_worst_remote_hops", 6, "mapping")
    _require(mapping, "shared_sram_average_remote_hops", 3.0, "mapping")
    expected_load = {str(endpoint): 8 for endpoint in range(16)}
    _require(mapping, "shared_sram_home_load_tiles", expected_load, "mapping")

    expected_shifts = tuple((1 + (wave + 1) * 3) % 16 for wave in range(8))
    if expected_shifts != MAPPING_SHIFTS:
        raise ArtifactContractError("reference mapping constants are internally inconsistent")
    direct_shifts = mapping.get("shared_sram_home_shifts")
    if direct_shifts is not None and tuple(direct_shifts) != MAPPING_SHIFTS:
        raise ArtifactContractError("artifact shared_sram_home_shifts differ from the checked mapping")

    # A capacity boundary is part of the address model, but not a reduction
    # metric.  Keep this assertion here so changes to the reference cannot
    # silently leave the checker accepting stale address assumptions.
    if DESTINATION_SPACE_BASE != TOTAL_SHARED_BYTES:
        raise ArtifactContractError("reference source/destination address spaces are inconsistent")
    if tuple(REMOTE_WAVES) != (0, 1, 2, 3, 5, 6, 7):
        raise ArtifactContractError("reference remote-wave set changed")

    reduction_fields = {
        "flow_summary.local_only_reduction_bytes",
        "flow_summary.remote_reduction_bytes",
        "flow_summary.remote_reduction_flow_count",
        "flow_summary.remote_reduction_packet_count",
        "simulation.delivery_flit_count_by_class.reduction",
        "schedule_parameters.reduction_vc",
    }
    return {
        "status": "ok",
        "artifact": str(artifact_path),
        "shared": {
            "contexts": CONTEXT_COUNT,
            "bytes": TOTAL_SHARED_BYTES,
            "packets": TOTAL_PACKETS,
            "flits": TOTAL_FLITS,
            "packet_bytes": PACKET_BYTES,
            "flits_per_packet": FLITS_PER_PACKET,
            "mapping_shifts": list(MAPPING_SHIFTS),
        },
        "retracted_reduction_validation": "ignored",
        "retracted_reduction_fields_not_used": sorted(reduction_fields),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    try:
        result = validate_artifact(args.artifact)
    except (ArtifactContractError, OSError, ValueError) as exc:
        print(f"attention-phase2-shared-contract: FAIL: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
