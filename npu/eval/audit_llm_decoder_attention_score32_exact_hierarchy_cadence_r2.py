#!/usr/bin/env python3
"""Revise the score32 cadence audit with functional GQA8 producer evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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

_MODEL = "llm_decoder_attention_score32_exact_hierarchy_cadence_audit_v2"
_DECISION = "score32_986_cycle_arithmetic_not_sustained_by_functional_exact_producer"
_TOKEN_BLOCKS = 128
_GQA_GROUPS = 4
_TOKEN_STREAMS = 2
_PAIRED_TOKEN_BLOCKS = _TOKEN_BLOCKS // _TOKEN_STREAMS
_PAIRED_GQA_JOBS = _PAIRED_TOKEN_BLOCKS * _GQA_GROUPS
_REFERENCE_CYCLES = 986
_MEASURED_CYCLES = 1681


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


def _job_distribution(datapaths: int) -> JsonDict:
    jobs_per_datapath = _PAIRED_GQA_JOBS // datapaths
    extra_jobs = _PAIRED_GQA_JOBS % datapaths
    return {
        "datapaths": datapaths,
        "paired_gqa_jobs": _PAIRED_GQA_JOBS,
        "datapaths_with_5_jobs": extra_jobs,
        "datapaths_with_4_jobs": datapaths - extra_jobs,
        "worst_loaded_commands": math.ceil(_PAIRED_GQA_JOBS / datapaths),
    }


def _build_report(args: argparse.Namespace) -> JsonDict:
    base = build_v1_report(args)
    producer_config_path = Path(args.functional_producer_config).resolve()
    producer_config = _load_json(producer_config_path)
    producer = build_producer_report(config=producer_config)

    expected = {
        "passed": True,
        "heads": 32,
        "commands": 5,
        "blocks_per_stream": 1,
        "head_dim": 128,
        "head_bases": [0, 8, 16, 24, 0],
        "outputs": 640,
        "interface_mode": "ideal",
        "integrated_drain_cycles": _MEASURED_CYCLES,
        "result_stall_cycles": 0,
        "llama_wave_reference_cycles": _REFERENCE_CYCLES,
        "llama_wave_drain_delta_vs_986": _MEASURED_CYCLES - _REFERENCE_CYCLES,
    }
    for key, value in expected.items():
        if producer.get(key) != value:
            raise ValueError(f"functional producer {key} must be {value!r}, got {producer.get(key)!r}")

    distribution_53 = _job_distribution(53)
    distribution_54 = _job_distribution(54)
    if distribution_53["datapaths_with_5_jobs"] != 44 or distribution_54["datapaths_with_5_jobs"] != 40:
        raise ValueError("unexpected paired GQA job distribution")

    base["version"] = 2
    base["model"] = _MODEL
    base["decision"] = _DECISION
    base["functional_producer_revision"] = {
        "mapping": {
            "token_blocks_per_1024_token_tile": _TOKEN_BLOCKS,
            "token_streams_per_producer": _TOKEN_STREAMS,
            "paired_token_blocks": _PAIRED_TOKEN_BLOCKS,
            "gqa_groups": _GQA_GROUPS,
            "paired_gqa_jobs_per_wave": _PAIRED_GQA_JOBS,
            "distribution_for_53_datapaths": distribution_53,
            "distribution_for_54_datapaths": distribution_54,
            "producer_command_contract": "one_paired_token_block_times_one_gqa8_head_group",
            "producer_blocks_per_stream_per_command": 1,
        },
        "measured_service": {
            key: producer[key]
            for key in (
                "passed",
                "heads",
                "commands",
                "blocks_per_stream",
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
            "reference_986_cycles_sustained": False,
            "measured_service_excess_cycles": _MEASURED_CYCLES - _REFERENCE_CYCLES,
            "measured_service_ratio": round(_MEASURED_CYCLES / _REFERENCE_CYCLES, 6),
            "limitation": (
                "ideal external interfaces remove injected stalls, but the five-command functional "
                "producer still serializes input and exact-partial output service"
            ),
            "required_next_measurement": (
                "functional 53/54-way local exact reducer with persistent state across eight waves"
            ),
        },
    }
    base["exact_hierarchy_gap"]["required_exact_hierarchy"][
        "functional_producer_block_distribution_per_wave"
    ] = base["functional_producer_revision"]["mapping"]
    base["next_l1_contract"] = {
        "completed_functional_block": "functional_2stream_gqa8_128mac_exact_partial_producer",
        "measured_ideal_service_cycles": _MEASURED_CYCLES,
        "arithmetic_reference_cycles": _REFERENCE_CYCLES,
        "reference_sustained": False,
        "next_required_block": "functional_53_54_way_local_exact_reducer_with_8_wave_persistent_state",
        "global_c16_reduction_after_local_aggregation": True,
    }
    base["non_claims"] = [
        "Do not promote the 986-cycle tile service point.",
        "The 1681-cycle result is ideal-interface functional simulation, not PPA or full producer-plus-NoC timing.",
        "No throughput revision is valid until the local reducer, persistent eight-wave state, and global c16 path are composed.",
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
    return base


def _build_markdown(report: JsonDict) -> str:
    revision = report["functional_producer_revision"]
    mapping = revision["mapping"]
    measured = revision["measured_service"]
    interpretation = revision["interpretation"]
    d53 = mapping["distribution_for_53_datapaths"]
    d54 = mapping["distribution_for_54_datapaths"]
    lines = [
        "# Score32 Exact Hierarchy Cadence Audit R2",
        "",
        f"- decision: `{report['decision']}`",
        f"- historical arithmetic reference: `{measured['llama_wave_reference_cycles']}` cycles",
        f"- functional ideal-interface service: `{measured['integrated_drain_cycles']}` cycles",
        f"- excess: `+{measured['llama_wave_drain_delta_vs_986']}` cycles",
        "",
        "## Corrected Mapping",
        "",
        f"- token blocks/tile: `{mapping['token_blocks_per_1024_token_tile']}`",
        f"- paired token blocks: `{mapping['paired_token_blocks']}`",
        f"- GQA8 groups: `{mapping['gqa_groups']}`",
        f"- paired GQA jobs/wave: `{mapping['paired_gqa_jobs_per_wave']}`",
        f"- 53 datapaths: `{d53['datapaths_with_5_jobs']}` carry 5 jobs, `{d53['datapaths_with_4_jobs']}` carry 4",
        f"- 54 datapaths: `{d54['datapaths_with_5_jobs']}` carry 5 jobs, `{d54['datapaths_with_4_jobs']}` carry 4",
        "",
        "A producer command covers one paired token block for one GQA8 head group. The prior stream-level "
        "1/2-block assignment did not account for all four GQA groups and is superseded by this mapping.",
        "",
        "## Functional Evidence",
        "",
        f"- commands on the worst-loaded datapath: `{measured['commands']}`",
        f"- head bases: `{measured['head_bases']}`",
        f"- head dimension: `{measured['head_dim']}`",
        f"- exact-partial output beats: `{measured['outputs']}`",
        f"- interface mode: `{measured['interface_mode']}`",
        f"- result stalls: `{measured['result_stall_cycles']}`",
        f"- measured/reference ratio: `{interpretation['measured_service_ratio']}`",
        "",
        "The functional producer does not sustain the 986-cycle arithmetic point even with ideal external "
        "interfaces. The current frontier must remain unpromoted.",
        "",
        "## Next Measurement",
        "",
        "- functional 53/54-way local exact reduction",
        "- persistent local exact state across eight waves",
        "- one global c16 exact reduction after local aggregation",
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
            "config_llama_wave.json"
        ),
    )
    parser.add_argument(
        "--functional-producer-probe",
        type=Path,
        default=_default("npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py"),
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
