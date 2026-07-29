from argparse import Namespace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from npu.eval.audit_llm_decoder_attention_score32_exact_reduction_recost import build_report


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _inputs(tmp_path: Path) -> Namespace:
    source_recost_json = tmp_path / "schedule_wrapper_recost.json"
    banked_config = tmp_path / "banked_config.json"
    _write(
        source_recost_json,
        {
            "diagnosis": {"decision": "dual_stream_feasible"},
            "best_requested": {
                "substituted_compute_arch": "attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2",
                "substituted_compute_variant_kind": "dual_stream_schedule_wrapper",
                "substituted_compute_semantic_profile": "score32_exp_lut_div",
                "replica_recost_area_fit_replica_count": 428,
                "replica_recost_compute_area_um2": 296797456.0,
                "replica_recost_compute_power_mw": 25979.6,
                "measured_dual_stream_composed_power_mw": 60.7,
                "replica_recost_macs_per_cycle": 109568,
                "base_cross_tile_reduction_cycles": 141,
                "base_cross_tile_local_cycles": 48,
                "base_cross_tile_noc_cycles": 64,
                "base_cross_tile_vector_cycles": 29,
                "cross_tile_reduction_cycles": 141,
                "replica_recost_layer_cycles": 8231,
                "layer_cycles": 8231,
                "replica_recost_total_cycles": 263392,
                "total_cycles": 263392,
                "layers": 32,
                "tile_waves": 8,
                "replica_recost_tile_service_cycles": 986,
                "tile_service_cycles": 986,
                "replica_recost_qkv_cycles": 192,
                "kv_write_cycles": 10,
                "replica_recost_clock_ns": 48.6509,
                "replica_recost_latency_us": 12814.257853,
                "adjusted_latency_us_if_feasible": 12814.257853,
                "latency_us": 1575.373891,
                "source_latency_us": 2138.84136,
                "unconstrained_latency_us": 2133.67369,
                "replica_recost_latency_slowdown_vs_source": 8.134106,
                "adjusted_speedup_if_feasible": 0.16691105989405908,
                "token_throughput_per_s": 78.038371946117,
            },
        },
    )
    _write(
        banked_config,
        {
            "top_name": "attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59",
            "attention_score32_exact_banked_finalized_tree": {
                "clusters": 16,
                "radix": 2,
                "value_slices": 16,
                "head_id_bits": 5,
                "divider_lanes": 8,
                "finalizer_banks": 59,
            },
        },
    )
    return Namespace(source_recost_json=source_recost_json, banked_config=banked_config)


def test_exact_reduction_recost_corrects_schedule_wrapper_contract(tmp_path: Path) -> None:
    report = build_report(_inputs(tmp_path))
    best = report["best_requested"]

    assert report["decision"] == "score32_exact_reduction_schedule_recost_recorded"
    assert report["source_contract"]["cross_tile_reduction_cycles"] == 141
    assert report["source_revision"]["source_item_id"] == (
        "l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1"
    )
    assert report["source_revision"]["source_best_requested_preserved"] is True
    assert report["source_revision"]["source_best_requested_field_count"] == len(report["source_best_requested"])
    assert report["source_revision"]["source_only_latency_fields_preserved"] == [
        "latency_us",
        "source_latency_us",
        "unconstrained_latency_us",
    ]
    assert report["source_revision"]["overridden_best_requested_fields"] == [
        "cross_tile_reduction_cycles",
        "replica_recost_layer_cycles",
        "layer_cycles",
        "replica_recost_total_cycles",
        "total_cycles",
        "replica_recost_latency_us",
        "adjusted_latency_us_if_feasible",
        "replica_recost_latency_slowdown_vs_source",
        "adjusted_speedup_if_feasible",
        "token_throughput_per_s",
        "base_cross_tile_reduction_cycles",
    ]
    assert report["source_revision"]["added_best_requested_fields"] == [
        "exact_reduction_replaces_legacy_component_breakdown"
    ]
    assert report["source_revision"]["legacy_component_breakdown_revision"] == {
        "source_base_cross_tile_reduction_cycles": 141,
        "replacement_base_cross_tile_reduction_cycles": 574,
        "historical_source_diagnostics": {
            "base_cross_tile_local_cycles": 48,
            "base_cross_tile_noc_cycles": 64,
            "base_cross_tile_vector_cycles": 29,
        },
    }
    assert report["source_best_requested"]["replica_recost_compute_area_um2"] == 296797456.0
    assert report["source_best_requested"]["replica_recost_compute_power_mw"] == 25979.6
    assert report["source_best_requested"]["measured_dual_stream_composed_power_mw"] == 60.7
    assert report["source_best_requested"]["adjusted_latency_us_if_feasible"] == 12814.257853
    assert report["corrected_contract"]["heads"] == 32
    assert report["corrected_contract"]["cross_tile_reduction_cycles"] == 574
    assert report["corrected_contract"]["base_cross_tile_reduction_cycles"] == 574
    assert report["corrected_contract"]["replica_recost_layer_cycles"] == 8664
    assert report["corrected_contract"]["replica_recost_total_cycles"] == 277248
    assert report["corrected_contract"]["replica_recost_latency_us"] == 13488.364723
    assert report["corrected_contract"]["adjusted_latency_us_if_feasible"] == 13488.364723
    assert report["corrected_contract"]["replica_recost_latency_slowdown_vs_source"] == pytest.approx(
        13488.364723 / 1575.373891
    )
    assert report["corrected_contract"]["adjusted_speedup_if_feasible"] == pytest.approx(
        2138.84136 / 13488.364723
    )
    assert report["corrected_contract"]["token_throughput_per_s"] == pytest.approx(74.137971543343)
    assert report["corrected_contract"]["exact_reduction_replaces_legacy_component_breakdown"] is True
    assert report["service_contract_provenance"]["service"]["first_output_cycle"] == 62
    assert report["service_contract_provenance"]["service"]["last_output_cycle"] == 573
    assert report["service_contract_provenance"]["service"]["drain_cycles"] == 574
    assert report["service_contract_provenance"]["service"]["interval_cycles"] == 511
    assert report["service_contract_provenance"]["service"]["cycles_per_beat"] == pytest.approx(1.0)
    assert report["service_contract_provenance"]["service"]["dispatch_stall_cycles"] == 0
    assert report["service_contract_provenance"]["service"]["divider_iterations_per_group"] == 57
    assert report["service_contract_provenance"]["service"]["per_bank_output_latency_cycles"] == 58
    assert report["service_contract_provenance"]["service"]["per_bank_accept_interval_cycles"] == 59
    assert report["service_contract_provenance"]["recorded_exact_output_hash"] == (
        "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"
    )
    assert "--finalizer-banks 59 --saturated --root-ready-pattern 1 --json" in (
        report["service_contract_provenance"]["recorded_probe_command"]
    )
    assert best["replica_recost_compute_area_um2"] == 296797456.0
    assert best["replica_recost_compute_power_mw"] == 25979.6
    assert best["measured_dual_stream_composed_power_mw"] == 60.7
    assert best["replica_recost_area_fit_replica_count"] == 428
    assert best["replica_recost_macs_per_cycle"] == 109568
    assert best["latency_us"] == 1575.373891
    assert best["source_latency_us"] == 2138.84136
    assert best["unconstrained_latency_us"] == 2133.67369
    assert best["base_cross_tile_local_cycles"] == 48
    assert best["base_cross_tile_noc_cycles"] == 64
    assert best["base_cross_tile_vector_cycles"] == 29
    assert best["base_cross_tile_reduction_cycles"] == 574
    assert best["cross_tile_reduction_cycles"] == 574
    assert best["replica_recost_layer_cycles"] == 8664
    assert best["layer_cycles"] == 8664
    assert best["replica_recost_total_cycles"] == 277248
    assert best["total_cycles"] == 277248
    assert best["replica_recost_latency_us"] == 13488.364723
    assert best["adjusted_latency_us_if_feasible"] == 13488.364723
    assert best["replica_recost_latency_slowdown_vs_source"] == pytest.approx(13488.364723 / 1575.373891)
    assert best["adjusted_speedup_if_feasible"] == pytest.approx(2138.84136 / 13488.364723)
    assert best["token_throughput_per_s"] == pytest.approx(74.137971543343)
    assert best["exact_reduction_replaces_legacy_component_breakdown"] is True
    assert report["delta_vs_source"]["base_cross_tile_reduction_cycles"] == 433
    assert report["delta_vs_source"]["cross_tile_reduction_cycles"] == 433
    assert report["delta_vs_source"]["replica_recost_layer_cycles"] == 433
    assert report["delta_vs_source"]["replica_recost_total_cycles"] == 13856
    assert report["delta_vs_source"]["adjusted_latency_us_if_feasible"] == pytest.approx(674.10687)
    assert report["delta_vs_source"]["replica_recost_latency_slowdown_vs_source"] == pytest.approx(
        (13488.364723 / 1575.373891) - 8.134106
    )
    assert report["delta_vs_source"]["adjusted_speedup_if_feasible"] == pytest.approx(
        (2138.84136 / 13488.364723) - 0.16691105989405908
    )
    assert report["delta_vs_source"]["token_throughput_per_s"] == pytest.approx(74.137971543343 - 78.038371946117)
    assert report["remaining_abstractions"] == [
        "Exact reducer PPA remains unclosed; this recost changes schedule cycles only.",
        "Exact reducer activity energy remains unclosed; no reduction toggle-energy closure is claimed here.",
        "328-bit exact transport, NoC, and SRAM composition remain unclosed.",
        "Producer arrival timing and overlap with the reducer are not embodied here; adding the 574-cycle drain after tile waves is a conservative serialized-stage schedule.",
    ]


def test_exact_reduction_recost_rejects_non_b59_config(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.banked_config.read_text(encoding="utf-8"))
    payload["attention_score32_exact_banked_finalized_tree"]["finalizer_banks"] = 58
    _write(args.banked_config, payload)

    with pytest.raises(ValueError, match="banked config finalizer_banks must be 59"):
        build_report(args)


def test_exact_reduction_recost_rejects_mismatched_source_contract(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.source_recost_json.read_text(encoding="utf-8"))
    payload["best_requested"]["cross_tile_reduction_cycles"] = 140
    _write(args.source_recost_json, payload)

    with pytest.raises(ValueError, match="source reduction cycles must be 141"):
        build_report(args)


def test_exact_reduction_recost_rejects_non_finite_source_values(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.source_recost_json.read_text(encoding="utf-8"))
    payload["best_requested"]["replica_recost_clock_ns"] = "nan"
    _write(args.source_recost_json, payload)

    with pytest.raises(ValueError, match="source replica_recost_clock_ns must be a finite number"):
        build_report(args)


def test_exact_reduction_recost_direct_script_runs_without_pythonpath(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    out = tmp_path / "report.json"
    out_md = tmp_path / "report.md"

    completed = subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_llm_decoder_attention_score32_exact_reduction_recost.py",
            "--source-recost-json",
            str(args.source_recost_json),
            "--banked-config",
            str(args.banked_config),
            "--out",
            str(out),
            "--out-md",
            str(out_md),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["model"] == "llm_decoder_attention_score32_exact_reduction_recost_v1"
