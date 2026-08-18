#!/usr/bin/env python3
"""Revise Phase-2 reduction traffic from the embodied exact RTL contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

DEFAULT_EXACT_MANIFEST = Path(
    "runs/designs/npu_blocks/"
    "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_"
    "p54x8_p53x8_c16_r2_l8_b59/verilog/"
    "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json"
)
DEFAULT_PRIOR_SCHEDULE = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)

INVALIDATED_ITEM_IDS = [
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1",
    "l1_noc_llama7b_phase2_command_scheduler_v1",
    "l2_decoder_attention_score32_noc_phase2_generated_scheduler_equivalence_llama7b_v1",
    "l2_decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost_llama7b_v1",
    "l2_decoder_attention_score32_finite_endpoint_final_frontier_llama7b_v1",
]


def _load(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _mode(
    *,
    name: str,
    bits_per_group: int,
    groups: int,
    remote_clusters: int,
    flit_bits: int,
    packet_flits: int,
    shared_packets: int,
    shared_flits: int,
) -> JsonDict:
    flits_per_group = _ceil_div(bits_per_group, flit_bits)
    packets_per_group = _ceil_div(flits_per_group, packet_flits)
    flits_per_cluster = flits_per_group * groups
    packets_per_cluster = packets_per_group * groups
    reduction_flits = flits_per_cluster * remote_clusters
    reduction_packets = packets_per_cluster * remote_clusters
    return {
        "name": name,
        "bits_per_group": bits_per_group,
        "flits_per_group": flits_per_group,
        "packets_per_group": packets_per_group,
        "flits_per_cluster_layer": flits_per_cluster,
        "packets_per_cluster_layer": packets_per_cluster,
        "remote_reduction_flits": reduction_flits,
        "remote_reduction_packets": reduction_packets,
        "total_phase2_flits": shared_flits + reduction_flits,
        "total_phase2_commands": shared_packets + reduction_packets,
    }


def build_report(*, exact_manifest: Path, prior_schedule: Path) -> JsonDict:
    manifest = _load(exact_manifest)
    prior = _load(prior_schedule)
    service = manifest.get("service_model")
    if not isinstance(service, dict):
        raise ValueError("exact manifest lacks service_model")

    expected = {
        "clusters": 16,
        "partial_link_bits_per_beat": 419,
        "partial_payload_bits_per_beat": 328,
    }
    for key, value in expected.items():
        if int(service.get(key, -1)) != value:
            raise ValueError(
                f"exact manifest {key} mismatch: expected {value}, observed {service.get(key)!r}"
            )
    if "group_major" not in str(service.get("command_wave_contract", "")):
        raise ValueError("exact manifest does not declare group-major wave scheduling")

    source = prior["source_contract"]
    simulation = prior["simulation"]
    flows = prior["flow_summary"]
    traffic = prior["traffic_quantities"]
    if int(source["attention_heads"]) != 32 or int(source["hidden_size"]) != 4096:
        raise ValueError("prior schedule is not the checked Llama7B 32-head/4096-hidden point")
    if int(source["declared_tile_waves"]) != 8:
        raise ValueError("prior schedule does not contain eight tile waves")
    if int(traffic["partial_reduction_payload_bytes"]) != 8320:
        raise ValueError("prior schedule no longer contains the invalidated 8320-byte reduction")

    clusters = int(service["clusters"])
    remote_clusters = clusters - 1
    groups = 4
    heads_per_group = 8
    slices_per_head = 16
    beats_per_group = heads_per_group * slices_per_head
    link_bits = int(service["partial_link_bits_per_beat"])
    value_bits = int(service["partial_payload_bits_per_beat"])
    stats_bits = 32 + 33
    flit_bits = 256
    packet_flits = 8
    shared_packets = int(flows["remote_shared_packet_count"])
    shared_flits = int(simulation["delivery_flit_count_by_class"]["shared"])

    aligned_bits_per_group = beats_per_group * _ceil_div(link_bits, flit_bits) * flit_bits
    packed_bits_per_group = beats_per_group * link_bits
    stats_once_bits_per_group = heads_per_group * (
        stats_bits + slices_per_head * value_bits
    )
    modes = [
        _mode(
            name="aligned_419b_two_flits_per_beat",
            bits_per_group=aligned_bits_per_group,
            groups=groups,
            remote_clusters=remote_clusters,
            flit_bits=flit_bits,
            packet_flits=packet_flits,
            shared_packets=shared_packets,
            shared_flits=shared_flits,
        ),
        _mode(
            name="packed_419b_group_bitstream",
            bits_per_group=packed_bits_per_group,
            groups=groups,
            remote_clusters=remote_clusters,
            flit_bits=flit_bits,
            packet_flits=packet_flits,
            shared_packets=shared_packets,
            shared_flits=shared_flits,
        ),
        _mode(
            name="stats_once_ordered_exact",
            bits_per_group=stats_once_bits_per_group,
            groups=groups,
            remote_clusters=remote_clusters,
            flit_bits=flit_bits,
            packet_flits=packet_flits,
            shared_packets=shared_packets,
            shared_flits=shared_flits,
        ),
    ]
    for mode in modes:
        mode["flit_reduction_vs_prior"] = (
            int(simulation["scheduled_flit_count"]) - int(mode["total_phase2_flits"])
        )
        mode["flit_ratio_vs_prior"] = round(
            int(mode["total_phase2_flits"]) / int(simulation["scheduled_flit_count"]),
            6,
        )

    return {
        "version": 1,
        "profile": "decoder_attention_score32_noc_phase2_exact_transport_revision",
        "decision": "prior_phase2_reduction_contract_retracted_exact_transport_required",
        "revision": {
            "reason": "wrong_precision_and_release_contract",
            "invalidates_item_ids": INVALIDATED_ITEM_IDS,
            "invalidates": {
                "prior_schedule": str(prior_schedule),
                "prior_partial_reduction_payload_bytes": int(
                    traffic["partial_reduction_payload_bytes"]
                ),
                "prior_reduction_release": "once_per_cluster_per_tile_wave",
            },
        },
        "exact_source": {
            "manifest": str(exact_manifest),
            "clusters": clusters,
            "head_groups": groups,
            "heads_per_group": heads_per_group,
            "persistent_local_waves_per_group": 8,
            "slices_per_head": slices_per_head,
            "aggregate_beats_per_group_per_cluster": beats_per_group,
            "partial_link_bits_per_beat": link_bits,
            "partial_payload_bits_per_beat": value_bits,
            "stats_bits_per_head": stats_bits,
            "release_contract": "one aggregate stream per head group after eight local waves",
        },
        "prior_quantities": {
            "scheduled_commands": int(simulation["scheduled_packet_count"]),
            "scheduled_flits": int(simulation["scheduled_flit_count"]),
            "remote_shared_packets": shared_packets,
            "remote_shared_flits": shared_flits,
            "remote_reduction_packets": int(flows["remote_reduction_packet_count"]),
            "remote_reduction_flits": int(
                simulation["delivery_flit_count_by_class"]["reduction"]
            ),
        },
        "exact_transport_modes": modes,
        "recommended_first_implementation": "aligned_419b_two_flits_per_beat",
        "recommended_frontier_candidate": "stats_once_ordered_exact",
        "recommendation": (
            "Implement aligned transport as the direct field-preserving equivalence anchor, "
            "then implement stats-once ordered packing and compare codec PPA plus actual "
            "producer/root backpressure before rebuilding the Phase-2 command schedule."
        ),
        "remaining_abstractions": [
            "Mode quantities do not yet include measured serializer/depacketizer PPA.",
            "Command release must be driven by actual local-reducer valid/ready events.",
            "Shared-tile traffic still requires SRAM-residency-driven release.",
            "HBM/DRAM control remains external by design.",
        ],
    }


def write_markdown(report: JsonDict, path: Path) -> None:
    prior = report["prior_quantities"]
    lines = [
        "# Llama7B Phase-2 Exact Transport Revision",
        "",
        f"- decision: `{report['decision']}`",
        f"- prior commands/flits: `{prior['scheduled_commands']}` / `{prior['scheduled_flits']}`",
        "- exact release: one aggregate stream per head group after eight local waves",
        "",
        "| Mode | Commands | Flits | Ratio vs prior | Reduction packets/cluster |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in report["exact_transport_modes"]:
        lines.append(
            f"| `{mode['name']}` | {mode['total_phase2_commands']} | "
            f"{mode['total_phase2_flits']} | {mode['flit_ratio_vs_prior']:.3f} | "
            f"{mode['packets_per_cluster_layer']} |"
        )
    lines.extend(["", "## Recommendation", "", report["recommendation"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-manifest", type=Path, default=DEFAULT_EXACT_MANIFEST)
    parser.add_argument("--prior-schedule", type=Path, default=DEFAULT_PRIOR_SCHEDULE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        exact_manifest=args.exact_manifest,
        prior_schedule=args.prior_schedule,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.report)
    print(json.dumps({"decision": payload["decision"], "modes": payload["exact_transport_modes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
