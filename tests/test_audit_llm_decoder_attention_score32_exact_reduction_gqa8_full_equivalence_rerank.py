from argparse import Namespace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from npu.eval.audit_llm_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank import build_report


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _equivalence_payload(*, logical_head_groups: int, source_links: dict | None = None) -> dict:
    totals = {
        1: {
            "producer_handshake_count": 1_048_576,
            "fill_target_accept_count": 128,
            "fill_row_accept_count": 262144,
            "sram_request_accept_count": 262144,
            "sram_response_accept_count": 262144,
            "cluster_row_count": 2048,
            "root_row_count": 128,
            "command_accept_count": 8,
            "cadence_command_accept_count": 8,
        },
        4: {
            "producer_handshake_count": 4_194_304,
            "fill_target_accept_count": 512,
            "fill_row_accept_count": 1048576,
            "sram_request_accept_count": 1048576,
            "sram_response_accept_count": 1048576,
            "cluster_row_count": 8192,
            "root_row_count": 512,
            "command_accept_count": 32,
            "cadence_command_accept_count": 32,
        },
    }[logical_head_groups]
    per_cluster = {
        1: {
            "wave_command_accept_count": 8,
            "completed_command_count": 1,
            "emitted_beat_count": 128,
            "fill_target_accept_count": 8,
            "fill_row_accept_count": 16384,
            "request_accept_count": 16384,
            "response_accept_count": 16384,
            "command_accept_count": 8,
            "command_release_count": 8,
        },
        4: {
            "wave_command_accept_count": 32,
            "completed_command_count": 4,
            "emitted_beat_count": 512,
            "fill_target_accept_count": 32,
            "fill_row_accept_count": 65536,
            "request_accept_count": 65536,
            "response_accept_count": 65536,
            "command_accept_count": 32,
            "command_release_count": 32,
        },
    }[logical_head_groups]
    command_ids = [0x8200] if logical_head_groups == 1 else [0x8200, 0x8201, 0x8202, 0x8203]
    head_bases = [0] if logical_head_groups == 1 else [0, 8, 16, 24]
    return {
        "passed": True,
        "classification": "passed",
        "counts_passed": True,
        "simulation_status": "ok",
        "normalized_returncode": 0,
        "logical_head_groups": logical_head_groups,
        "head_dimension": 128,
        "score_accumulation_beats_per_block": 128,
        "head_bases": head_bases,
        "command_ids": command_ids,
        "summary": {**totals, "protocol_error": 0},
        "cluster_summaries": [
            {"cluster": cluster, **per_cluster, "errors": 0}
            for cluster in range(16)
        ],
        "compositional_components": {
            "strict_generated_top_guard": "passed",
            "producer_replay_parallelism": 1,
            "global_sidecar": {
                "value_packing": "canonical_pack_numerators",
                "numerator_bits": 41,
                "numerator_lanes": 8,
                "row_bits": 419,
                "value_offset": 91,
            }
        },
        "full_row_audit": {
            "passed": True,
            "clusters": [{"passed": True} for _ in range(16)],
            "root": {"passed": True},
        },
        **({"source_links": source_links} if source_links is not None else {}),
    }


