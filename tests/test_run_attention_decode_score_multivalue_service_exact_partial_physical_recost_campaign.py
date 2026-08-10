import csv
import hashlib
import json
from pathlib import Path

import pytest

from npu.eval.run_attention_decode_score_multivalue_service_exact_partial_physical_recost_campaign import (
    _validate_campaign,
    run_campaign,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_REL = Path(
    "runs/campaigns/npu/"
    "attention_decode_score_multivalue_service_exact_partial_physical_recost_v1/campaign.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _materialize_committed_campaign(tmp_path: Path) -> tuple[Path, dict]:
    repo_root = tmp_path / "repo"
    campaign_path = repo_root / CAMPAIGN_REL
    campaign_path.parent.mkdir(parents=True)
    campaign_path.write_text((REPO_ROOT / CAMPAIGN_REL).read_text(encoding="utf-8"), encoding="utf-8")
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    fixed = campaign["fixed_inputs"]

    input_paths = [fixed["service_activity_power_json"]]
    for domain in ("source", "destination"):
        bundle = fixed[f"async_fifo_{domain}"]
        input_paths.extend(
            [bundle["metrics_csv"], bundle["config_json"], bundle["macro_manifest_json"]]
        )
    for point in campaign["points"]:
        input_paths.extend(
            [
                point["temporal_metrics_csv"],
                point["temporal_config_json"],
                point["temporal_macro_manifest_json"],
                point["functional_probe_json"],
            ]
        )
    for relative in input_paths:
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture for {relative}\n", encoding="utf-8")

    workload_path = repo_root / fixed["workload_correspondence_json"]
    workload_path.parent.mkdir(parents=True, exist_ok=True)
    workload_path.write_text(
        json.dumps(
            {
                "model": "attention_decode_score_multivalue_service_workload_correspondence_v1",
                "passed": True,
                "workload": {"sequence_length": 131072, "windows_per_head": 5462},
                "lane_reports": [
                    {
                        "divider_lanes": lane,
                        "affine_recurrence_proof": {
                            "proven": True,
                            "bounded_window_counts": [1, 2, 3, 4],
                            "startup_cycles": 1051,
                            "steady_state_cycles_per_additional_full_window": 1076,
                            "measured_service_span_cycles": [1051, 2127, 3203, 4279],
                            "counter_deltas": [1076, 1076, 1076],
                        },
                        "tail_adjustment_used_in_projection": False,
                        "projection": {
                            "windows_per_head": 5462,
                            "service_cycles_per_head": 5_877_087,
                            "temporal_final_drain_cycles_per_head": 16 * (57 * (8 // lane) + 2),
                            "head_latency_ns_serial_upper_bound": (
                                5_877_087 * 10.0 + 16 * (57 * (8 // lane) + 2) * 12.0
                            ),
                            "layer_latency_ns_serial_upper_bound": (
                                (5_877_087 * 10.0 + 16 * (57 * (8 // lane) + 2) * 12.0)
                                * 32
                            ),
                        },
                    }
                    for lane in (1, 2, 4, 8)
                ],
            }
        ),
        encoding="utf-8",
    )

    summary_path = repo_root / fixed["functional_probe_summary_json"]
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "model": "attention_decode_score_multivalue_service_finalized_cdc_lane_campaign_summary_v1",
        "campaign_id": "attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1",
        "passed": True,
        "fixed_parameters": {"service_period_ns": 10.0, "temporal_period_ns": 12.0},
        "divider_lanes": [1, 2, 4, 8],
        "point_count": 4,
        "points": [
            {
                "divider_lanes": point["divider_lanes"],
                "output": point["functional_probe_json"],
                "sha256": _sha256(repo_root / point["functional_probe_json"]),
            }
            for point in campaign["points"]
        ],
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return repo_root, campaign


def _fake_audit(**kwargs) -> dict:
    lane = int(str(kwargs["temporal_design"]).rsplit("_l", 1)[1])
    assert kwargs["temporal_clock_period_ns"] == 12.0
    assert kwargs["async_fifo_source_clock_period_ns"] == 10.0
    assert kwargs["async_fifo_destination_clock_period_ns"] == 12.0
    row = {
        "divider_lanes": lane,
        "candidate_id": f"candidate_l{lane}",
        "overlap_lower_bound_ns": 1200.0 + lane,
        "serial_upper_bound_ns": 1600.0 + lane,
        "energy_status": "bounded_provisional_activity_plus_openroad_physical_power_not_exact_token_energy",
    }
    return {
        "model": "decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1",
        "candidate_id": row["candidate_id"],
        "inputs": {"functional_probe_json": str(kwargs["functional_probe_json"])},
        "input_hashes": {"functional_probe_json": {"file_sha256": _sha256(kwargs["functional_probe_json"])}},
        "timing_bounds": {
            "overlap_lower_bound_ns": row["overlap_lower_bound_ns"],
            "serial_upper_bound_ns": row["serial_upper_bound_ns"],
        },
        "composed_physical": {
            "instance_area_um2": 3_000_000.0 + lane,
            "power_provenance": {
                "generic_composed_total_power_mw": "homogeneous_generic_openroad_power_sum_only"
            },
            "composition_contract": {"fifo_instance_area_added_once": True},
        },
        "energy_contract": {
            "status": row["energy_status"],
            "exact_token_energy_claimed": False,
        },
        "functional_contract": {"divider_lanes": lane},
        "rows": [row],
    }


def test_committed_campaign_contract_requires_exact_dependencies() -> None:
    campaign = json.loads((REPO_ROOT / CAMPAIGN_REL).read_text(encoding="utf-8"))
    validated = _validate_campaign(campaign)

    assert validated["campaign_id"] == (
        "attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r1"
    )
    assert [point["divider_lanes"] for point in validated["points"]] == [1, 2, 4, 8]
    assert validated["depends_on_item_ids"] == [
        "l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1",
        "l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r1",
        "l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1",
    ]
    assert validated["fixed_inputs"]["functional_probe_summary_json"].endswith(
        "_finalized_cdc_lane_probe_10ns_12ns_v1_r1/campaign_summary.json"
    )
    assert validated["fixed_inputs"]["workload_correspondence_json"].endswith(
        "_exact_partial_c1_workload_correspondence_llama7b_v1_r1.json"
    )
    assert validated["outputs"]["report_json"].endswith(
        "_exact_partial_physical_recost_10ns_12ns_v1_r1.json"
    )
    assert validated["outputs"]["rows_csv"].endswith(
        "_exact_partial_physical_recost_10ns_12ns_v1_r1.csv"
    )

    campaign["depends_on_item_ids"].pop()
    with pytest.raises(ValueError, match="must require exactly"):
        _validate_campaign(campaign)


def test_run_campaign_writes_one_lightweight_report_and_four_row_csv(tmp_path: Path) -> None:
    repo_root, _campaign = _materialize_committed_campaign(tmp_path)
    out = repo_root / "outputs" / "recost.json"
    csv_out = repo_root / "outputs" / "recost.csv"

    summary = run_campaign(
        campaign_path=repo_root / CAMPAIGN_REL,
        out=out,
        csv_out=csv_out,
        repo_root=repo_root,
        audit_runner=_fake_audit,
    )

    assert summary["passed"] is True
    assert summary["divider_lanes"] == [1, 2, 4, 8]
    assert summary["point_count"] == 4
    assert summary["dependency_contract"]["all_dependencies_materialized"] is True
    assert summary["artifact_contract"]["per_lane_recost_reports_omitted"] is True
    assert summary["artifact_contract"]["overlap_and_serial_bounds_preserved"] is True
    assert summary["artifact_contract"]["provisional_energy_provenance_preserved"] is True
    assert summary["artifact_contract"]["llama7b_workload_projection_preserved"] is True
    assert summary["rows"][0]["workload_service_cycles_per_head"] == 5_877_087
    assert summary["points"][3]["workload_correspondence"]["projection"][
        "temporal_final_drain_cycles_per_head"
    ] == 944
    assert all(point["energy_contract"]["exact_token_energy_claimed"] is False for point in summary["points"])
    with csv_out.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["divider_lanes"]) for row in rows] == [1, 2, 4, 8]
    assert sorted(path.name for path in out.parent.iterdir()) == ["recost.csv", "recost.json"]


def test_run_campaign_fails_closed_on_missing_physical_lane(tmp_path: Path) -> None:
    repo_root, campaign = _materialize_committed_campaign(tmp_path)
    missing = repo_root / campaign["points"][2]["temporal_metrics_csv"]
    missing.unlink()
    out = repo_root / "outputs" / "recost.json"
    csv_out = repo_root / "outputs" / "recost.csv"

    with pytest.raises(ValueError, match="not materialized"):
        run_campaign(
            campaign_path=repo_root / CAMPAIGN_REL,
            out=out,
            csv_out=csv_out,
            repo_root=repo_root,
            audit_runner=_fake_audit,
        )
    assert not out.exists()
    assert not csv_out.exists()


def test_run_campaign_fails_closed_on_functional_probe_hash_mismatch(tmp_path: Path) -> None:
    repo_root, campaign = _materialize_committed_campaign(tmp_path)
    probe = repo_root / campaign["points"][0]["functional_probe_json"]
    probe.write_text("changed after producer summary\n", encoding="utf-8")
    out = repo_root / "outputs" / "recost.json"
    csv_out = repo_root / "outputs" / "recost.csv"

    with pytest.raises(ValueError, match="hash mismatch"):
        run_campaign(
            campaign_path=repo_root / CAMPAIGN_REL,
            out=out,
            csv_out=csv_out,
            repo_root=repo_root,
            audit_runner=_fake_audit,
        )
    assert not out.exists()
    assert not csv_out.exists()


def test_run_campaign_fails_closed_on_invalid_workload_projection(tmp_path: Path) -> None:
    repo_root, campaign = _materialize_committed_campaign(tmp_path)
    workload = repo_root / campaign["fixed_inputs"]["workload_correspondence_json"]
    payload = json.loads(workload.read_text(encoding="utf-8"))
    payload["lane_reports"][0]["affine_recurrence_proof"]["proven"] = False
    workload.write_text(json.dumps(payload), encoding="utf-8")
    out = repo_root / "outputs" / "recost.json"
    csv_out = repo_root / "outputs" / "recost.csv"

    with pytest.raises(ValueError, match="affine proof missing"):
        run_campaign(
            campaign_path=repo_root / CAMPAIGN_REL,
            out=out,
            csv_out=csv_out,
            repo_root=repo_root,
            audit_runner=_fake_audit,
        )
    assert not out.exists()
    assert not csv_out.exists()
