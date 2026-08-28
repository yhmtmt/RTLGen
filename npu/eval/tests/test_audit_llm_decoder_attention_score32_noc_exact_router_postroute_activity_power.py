from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from npu.eval import (
    audit_llm_decoder_attention_score32_noc_exact_router_postroute_activity_power as audit,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_audit_command_line_entry_point_loads_from_repo_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_llm_decoder_attention_score32_noc_exact_router_postroute_activity_power.py",
            "--help",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "exact VC0/VC1" in result.stdout


def _power_phase(name: str, *, group: int | None, cycles: int, flits: int) -> dict:
    return {
        "phase": name,
        "transport_class": "shared" if group is None else "reduction",
        "group": group,
        "measured_cycles": cycles,
        "full_context_cycles": cycles,
        "packet_count": 7616 if group is None else 315,
        "flit_count": flits,
        "macro_activity_assignment_count": 0,
        "annotation_gate_pass": True,
        "sequential_register_activity_gate_pass": True,
        "clock_period_gate_pass": True,
        "power_numeric_gate_pass": True,
        "structural_macro_activity_gate_pass": True,
        "phase_gate_pass": True,
        "power": {
            "internal_w": 0.1,
            "switching_w": 0.2,
            "leakage_w": 0.05,
            "total_w": 0.35,
        },
    }


def test_measure_point_sums_all_exact_phase_energy(tmp_path: Path, monkeypatch) -> None:
    phases = [
        _power_phase("shared_vc0_full_context_service", group=None, cycles=100, flits=60928),
        *(
            _power_phase(
                f"reduction_vc1_group_{group}",
                group=group,
                cycles=10,
                flits=2505,
            )
            for group in range(4)
        ),
    ]
    monkeypatch.setattr(
        audit,
        "build_power_report",
        lambda **_kwargs: {"promotion_gate_pass": True, "phases": phases},
    )
    physical = {
        "effective_flow_variant": "router_node5_bare_v1__abc",
        "target_clock_ns": 1.8,
        "critical_path_ns": 1.7,
        "timing_feasible": True,
        "core_utilization_pct": 50.0,
        "die_area_um2": 100.0,
        "instance_area_um2": 80.0,
    }
    measured = audit._measure_point(
        physical=physical,
        activity_manifest={"clock_period_ns": 1.8},
        activity_manifest_path=tmp_path / "activity.json",
        orfs_design_config=tmp_path / "config.mk",
        timeout_seconds=10,
    )

    assert measured["phase_count"] == 5
    assert measured["total_cycles"] == 140
    assert measured["total_flits"] == 70948
    assert measured["exact_transport_energy_j"]["dynamic"] == 0.3 * 140 * 1.8e-9
    assert measured["exact_transport_energy_j"]["leakage"] == 0.05 * 140 * 1.8e-9


def test_measure_point_rejects_missing_exact_group(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        audit,
        "build_power_report",
        lambda **_kwargs: {
            "promotion_gate_pass": True,
            "phases": [
                _power_phase(
                    "shared_vc0_full_context_service",
                    group=None,
                    cycles=100,
                    flits=60928,
                )
            ],
        },
    )
    physical = {
        "effective_flow_variant": "router_node5_bare_v1__abc",
        "target_clock_ns": 1.8,
        "critical_path_ns": 1.7,
    }
    try:
        audit._measure_point(
            physical=physical,
            activity_manifest={"clock_period_ns": 1.8},
            activity_manifest_path=tmp_path / "activity.json",
            orfs_design_config=tmp_path / "config.mk",
            timeout_seconds=10,
        )
    except ValueError as exc:
        assert "five required phases" in str(exc)
    else:
        raise AssertionError("missing exact reduction phases were accepted")


def test_measure_point_rejects_wrong_exact_phase_count(tmp_path: Path, monkeypatch) -> None:
    phases = [
        _power_phase("shared_vc0_full_context_service", group=None, cycles=100, flits=60927),
        *(
            _power_phase(
                f"reduction_vc1_group_{group}",
                group=group,
                cycles=10,
                flits=2505,
            )
            for group in range(4)
        ),
    ]
    monkeypatch.setattr(
        audit,
        "build_power_report",
        lambda **_kwargs: {"promotion_gate_pass": True, "phases": phases},
    )
    physical = {
        "effective_flow_variant": "router_node5_bare_v1__abc",
        "target_clock_ns": 1.8,
        "critical_path_ns": 1.7,
    }

    try:
        audit._measure_point(
            physical=physical,
            activity_manifest={"clock_period_ns": 1.8},
            activity_manifest_path=tmp_path / "activity.json",
            orfs_design_config=tmp_path / "config.mk",
            timeout_seconds=10,
        )
    except ValueError as exc:
        assert "phase count mismatch" in str(exc)
    else:
        raise AssertionError("wrong exact phase cardinality was accepted")
