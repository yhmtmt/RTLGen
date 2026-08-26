#!/usr/bin/env python3
"""Generate a bounded exact-router activity manifest from the Llama7B Phase 2 schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as phase2  # noqa: E402
from npu.sim.perf.noc_segmented_mesh import (  # noqa: E402
    ENDPOINTS,
    PORT_NAMES,
    PORTS,
    MeshSimulationResult,
    ModelFlit,
    iter_router_replay_cycles,
    packetize_traffic_flow,
    simulate_scheduled_flits,
    verify_router_replay,
)

JsonDict = dict[str, Any]

DEFAULT_SCHEDULE_JSON = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)
_REPRODUCED_FIELDS = (
    "source_contract",
    "traffic_quantities",
    "mapping",
    "schedule_parameters",
    "simulation",
    "tag_semantics",
    "flow_summary",
)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_normalize(value: object) -> object:
    return json.loads(json.dumps(value, sort_keys=True))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked_wire_flit(flit: ModelFlit) -> bytes:
    fields = (
        ("destination", flit.destination, 4),
        ("source", flit.source, 4),
        ("tag", flit.tag, 8),
        ("fragment", flit.fragment, 3),
        ("vc", flit.vc, 2),
        ("data", flit.data, 256),
    )
    for name, value, width in fields:
        if not 0 <= int(value) < (1 << width):
            raise ValueError(f"router replay {name}={value} exceeds its {width}-bit RTL field")
    return struct.pack(
        ">BBBBB",
        flit.destination,
        flit.source,
        flit.tag,
        flit.fragment,
        (int(flit.last) << 2) | flit.vc,
    ) + int(flit.data).to_bytes(32, byteorder="big")


def _signal_digest_and_counts(mesh_result: MeshSimulationResult, *, node: int) -> tuple[str, JsonDict]:
    digest = hashlib.sha256()
    valid_by_port = [0] * PORTS
    backpressure_by_port = [0] * PORTS
    nondefault_input_cycles = 0
    nondefault_backpressure_cycles = 0
    recorded_mesh_cycles = 0
    for cycle, inputs, out_ready, expected_trace in iter_router_replay_cycles(
        mesh_result,
        node=node,
    ):
        valid_mask = 0
        ready_mask = 0
        for port, ready in enumerate(out_ready):
            if ready:
                ready_mask |= 1 << port
            else:
                backpressure_by_port[port] += 1
        valid_flits: list[tuple[int, ModelFlit]] = []
        for port, slot in enumerate(inputs):
            if not slot.valid:
                if slot.flit is not None:
                    raise ValueError("invalid router replay slot carries a flit")
                continue
            if slot.flit is None:
                raise ValueError("valid router replay slot is missing its flit")
            valid_mask |= 1 << port
            valid_by_port[port] += 1
            valid_flits.append((port, slot.flit))
        digest.update(struct.pack(">QBBB", cycle, valid_mask, ready_mask, len(valid_flits)))
        for port, flit in valid_flits:
            digest.update(bytes((port,)))
            digest.update(_checked_wire_flit(flit))
        nondefault_input_cycles += int(bool(valid_mask))
        nondefault_backpressure_cycles += int(ready_mask != (1 << PORTS) - 1)
        recorded_mesh_cycles += int(expected_trace is not None)
    return digest.hexdigest(), {
        "input_valid_port_cycles": dict(zip(PORT_NAMES, valid_by_port)),
        "out_backpressure_port_cycles": dict(zip(PORT_NAMES, backpressure_by_port)),
        "nondefault_input_cycles": nondefault_input_cycles,
        "nondefault_backpressure_cycles": nondefault_backpressure_cycles,
        "recorded_mesh_cycles": recorded_mesh_cycles,
        "restored_idle_cycles": mesh_result.cycles - recorded_mesh_cycles,
    }


def build_router_activity_manifest(
    mesh_result: MeshSimulationResult,
    *,
    node: int,
    source_schedule_path: str,
    source_schedule_sha256: str,
    source_schedule_semantic_sha256: str,
    clock_period_ns: float,
) -> JsonDict:
    if not 0 <= node < ENDPOINTS:
        raise ValueError(f"node must be in [0, {ENDPOINTS - 1}]")
    replay_sha256, activity_counts = _signal_digest_and_counts(mesh_result, node=node)
    verification = verify_router_replay(mesh_result, node=node)
    x_coord = node % 4
    y_coord = node // 4
    return {
        "version": 1,
        "model": "llama7b_score32_noc_router_exact_activity",
        "scope": "one physical five-port segmented router",
        "node": node,
        "coordinates": {"x": x_coord, "y": y_coord},
        "clock_cycles": mesh_result.cycles,
        "clock_period_ns": clock_period_ns,
        "source_schedule": {
            "path": source_schedule_path,
            "file_sha256": source_schedule_sha256,
            "reproduced_semantic_sha256": source_schedule_semantic_sha256,
        },
        "replay_contract": {
            "default_inputs": "all five in_valid bits are zero",
            "default_out_ready": "all five out_ready bits are one",
            "fast_forwarded_idle_cycles_restored": True,
            "signal_hash_encoding": (
                "per cycle: big-endian u64 cycle, valid mask, ready mask, valid-flit count, then "
                "each valid port and RTL-width flit fields"
            ),
            "replay_signal_sha256": replay_sha256,
            "portable_payload": "summary and exact provenance only; raw VCD and cycle vectors stay evaluator-local",
        },
        "activity_counts": activity_counts,
        "router_counters": asdict(verification),
        "equivalence": {
            "status": "pass",
            "proof": "streamed independent router replay equals every captured mesh-router cycle and final counters",
            "checked_cycles": verification.cycle_count,
        },
        "remaining_abstractions": [
            "This manifest proves performance-model replay inputs and counters; "
            "RTL VCD equivalence is a separate gate.",
            "Inter-router wire and composed clock-tree power require the routed 4x4 mesh measurement.",
            "HBM/DRAM controller and PHY power remain outside the on-chip router scope.",
        ],
    }


def _reproduction_args(repo_root: Path, schedule: JsonDict) -> SimpleNamespace:
    source_artifacts = schedule["source_artifacts"]
    mapping = schedule["mapping"]
    parameters = schedule["schedule_parameters"]
    return SimpleNamespace(
        repo_root=repo_root,
        source_json=Path(source_artifacts["score32_recost_json"]),
        measured_l1_costs=Path(source_artifacts["measured_l1_costs_json"]),
        wave_limit=parameters["requested_wave_limit"],
        packet_payload_bytes=int(parameters["packet_payload_bytes"]),
        cluster_endpoints=list(mapping["cluster_endpoints"]),
        root_endpoint=int(mapping["root_endpoint"]),
        shared_vc=int(parameters["shared_vc"]),
        reduction_vc=int(parameters["reduction_vc"]),
        compute_clock_ns=float(parameters["compute_clock_ns"]),
        noc_clock_ns=float(parameters["noc_clock_ns"]),
        max_cycles=max(1_000_000, int(schedule["simulation"]["cycles_to_drain"]) + 1),
    )


def build_manifest(*, repo_root: Path, schedule_json: Path, node: int) -> JsonDict:
    absolute_schedule = schedule_json if schedule_json.is_absolute() else repo_root / schedule_json
    schedule = json.loads(absolute_schedule.read_text(encoding="utf-8"))
    if schedule.get("profile") != "decoder_attention_score32_noc_phase2_schedule":
        raise ValueError("source is not the checked Llama7B Phase 2 NoC schedule")
    packet_specs: list[phase2.PacketSpec] = []
    reproduced = phase2.build_report(
        _reproduction_args(repo_root, schedule),
        packet_spec_output=packet_specs,
    )
    expected_semantics = {field: schedule[field] for field in _REPRODUCED_FIELDS}
    reproduced_semantics = _json_normalize(
        {field: reproduced[field] for field in _REPRODUCED_FIELDS}
    )
    if reproduced_semantics != expected_semantics:
        raise ValueError("current simulator does not reproduce the checked Phase 2 schedule")
    flows = phase2._packetize_specs_with_concrete_tags(packet_specs)
    scheduled_flits = [item for flow in flows for item in packetize_traffic_flow(flow)]
    mesh_result = simulate_scheduled_flits(
        scheduled_flits,
        max_cycles=max(1_000_000, int(schedule["simulation"]["cycles_to_drain"]) + 1),
        fast_forward_idle=True,
        capture_router_replay_nodes=(node,),
    )
    return build_router_activity_manifest(
        mesh_result,
        node=node,
        source_schedule_path=str(schedule_json),
        source_schedule_sha256=_sha256_file(absolute_schedule),
        source_schedule_semantic_sha256=_canonical_sha256(reproduced_semantics),
        clock_period_ns=float(schedule["source_contract"]["noc_clock_ns"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--schedule-json", type=Path, default=DEFAULT_SCHEDULE_JSON)
    parser.add_argument("--node", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = build_manifest(
        repo_root=args.repo_root.resolve(),
        schedule_json=args.schedule_json,
        node=args.node,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
