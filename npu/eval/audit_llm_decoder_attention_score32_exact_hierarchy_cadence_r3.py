#!/usr/bin/env python3
"""Correct the score32 cadence audit with the R3 GQA8 group-major producer mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_score32_exact_hierarchy_cadence import (
    _build_report as build_v1_report,
)
from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import (
    build_report as build_producer_report,
)

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_hierarchy_cadence_audit_v3"
_REFERENCE_CYCLES = 986
_TOKEN_BLOCKS = 128
_TOKEN_STREAMS = 2
_GQA_GROUPS = 4
_WAVES = 8
_EXPECTED_PROBE = {
    "passed": True,
    "heads": 32,
    "commands": 4,
    "blocks_per_stream": 2,
    "block_counts_per_stream": [2, 1, 1, 1],
    "head_dim": 128,
    "head_bases": [0, 8, 16, 24],
    "outputs": 512,
    "interface_mode": "ideal",
    "integrated_drain_cycles": 1536,
    "result_stall_cycles": 0,
    "llama_wave_reference_cycles": _REFERENCE_CYCLES,
    "llama_wave_drain_delta_vs_986": 550,
}


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _distribution(*, datapaths: int, two_block_datapaths_per_group: int) -> JsonDict:
    one_block_datapaths_per_group = datapaths - two_block_datapaths_per_group
    rotated_two_block_assignments = two_block_datapaths_per_group * _GQA_GROUPS
    return {
        "dual_stream_datapaths": datapaths,
        "group_commands_per_datapath_per_wave": _GQA_GROUPS,
        "two_block_commands_per_stream_per_group": two_block_datapaths_per_group,
        "one_block_commands_per_stream_per_group": one_block_datapaths_per_group,
        "rotated_two_block_assignments_across_4_groups": rotated_two_block_assignments,
        "datapaths_with_one_two_block_command": rotated_two_block_assignments,
        "datapaths_with_zero_two_block_commands": datapaths - rotated_two_block_assignments,
        "worst_loaded_block_counts_per_stream": [2, 1, 1, 1],
    }


def _decision(measured_cycles: int) -> str:
    if measured_cycles > _REFERENCE_CYCLES:
        return "score32_986_cycle_arithmetic_not_sustained_by_corrected_group_command_mapping"
    return "score32_corrected_group_command_mapping_clears_single_wave_producer_but_group_major_reducer_still_open"


def _build_report(args: argparse.Namespace) -> JsonDict:
    base = build_v1_report(args)
    producer_config_path = Path(args.functional_producer_config).resolve()
    producer_config = _load_json(producer_config_path)
    producer = build_producer_report(config=producer_config)

    for key, value in _EXPECTED_PROBE.items():
        if producer.get(key) != value:
            raise ValueError(f"functional producer {key} must be {value!r}, got {producer.get(key)!r}")

    measured_cycles = int(producer["integrated_drain_cycles"])
    delta_cycles = int(producer["llama_wave_drain_delta_vs_986"])
    sustained = measured_cycles <= _REFERENCE_CYCLES
    decision = _decision(measured_cycles)

    mapping = {
        "token_blocks_per_1024_token_tile": _TOKEN_BLOCKS,
        "token_streams_per_producer": _TOKEN_STREAMS,
        "gqa_groups": _GQA_GROUPS,
        "producer_command_contract": "one_gqa8_head_group_for_one_tile_wave_with_1or2_blocks_per_stream",
        "per_datapath_group_commands_per_wave": _GQA_GROUPS,
        "distribution_for_53_datapaths": _distribution(datapaths=53, two_block_datapaths_per_group=11),
        "distribution_for_54_datapaths": _distribution(datapaths=54, two_block_datapaths_per_group=10),
    }

    base["version"] = 3
    base["model"] = _MODEL
    base["decision"] = decision
    base["functional_producer_revision"] = {
        "supersedes": {
            "audit_model": "llm_decoder_attention_score32_exact_hierarchy_cadence_audit_v2",
            "generated_json": "npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v2.json",
            "generated_markdown": "npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v2.md",
            "reason": "R2 modeled five one-block producer commands instead of four group commands with a rotated [2,1,1,1] worst-load schedule.",
        },
        "mapping": mapping,
        "measured_service": {
            key: producer[key]
            for key in (
                "passed",
                "heads",
                "commands",
                "blocks_per_stream",
                "block_counts_per_stream",
                "head_dim",
                "head_bases",
                "outputs",
                "interface_mode",
                "integrated_drain_cycles",
                "result_stall_cycles",
                "llama_wave_reference_cycles",
                "llama_wave_drain_delta_vs_986",
            )
        },
        "interpretation": {
            "reference_986_cycles_sustained": sustained,
            "measured_service_excess_cycles": delta_cycles,
            "measured_service_ratio": round(measured_cycles / _REFERENCE_CYCLES, 6),
            "r2_service_measurement_superseded": True,
            "current_scope": "single_wave_worst_loaded_datapath_functional_producer_only",
            "limitation": (
                "The corrected producer probe still excludes 53/54-way local exact reduction, group-major persistence across eight tile waves, and the final c16 exact reduction."
            ),
            "required_next_measurement": (
                "functional_53_54_way_local_exact_reducer_with_group_major_8_wave_persistence_then_global_c16_exact_reduction"
            ),
        },
        "group_major_reducer_schedule": {
            "tile_waves": _WAVES,
            "gqa_groups": _GQA_GROUPS,
            "schedule_contract": "process_one_fixed_gqa8_group_across_all_8_tile_waves_then_emit_finalize_before_next_head_base",
            "safe_interleave_status": "not_established",
        },
    }
    base["exact_hierarchy_gap"]["required_exact_hierarchy"][
        "functional_producer_block_distribution_per_wave"
    ] = mapping
    base["next_l1_contract"] = {
        "completed_functional_block": "functional_2stream_gqa8_128mac_exact_partial_producer",
        "measured_ideal_service_cycles": measured_cycles,
        "arithmetic_reference_cycles": _REFERENCE_CYCLES,
        "reference_sustained": sustained,
        "next_required_block": "functional_53_54_way_local_exact_reducer_with_group_major_8_wave_persistent_state",
        "group_major_local_schedule_required": True,
        "global_c16_reduction_after_local_aggregation": True,
    }
    base["non_claims"] = [
        "Do not treat the historical R2 five-command producer measurement as current evidence.",
        "Do not promote the 986-cycle tile service point from producer-only evidence.",
        "The 1536-cycle result is ideal-interface functional simulation for one tile wave on the worst-loaded datapath, not PPA or full producer-plus-NoC timing.",
        "No throughput revision is valid until the local reducer, group-major eight-wave persistence, and global c16 path are composed.",
    ]
    base["source_artifacts"]["functional_producer_config_json"] = {
        "path": _portable(producer_config_path),
        "file_sha256": _sha256(producer_config_path),
        "canonical_json_sha256": hashlib.sha256(
            json.dumps(producer_config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    base["source_artifacts"]["functional_producer_probe_py"] = {
        "path": _portable(Path(args.functional_producer_probe)),
        "file_sha256": _sha256(Path(args.functional_producer_probe)),
    }
    base["source_artifacts"]["superseded_audit_json"] = {
        "path": _portable(Path(args.superseded_audit_json)),
        "file_sha256": _sha256(Path(args.superseded_audit_json)),
    }
    return base


def _build_markdown(report: JsonDict) -> str:
    revision = report["functional_producer_revision"]
    mapping = revision["mapping"]
    measured = revision["measured_service"]
    interpretation = revision["interpretation"]
    reducer_schedule = revision["group_major_reducer_schedule"]
    d53 = mapping["distribution_for_53_datapaths"]
    d54 = mapping["distribution_for_54_datapaths"]
    lines = [
        "# Score32 Exact Hierarchy Cadence Audit R3",
        "",
        f"- decision: `{report['decision']}`",
        "- supersedes only the erroneous R2 producer mapping/service conclusion",
        f"- historical arithmetic reference: `{measured['llama_wave_reference_cycles']}` cycles",
        f"- corrected ideal-interface producer service: `{measured['integrated_drain_cycles']}` cycles",
        f"- excess: `+{measured['llama_wave_drain_delta_vs_986']}` cycles",
        "",
        "## Corrected Producer Mapping",
        "",
        f"- token blocks/tile: `{mapping['token_blocks_per_1024_token_tile']}`",
        f"- token streams/producer: `{mapping['token_streams_per_producer']}`",
        f"- GQA8 groups: `{mapping['gqa_groups']}`",
        f"- producer commands/datapath/wave: `{mapping['per_datapath_group_commands_per_wave']}`",
        f"- p53 per group: `{d53['two_block_commands_per_stream_per_group']}` datapaths at 2 blocks/stream, `{d53['one_block_commands_per_stream_per_group']}` at 1",
        f"- p54 per group: `{d54['two_block_commands_per_stream_per_group']}` datapaths at 2 blocks/stream, `{d54['one_block_commands_per_stream_per_group']}` at 1",
        f"- rotated p53 extras across 4 groups: `{d53['datapaths_with_one_two_block_command']}` datapaths get one `2`-block command, `{d53['datapaths_with_zero_two_block_commands']}` get none",
        f"- rotated p54 extras across 4 groups: `{d54['datapaths_with_one_two_block_command']}` datapaths get one `2`-block command, `{d54['datapaths_with_zero_two_block_commands']}` get none",
        f"- worst-loaded per-wave schedule: `{measured['block_counts_per_stream']}`",
        "",
        "One dual-stream producer command covers one GQA8 head group for one tile wave and may aggregate either one or two token blocks per stream. R2's five-command one-block mapping is superseded.",
        "",
        "## Corrected Producer Probe",
        "",
        f"- commands: `{measured['commands']}`",
        f"- head bases: `{measured['head_bases']}`",
        f"- head dimension: `{measured['head_dim']}`",
        f"- exact-partial output beats: `{measured['outputs']}`",
        f"- interface mode: `{measured['interface_mode']}`",
        f"- result stalls: `{measured['result_stall_cycles']}`",
        f"- measured/reference ratio: `{interpretation['measured_service_ratio']}`",
        "",
        "## Group-Major Reducer Schedule",
        "",
        f"- tile waves: `{reducer_schedule['tile_waves']}`",
        f"- schedule: `{reducer_schedule['schedule_contract']}`",
        f"- safe interleave: `{reducer_schedule['safe_interleave_status']}`",
        "",
        "## Non-Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    return "\n".join(lines) + "\n"


def _default(relative: str) -> Path:
    return REPO_ROOT / relative


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-recost-json",
        type=Path,
        default=_default(
            "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
            "decoder_attention_composed_datapath_physical_feasibility__"
            "l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json"
        ),
    )
    parser.add_argument(
        "--wrapper-config",
        type=Path,
        default=_default("runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/config.json"),
    )
    parser.add_argument(
        "--wrapper-metrics",
        type=Path,
        default=_default("runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv"),
    )
    parser.add_argument(
        "--exact-c16-config",
        type=Path,
        default=_default("runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c16_r2_l8_b59/config.json"),
    )
    parser.add_argument(
        "--subtile-pipeline-generator",
        type=Path,
        default=_default("npu/eval/estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py"),
    )
    parser.add_argument(
        "--schedule-wrapper-generator",
        type=Path,
        default=_default("npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py"),
    )
    parser.add_argument(
        "--composed-generator",
        type=Path,
        default=_default("npu/rtlgen/gen_attention_dual_stream_composed.py"),
    )
    parser.add_argument(
        "--exact-c16-generator",
        type=Path,
        default=_default("npu/rtlgen/gen_attention_score32_exact_partial_producer_tree_c16.py"),
    )
    parser.add_argument(
        "--producer-cluster-generator",
        type=Path,
        default=_default("npu/rtlgen/gen_attention_decode_score_multivalue_cluster.py"),
    )
    parser.add_argument(
        "--attention-online-source",
        type=Path,
        default=_default("npu/sim/perf/attention_online.py"),
    )
    parser.add_argument(
        "--functional-producer-config",
        type=Path,
        default=_default(
            "runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/"
            "config_llama_wave_worst4_group_major.json"
        ),
    )
    parser.add_argument(
        "--functional-producer-probe",
        type=Path,
        default=_default("npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py"),
    )
    parser.add_argument(
        "--superseded-audit-json",
        type=Path,
        default=_default("npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v2.json"),
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