def _inputs(tmp_path: Path) -> Namespace:
    args = Namespace(
        exact_reduction_json=tmp_path / "exact_reduction.json",
        quality_aware_frontier_json=tmp_path / "frontier.json",
        one_group_equivalence_json=tmp_path / "one_group.json",
        four_group_equivalence_json=tmp_path / "four_group.json",
    )
    _write(
        args.exact_reduction_json,
        {
            "model": "llm_decoder_attention_score32_exact_reduction_recost_v1",
            "decision": "score32_exact_reduction_schedule_recost_recorded",
            "source_contract": {
                "cross_tile_reduction_cycles": 141,
                "replica_recost_latency_us": 12814.257853,
                "token_throughput_per_s": 78.038073798,
            },
            "corrected_contract": {
                "cross_tile_reduction_cycles": 574,
                "replica_recost_latency_us": 13488.364723,
                "token_throughput_per_s": 74.137971543343,
            },
            "best_requested": {
                "cross_tile_reduction_cycles": 574,
                "exact_reduction_replaces_legacy_component_breakdown": True,
            },
            "delta_vs_source": {
                "replica_recost_latency_us": 674.10687,
            },
            "remaining_abstractions": [
                "Exact reducer PPA remains unclosed; this recost changes schedule cycles only."
            ],
        },
    )
    _write(
        args.quality_aware_frontier_json,
        {
            "model": "llm_decoder_attention_score32_integrated_frontier_ranking_v1",
            "decision": "score32_integrated_frontier_best_precision_safe_throughput",
            "diagnosis": {
                "best_precision_safe_candidate": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
                "current_recommended_candidate": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
                "mixed_int8_quality_status": "quality_invalidated_low_precision_score_softmax",
                "score32_quality_status": "mixed_int8_generation_quality_pass",
            },
            "rows": [
                {
                    "candidate_id": "physical_hbm_gqa8_kv8_service_frontier",
                    "family": "abstract_integrated_gqa8_kv8",
                    "latency_us": 30.944,
                    "token_throughput_per_s": 32316.442605997934,
                    "energy_mj_per_token": 8.14357724928343,
                    "compute_energy_mj_per_token": 0.0,
                    "hbm_energy_mj_per_token": 0.0,
                    "die_area_mm2": 100.0,
                    "compute_area_mm2": 0.0,
                    "precision_status": "planning_only_native_gqa8_kv8",
                    "promotable": False,
                    "quality_backed": False,
                    "remaining_abstractions": ["abstract_compute_capacity"],
                    "source_artifact": "integrated_energy_closure_r2",
                },
                {
                    "candidate_id": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
                    "family": "score32_exp_lut_div",
                    "latency_us": 12814.257853,
                    "token_throughput_per_s": 78.038073798,
                    "energy_mj_per_token": 467.191305313106,
                    "compute_energy_mj_per_token": 332.910690072106,
                    "hbm_energy_mj_per_token": 134.280615241,
                    "die_area_mm2": 800.0,
                    "compute_area_mm2": 296.8263662009,
                    "macs_per_cycle": 109568.0,
                    "precision_status": "mixed_int8_generation_quality_pass",
                    "promotable": True,
                    "quality_backed": True,
                    "remaining_abstractions": [
                        "HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.",
                        "does not include vendor HBM current signoff",
                    ],
                    "source_artifact": "score32_schedule_wrapper_hbm_controller_replay",
                    "score32_hbm_controller_replay_ppa": {
                        "controller_energy_mj_per_token": 0.001396754106,
                        "controller_power_mw": 0.109,
                    },
                },
                {
                    "candidate_id": "die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512",
                    "family": "measured_exact_fp16_gqa8_kv8",
                    "latency_us": 72544.06213406654,
                    "token_throughput_per_s": 13.784725731954872,
                    "energy_mj_per_token": 81.66413005453946,
                    "compute_energy_mj_per_token": 18.095420734855,
                    "hbm_energy_mj_per_token": 63.520046663430314,
                    "die_area_mm2": 1200.0,
                    "compute_area_mm2": 479.60213,
                    "macs_per_cycle": 132736.0,
                    "precision_status": "conservative_native_gqa8_kv8",
                    "promotable": True,
                    "quality_backed": True,
                    "remaining_abstractions": ["source_backed_aggregate_hbm_energy_not_vendor_current_signoff"],
                    "source_artifact": "measured_compute_energy_closure",
                },
            ],
        },
    )
    _write(
        args.one_group_equivalence_json,
        _equivalence_payload(
            logical_head_groups=1,
            source_links={
                "proposal_id": "prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1",
                "proposal_path": "docs/proposals/prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1/proposal.json",
                "item_id": "l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r8",
            },
        ),
    )
    _write(
        args.four_group_equivalence_json,
        _equivalence_payload(
            logical_head_groups=4,
            source_links={
                "proposal_id": "prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1",
                "proposal_path": "docs/proposals/prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1/proposal.json",
                "item_id": "l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r2",
            },
        ),
    )
    return args


