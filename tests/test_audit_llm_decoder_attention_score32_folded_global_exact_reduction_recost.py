from argparse import Namespace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_score32_folded_global_exact_reduction_recost import (
    build_report,
)


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        superseded_recost_json=REPO_ROOT
        / "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_recost__l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json",
        cadence_audit_json=REPO_ROOT / "npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v3.json",
        tree_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/config.json",
        tree_metrics=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/metrics.csv",
        root_finalizer_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l8/config.json",
        root_finalizer_metrics=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l8/metrics.csv",
        bank_control_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/config.json",
        bank_control_metrics=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/metrics.csv",
        producer_config=REPO_ROOT
        / "runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config.json",
        producer_probe_script=REPO_ROOT
        / "npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py",
        exact_partial_module=REPO_ROOT / "npu/sim/perf/attention_exact_partial.py",
        out=tmp_path / "report.json",
        out_md=tmp_path / "report.md",
    )


def test_folded_global_exact_reduction_recost_records_bounded_analysis(tmp_path: Path) -> None:
    report = build_report(_args(tmp_path))

    assert report["model"] == "llm_decoder_attention_score32_folded_global_exact_reduction_recost_v2"
    assert report["decision"] == "folded_global_exact_reduction_bounded_recost_recorded"
    assert report["quality_rerun_required"] is False
    assert report["supersession"]["superseded_source_item_id"] == (
        "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1"
    )
    assert report["supersession"]["superseded_timing_contract"] == {
        "cross_tile_reduction_cycles": 574,
        "replica_recost_tile_service_cycles": 986,
        "tile_service_cycles": 986,
    }

    cadence = report["cadence_evidence"]
    assert cadence["worst_loaded_single_datapath_wave_cycles"] == 1536
    assert cadence["worst_loaded_block_counts_per_stream"] == [2, 1, 1, 1]
    assert cadence["safe_interleave_status"] == "not_established"
    assert cadence["reference_986_cycles_sustained"] is False

    producer = report["producer_command_service_evidence"]
    assert producer["one_block_command_drain_cycles"] == 337
    assert producer["two_block_command_drain_cycles"] == 528
    assert producer["conservative_cluster_barrier_per_group_cycles"] == 4224
    assert producer["distinguished_from_single_datapath_worst_wave_cycles"] == 1536

    tree = report["global_folded_tree_service"]
    assert tree["root_beats"] == 128
    assert tree["first_root_output_cycle"] == 80
    assert tree["last_root_output_cycle"] == 2620
    assert tree["drain_cycle"] == 2620
    assert tree["root_output_initiation_interval_cycles"] == 20

    finalizer = report["finalizer_contract"]
    assert finalizer["minimum_banks_for_tree_ii"] == 3
    assert finalizer["measured_bank_control_banks"] == 4
    assert finalizer["per_bank_output_latency_cycles"] == 58
    assert finalizer["per_bank_accept_interval_cycles"] == 59
    assert finalizer["same_bank_revisit_cycles_with_b4"] == 80
    assert finalizer["composed_global_final_output_drain_cycles"] == 2678

    ppa = report["measured_component_ppa_estimate"]["composed_global_exact_reduction_path"]
    assert ppa["estimated_critical_path_ns"] == 7.9837
    assert ppa["estimated_stdcell_area_um2"] == pytest.approx(892551.77)
    assert ppa["estimated_stdcell_count"] == 514339
    assert ppa["estimated_total_power_mw"] == pytest.approx(4.20296)

    bounds = report["bounded_schedule_analysis"]
    assert bounds["strict_serialized_bound_per_group_cycles"] == 6902
    assert bounds["strict_serialized_bound_all_4_groups_cycles"] == 27608
    assert bounds["conditional_overlap_margin_cycles"] == 1546
    assert bounds["conditional_overlap_lower_bound_status"] == "not_established"

    decision = report["decision_summary"]
    assert decision["global_folded_tree_finalizer_physically_plausible"] is True
    assert decision["necessarily_throughput_dominant"] is False
    assert decision["do_not_start_global_tree_before_local_group_aggregate"] is True


def test_folded_global_exact_reduction_recost_script_runs_without_pythonpath(tmp_path: Path) -> None:
    args = _args(tmp_path)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_llm_decoder_attention_score32_folded_global_exact_reduction_recost.py",
            "--superseded-recost-json",
            str(args.superseded_recost_json),
            "--cadence-audit-json",
            str(args.cadence_audit_json),
            "--tree-config",
            str(args.tree_config),
            "--tree-metrics",
            str(args.tree_metrics),
            "--root-finalizer-config",
            str(args.root_finalizer_config),
            "--root-finalizer-metrics",
            str(args.root_finalizer_metrics),
            "--bank-control-config",
            str(args.bank_control_config),
            "--bank-control-metrics",
            str(args.bank_control_metrics),
            "--producer-config",
            str(args.producer_config),
            "--producer-probe-script",
            str(args.producer_probe_script),
            "--exact-partial-module",
            str(args.exact_partial_module),
            "--out",
            str(args.out),
            "--out-md",
            str(args.out_md),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.stdout == ""
    payload = json.loads(args.out.read_text(encoding="utf-8"))
    assert payload["summary"]["strict_serialized_bound_all_4_groups_cycles"] == 27608
    markdown = args.out_md.read_text(encoding="utf-8")
    assert "strict serialized bound: `6902` cycles per group, `27608` cycles for 4 groups" in markdown
    assert "Do not start the global folded tree before the local 53/54-way group-major reducer emits valid per-cluster group aggregates." in markdown
