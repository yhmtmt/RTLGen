#!/usr/bin/env python3
"""Build a bounded Phase 2 routed NoC schedule from existing Llama7B score32 artifacts."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.sim.perf.noc_segmented_mesh import (  # noqa: E402
    TrafficFlow,
    coordinates,
    deterministic_xy_path,
    packetize_traffic_flow,
    simulate_scheduled_flits,
)

JsonDict = dict[str, Any]

DEFAULT_SOURCE_JSON = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_exact_reduction_recost__"
    "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json"
)
DEFAULT_MEASURED_L1_COSTS = Path(
    "runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_endpoint_v1.json"
)


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if float(numerator) <= 0.0:
        return 0
    return int(math.ceil(float(numerator) / float(denominator)))


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integers")
    return items


def _require_fields(payload: JsonDict, fields: list[str], *, label: str) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(f"{label} is missing required quantities: {', '.join(missing)}")


def _profile_by_name(costs_payload: JsonDict, name: str) -> JsonDict:
    profiles = costs_payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("measured L1 cost payload must provide a profiles list")
    for profile in profiles:
        if isinstance(profile, dict) and str(profile.get("name")) == name:
            return profile
    raise ValueError(f"measured L1 cost payload does not contain profile {name!r}")


def _hop_count(source: int, destination: int) -> int:
    return len(deterministic_xy_path(source, destination)) - 1


def _format_endpoint(node: int) -> str:
    x_coord, y_coord = coordinates(node)
    return f"{node}({x_coord},{y_coord})"


def _choose_home_mapping(
    cluster_endpoints: list[int],
    *,
    wave_count: int,
    tile_count: int,
    active_clusters: int,
    declared_noc_hops: int,
) -> JsonDict:
    target_average = max(1.0, declared_noc_hops / 2.0)
    best_choice: JsonDict | None = None
    count = len(cluster_endpoints)
    for stride in range(1, count):
        if math.gcd(stride, count) != 1:
            continue
        for offset in range(count):
            loads = Counter()
            remote_hops: list[int] = []
            total_hops = 0
            remote_tiles = 0
            for wave in range(wave_count):
                wave_tiles = min(active_clusters, max(0, tile_count - wave * active_clusters))
                for cluster_index in range(wave_tiles):
                    compute = cluster_endpoints[cluster_index]
                    home = cluster_endpoints[(cluster_index + offset + ((wave + 1) * stride)) % count]
                    loads[home] += 1
                    hops = _hop_count(home, compute)
                    total_hops += hops
                    if home != compute:
                        remote_tiles += 1
                        remote_hops.append(hops)
            if remote_tiles == 0:
                continue
            average_remote_hops = sum(remote_hops) / len(remote_hops)
            score = (
                abs(max(remote_hops) - declared_noc_hops),
                abs(average_remote_hops - target_average),
                max(loads.values()) - min(loads.values()),
                offset,
                stride,
            )
            choice = {
                "offset": offset,
                "stride": stride,
                "average_remote_hops": round(average_remote_hops, 6),
                "worst_remote_hops": max(remote_hops),
                "remote_tile_count": remote_tiles,
                "per_home_tile_count": dict(sorted(loads.items())),
                "score": score,
            }
            if best_choice is None or score < best_choice["score"]:
                best_choice = choice
    if best_choice is None:
        raise ValueError("failed to construct a deterministic shared-SRAM home mapping")
    return best_choice


def _home_endpoint(cluster_endpoints: list[int], *, cluster_index: int, wave: int, offset: int, stride: int) -> int:
    return cluster_endpoints[(cluster_index + offset + ((wave + 1) * stride)) % len(cluster_endpoints)]


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root.resolve()
    source_json = repo_root / args.source_json
    costs_json = repo_root / args.measured_l1_costs
    source_payload = _load_json(source_json)
    source_row = source_payload.get("best_requested")
    if not isinstance(source_row, dict):
        raise ValueError("source recost payload is missing best_requested")
    _require_fields(
        source_row,
        [
            "active_clusters",
            "cluster_count",
            "sequence_length",
            "tile_tokens",
            "tile_waves",
            "hidden_size",
            "attention_heads",
            "kv_heads",
            "kv_bits",
            "shared_byte_share",
            "partial_reduction_payload_bytes",
            "cross_tile_reduction_payload_bytes",
            "tile_attention_cycles",
            "qkv_cycles",
            "noc_hops",
            "measured_l1_profile",
        ],
        label="source best_requested",
    )
    costs_payload = _load_json(costs_json)
    measured_profile = _profile_by_name(costs_payload, str(source_row["measured_l1_profile"]))

    active_clusters = int(source_row["active_clusters"])
    cluster_count = int(source_row["cluster_count"])
    if active_clusters <= 0 or active_clusters > 16 or cluster_count > 16:
        raise ValueError("Phase 2 scheduler only supports up to the 4x4 mesh envelope")

    cluster_endpoints = list(args.cluster_endpoints or list(range(active_clusters)))
    if len(cluster_endpoints) < active_clusters:
        raise ValueError("cluster_endpoints must name at least active_clusters endpoints")
    cluster_endpoints = cluster_endpoints[:active_clusters]
    if len(set(cluster_endpoints)) != len(cluster_endpoints):
        raise ValueError("cluster_endpoints must be unique")
    if any(endpoint < 0 or endpoint >= 16 for endpoint in cluster_endpoints):
        raise ValueError("cluster_endpoints must be mesh endpoints in [0, 15]")
    root_endpoint = int(args.root_endpoint)
    if root_endpoint < 0 or root_endpoint >= 16:
        raise ValueError("root_endpoint must be in [0, 15]")

    hidden_size = int(source_row["hidden_size"])
    attention_heads = int(source_row["attention_heads"])
    kv_heads = int(source_row["kv_heads"])
    kv_bits = int(source_row["kv_bits"])
    tile_tokens = int(source_row["tile_tokens"])
    sequence_length = int(source_row["sequence_length"])
    declared_tile_waves = int(source_row["tile_waves"])
    head_dim = hidden_size // attention_heads
    full_tile_bytes = int(2 * tile_tokens * kv_heads * head_dim * kv_bits / 8)
    shared_tile_payload_bytes = int(math.ceil(full_tile_bytes * float(source_row["shared_byte_share"])))
    local_tile_payload_bytes = full_tile_bytes - shared_tile_payload_bytes
    tile_count = _ceil_div(sequence_length, tile_tokens)
    wave_count = min(declared_tile_waves, args.wave_limit if args.wave_limit is not None else declared_tile_waves)
    if wave_count <= 0:
        raise ValueError("wave_limit must leave at least one simulated wave")

    mapping = _choose_home_mapping(
        cluster_endpoints,
        wave_count=wave_count,
        tile_count=tile_count,
        active_clusters=active_clusters,
        declared_noc_hops=int(source_row["noc_hops"]),
    )

    packet_payload_bytes = int(args.packet_payload_bytes)
    if packet_payload_bytes <= 0 or packet_payload_bytes > 256:
        raise ValueError("packet_payload_bytes must be in [1, 256]")

    qkv_cycles = int(source_row["qkv_cycles"])
    tile_attention_cycles = int(source_row["tile_attention_cycles"])
    reduction_payload_bytes = int(source_row["partial_reduction_payload_bytes"])

    flows: list[TrafficFlow] = []
    local_only_shared_bytes = 0
    local_only_reduction_bytes = 0
    remote_shared_hops: list[int] = []
    remote_reduction_hops: list[int] = []
    flow_counter = 0

    for wave in range(wave_count):
        wave_tiles = min(active_clusters, max(0, tile_count - wave * active_clusters))
        wave_start = qkv_cycles + (wave * tile_attention_cycles)
        reduction_release = wave_start + tile_attention_cycles
        for cluster_index in range(wave_tiles):
            compute_endpoint = cluster_endpoints[cluster_index]
            home_endpoint = _home_endpoint(
                cluster_endpoints,
                cluster_index=cluster_index,
                wave=wave,
                offset=int(mapping["offset"]),
                stride=int(mapping["stride"]),
            )
            if shared_tile_payload_bytes > 0:
                if home_endpoint == compute_endpoint:
                    local_only_shared_bytes += shared_tile_payload_bytes
                else:
                    remote_shared_hops.append(_hop_count(home_endpoint, compute_endpoint))
                    flows.append(
                        TrafficFlow(
                            name=f"shared_w{wave}_c{cluster_index}",
                            source=home_endpoint,
                            destination=compute_endpoint,
                            payload_bytes=shared_tile_payload_bytes,
                            vc=int(args.shared_vc),
                            release_cycle=wave_start,
                            packet_payload_bytes=packet_payload_bytes,
                            tag_base=(flow_counter * 37) & 0xFF,
                            data_seed=flow_counter,
                        )
                    )
                    flow_counter += 1
            if reduction_payload_bytes > 0:
                if compute_endpoint == root_endpoint:
                    local_only_reduction_bytes += reduction_payload_bytes
                else:
                    remote_reduction_hops.append(_hop_count(compute_endpoint, root_endpoint))
                    flows.append(
                        TrafficFlow(
                            name=f"reduction_w{wave}_c{cluster_index}",
                            source=compute_endpoint,
                            destination=root_endpoint,
                            payload_bytes=reduction_payload_bytes,
                            vc=int(args.reduction_vc),
                            release_cycle=reduction_release,
                            packet_payload_bytes=packet_payload_bytes,
                            tag_base=(flow_counter * 37) & 0xFF,
                            data_seed=flow_counter,
                        )
                    )
                    flow_counter += 1

    scheduled_flits = [scheduled for flow in flows for scheduled in packetize_traffic_flow(flow)]
    mesh_result = simulate_scheduled_flits(scheduled_flits, max_cycles=args.max_cycles)
    flow_names = {flow.name for flow in flows}
    if not flow_names:
        raise ValueError("bounded Phase 2 schedule produced no remote NoC traffic")

    delivery_by_prefix = Counter()
    last_delivery_cycle_by_prefix: dict[str, int] = {}
    for delivery in mesh_result.deliveries:
        prefix = delivery.flit.label.split("_", 1)[0]
        delivery_by_prefix[prefix] += 1
        last_delivery_cycle_by_prefix[prefix] = max(
            delivery.cycle,
            last_delivery_cycle_by_prefix.get(prefix, -1),
        )

    link_usage = Counter(
        (transfer.source_node, transfer.destination_node) for transfer in mesh_result.link_transfers
    )
    router_contention_cycles = sum(
        1
        for trace in mesh_result.traces
        if any(router_trace.contention for router_trace in trace.router_traces)
    )
    max_router_input_occupancy = max(
        summary.max_input_occupancy for summary in mesh_result.router_summaries
    )

    total_shared_remote_bytes = sum(
        flow.payload_bytes for flow in flows if flow.name.startswith("shared_")
    )
    total_reduction_remote_bytes = sum(
        flow.payload_bytes for flow in flows if flow.name.startswith("reduction_")
    )

    payload = {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_schedule",
        "source_artifacts": {
            "score32_recost_json": str(args.source_json),
            "measured_l1_costs_json": str(args.measured_l1_costs),
            "measured_l1_profile": measured_profile["name"],
        },
        "source_contract": {
            "active_clusters": active_clusters,
            "cluster_count": cluster_count,
            "sequence_length": sequence_length,
            "tile_tokens": tile_tokens,
            "declared_tile_waves": declared_tile_waves,
            "simulated_wave_count": wave_count,
            "hidden_size": hidden_size,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "kv_bits": kv_bits,
            "shared_byte_share": float(source_row["shared_byte_share"]),
            "declared_cross_tile_reduction_cycles": int(source_row["cross_tile_reduction_cycles"]),
            "declared_noc_hops": int(source_row["noc_hops"]),
            "topology": source_row.get("topology"),
            "scheduler_policy": source_row.get("scheduler_policy"),
            "reduction_strategy": source_row.get("reduction_strategy"),
        },
        "traffic_quantities": {
            "full_tile_bytes": full_tile_bytes,
            "shared_tile_payload_bytes": shared_tile_payload_bytes,
            "local_tile_payload_bytes": local_tile_payload_bytes,
            "partial_reduction_payload_bytes": reduction_payload_bytes,
            "cross_tile_reduction_payload_bytes_declared": int(source_row["cross_tile_reduction_payload_bytes"]),
            "tile_count": tile_count,
            "simulated_tiles": min(tile_count, wave_count * active_clusters),
        },
        "mapping": {
            "cluster_endpoints": cluster_endpoints,
            "cluster_endpoint_labels": [_format_endpoint(endpoint) for endpoint in cluster_endpoints],
            "root_endpoint": root_endpoint,
            "root_endpoint_label": _format_endpoint(root_endpoint),
            "shared_sram_home_offset": mapping["offset"],
            "shared_sram_home_stride": mapping["stride"],
            "shared_sram_average_remote_hops": mapping["average_remote_hops"],
            "shared_sram_worst_remote_hops": mapping["worst_remote_hops"],
            "shared_sram_home_load_tiles": mapping["per_home_tile_count"],
        },
        "schedule_parameters": {
            "packet_payload_bytes": packet_payload_bytes,
            "shared_vc": int(args.shared_vc),
            "reduction_vc": int(args.reduction_vc),
            "qkv_cycles_before_wave0": qkv_cycles,
            "tile_attention_cycles_per_wave": tile_attention_cycles,
            "reduction_release_offset_cycles": tile_attention_cycles,
        },
        "simulation": {
            "cycles_to_drain": mesh_result.cycles,
            "scheduled_flit_count": len(scheduled_flits),
            "scheduled_packet_count": sum(
                _ceil_div(flow.payload_bytes, packet_payload_bytes) for flow in flows
            ),
            "endpoint_injected_flit_count": mesh_result.endpoint_injected_flit_count,
            "delivered_flit_count": len(mesh_result.deliveries),
            "router_contention_cycles": router_contention_cycles,
            "max_router_input_occupancy": max_router_input_occupancy,
            "endpoint_input_stall_cycles_total": sum(mesh_result.endpoint_input_stall_cycles),
            "endpoint_input_stall_cycles_by_endpoint": {
                str(index): int(value)
                for index, value in enumerate(mesh_result.endpoint_input_stall_cycles)
                if value
            },
            "remote_shared_average_hops_observed": round(
                sum(remote_shared_hops) / len(remote_shared_hops), 6
            )
            if remote_shared_hops
            else 0.0,
            "remote_shared_worst_hops_observed": max(remote_shared_hops) if remote_shared_hops else 0,
            "remote_reduction_average_hops_observed": round(
                sum(remote_reduction_hops) / len(remote_reduction_hops), 6
            )
            if remote_reduction_hops
            else 0.0,
            "remote_reduction_worst_hops_observed": max(remote_reduction_hops) if remote_reduction_hops else 0,
            "delivery_flit_count_by_class": dict(sorted(delivery_by_prefix.items())),
            "last_delivery_cycle_by_class": dict(sorted(last_delivery_cycle_by_prefix.items())),
            "top_link_flit_counts": [
                {
                    "source": source,
                    "destination": destination,
                    "source_label": _format_endpoint(source),
                    "destination_label": _format_endpoint(destination),
                    "flits": count,
                }
                for (source, destination), count in link_usage.most_common(12)
            ],
        },
        "flow_summary": {
            "remote_shared_flow_count": sum(1 for flow in flows if flow.name.startswith("shared_")),
            "remote_reduction_flow_count": sum(1 for flow in flows if flow.name.startswith("reduction_")),
            "remote_shared_bytes": total_shared_remote_bytes,
            "remote_reduction_bytes": total_reduction_remote_bytes,
            "local_only_shared_bytes": local_only_shared_bytes,
            "local_only_reduction_bytes": local_only_reduction_bytes,
        },
        "measured_l1_profile": measured_profile,
        "explicit_assumptions": [
            "Producer compute, local SRAM access, and local reducer accumulation stay intra-cluster and do not consume the mesh in this Phase 2 schedule.",
            "Only two remote traffic classes are routed: shared SRAM tile payloads and local-reducer-to-root partial reductions.",
            "Tile-to-cluster assignment is static wave-major round robin over the named cluster endpoints.",
            "Shared SRAM homes use a deterministic rotating stride/offset mapping chosen only from explicit 4x4 permutations to approximate the declared hop envelope while keeping load balanced.",
            "The root endpoint is explicit and fixed; root-finalizer output remains local to that endpoint.",
            "Wave start and reduction release times are derived from the checked-in score32 recost quantities qkv_cycles and tile_attention_cycles only.",
            "HBM/DRAM timing is intentionally excluded; no remote traffic or timing claim is made for HBM service.",
            "Each packet carries up to packet_payload_bytes of payload and is segmented into 256-bit flits with no extra header flit modeled.",
        ],
        "remaining_abstractions": [
            "The schedule uses static wave timing from checked-in recost quantities and does not yet prove end-to-end command/control RTL cadence.",
            "Shared SRAM home placement is deterministic and explicit, but still a topology adapter rather than a measured SRAM floorplan.",
            "HBM/DRAM service and controller timing remain intentionally out of scope.",
            "Root-finalizer internal compute is not rerouted here; the mesh model stops at root ingress.",
        ],
    }
    return payload


def write_report(payload: JsonDict, report: Path) -> None:
    lines = [
        "# Llama7B Score32 NoC Phase 2 Schedule",
        "",
        "## Source Contract",
        "",
        f"- source recost: `{payload['source_artifacts']['score32_recost_json']}`",
        f"- measured L1 cost file: `{payload['source_artifacts']['measured_l1_costs_json']}`",
        f"- measured L1 profile: `{payload['source_artifacts']['measured_l1_profile']}`",
        f"- declared waves: `{payload['source_contract']['declared_tile_waves']}`",
        f"- simulated waves: `{payload['source_contract']['simulated_wave_count']}`",
        "",
        "## Mapping",
        "",
        f"- cluster endpoints: `{', '.join(payload['mapping']['cluster_endpoint_labels'])}`",
        f"- root endpoint: `{payload['mapping']['root_endpoint_label']}`",
        f"- shared-SRAM stride/offset: `{payload['mapping']['shared_sram_home_stride']}` / `{payload['mapping']['shared_sram_home_offset']}`",
        f"- shared-SRAM observed average/worst hops: `{payload['mapping']['shared_sram_average_remote_hops']}` / `{payload['mapping']['shared_sram_worst_remote_hops']}`",
        "",
        "## Traffic",
        "",
        f"- full tile bytes: `{payload['traffic_quantities']['full_tile_bytes']}`",
        f"- shared tile bytes: `{payload['traffic_quantities']['shared_tile_payload_bytes']}`",
        f"- local tile bytes: `{payload['traffic_quantities']['local_tile_payload_bytes']}`",
        f"- reduction bytes per cluster-wave: `{payload['traffic_quantities']['partial_reduction_payload_bytes']}`",
        f"- simulated tiles: `{payload['traffic_quantities']['simulated_tiles']}`",
        "",
        "## Routed Result",
        "",
        f"- drain cycles: `{payload['simulation']['cycles_to_drain']}`",
        f"- scheduled flits: `{payload['simulation']['scheduled_flit_count']}`",
        f"- contention cycles: `{payload['simulation']['router_contention_cycles']}`",
        f"- max router input occupancy: `{payload['simulation']['max_router_input_occupancy']}`",
        f"- total endpoint input stall cycles: `{payload['simulation']['endpoint_input_stall_cycles_total']}`",
        "",
        "## Assumptions",
        "",
    ]
    for item in payload["explicit_assumptions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Remaining Abstractions",
            "",
        ]
    )
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-json", type=Path, default=DEFAULT_SOURCE_JSON)
    parser.add_argument("--measured-l1-costs", type=Path, default=DEFAULT_MEASURED_L1_COSTS)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--wave-limit", type=int, default=1)
    parser.add_argument("--packet-payload-bytes", type=int, default=256)
    parser.add_argument("--cluster-endpoints", type=_int_list, default=None)
    parser.add_argument("--root-endpoint", type=int, default=15)
    parser.add_argument("--shared-vc", type=int, default=0)
    parser.add_argument("--reduction-vc", type=int, default=1)
    parser.add_argument("--max-cycles", type=int, default=200000)
    args = parser.parse_args()

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
