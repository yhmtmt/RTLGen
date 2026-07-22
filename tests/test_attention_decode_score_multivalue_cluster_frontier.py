import json
from pathlib import Path

import pytest

from npu.eval.audit_attention_decode_score_multivalue_cluster_frontier import build_report


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    source = _write(
        tmp_path / "source.json",
        {
            "source_schedule": {
                "hidden_size": 4096,
                "attention_heads": 32,
                "kv_heads": 4,
                "sequence_length": 131072,
                "clock_ns": 6.0,
                "layers": 32,
                "compute_budget_um2": 400_000_000,
                "logic_area_used_um2": 399_000_000,
                "compute_area_um2": 396_000_000,
                "measured_shared_sram_used_area_um2": 240_000_000,
                "measured_tile_local_sram_area_um2": 40_000_000,
                "command_dispatch_cycles": 2,
                "kv_write_cycles": 10,
            }
        },
    )
    prior = _write(
        tmp_path / "prior.json",
        {
            "inputs": {"prior_frontier_json": str(source)},
            "dense_qkv_tile": {"area_um2": 10_000, "effective_macs_per_cycle": 8.0},
        },
    )
    phases = [
        {
            "name": "fill",
            "full_context_cycles": 200,
            "clock_period_ns": 8.0,
            "power": {"internal_w": 1.0, "switching_w": 0.5, "leakage_w": 0.1},
        },
        {
            "name": "replay",
            "full_context_cycles": 100,
            "clock_period_ns": 8.0,
            "power": {"internal_w": 0.5, "switching_w": 0.25, "leakage_w": 0.1},
        },
    ]
    energy = sum(
        (p["power"]["internal_w"] + p["power"]["switching_w"] + p["power"]["leakage_w"])
        * p["full_context_cycles"]
        * p["clock_period_ns"]
        * 1e-9
        for p in phases
    )
    activity = _write(
        tmp_path / "activity.json",
        {
            "model": "decoder_attention_decode_score_multivalue_cluster_activity_power_v1",
            "decision": "activity_backed_cluster_power_measured",
            "promotion_gate_pass": True,
            "precision_status": "unchanged_integer_contract_from_merged_multivalue_equivalence",
            "equivalence": {
                "equivalence_pass": True,
                "decision": "decode_score_multivalue_cluster_equivalence_pass",
                "score_tensor_hash": "score",
                "final_tensor_hash": "final",
            },
            "best_candidate_id": "cluster",
            "best": {
                "candidate_id": "cluster",
                "flow_variant": "v1",
                "status": "activity_backed",
                "ppa_metric": {"instance_area_um2": "2000000", "critical_path_ns": "7.5"},
                "activity_power": {
                    "promotion_gate_pass": True,
                    "clock_period_ns": 8.0,
                    "full_context_cycles": 300,
                    "full_context_energy_j": energy,
                    "phases": phases,
                },
            },
        },
    )
    return prior, activity