def test_exact_reduction_full_gqa8_rerank_recosts_score32_row_and_preserves_rank_dimensions(tmp_path: Path) -> None:
    report = build_report(_inputs(tmp_path))

    assert report["decision"] == "score32_exact_reduction_gqa8_full_equivalence_frontier_recorded"
    score32_row = next(row for row in report["rows"] if row["family"] == "score32_exp_lut_div")
    assert score32_row["latency_us"] == 13488.364723
    assert score32_row["token_throughput_per_s"] == 74.137971543343
    assert score32_row["compute_energy_mj_per_token_lower_bound"] == 332.910690072106
    assert score32_row["compute_energy_mj_per_token_conservative_upper_bound"] == 350.423790389618
    assert score32_row["compute_energy_mj_per_token"] == 350.423790389618
    assert score32_row["energy_mj_per_token_lower_bound"] == 467.191305313106
    assert score32_row["energy_mj_per_token_conservative_upper_bound"] == 484.704405630618
    assert score32_row["energy_mj_per_token"] == 484.704405630618
    assert score32_row["energy_estimate_status"] == "conservative_upper_bound_latency_scaled_non_hbm_energy"
    assert score32_row["exact_reduction_recost"]["source_reduction_cycles"] == 141
    assert score32_row["exact_reduction_recost"]["corrected_reduction_cycles"] == 574
    assert (
        score32_row["exact_reduction_recost"]["source_total_energy_mj_per_token_lower_bound"] == 467.191305313106
    )
    assert (
        score32_row["exact_reduction_recost"]["total_energy_mj_per_token_conservative_upper_bound"]
        == 484.704405630618
    )
    assert report["diagnosis"]["best_precision_safe_candidate"] == (
        "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
    )
    assert report["diagnosis"]["best_precision_safe_energy_candidate"] == (
        "die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512"
    )
    assert report["diagnosis"]["score32_vs_measured_fp16_throughput_ratio"] == 5.378269614
    assert report["diagnosis"]["score32_vs_measured_fp16_energy_ratio"] == 5.935340342
    assert report["diagnosis"]["score32_total_energy_mj_per_token_lower_bound"] == 467.191305313106
    assert report["diagnosis"]["score32_energy_estimate_status"] == (
        "conservative_upper_bound_latency_scaled_non_hbm_energy"
    )
    assert report["diagnosis"]["exact_energy_ranking_status"] == (
        "provisional_pending_reducer_and_global_tree_activity_power_measurement"
    )
    assert report["equivalence_prerequisites"]["one_group"]["source_links"]["item_id"] == (
        "l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r8"
    )


def test_exact_reduction_full_gqa8_rerank_rejects_frontier_latency_mismatch(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.quality_aware_frontier_json.read_text(encoding="utf-8"))
    payload["rows"][1]["latency_us"] = 12815.0
    _write(args.quality_aware_frontier_json, payload)

    with pytest.raises(ValueError, match="frontier score32 latency must be"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_failed_four_group_equivalence(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.four_group_equivalence_json.read_text(encoding="utf-8"))
    payload["passed"] = False
    _write(args.four_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="four-group equivalence must pass"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_legacy_one_dimension_evidence(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.one_group_equivalence_json.read_text(encoding="utf-8"))
    payload["head_dimension"] = 1
    payload["score_accumulation_beats_per_block"] = 1
    payload["summary"]["producer_handshake_count"] = 8192
    _write(args.one_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="one-group head_dimension must be 128"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_requires_explicit_head_dimension_contract(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.four_group_equivalence_json.read_text(encoding="utf-8"))
    del payload["head_dimension"]
    _write(args.four_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="four-group head_dimension must be a finite number"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_missing_r8_one_group_artifact(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    args.one_group_equivalence_json = tmp_path / "missing_r8.json"

    with pytest.raises(FileNotFoundError):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_noncanonical_global_packing(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.four_group_equivalence_json.read_text(encoding="utf-8"))
    payload["compositional_components"]["global_sidecar"]["row_bits"] = 418
    _write(args.four_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="four-group global_sidecar row_bits must be 419"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_requires_serial_producer_replay(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.one_group_equivalence_json.read_text(encoding="utf-8"))
    del payload["compositional_components"]["producer_replay_parallelism"]
    _write(args.one_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="one-group producer_replay_parallelism must be a finite number"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_protocol_summary_or_full_row_failures(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.one_group_equivalence_json.read_text(encoding="utf-8"))
    payload["summary"]["protocol_error"] = 1
    _write(args.one_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="one-group summary protocol_error must be 0"):
        build_report(args)

    args = _inputs(tmp_path)
    payload = json.loads(args.four_group_equivalence_json.read_text(encoding="utf-8"))
    payload["full_row_audit"]["clusters"][3]["passed"] = False
    _write(args.four_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="four-group full_row_audit cluster 3 must pass"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_rejects_source_link_identity_mismatch(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.one_group_equivalence_json.read_text(encoding="utf-8"))
    payload["source_links"]["proposal_id"] = "wrong_proposal"
    _write(args.one_group_equivalence_json, payload)

    with pytest.raises(ValueError, match="one-group source_links proposal_id must be"):
        build_report(args)


def test_exact_reduction_full_gqa8_rerank_direct_script_reaches_argument_handling_without_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_llm_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank.py",
            "--help",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout
