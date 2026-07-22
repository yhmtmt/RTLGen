#!/usr/bin/env python3
"""Tests for the multivalue-cluster activity power frontier audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest import mock

from npu.eval import audit_attention_decode_score_multivalue_cluster_activity_power as audit


def _write_metrics(path: Path) -> None:
    fields = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "instance_area_um2",
        "params_json",
    ]
    rows = [
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p10",
            "tag": "die2500",
            "status": "ok",
            "critical_path_ns": "7.0",
            "die_area": "6250000",
            "instance_area_um2": "3000000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 10, "FLOW_VARIANT": "cluster_die2500"}
            ),
        },
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p8a",
            "tag": "die2500",
            "status": "ok",
            "critical_path_ns": "7.5",
            "die_area": "6250000",
            "instance_area_um2": "3100000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 8, "FLOW_VARIANT": "cluster_die2500"}
            ),
        },
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p8b",
            "tag": "die3000",
            "status": "ok",
            "critical_path_ns": "8.1",
            "die_area": "9000000",
            "instance_area_um2": "3050000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 8, "FLOW_VARIANT": "cluster_die3000"}
            ),
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_metrics_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "instance_area_um2",
        "params_json",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_feasible_metrics_selects_exact_clock_and_timing(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    rows = audit._feasible_metrics(metrics, 8.0)
    assert [audit._params(row)["FLOW_VARIANT"] for row in rows] == ["cluster_die2500"]


def test_feasible_metrics_excludes_non_matching_onehot_rows(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p1",
                "tag": "onehot",
                "status": "ok",
                "critical_path_ns": "7.2",
                "die_area": "6100000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_onehot_fsm_v3_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p2",
                "tag": "binary",
                "status": "ok",
                "critical_path_ns": "7.4",
                "die_area": "6000000",
                "instance_area_um2": "3020000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v2_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
        ],
    )
    try:
        audit._feasible_metrics(
            metrics,
            8.0,
            required_flow_variant=(
                "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
            ),
            required_synth_args="-nofsm",
        )
    except ValueError as exc:
        assert "FLOW_VARIANT=decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500" in str(
            exc
        )
    else:
        raise AssertionError("one-hot row mismatch was not rejected")


def test_feasible_metrics_rejects_wrong_synth_args(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p1",
                "tag": "binary",
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6000000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
                        "SYNTH_ARGS": "-fsm",
                    }
                ),
            },
        ],
    )
    try:
        audit._feasible_metrics(
            metrics,
            8.0,
            required_flow_variant=(
                "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
            ),
            required_synth_args="-nofsm",
        )
    except ValueError as exc:
        assert "SYNTH_ARGS=-nofsm" in str(exc)
    else:
        raise AssertionError("wrong synth args was not rejected")


def test_feasible_metrics_accepts_exact_binary_row_with_strict_contract(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p1",
                "tag": "binary",
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6000000",
                "instance_area_um2": "3050000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p2",
                "tag": "other",
                "status": "ok",
                "critical_path_ns": "7.2",
                "die_area": "6100000",
                "instance_area_um2": "3060000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v2_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
        ],
    )
    rows = audit._feasible_metrics(
        metrics,
        8.0,
        required_flow_variant="decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
        required_synth_args="-nofsm",
    )
    assert [audit._params(row)["FLOW_VARIANT"] for row in rows] == [
        "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
    ]


def test_feasible_metrics_rejects_v14_nofsm_and_base_fallback_for_targeted_contract(
    tmp_path: Path,
) -> None:
    metrics = tmp_path / "metrics.csv"
    targeted = "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
    rows = []
    for param_hash, flow_variant, synth_args in (
        ("targeted-nofsm", targeted, "-nofsm"),
        (
            "v14",
            "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4_proxy_die_2500",
            "",
        ),
        ("base", "decode_score_multivalue_cluster_v1_8ns_proxy_die_2500", ""),
    ):
        rows.append(
            {
                "design": "cluster",
                "platform": "nangate45",
                "config_hash": "config-targeted",
                "param_hash": param_hash,
                "tag": param_hash,
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6250000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": flow_variant,
                        "SYNTH_ARGS": synth_args,
                    }
                ),
            }
        )
    _write_metrics_rows(metrics, rows)

    try:
        audit._feasible_metrics(
            metrics,
            8.0,
            required_flow_variant=targeted,
            required_synth_args="",
        )
    except ValueError as exc:
        assert "SYNTH_ARGS=<empty/default>" in str(exc)
    else:
        raise AssertionError("v14, -nofsm, or base fallback row was accepted")


def _targeted_diagnostic(*, param_hash: str = "targeted-param") -> dict[str, object]:
    flow_variant = (
        "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
    )
    return {
        "version": 1,
        "checker": "attention_decode_score_multivalue_cluster_targeted_binary_fsm_v1",
        "profile": "targeted_binary",
        "expected_flow_variant": flow_variant,
        "selected_exact_row": {
            "design": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
            "platform": "nangate45",
            "tag": "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_targeted",
            "status": "ok",
            "flow_variant": flow_variant,
            "clock_period_ns": 8.0,
            "critical_path_ns": 7.1,
            "die_area": "0 0 2500 2500",
            "core_area": "50 50 2450 2450",
            "place_density": "0.4",
            "synth_hierarchical": "1",
            "synth_memory_max_bits": "65536",
            "synth_args": "",
            "failure_stage": None,
            "failure_returncode": None,
            "failure_signature": None,
            "config_hash": "targeted-config",
            "param_hash": param_hash,
        },
        "expected_logical_netlist_path": (
            "results/nangate45/"
            "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
            f"{flow_variant}/1_synth.v"
        ),
        "netlist_exists": True,
        "signals": {
            "state_q": {
                "expected_bit_indices": [0, 1, 2],
                "observed_packed_ranges": [{"msb": 2, "lsb": 0}],
                "observed_bit_indices": [],
            },
            "reducer.state": {
                "expected_bit_indices": [0, 1, 2, 3],
                "observed_packed_ranges": [],
                "observed_bit_indices": [0, 1, 2, 3],
            },
        },
        "width_valid": True,
        "promotion_valid": True,
        "promotion_reasons": [],
    }


def _strict_activity_power(manifest: dict[str, object]) -> dict[str, object]:
    flow_variant = (
        "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
    )
    phases = []
    for phase in manifest["phases"]:
        phase_name = phase["phase"]
        phases.append(
            {
                "phase": phase_name,
                "direct_vcd_annotation_pin_gate_pass": True,
                "trace_coverage_gate_pass": True,
                "annotation_gate_pass": True,
                "sequential_register_activity_gate_pass": True,
                "clock_period_gate_pass": True,
                "power_numeric_gate_pass": True,
                "phase_gate_pass": True,
                "sequential_register_activity_coverage": 1.0,
                "sequential_register_activity_assignment_count": 16,
                "sequential_register_activity_matched_count": 16,
                "sequential_register_activity_applied_count": 16,
                "power": {
                    "internal_w": 0.1,
                    "switching_w": 0.1,
                    "leakage_w": 0.01,
                    "total_w": 0.21,
                },
            }
        )
    return {
        "model": "postroute_phase_vcd_power_v1",
        "status": "activity_backed",
        "promotion_gate_pass": True,
        "flow_variant": flow_variant,
        "clock_period_ns": 8.0,
        "min_sequential_register_activity_coverage": 1.0,
        "full_context_energy_j": 0.001,
        "phases": phases,
    }


def test_build_report_accepts_only_matching_targeted_diagnostic_and_strict_power(
    tmp_path: Path,
) -> None:
    flow_variant = (
        "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
    )
    config = (
        tmp_path
        / "runs/designs/npu_blocks/"
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
        "config_targeted_binary_fsm.json"
    )
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "attention_decode_score_multivalue_cluster": {
                    "fsm_encoding": "binary",
                }
            }
        ),
        encoding="utf-8",
    )
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
                "platform": "nangate45",
                "config_hash": "targeted-config",
                "param_hash": "targeted-param",
                "tag": "targeted",
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6250000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": flow_variant,
                        "SYNTH_ARGS": "",
                    }
                ),
            }
        ],
    )
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(json.dumps({"equivalence_pass": True}), encoding="utf-8")
    diagnostic = tmp_path / "targeted_binary_fsm_diagnostic.json"
    diagnostic.write_text(json.dumps(_targeted_diagnostic()), encoding="utf-8")
    manifest = {
        "clock_period_ns": 8.0,
        "block_count": 3,
        "representative_full_transaction_cycles": 8334,
        "phase_partition_cycle_sum": 8334,
        "phases": [
            {"phase": "score_fill"},
            {"phase": "replay_value"},
            {"phase": "finalize_result"},
        ],
    }
    power = _strict_activity_power(manifest)

    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit, "build_power_report", return_value=power
    ):
        payload = audit.build_report(
            config=config,
            cluster_metrics_csv=metrics,
            equivalence_json=equivalence,
            orfs_design_config=tmp_path / "config.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
            min_sequential_register_activity_coverage=1.0,
            required_flow_variant=flow_variant,
            required_synth_args="",
            source_pnr_item_id=(
                "l1_decoder_attention_decode_score_multivalue_cluster_pnr_"
                "targeted_binary_fsm_8ns_v1"
            ),
            binary_fsm_diagnostic=diagnostic,
            required_binary_fsm_profile="targeted_binary",
        )

    assert payload["promotion_gate_pass"] is True
    assert payload["selection_contract"]["required_synth_args"] == ""
    assert payload["selection_contract"]["required_binary_fsm_profile"] == "targeted_binary"
    assert payload["source_dependencies"][0].endswith("targeted_binary_fsm_8ns_v1")
    assert str(tmp_path) not in json.dumps(payload)


def test_strict_activity_power_rejects_nonfinite_required_phase() -> None:
    manifest = {"phases": [{"phase": "score_fill"}]}
    power = _strict_activity_power(manifest)
    power["phases"][0]["power"]["total_w"] = float("nan")
    try:
        audit._validate_strict_activity_power(
            power,
            activity_manifest=manifest,
            flow_variant=power["flow_variant"],
            clock_period_ns=8.0,
        )
    except ValueError as exc:
        assert "non-finite total_w" in str(exc)
    else:
        raise AssertionError("non-finite required phase power was accepted")


def test_targeted_diagnostic_rejects_v14_profile_and_stale_row(tmp_path: Path) -> None:
    diagnostic_path = tmp_path / "targeted_binary_fsm_diagnostic.json"
    diagnostic = _targeted_diagnostic()
    diagnostic["profile"] = "v4_nofsm"
    diagnostic_path.write_text(json.dumps(diagnostic), encoding="utf-8")
    try:
        audit._validate_targeted_binary_fsm_diagnostic(
            diagnostic_path,
            required_profile="targeted_binary",
            required_flow_variant=(
                "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
            ),
            required_synth_args="",
        )
    except ValueError as exc:
        assert "profile" in str(exc)
    else:
        raise AssertionError("v14 checker profile was accepted")

    diagnostic = _targeted_diagnostic(param_hash="stale-param")
    diagnostic_path.write_text(json.dumps(diagnostic), encoding="utf-8")
    validated = audit._validate_targeted_binary_fsm_diagnostic(
        diagnostic_path,
        required_profile="targeted_binary",
        required_flow_variant=(
            "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
        ),
        required_synth_args="",
    )
    try:
        audit._validate_binary_fsm_metric_identity(
            validated,
            {
                "design": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
                "platform": "nangate45",
                "config_hash": "targeted-config",
                "param_hash": "current-param",
                "critical_path_ns": "7.1",
            },
        )
    except ValueError as exc:
        assert "does not match the selected PPA metrics row" in str(exc)
    else:
        raise AssertionError("stale diagnostic row was accepted")


def test_targeted_diagnostic_rejects_wrong_netlist_and_signal_evidence(tmp_path: Path) -> None:
    diagnostic_path = tmp_path / "targeted_binary_fsm_diagnostic.json"
    mutations = (
        ("version", lambda payload: payload.__setitem__("version", 2)),
        ("netlist existence", lambda payload: payload.__setitem__("netlist_exists", False)),
        (
            "netlist path",
            lambda payload: payload.__setitem__(
                "expected_logical_netlist_path", "results/nangate45/wrong/1_synth.v"
            ),
        ),
        (
            "state expected indices",
            lambda payload: payload["signals"]["state_q"].__setitem__(
                "expected_bit_indices", [0, 1, 3]
            ),
        ),
        (
            "state packed range",
            lambda payload: payload["signals"]["state_q"].__setitem__(
                "observed_packed_ranges", [{"msb": 3, "lsb": 0}]
            ),
        ),
        (
            "reducer bit indices",
            lambda payload: payload["signals"]["reducer.state"].__setitem__(
                "observed_bit_indices", [0, 1, 2, 4]
            ),
        ),
        (
            "inconsistent representations",
            lambda payload: payload["signals"]["state_q"].__setitem__(
                "observed_bit_indices", [0, 1, 2]
            ),
        ),
        (
            "missing signal",
            lambda payload: payload["signals"].pop("reducer.state"),
        ),
        (
            "extra signal",
            lambda payload: payload["signals"].__setitem__(
                "other.state", payload["signals"]["state_q"]
            ),
        ),
    )

    for label, mutate in mutations:
        diagnostic = json.loads(json.dumps(_targeted_diagnostic()))
        mutate(diagnostic)
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_valid"] is True
        diagnostic_path.write_text(json.dumps(diagnostic), encoding="utf-8")
        try:
            audit._validate_targeted_binary_fsm_diagnostic(
                diagnostic_path,
                required_profile="targeted_binary",
                required_flow_variant=(
                    "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
                ),
                required_synth_args="",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid targeted diagnostic {label} was accepted")


def test_targeted_diagnostic_rejects_wrong_physical_identity(tmp_path: Path) -> None:
    diagnostic_path = tmp_path / "targeted_binary_fsm_diagnostic.json"
    mutations = (
        ("design", "design", "wrong_design"),
        ("platform", "platform", "sky130hd"),
        ("tag", "tag", "wrong_tag"),
        ("clock", "clock_period_ns", 10.0),
        ("critical path limit", "critical_path_ns", 8.000001),
        ("critical path finiteness", "critical_path_ns", "nan"),
        ("die area", "die_area", "0 0 2600 2600"),
        ("core area", "core_area", "50 50 2550 2550"),
        ("place density", "place_density", "0.45"),
        ("hierarchy", "synth_hierarchical", "0"),
        ("memory limit", "synth_memory_max_bits", "32768"),
        ("synth args", "synth_args", "-nofsm"),
        ("failure stage", "failure_stage", "globalplace"),
        ("failure return code", "failure_returncode", 1),
        ("failure signature", "failure_signature", "RSZ-1008"),
    )

    for label, field, value in mutations:
        diagnostic = json.loads(json.dumps(_targeted_diagnostic()))
        diagnostic["selected_exact_row"][field] = value
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_valid"] is True
        diagnostic_path.write_text(json.dumps(diagnostic), encoding="utf-8")
        try:
            audit._validate_targeted_binary_fsm_diagnostic(
                diagnostic_path,
                required_profile="targeted_binary",
                required_flow_variant=(
                    "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
                ),
                required_synth_args="",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid selected-row {label} was accepted")


def test_metric_identity_rejects_same_hashes_with_wrong_design_platform_or_timing() -> None:
    diagnostic = _targeted_diagnostic()
    metric = {
        "design": "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
        "platform": "nangate45",
        "config_hash": "targeted-config",
        "param_hash": "targeted-param",
        "critical_path_ns": "7.1",
    }
    audit._validate_binary_fsm_metric_identity(diagnostic, metric)

    for field, value in (
        ("design", "wrong_design"),
        ("platform", "sky130hd"),
        ("critical_path_ns", "7.1000000001"),
        ("critical_path_ns", "nan"),
    ):
        mismatched = dict(metric)
        mismatched[field] = value
        try:
            audit._validate_binary_fsm_metric_identity(diagnostic, mismatched)
        except ValueError as exc:
            assert "does not match the selected PPA metrics row" in str(exc)
        else:
            raise AssertionError(f"same-hash metric with wrong {field} was accepted")


def test_build_report_records_strict_selection_contract_and_pnr_dependency(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p1",
                "tag": "binary",
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6000000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
        ],
    )
    manifest = {
        "clock_period_ns": 8.0,
        "block_count": 3,
        "representative_full_transaction_cycles": 8334,
        "phase_partition_cycle_sum": 8334,
        "phases": [],
    }
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "equivalence_pass": True,
                "decision": "shared_score_multivalue_cluster_equivalent",
            }
        ),
        encoding="utf-8",
    )
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit, "build_power_report",
        return_value={"promotion_gate_pass": True, "full_context_energy_j": 1.0},
    ):
        payload = audit.build_report(
            config=config,
            cluster_metrics_csv=metrics,
            equivalence_json=equivalence,
            orfs_design_config=tmp_path / "config.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
            required_flow_variant="decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
            required_synth_args="-nofsm",
            source_pnr_item_id="l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3",
        )
    assert payload["selection_contract"] == {
        "required_flow_variant": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
        "required_synth_args": "-nofsm",
        "min_sequential_register_activity_coverage": 0.95,
    }
    assert payload["source_dependencies"] == [
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3",
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
    ]


def test_build_report_keeps_legacy_source_dependencies_without_v14_source_pnr_id(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    manifest = {
        "clock_period_ns": 8.0,
        "block_count": 3,
        "representative_full_transaction_cycles": 8334,
        "phase_partition_cycle_sum": 8334,
        "phases": [],
    }
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "equivalence_pass": True,
                "decision": "shared_score_multivalue_cluster_equivalent",
            }
        ),
        encoding="utf-8",
    )
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit, "build_power_report",
        return_value={"promotion_gate_pass": True, "full_context_energy_j": 1.0},
    ):
        payload = audit.build_report(
            config=config,
            cluster_metrics_csv=metrics,
            equivalence_json=equivalence,
            orfs_design_config=tmp_path / "config.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
        )
    assert payload["source_dependencies"] == [
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
    ]
    assert payload["selection_contract"] == {
        "required_flow_variant": None,
        "required_synth_args": None,
        "min_sequential_register_activity_coverage": 0.95,
    }


def test_build_report_rejects_invalid_min_sequential_register_activity_coverage(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    _write_metrics_rows(
        metrics,
        [
            {
                "design": "cluster",
                "platform": "nangate45",
                "param_hash": "p1",
                "tag": "binary",
                "status": "ok",
                "critical_path_ns": "7.1",
                "die_area": "6000000",
                "instance_area_um2": "3000000",
                "params_json": json.dumps(
                    {
                        "CLOCK_PERIOD": 8,
                        "FLOW_VARIANT": "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
                        "SYNTH_ARGS": "-nofsm",
                    }
                ),
            },
        ],
    )
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(json.dumps({"equivalence_pass": True}), encoding="utf-8")
    for coverage in (0.0, 1.1):
        try:
            audit.build_report(
                config=config,
                cluster_metrics_csv=metrics,
                equivalence_json=equivalence,
                orfs_design_config=tmp_path / "config.mk",
                clock_period_ns=8.0,
                activity_dir=tmp_path / "activity",
                min_sequential_register_activity_coverage=coverage,
            )
        except ValueError as exc:
            assert "min_sequential_register_activity_coverage must be in (0, 1]" in str(exc)
        else:
            raise AssertionError(
                f"invalid min sequential register activity coverage {coverage} was accepted"
            )


def test_build_report_rejects_unproven_equivalence(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text('{"equivalence_pass": false}', encoding="utf-8")
    with mock.patch.object(audit, "generate_phase_activity") as generate:
        try:
            audit.build_report(
                config=tmp_path / "config.json",
                cluster_metrics_csv=tmp_path / "metrics.csv",
                equivalence_json=equivalence,
                orfs_design_config=tmp_path / "config.mk",
                clock_period_ns=8.0,
                activity_dir=tmp_path / "activity",
            )
        except ValueError as exc:
            assert "equivalence did not pass" in str(exc)
        else:
            raise AssertionError("unproven equivalence was accepted")
    generate.assert_not_called()


def test_build_report_records_promoted_and_failed_variants(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    # Make the second 8 ns row feasible so both physical variants are attempted.
    rows = list(csv.DictReader(metrics.open(encoding="utf-8")))
    rows[-1]["critical_path_ns"] = "7.9"
    with metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "clock_period_ns": 8.0,
        "block_count": 3,
        "representative_full_transaction_cycles": 8334,
        "phase_partition_cycle_sum": 8334,
        "phases": [],
    }
    power_ok = {
        "promotion_gate_pass": True,
        "full_context_energy_j": 0.002,
        "full_context_cycles": 3399201,
        "full_context_latency_s": 0.027193608,
    }
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "equivalence_pass": True,
                "decision": "shared_score_multivalue_cluster_equivalent",
                "score_tensor_hash": "score-hash",
                "final_tensor_hash": "final-hash",
            }
        ),
        encoding="utf-8",
    )
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit,
        "build_power_report",
        side_effect=[power_ok, RuntimeError("/orfs/missing result")],
    ):
        payload = audit.build_report(
            config=config,
            cluster_metrics_csv=metrics,
            equivalence_json=equivalence,
            orfs_design_config=tmp_path / "config.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
        )
    assert payload["decision"] == "activity_backed_cluster_power_measured"
    assert payload["source_dependencies"] == [
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
    ]
    assert payload["promoted_candidate_count"] == 1
    assert payload["best_candidate_id"] == "multivalue_cluster_activity_cluster_die2500"
    assert payload["equivalence"]["final_tensor_hash"] == "final-hash"
    assert payload["candidates"][1]["status"] == "measurement_failed"
    assert "/orfs/" not in json.dumps(payload)


def test_sanitized_failure_preserves_openroad_detail_without_local_paths() -> None:
    message = (
        "post-route VCD power failed:\n"
        "command: make --no-print-directory DESIGN_CONFIG=/tmp/workspaces/runner/config.mk ...\n"
        "stdout:\n"
        "   File /tmp/workspaces/runner/activities/runner.tcl\n"
        "   Tcl line 42: ERROR: undefined variable\n"
        "stderr:\n"
        '   openroad command "/orfs/tools/openroad/bin/openroad" -gui /home/user/project/design/openroad.tcl\n'
    )
    failure = audit._sanitized_failure(RuntimeError(message))
    detail = failure["detail"]
    assert failure["error_type"] == "RuntimeError"
    assert failure["error_summary"].startswith("post-route VCD power failed:")
    assert len(detail) <= 16
    assert all(len(line) <= 400 for line in detail)
    assert sum(len(line) for line in detail) <= 4096
    assert all(
        basename not in line for line in detail for basename in ("runner.tcl", "config.mk", "openroad.tcl")
    )
    assert any("<evaluator-local-path>" in line for line in detail)
    assert all("/tmp/" not in line for line in detail)
    assert all(" /home/" not in line and " /orfs/" not in line for line in detail)
    assert any("openroad command" in line for line in detail)
    assert any("Tcl line 42" in line for line in detail)


def test_sanitized_failure_bounds_to_tail_lines() -> None:
    message = "\n".join(
        [
            f"line {index}: this is a long diagnostic line with extra padding."
            + "x" * 600
            + f" /tmp/job/{index}/artifact.log"
            for index in range(30)
        ]
    )
    failure = audit._sanitized_failure(RuntimeError(message))
    detail = failure["detail"]
    assert len(detail) <= 16
    assert len(detail[0]) <= 400
    assert len(detail[-1]) <= 400
    assert detail[0].startswith("line 20")
    assert detail[-1].startswith("line 29")
    assert all("/tmp/" not in line for line in detail)
    assert all("artifact.log" not in line for line in detail)