def test_recost_uses_full_head_commands_activity_energy_and_linked_schedule(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    report = build_report(
        prior_frontier_json=prior, activity_power_json=activity, cluster_counts=[1, 2, 4, 8, 16, 32]
    )

    rows = {row["cluster_count"]: row for row in report["rows"]}
    assert report["inputs"]["source_schedule_json"].endswith("source.json")
    assert report["schedule_contract"]["full_head_commands_per_layer"] == 32
    assert report["schedule_contract"]["full_head_command_cycles"] == 300
    assert report["schedule_contract"]["full_head_phase_cycles"] == {"fill": 200, "replay": 100}
    assert rows[1]["cluster_waves_per_layer"] == 32
    assert rows[32]["cluster_waves_per_layer"] == 1
    assert rows[32]["attention_cycles"] == 300
    assert rows[32]["clock_ns"] == 8.0
    assert rows[32]["dense_qkv_tile_count"] == 640
    assert rows[1]["attention_cluster_dynamic_energy_mj_per_token"] == pytest.approx(
        rows[32]["attention_cluster_dynamic_energy_mj_per_token"]
    )
    assert rows[1]["attention_cluster_service_window_leakage_energy_mj_per_token"] == pytest.approx(
        rows[32]["attention_cluster_service_window_leakage_energy_mj_per_token"]
    )
    assert "attention_cluster_leakage_energy_mj_per_token" not in rows[32]
    assert "service_windows_only" in rows[32]["energy_status"]
    assert report["precision"]["decision"] == "decode_score_multivalue_cluster_equivalence_pass"
    assert report["precision"]["final_tensor_hash"] == "final"
    assert report["promotion_status"].endswith("full_architecture_promotion_blocked")


def test_recost_rejects_unpromoted_activity_and_unsupported_cluster_count(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    payload["promotion_gate_pass"] = False
    activity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion gate"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, cluster_counts=[1])

    _, activity = _inputs(tmp_path)
    with pytest.raises(ValueError, match="cluster count"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, cluster_counts=[64])


def test_recost_reserves_retained_noncompute_logic_from_compute_budget(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    prior_payload = json.loads(prior.read_text(encoding="utf-8"))
    source = Path(prior_payload["inputs"]["prior_frontier_json"])
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    source_payload["source_schedule"].update(
        {
            "compute_budget_um2": 10_000_000,
            "logic_area_used_um2": 4_000_000,
            "compute_area_um2": 1_000_000,
        }
    )
    source.write_text(json.dumps(source_payload), encoding="utf-8")
    prior_payload["dense_qkv_tile"]["area_um2"] = 1_000_000
    prior.write_text(json.dumps(prior_payload), encoding="utf-8")

    report = build_report(
        prior_frontier_json=prior,
        activity_power_json=activity,
        cluster_counts=[1],
    )

    row = report["rows"][0]
    assert row["retained_noncompute_logic_area_mm2"] == 3.0
    assert row["dense_qkv_tile_count"] == 5
    assert row["compute_budget_slack_mm2"] == 0.0
    assert row["logic_area_mm2"] == 10.0
    assert row["compute_budget_area_fit"] is True


@pytest.mark.parametrize(
    ("field_path", "bad_value", "message"),
    [
        (("model",), "wrong-model", "unexpected model"),
        (("decision",), "wrong-decision", "unexpected decision"),
        (("best_candidate_id",), "other", "identity does not match"),
        (("best", "status"), "rejected_gate", "not activity-backed"),
        (
            ("best", "activity_power", "promotion_gate_pass"),
            False,
            "best candidate promotion gate",
        ),
        (("precision_status",), "exact", "unexpected precision status"),
        (("equivalence", "equivalence_pass"), False, "equivalence did not pass"),
        (("equivalence", "decision"), "wrong", "equivalence has an unexpected decision"),
        (("equivalence", "score_tensor_hash"), "", "lacks score_tensor_hash"),
        (("equivalence", "final_tensor_hash"), "  ", "lacks final_tensor_hash"),
    ],
)
def test_recost_rejects_invalid_activity_promotion_contract(
    tmp_path: Path,
    field_path: tuple[str, ...],
    bad_value: object,
    message: str,
) -> None:
    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    target = payload
    for field in field_path[:-1]:
        target = target[field]
    target[field_path[-1]] = bad_value
    activity.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        build_report(
            prior_frontier_json=prior,
            activity_power_json=activity,
            cluster_counts=[1],
        )


def test_recost_rejects_schedule_clock_slower_than_activity_clock(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    prior_payload = json.loads(prior.read_text(encoding="utf-8"))
    source = Path(prior_payload["inputs"]["prior_frontier_json"])
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    source_payload["source_schedule"]["clock_ns"] = 9.0
    source.write_text(json.dumps(source_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="schedule clock is slower"):
        build_report(
            prior_frontier_json=prior,
            activity_power_json=activity,
            cluster_counts=[1],
        )


@pytest.mark.parametrize(
    ("field_path", "bad_value"),
    [
        (("best", "activity_power", "full_context_cycles"), 0),
        (("best", "activity_power", "full_context_cycles"), 300.5),
        (("best", "activity_power", "phases", 0, "full_context_cycles"), 0),
        (("best", "activity_power", "phases", 0, "full_context_cycles"), 200.5),
    ],
)
def test_recost_rejects_nonpositive_or_fractional_activity_cycles(
    tmp_path: Path,
    field_path: tuple[object, ...],
    bad_value: object,
) -> None:
    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    target = payload
    for field in field_path[:-1]:
        target = target[field]
    target[field_path[-1]] = bad_value
    activity.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="must be a positive integer"):
        build_report(
            prior_frontier_json=prior,
            activity_power_json=activity,
            cluster_counts=[1],
        )


def test_recost_rejects_nondivisor_cluster_count(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    with pytest.raises(ValueError, match="does not divide 32 heads"):
        build_report(
            prior_frontier_json=prior,
            activity_power_json=activity,
            cluster_counts=[3],
        )
