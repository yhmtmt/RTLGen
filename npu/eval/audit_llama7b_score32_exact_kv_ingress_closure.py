#!/usr/bin/env python3
"""Audit the remaining exact K/V ingress gap behind the shared-mesh frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.model_llama7b_shared_sram_residency import (
    LAYER_BALANCED_CONTIGUOUS,
    LOCALITY_AWARE,
    build_residency_report,
)
from npu.sim.perf.attention_kv_tile_layout import (
    BYTES_PER_HEAD_TILE,
    BYTES_PER_KV_TILE,
    FILL_ROW_BYTES,
    FILL_ROWS_PER_HEAD_TILE,
    HEAD_DIM,
    KV_HEADS,
    TILE_TOKENS,
    key_ingress_architecture_service,
    kv_transpose_service,
    kv_token_range_segments,
)
from npu.sim.perf.attention_kv_capacity_gather_scheduler import (
    CONSUME,
    HBM,
    HBM_CORNER_ENDPOINTS,
    REFILL,
    RESIDENT,
    layer_descriptors,
    llama7b_descriptors,
)
from npu.sim.perf.attention_kv_gather_packetizer import (
    FLITS_PER_PACKET,
    PACKET_BYTES,
    full_schedule_packet_summary,
)


JsonDict = dict[str, Any]
MODEL = "llama7b_score32_exact_kv_ingress_closure_audit_v1"
LAYERS = 32
CLUSTERS = 16
WAVES = 8
GROUPS = 4
HISTORICAL_CONTEXT_BYTES = 17_408
HISTORICAL_REMOTE_CONTEXTS = 112
HISTORICAL_LOCAL_CONTEXTS = 16
SHARED_CAPACITY_BYTES = 68 * 1024 * 1024


def _source_ref(path: Path) -> JsonDict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build_report(*, phase2: JsonDict, source_paths: list[Path] | None = None) -> JsonDict:
    if phase2.get("profile") != "decoder_attention_score32_noc_phase2_schedule":
        raise ValueError("unexpected Phase-2 schedule profile")
    flows = phase2.get("flow_summary")
    if not isinstance(flows, dict):
        raise ValueError("Phase-2 schedule is missing flow_summary")
    remote_bytes = int(flows.get("remote_shared_bytes", -1))
    local_bytes = int(flows.get("local_only_shared_bytes", -1))
    if remote_bytes != HISTORICAL_REMOTE_CONTEXTS * HISTORICAL_CONTEXT_BYTES:
        raise ValueError("Phase-2 remote shared bytes differ from the historical fractional policy")
    if local_bytes != HISTORICAL_LOCAL_CONTEXTS * HISTORICAL_CONTEXT_BYTES:
        raise ValueError("Phase-2 local shared bytes differ from the historical fractional policy")

    residency = build_residency_report(
        LAYER_BALANCED_CONTIGUOUS,
        sequence_length=131_072,
        tile_tokens=TILE_TOKENS,
        layers=LAYERS,
        kv_heads=KV_HEADS,
        head_dim=HEAD_DIM,
        kv_bits=8,
        shared_capacity_bytes=SHARED_CAPACITY_BYTES,
    )
    locality_residency = build_residency_report(
        LOCALITY_AWARE,
        sequence_length=131_072,
        tile_tokens=TILE_TOKENS,
        layers=LAYERS,
        kv_heads=KV_HEADS,
        head_dim=HEAD_DIM,
        kv_bits=8,
        shared_capacity_bytes=SHARED_CAPACITY_BYTES,
    )
    resident_per_layer = int(residency["residency"]["resident_bytes"]) // LAYERS
    layer_kv_bytes = (131_072 // TILE_TOKENS) * BYTES_PER_KV_TILE
    value_commands = CLUSTERS * WAVES * GROUPS
    value_fill_bytes = value_commands * BYTES_PER_HEAD_TILE
    if layer_kv_bytes != 2 * value_fill_bytes:
        raise AssertionError("exact K/V and cluster V-fill byte conservation failed")
    if remote_bytes + local_bytes != resident_per_layer:
        raise AssertionError("historical fractional bytes must equal the capacity share per layer")
    full_tile_segments = kv_token_range_segments(token_start=0, token_count=TILE_TOKENS)
    tail_segments = kv_token_range_segments(token_start=0, token_count=128)
    value_transpose = kv_transpose_service(tensor="v")
    key_transpose = kv_transpose_service(tensor="k")
    key_architectures = {
        name: key_ingress_architecture_service(architecture=name)
        for name in (
            "one_buffer_serial",
            "pingpong_serial",
            "one_buffer_wide",
            "pingpong_wide_auto",
        )
    }
    gather_layer = layer_descriptors(0)
    gather_full = llama7b_descriptors()
    refill_descriptors = [row for row in gather_layer if row.operation == REFILL]
    consume_descriptors = [row for row in gather_layer if row.operation == CONSUME]
    resident_consume = [row for row in consume_descriptors if row.source == RESIDENT]
    direct_hbm_consume = [row for row in consume_descriptors if row.source == HBM]
    hbm_source = [row for row in gather_layer if row.source == HBM]
    consume_bytes_by_cluster = {
        cluster: sum(
            row.payload_bytes
            for row in consume_descriptors
            if row.destination_cluster == cluster
        )
        for cluster in range(CLUSTERS)
    }
    if sum(row.payload_bytes for row in refill_descriptors) != resident_per_layer:
        raise AssertionError("gather refill bytes differ from transient resident capacity")
    if sum(row.payload_bytes for row in resident_consume) != resident_per_layer:
        raise AssertionError("resident consume bytes differ from resident capacity")
    if sum(row.payload_bytes for row in direct_hbm_consume) != layer_kv_bytes - resident_per_layer:
        raise AssertionError("direct HBM bytes differ from the unresident K/V range")
    if sum(row.payload_bytes for row in hbm_source) != layer_kv_bytes:
        raise AssertionError("transient refill plus direct HBM bytes must cover the layer")
    if set(consume_bytes_by_cluster.values()) != {layer_kv_bytes // CLUSTERS}:
        raise AssertionError("locality-aware tile ownership is not cluster balanced")
    packet_summary = full_schedule_packet_summary()
    if packet_summary["hbm_source_packet_count"] * PACKET_BYTES != (
        LAYERS * layer_kv_bytes
    ):
        raise AssertionError("packetized HBM bytes differ from the complete model K/V")
    if packet_summary["canonical_consume_packet_count"] * PACKET_BYTES != (
        LAYERS * layer_kv_bytes
    ):
        raise AssertionError("packetized canonical consume bytes differ from complete K/V")

    whole_contexts = residency["residency"]["context_payload_distribution"]
    return {
        "version": 1,
        "model": MODEL,
        "decision": "historical_fractional_vc0_cannot_serve_as_exact_cluster_fill_contract",
        "source_refs": [_source_ref(path) for path in source_paths or []],
        "llama7b_layer_shape": {
            "sequence_length": 131_072,
            "tile_tokens": TILE_TOKENS,
            "tiles": 128,
            "kv_heads": KV_HEADS,
            "head_dim": HEAD_DIM,
            "kv_bits": 8,
            "kv_tile_bytes": BYTES_PER_KV_TILE,
            "layer_kv_bytes": layer_kv_bytes,
            "layer_k_bytes": value_fill_bytes,
            "layer_v_bytes": value_fill_bytes,
        },
        "cluster_consumption": {
            "clusters": CLUSTERS,
            "waves": WAVES,
            "head_groups": GROUPS,
            "value_fill_commands": value_commands,
            "value_bytes_per_command": BYTES_PER_HEAD_TILE,
            "value_rows_per_command": FILL_ROWS_PER_HEAD_TILE,
            "value_row_bytes": FILL_ROW_BYTES,
            "total_value_fill_rows": value_commands * FILL_ROWS_PER_HEAD_TILE,
            "total_value_fill_bytes": value_fill_bytes,
            "key_stream_bytes": value_fill_bytes,
        },
        "capacity_driven_residency": {
            "scope": (
                "transient resident cache; exact source descriptors are included, while "
                "HBM-return packetization and routing remain on-chip ingress obligations"
            ),
            "shared_capacity_bytes": SHARED_CAPACITY_BYTES,
            "resident_bytes_per_layer": resident_per_layer,
            "resident_share_of_layer_kv": resident_per_layer / layer_kv_bytes,
            "whole_context_payload_distribution_all_layers": whole_contexts,
            "exact_planar_gather_segments_per_layer": (
                2 * len(full_tile_segments) + len(tail_segments)
            ),
            "full_tile_contiguous_segments": len(full_tile_segments),
            "tail_128_token_contiguous_segments": len(tail_segments),
            "tail_segment_bytes": [segment.payload_bytes for segment in tail_segments],
            "unresident_hbm_return_bytes_per_layer": layer_kv_bytes - resident_per_layer,
            "transient_refill_bytes_per_layer": resident_per_layer,
            "total_hbm_read_bytes_per_layer": layer_kv_bytes,
            "placement_options": {
                "remote_balanced_contiguous": {
                    "remote_transport_bytes_per_layer": int(
                        residency["transport"]["remote_transport_bytes"]
                    )
                    // LAYERS,
                    "local_resident_bytes_per_layer": int(
                        residency["transport"]["local_resident_bytes"]
                    )
                    // LAYERS,
                },
                "locality_aware_owner_compute": {
                    "remote_transport_bytes_per_layer": int(
                        locality_residency["transport"]["remote_transport_bytes"]
                    )
                    // LAYERS,
                    "local_resident_bytes_per_layer": int(
                        locality_residency["transport"]["local_resident_bytes"]
                    )
                    // LAYERS,
                    "scheduler_requirement": (
                        "assign each cached independent attention tile to its home cluster"
                    ),
                    "does_not_include": "transient HBM-return transport",
                },
            },
            "recommended_onchip_baseline": "locality_aware_owner_compute",
        },
        "capacity_hbm_gather_scheduler": {
            "persistence_mode": "transient",
            "descriptor_granularity": "contiguous canonical byte span",
            "descriptors_per_layer": len(gather_layer),
            "refill_descriptors_per_layer": len(refill_descriptors),
            "consume_descriptors_per_layer": len(consume_descriptors),
            "full_model_descriptors": len(gather_full),
            "resident_refill_bytes_per_layer": sum(
                row.payload_bytes for row in refill_descriptors
            ),
            "resident_consume_bytes_per_layer": sum(
                row.payload_bytes for row in resident_consume
            ),
            "direct_hbm_consume_bytes_per_layer": sum(
                row.payload_bytes for row in direct_hbm_consume
            ),
            "total_hbm_source_bytes_per_layer": sum(
                row.payload_bytes for row in hbm_source
            ),
            "total_canonical_consume_bytes_per_layer": sum(
                row.payload_bytes for row in consume_descriptors
            ),
            "consume_bytes_per_cluster": consume_bytes_by_cluster,
            "hbm_source_endpoints": list(HBM_CORNER_ENDPOINTS),
            "owner_cluster_rule": "(layer*3+tile)%16",
            "partial_tile_policy": (
                "eight ordered planes, each consuming a 16KiB resident prefix followed "
                "by a 112KiB direct-HBM suffix"
            ),
            "ready_valid_stall_stability_verified": True,
            "python_rtl_descriptor_equivalence_verified": True,
            "packet_expansion": {
                "packet_bytes": PACKET_BYTES,
                "flits_per_packet": FLITS_PER_PACKET,
                **packet_summary,
                "maximum_packets_per_span": BYTES_PER_KV_TILE // PACKET_BYTES,
                "representative_rtl_packets_verified": 4608,
                "maximum_span_terminal_index_verified": True,
            },
            "does_not_include": [
                "HBM controller or PHY",
                "multi-source packet dispatch",
                "shared-mesh transport",
                "canonical K/V payload movement",
            ],
        },
        "historical_phase2_vc0": {
            "policy": "fractional_smear",
            "context_bytes": HISTORICAL_CONTEXT_BYTES,
            "remote_contexts": HISTORICAL_REMOTE_CONTEXTS,
            "local_contexts": HISTORICAL_LOCAL_CONTEXTS,
            "remote_transport_bytes": remote_bytes,
            "local_resident_bytes": local_bytes,
            "represented_resident_bytes": remote_bytes + local_bytes,
            "exact_tensor_address_metadata": False,
            "direct_cluster_fill_compatible": False,
            "accounting_role": "resident-capacity traffic bound only",
        },
        "port_gap": {
            "vc0_write_bits": 256,
            "cluster_fill_bits": 512,
            "payload_equivalent_vc0_flits_per_value_fill_row": 2,
            "consecutive_flits_form_one_value_fill_row": False,
            "value_transpose_extent_bytes": 1024,
            "key_paired_stream_transpose_extent_bytes": 2048,
            "current_max_packets_per_context": 68,
            "current_max_context_bytes": HISTORICAL_CONTEXT_BYTES,
            "whole_kv_tile_packets_256B": BYTES_PER_KV_TILE // 256,
            "partial_128KiB_packets_256B": BYTES_PER_HEAD_TILE // 256,
            "missing_metadata": [
                "tensor_kind_k_or_v",
                "kv_head",
                "tile_index",
                "token_in_tile",
                "dimension",
                "valid_payload_bytes_for_partial_context",
            ],
            "historical_single_base_plus_offset_cannot_represent_partial_planar_range": True,
        },
        "canonical_layout": {
            "tile_byte_order": "K[kv_head][token][dimension] then V[kv_head][token][dimension]",
            "resident_range_mapping": (
                "a full 1024-token tile is contiguous; a 128-token tail requires eight "
                "strided 16KiB gather spans, one from each K/V head plane"
            ),
            "value_fill_mapping": (
                "stream=token//512; block_slot=(token%512)//8; "
                "slice=dimension//8; byte=(token%8)*8+(dimension%8)"
            ),
            "value_reorder_requirement": (
                "one 1024-byte token-major block maps to sixteen 64-byte fill rows; "
                "a sequential 256-bit flit contributes to four rows, so two consecutive "
                "flits do not form one row"
            ),
            "key_mapping": (
                "block_slot=(token%512)//8; invert the corrected per-group p53/p54 slot bases; "
                "for each dimension, the 128-bit beat packs eight stream-0 and eight "
                "stream-1 token bytes"
            ),
            "key_reorder_requirement": (
                "pair one 1024-byte block from each stream and transpose the 16 by 128 "
                "byte matrix into 128 producer beats"
            ),
        },
        "one_buffer_transpose_reference": {
            "overlap": False,
            "value": {
                "input_flits": value_transpose.input_flits,
                "output_rows": value_transpose.output_beats,
                "transfer_cycles_without_stall": value_transpose.transfer_cycles_without_stall,
                "minimum_target_ii_cycles": value_transpose.minimum_target_ii_cycles,
            },
            "key": {
                "input_flits": key_transpose.input_flits,
                "output_beats": key_transpose.output_beats,
                "transfer_cycles_without_stall": key_transpose.transfer_cycles_without_stall,
                "minimum_target_ii_cycles": key_transpose.minimum_target_ii_cycles,
            },
            "key_output_role": (
                "serial writes into the embodied 64-bank producer-local K staging store"
            ),
            "not_a_cluster_throughput_claim": True,
        },
        "key_ingress_architecture_frontier": {
            name: {
                "transpose_buffers": service.transpose_buffers,
                "stage_write_bits": service.stage_write_bits,
                "target_from_first_flit": service.target_from_first_flit,
                "head_cycles_without_stall": service.head_cycles_without_stall,
                "ingress_floor_cycles": service.ingress_floor_cycles,
                "rtl_verified": name in {"one_buffer_serial", "pingpong_wide_auto"},
            }
            for name, service in key_architectures.items()
        },
        "implementation_status": {
            "embodied_rtl": [
                "canonical planar address and byte-valid K/V block transposer",
                "64-bank 128KiB K staging store",
                "1KiB shared Q group store and duplicate-stream broadcast",
                "per-lane p53/p54 producer pending-mask scheduler",
                "canonical K flit through producer-output composition",
                "automatic-target ping-pong K transpose with paired-dimension bank writes",
                "canonical V flit through 16-bank double-buffer cluster-SRAM residency",
                "capacity-driven transient-refill and direct-HBM gather descriptor scheduler",
                "locality-aware balanced tile-to-cluster ownership",
                "four-corner HBM source selection and exact canonical span addresses",
                "256-byte span packetization through the 4,096-packet full-tile boundary",
            ],
            "verified_counts": {
                "canonical_k_input_flits_per_head": 4096,
                "producer_output_beats_per_head": 8192,
                "pingpong_k_head_cycles_without_stall": 4160,
                "consecutive_pingpong_k_input_flits": 4096,
                "canonical_v_input_flits_per_head": 4096,
                "cluster_sram_v_rows_per_head": 2048,
                "gather_descriptors_per_layer": len(gather_layer),
                "gather_descriptors_full_model": len(gather_full),
                "gather_hbm_source_bytes_per_layer": sum(
                    row.payload_bytes for row in hbm_source
                ),
                "gather_consume_bytes_per_cluster": layer_kv_bytes // CLUSTERS,
                "gather_packets_full_model": packet_summary["packet_count"],
                "gather_hbm_packets_full_model": packet_summary[
                    "hbm_source_packet_count"
                ],
            },
            "remaining_before_frontier_recost": [
                "multi-source shared-mesh dispatch and canonical-ingress payload routing",
                "V transpose ping-pong or proven fill-drain overlap",
                "characterized SRAM macro substitution",
            ],
        },
        "required_rtl_ownership": [
            "external HBM-return ready/valid ingress boundary, excluding controller and PHY",
            "multi-source packet dispatch and on-chip routing for HBM-return K/V bytes",
            "composition of capacity/HBM source descriptors with canonical K/V payload ingress",
            "backpressure from cluster SRAM and producers through ingress and mesh",
            "overlapped V transpose buffering selected from measured PPA",
            "physical cost of ping-pong K transpose and paired-dimension write control",
            "characterized SRAM macro substitution for inferred K/Q and cluster stores",
        ],
        "revision_effect": {
            "shared_mesh_15769_cycle_result_role": "standalone_historical_traffic_capacity_bound_only",
            "release_coupled_vc1_role": "exact_reduction_transport_timing_with_vc0_ingress_still_open",
            "frontier_recost_allowed": False,
            "reason": (
                "Exact K/V endpoint paths, capacity/HBM source descriptors, and packetization "
                "are embodied, but shared-mesh payload composition, overlap selection, and "
                "physical memory "
                "costs are not yet closed for the complete score32 cluster path."
            ),
        },
        "next_gate": (
            "Dispatch exact gather packets through shared-mesh source routing into "
            "canonical K/V ingress and verify end-to-end backpressure; then measure V buffering "
            "parallelism and substitute characterized SRAM macros."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    shape = report["llama7b_layer_shape"]
    resident = report["capacity_driven_residency"]
    historical = report["historical_phase2_vc0"]
    cluster = report["cluster_consumption"]
    transpose = report["one_buffer_transpose_reference"]
    key_frontier = report["key_ingress_architecture_frontier"]
    gather = report["capacity_hbm_gather_scheduler"]
    packets = gather["packet_expansion"]
    lines = [
        "# Llama7B Exact K/V Ingress Closure Audit",
        "",
        f"- decision: `{report['decision']}`",
        f"- complete layer K/V: `{shape['layer_kv_bytes']}` bytes",
        f"- exact cluster V fills: `{cluster['total_value_fill_bytes']}` bytes",
        f"- exact cluster K stream: `{cluster['key_stream_bytes']}` bytes",
        f"- capacity-driven resident share per layer: `{resident['resident_bytes_per_layer']}` bytes",
        f"- historical remote VC0 bytes: `{historical['remote_transport_bytes']}` bytes",
        "",
        "The historical VC0 quantity matches a capacity share in aggregate, but its fractional-smear "
        "contexts do not identify exact K/V tensor bytes and cannot be wired directly to cluster fill.",
        "",
        "## One-Buffer Transpose Reference",
        "",
        f"- V block: `{transpose['value']['transfer_cycles_without_stall']}` transfer cycles, "
        f"target II `{transpose['value']['minimum_target_ii_cycles']}`",
        f"- paired-stream K block: `{transpose['key']['transfer_cycles_without_stall']}` transfer cycles, "
        f"target II `{transpose['key']['minimum_target_ii_cycles']}`",
        "- K output writes the embodied 64-bank store; p53/p54 parallel readout is verified",
        "",
        "## K Ingress Architecture Frontier",
        "",
        *[
            f"- {name}: `{row['head_cycles_without_stall']}` cycles/head, "
            f"{row['transpose_buffers']} buffer(s), {row['stage_write_bits']}-bit stage write, "
            f"RTL verified `{str(row['rtl_verified']).lower()}`"
            for name, row in key_frontier.items()
        ],
        "",
        "## Capacity/HBM Gather Scheduler",
        "",
        f"- persistence: `{gather['persistence_mode']}`",
        f"- descriptors: `{gather['descriptors_per_layer']}` per layer, "
        f"`{gather['full_model_descriptors']}` over 32 layers",
        f"- HBM source bytes per layer: `{gather['total_hbm_source_bytes_per_layer']}`",
        f"- canonical bytes delivered per layer: "
        f"`{gather['total_canonical_consume_bytes_per_layer']}`",
        f"- balanced delivery: `{next(iter(gather['consume_bytes_per_cluster'].values()))}` "
        "bytes per cluster",
        "- Python/RTL descriptors and ready-valid stall stability: verified",
        f"- exact packet expansion: `{packets['packet_count']}` commands, "
        f"`{packets['flits_per_packet']}` flits each",
        f"- maximum span: `{packets['maximum_packets_per_span']}` packets, terminal index verified",
        "",
        "## Required RTL Ownership",
        "",
        *[f"- {item}" for item in report["required_rtl_ownership"]],
        "",
        "## Next Gate",
        "",
        report["next_gate"],
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase2", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)
    phase2 = json.loads(args.phase2.read_text(encoding="utf-8"))
    report = build_report(phase2=phase2, source_paths=args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
