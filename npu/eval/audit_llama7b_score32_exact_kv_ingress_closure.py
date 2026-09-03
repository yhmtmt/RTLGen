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
    kv_transpose_service,
    kv_token_range_segments,
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
                "resident_cache_bytes_only; transient HBM-return routing is excluded "
                "and remains an on-chip ingress obligation"
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
        "implementation_status": {
            "embodied_rtl": [
                "canonical planar address and byte-valid K/V block transposer",
                "64-bank 128KiB K staging store",
                "1KiB shared Q group store and duplicate-stream broadcast",
                "per-lane p53/p54 producer pending-mask scheduler",
                "canonical K flit through producer-output composition",
            ],
            "verified_counts": {
                "canonical_k_input_flits_per_head": 4096,
                "producer_output_beats_per_head": 8192,
            },
            "remaining_before_frontier_recost": [
                "V transpose to cluster fill and residency composition",
                "capacity-resident and transient-HBM gather descriptor scheduler",
                "multiple transpose buffers or proven fill-drain overlap",
                "characterized SRAM macro substitution",
            ],
        },
        "required_rtl_ownership": [
            "external HBM-return ready/valid ingress boundary, excluding controller and PHY",
            "capacity-driven resident-range descriptor and source selection",
            "planar gather descriptor generation for partial resident token ranges",
            "locality-aware tile-to-cluster scheduler preserving balanced waves",
            "on-chip packet routing for remote resident K/V bytes",
            "capacity/HBM source descriptor to canonical K/V tensor-address ingress",
            "1KiB token-major-to-fill-row V transpose buffer and assembler",
            "V transpose output to exact cluster-SRAM fill composition",
            "per-cluster V fill target, double-buffer residency, and command release",
            "backpressure from cluster SRAM and producers through ingress and mesh",
            "overlapped or multi-lane K/V transpose buffering selected from measured PPA",
            "characterized SRAM macro substitution for inferred K/Q and cluster stores",
        ],
        "revision_effect": {
            "shared_mesh_15769_cycle_result_role": "standalone_historical_traffic_capacity_bound_only",
            "release_coupled_vc1_role": "exact_reduction_transport_timing_with_vc0_ingress_still_open",
            "frontier_recost_allowed": False,
            "reason": (
                "Neither historical fractional VC0 bytes nor the external synthetic fill plane proves "
                "the complete exact K/V data path consumed by the score32 clusters."
            ),
        },
        "next_gate": (
            "Compose the embodied V transposer with exact cluster-SRAM fill, then implement the "
            "capacity-driven resident/HBM gather scheduler and measure K/V buffering parallelism."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    shape = report["llama7b_layer_shape"]
    resident = report["capacity_driven_residency"]
    historical = report["historical_phase2_vc0"]
    cluster = report["cluster_consumption"]
    transpose = report["one_buffer_transpose_reference"]
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
