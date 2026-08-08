import csv
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_attention_decode_score_multivalue_service_exact_partial_physical_recost import (  # noqa: E402
    build_report,
)


@pytest.fixture
def service_anchor_fixture() -> dict:
    return {
        "model": "decoder_attention_decode_score_multivalue_service_activity_power_v1",
        "decision": "activity_backed_service_power_measured",
        "promotion_gate_pass": True,
        "selection_contract": {"case_id": "c1_p128_b4_rr"},
        "source_item_id": "l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3",
        "activity_contract": {
            "clock_period_ns": 10.0,
            "cycle_count": 8719,
        },
        "dependency_contract": {
            "integrated_service_c1": {
                "exact_match": True,
                "no_protocol_errors": True,
                "cycle_bound_ok": True,
            }
        },
        "best": {
            "activity_power": {
                "status": "activity_backed",
                "scope": "tb/dut",
            },
            "ppa_metric": {
                "design": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr",
                "platform": "nangate45",
                "status": "ok",
            },
            "authoritative_composed_c1_total_ppa": {
                "critical_path_ns": 6.7148,
                "instance_area_um2": 2_921_450.0,
                "die_area": 9_000_000.0,
                "total_power_mw": 0.26,
            },
            "component_service_window_energy": {
                "cycle_count": 8719,
                "duration_s": 8.719000000000001e-05,
                "is_total_token_energy": False,
                "label": "component_service_window_energy",
                "power_w": {
                    "dynamic": 0.2401678636674,
                    "leakage": 0.116741158068,
                    "total": 0.356909006834,
                },
                "energy_j": {
                    "dynamic": 2.094023603316061e-05,
                    "leakage": 1.0178661571948921e-05,
                    "dynamic_plus_leakage": 3.111889760510953e-05,
                },
            },
        },
    }


@pytest.fixture
def functional_probe_fixture() -> dict:
    return {
        "model": "attention_decode_score_multivalue_service_finalized_cdc_probe_v1",
        "passed": True,
        "divider_lanes": 8,
        "service_period_ns": 10.0,
        "temporal_period_ns": 7.0,
        "summary": {
            "service_cycles": 120,
            "temporal_cycles": 36,
            "finalizer_cycles": 12,
            "cdc_accepted": 32,
            "cdc_emitted": 32,
            "finalizer_completed": 16,
        },
    }


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_metrics_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    fieldnames = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "instance_area_um2",
        "stdcell_area_um2",
        "stdcell_count",
        "core_area_um2",
        "utilization_pct",
        "flow_elapsed_seconds",
        "stage_elapsed_seconds",
        "params_json",
        "result_path",
        "work_result_json",
        "failure_stage",
        "failure_returncode",
        "failure_signature",
        "failure_log_path",
        "synth_script_path",
        "synth_script_sha1",
        "fsm_encfile_path",
        "fsm_encfile_sha1",
        "fsm_encfile_sha256",
        "fsm_encoding_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            rendered = {field: "" for field in fieldnames}
            rendered.update(row)
            writer.writerow(rendered)
    return path


def _metrics_row(
    *,
    design: str,
    clock_period_ns: float,
    critical_path_ns: float,
    die_area: float,
    total_power_mw: float,
    instance_area_um2: float,
    status: str = "ok",
    config_hash: str = "cfg",
    param_hash: str = "param",
    tag: str = "tag",
    platform: str = "nangate45",
) -> dict[str, object]:
    return {
        "design": design,
        "platform": platform,
        "config_hash": config_hash,
        "param_hash": param_hash,
        "tag": tag,
        "status": status,
        "critical_path_ns": critical_path_ns,
        "die_area": die_area,
        "total_power_mw": total_power_mw,
        "instance_area_um2": instance_area_um2,
        "stdcell_area_um2": instance_area_um2,
        "stdcell_count": 1234.0,
        "core_area_um2": 202500.0,
        "utilization_pct": 2.4,
        "flow_elapsed_seconds": 12.0,
        "stage_elapsed_seconds": "",
        "params_json": json.dumps(
            {
                "CLOCK_PERIOD": clock_period_ns,
                "CORE_AREA": "25 25 475 475",
                "DIE_AREA": "0 0 500 500",
                "PLACE_DENSITY": 0.4,
                "SYNTH_HIERARCHICAL": 1,
                "tag_prefix": "test_prefix",
            },
            sort_keys=True,
        ),
        "result_path": f"/orfs/flow/reports/{design}/{param_hash}/6_finish.rpt",
        "work_result_json": f"runs/designs/npu_blocks/{design}/work/{param_hash}/result.json",
    }


def _write_temporal_bundle(tmp_path: Path, *, clock_period_ns: float = 7.0) -> dict[str, Path | str | float]:
    design = "attention_score32_exact_partial_temporal_finalizer_physical_l8"
    metrics_csv = _write_metrics_csv(
        tmp_path / "temporal_metrics.csv",
        [
            _metrics_row(
                design=design,
                clock_period_ns=clock_period_ns,
                critical_path_ns=6.8,
                die_area=800_000.0,
                total_power_mw=0.55,
                instance_area_um2=120_000.0,
                config_hash="cfg-temporal",
                param_hash="temporal-ok",
                tag="temporal-tag",
            )
        ],
    )
    config_json = _write_json(
        tmp_path / "temporal_config.json",
        {
            "top_name": design,
            "attention_score32_exact_partial_temporal_finalizer_physical_harness": {
                "divider_lanes": 8,
                "heads": 2,
                "windows": 2,
            },
            "report_links": {
                "proposal_id": "prop_l1_decoder_attention_exact_partial_physical_calibration_v1",
                "proposal_path": "docs/proposals/prop_l1_decoder_attention_exact_partial_physical_calibration_v1/proposal.json",
            },
        },
    )
    macro_manifest_json = _write_json(
        tmp_path / "temporal_macro_manifest.json",
        {
            "module": design,
            "platform": "nangate45",
            "manifest_params": {
                "macro_count": 104,
                "total_macro_area_um2": 129024.896,
            },
        },
    )
    return {
        "metrics_csv": metrics_csv,
        "design": design,
        "clock_period_ns": clock_period_ns,
        "config_json": config_json,
        "macro_manifest_json": macro_manifest_json,
    }


def _write_fifo_bundle(
    tmp_path: Path,
    *,
    timed_domain: str,
    clock_period_ns: float | None = None,
    instance_area_um2: float = 4950.0,
    total_power_mw: float = 0.0005,
    die_area: float = 250000.0,
) -> dict[str, Path | str | float]:
    if clock_period_ns is None:
        clock_period_ns = 10.0 if timed_domain == "source" else 7.0
    design = f"attention_exact_partial_async_fifo_d4_{timed_domain}_domain_physical"
    metrics_csv = _write_metrics_csv(
        tmp_path / f"fifo_{timed_domain}_metrics.csv",
        [
            _metrics_row(
                design=design,
                clock_period_ns=clock_period_ns,
                critical_path_ns=0.65,
                die_area=die_area,
                total_power_mw=total_power_mw,
                instance_area_um2=instance_area_um2,
                config_hash=f"cfg-fifo-{timed_domain}",
                param_hash=f"fifo-{timed_domain}",
                tag=f"fifo-{timed_domain}-tag",
            )
        ],
    )
    config_json = _write_json(
        tmp_path / f"fifo_{timed_domain}_config.json",
        {
            "top_name": design,
            "attention_exact_partial_async_fifo_physical_harness": {
                "depth": 4,
                "timed_domain": timed_domain,
            },
            "report_links": {
                "proposal_id": "prop_l1_decoder_attention_exact_partial_physical_calibration_v1",
                "proposal_path": "docs/proposals/prop_l1_decoder_attention_exact_partial_physical_calibration_v1/proposal.json",
            },
        },
    )
    macro_manifest_json = _write_json(
        tmp_path / f"fifo_{timed_domain}_macro_manifest.json",
        {
            "module": design,
            "platform": "nangate45",
            "manifest_params": {
                "macro_count": 0,
                "timed_domain": timed_domain,
            },
        },
    )
    return {
        "metrics_csv": metrics_csv,
        "design": design,
        "clock_period_ns": clock_period_ns,
        "config_json": config_json,
        "macro_manifest_json": macro_manifest_json,
    }


def _build_report(
    *,
    tmp_path: Path,
    service_anchor: dict,
    functional_probe: dict,
    temporal_bundle: dict[str, Path | str | float],
    fifo_source_bundle: dict[str, Path | str | float],
    fifo_destination_bundle: dict[str, Path | str | float],
    csv_out: Path | None = None,
) -> dict:
    return build_report(
        service_activity_power_json=_write_json(tmp_path / "service.json", service_anchor),
        temporal_metrics_csv=temporal_bundle["metrics_csv"],  # type: ignore[arg-type]
        temporal_design=temporal_bundle["design"],  # type: ignore[arg-type]
        temporal_clock_period_ns=temporal_bundle["clock_period_ns"],  # type: ignore[arg-type]
        temporal_config_json=temporal_bundle["config_json"],  # type: ignore[arg-type]
        temporal_macro_manifest_json=temporal_bundle["macro_manifest_json"],  # type: ignore[arg-type]
        async_fifo_source_metrics_csv=fifo_source_bundle["metrics_csv"],  # type: ignore[arg-type]
        async_fifo_source_design=fifo_source_bundle["design"],  # type: ignore[arg-type]
        async_fifo_source_clock_period_ns=fifo_source_bundle["clock_period_ns"],  # type: ignore[arg-type]
        async_fifo_source_config_json=fifo_source_bundle["config_json"],  # type: ignore[arg-type]
        async_fifo_source_macro_manifest_json=fifo_source_bundle["macro_manifest_json"],  # type: ignore[arg-type]
        async_fifo_destination_metrics_csv=fifo_destination_bundle["metrics_csv"],  # type: ignore[arg-type]
        async_fifo_destination_design=fifo_destination_bundle["design"],  # type: ignore[arg-type]
        async_fifo_destination_clock_period_ns=fifo_destination_bundle["clock_period_ns"],  # type: ignore[arg-type]
        async_fifo_destination_config_json=fifo_destination_bundle["config_json"],  # type: ignore[arg-type]
        async_fifo_destination_macro_manifest_json=fifo_destination_bundle["macro_manifest_json"],  # type: ignore[arg-type]
        functional_probe_json=_write_json(tmp_path / "probe.json", functional_probe),
        csv_out=csv_out,
    )


def test_build_report_accepts_actual_r8_shape_and_consumes_both_fifo_views_once(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source", instance_area_um2=4955.85, total_power_mw=0.000607)
    fifo_destination = _write_fifo_bundle(
        tmp_path,
        timed_domain="destination",
        instance_area_um2=4908.76,
        total_power_mw=0.000485,
    )

    report = _build_report(
        tmp_path=tmp_path,
        service_anchor=service_anchor_fixture,
        functional_probe=functional_probe_fixture,
        temporal_bundle=temporal,
        fifo_source_bundle=fifo_source,
        fifo_destination_bundle=fifo_destination,
    )

    fifo_pair = report["normalized_measurements"]["async_fifo_pair"]
    assert fifo_pair["source_view"]["timed_domain"] == "source"
    assert fifo_pair["destination_view"]["timed_domain"] == "destination"
    assert fifo_pair["canonical_view"]["timed_domain"] == "source"
    assert fifo_pair["diagnostic_view"]["timed_domain"] == "destination"
    assert report["composed_physical"]["instance_area_um2"] == pytest.approx(2921450.0 + 120000.0 + 4955.85)
    assert report["composed_physical"]["generic_composed_total_power_mw"] == pytest.approx(0.26 + 0.55 + 0.000607)
    assert report["composed_physical"]["fifo_diagnostics"]["source_view"]["instance_area_um2"] == pytest.approx(4955.85)
    assert report["composed_physical"]["fifo_diagnostics"]["destination_view"]["instance_area_um2"] == pytest.approx(4908.76)
    assert report["composed_physical"]["composition_contract"]["both_fifo_domain_views_consumed_for_validation"] is True
    assert report["composed_physical"]["composition_contract"]["both_fifo_domain_views_added"] is False
    assert report["rows"][0]["fifo_canonical_rule"] == "source_domain_preferred_single_fifo_accounting"
    assert report["rows"][0]["fifo_canonical_design"] == "attention_exact_partial_async_fifo_d4_source_domain_physical"
    assert report["rows"][0]["fifo_source_design"] == "attention_exact_partial_async_fifo_d4_source_domain_physical"
    assert report["rows"][0]["fifo_destination_design"] == "attention_exact_partial_async_fifo_d4_destination_domain_physical"
    assert report["timing_bounds"]["service_domain"]["period_ns"] == pytest.approx(10.0)
    assert report["timing_bounds"]["temporal_domain"]["period_ns"] == pytest.approx(7.0)
    assert fifo_pair["source_view"]["clock_period_ns"] == pytest.approx(10.0)
    assert fifo_pair["destination_view"]["clock_period_ns"] == pytest.approx(7.0)
    assert fifo_pair["domain_periods_may_differ"] is True
    assert report["timing_bounds"]["temporal_domain"]["cycles"] == 36
    assert report["timing_bounds"]["temporal_domain"]["time_ns"] == pytest.approx(252.0)
    assert report["timing_bounds"]["temporal_domain"]["components"] == {
        "elapsed_wall_clock_temporal_cycles": 36,
        "finalizer_counter_cycles_diagnostic_only": 12,
        "finalizer_counter_added_to_elapsed_cycles": False,
    }
    assert report["timing_bounds"]["serial_upper_bound_ns"] == pytest.approx(1452.0)


def test_build_report_emits_csv_with_real_metrics_columns_and_provisional_energy_status(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")
    csv_out = tmp_path / "rows.csv"

    report = _build_report(
        tmp_path=tmp_path,
        service_anchor=service_anchor_fixture,
        functional_probe=functional_probe_fixture,
        temporal_bundle=temporal,
        fifo_source_bundle=fifo_source,
        fifo_destination_bundle=fifo_destination,
        csv_out=csv_out,
    )

    assert report["energy_contract"]["status"] == "bounded_provisional_activity_plus_openroad_physical_power_not_exact_token_energy"
    assert report["energy_contract"]["exact_token_energy_claimed"] is False
    assert report["energy_contract"]["service_activity_window_cycles_not_proven_same_as_functional_probe_service_cycles"] is True
    assert report["timing_bounds"]["service_domain"]["activity_window_cycle_count_not_assumed_equal"] == 8719
    assert report["timing_bounds"]["service_domain"]["cycles"] == 120
    assert report["composed_physical"]["power_provenance"]["service_generic_total_power_mw"] == "generic_openroad_routed_ppa_not_activity_backed"
    assert report["composed_physical"]["power_provenance"]["service_activity_window_power_mw"] == "activity_backed_service_window_power_from_component_service_window_energy"
    assert report["composed_physical"]["power_provenance"]["async_fifo_generic_total_power_mw"] == "openroad_physical_estimate_only_not_activity_backed_counted_once_via_canonical_fifo_view"
    with csv_out.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["energy_status"] == "bounded_provisional_activity_plus_openroad_physical_power_not_exact_token_energy"
    assert float(rows[0]["service_generic_total_power_mw"]) == pytest.approx(0.26)
    assert float(rows[0]["generic_composed_total_power_mw"]) == pytest.approx(0.8105, abs=1e-4)
    assert float(rows[0]["service_activity_window_power_mw"]) == pytest.approx(356.909006834)
    assert rows[0]["platform"] == "nangate45"
    assert int(rows[0]["divider_lanes"]) == 8


def test_build_report_rejects_duplicate_matching_temporal_rows(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    _write_metrics_csv(
        temporal["metrics_csv"],  # type: ignore[arg-type]
        [
            _metrics_row(
                design=temporal["design"],  # type: ignore[arg-type]
                clock_period_ns=temporal["clock_period_ns"],  # type: ignore[arg-type]
                critical_path_ns=6.8,
                die_area=800000.0,
                total_power_mw=0.55,
                instance_area_um2=120000.0,
                param_hash="temporal-a",
            ),
            _metrics_row(
                design=temporal["design"],  # type: ignore[arg-type]
                clock_period_ns=temporal["clock_period_ns"],  # type: ignore[arg-type]
                critical_path_ns=6.7,
                die_area=800000.0,
                total_power_mw=0.54,
                instance_area_um2=120100.0,
                param_hash="temporal-b",
            ),
        ],
    )
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")

    with pytest.raises(ValueError, match="exactly one status=ok row"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


def test_build_report_rejects_timing_infeasible_or_failed_rows(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    _write_metrics_csv(
        temporal["metrics_csv"],  # type: ignore[arg-type]
        [
            _metrics_row(
                design=temporal["design"],  # type: ignore[arg-type]
                clock_period_ns=temporal["clock_period_ns"],  # type: ignore[arg-type]
                critical_path_ns=7.5,
                die_area=800000.0,
                total_power_mw=0.55,
                instance_area_um2=120000.0,
            )
        ],
    )
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")

    with pytest.raises(ValueError, match="not timing-feasible"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )

    temporal = _write_temporal_bundle(tmp_path)
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    _write_metrics_csv(
        fifo_source["metrics_csv"],  # type: ignore[arg-type]
        [
            _metrics_row(
                design=fifo_source["design"],  # type: ignore[arg-type]
                clock_period_ns=fifo_source["clock_period_ns"],  # type: ignore[arg-type]
                critical_path_ns=0.65,
                die_area=250000.0,
                total_power_mw=0.0005,
                instance_area_um2=4950.0,
                status="flow_failed",
            )
        ],
    )
    with pytest.raises(ValueError, match="exactly one status=ok row"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


def test_build_report_rejects_macro_or_proposal_lineage_mismatch(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    temporal_manifest = json.loads(Path(temporal["macro_manifest_json"]).read_text(encoding="utf-8"))  # type: ignore[arg-type]
    temporal_manifest["manifest_params"]["macro_count"] = 103
    _write_json(temporal["macro_manifest_json"], temporal_manifest)  # type: ignore[arg-type]
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")

    with pytest.raises(ValueError, match="macro_count must be 104"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )

    temporal = _write_temporal_bundle(tmp_path)
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")
    fifo_dest_config = json.loads(Path(fifo_destination["config_json"]).read_text(encoding="utf-8"))  # type: ignore[arg-type]
    fifo_dest_config["report_links"]["proposal_id"] = "prop_wrong"
    _write_json(fifo_destination["config_json"], fifo_dest_config)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="proposal lineage mismatches"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


def test_build_report_rejects_inconsistent_fifo_views_but_counts_one_when_consistent(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source", instance_area_um2=4955.85)
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination", instance_area_um2=7000.0)

    with pytest.raises(ValueError, match="instance_area_um2 mismatch"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


def test_build_report_rejects_probe_lane_mismatch(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    functional_probe_fixture["divider_lanes"] = 4

    with pytest.raises(ValueError, match="divider_lanes must match"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=_write_temporal_bundle(tmp_path),
            fifo_source_bundle=_write_fifo_bundle(tmp_path, timed_domain="source"),
            fifo_destination_bundle=_write_fifo_bundle(tmp_path, timed_domain="destination"),
        )


@pytest.mark.parametrize(
    ("period_field", "period_ns", "error"),
    [
        ("service_period_ns", 9.0, "service_period_ns must match"),
        ("temporal_period_ns", 8.0, "temporal_period_ns must match"),
    ],
)
def test_build_report_rejects_probe_period_mismatch(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
    period_field: str,
    period_ns: float,
    error: str,
) -> None:
    functional_probe_fixture[period_field] = period_ns

    with pytest.raises(ValueError, match=error):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=_write_temporal_bundle(tmp_path),
            fifo_source_bundle=_write_fifo_bundle(tmp_path, timed_domain="source"),
            fifo_destination_bundle=_write_fifo_bundle(tmp_path, timed_domain="destination"),
        )


@pytest.mark.parametrize(
    ("domain", "period_ns", "error"),
    [
        ("source", 11.0, "service anchor clock period must match"),
        ("destination", 8.0, "temporal physical row clock period must match"),
    ],
)
def test_build_report_rejects_incompatible_physical_domain_periods(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
    domain: str,
    period_ns: float,
    error: str,
) -> None:
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")
    mismatched = _write_fifo_bundle(tmp_path, timed_domain=domain, clock_period_ns=period_ns)
    if domain == "source":
        fifo_source = mismatched
    else:
        fifo_destination = mismatched

    with pytest.raises(ValueError, match=error):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=_write_temporal_bundle(tmp_path),
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


@pytest.mark.parametrize("component", ["service", "temporal", "fifo_source", "fifo_destination"])
def test_build_report_rejects_non_nangate45_physical_platform(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
    component: str,
) -> None:
    temporal = _write_temporal_bundle(tmp_path)
    fifo_source = _write_fifo_bundle(tmp_path, timed_domain="source")
    fifo_destination = _write_fifo_bundle(tmp_path, timed_domain="destination")
    if component == "service":
        service_anchor_fixture["best"]["ppa_metric"]["platform"] = "sky130hd"
    else:
        bundle = {
            "temporal": temporal,
            "fifo_source": fifo_source,
            "fifo_destination": fifo_destination,
        }[component]
        metrics_path = Path(bundle["metrics_csv"])
        metrics_path.write_text(
            metrics_path.read_text(encoding="utf-8").replace("nangate45", "sky130hd", 1),
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="platform must be"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=temporal,
            fifo_source_bundle=fifo_source,
            fifo_destination_bundle=fifo_destination,
        )


def test_build_report_rejects_service_activity_cycle_count_mismatch(
    tmp_path: Path,
    service_anchor_fixture: dict,
    functional_probe_fixture: dict,
) -> None:
    service_anchor_fixture["best"]["component_service_window_energy"]["cycle_count"] = 8718

    with pytest.raises(ValueError, match="cycle_count must match activity_contract.cycle_count"):
        _build_report(
            tmp_path=tmp_path,
            service_anchor=service_anchor_fixture,
            functional_probe=functional_probe_fixture,
            temporal_bundle=_write_temporal_bundle(tmp_path),
            fifo_source_bundle=_write_fifo_bundle(tmp_path, timed_domain="source"),
            fifo_destination_bundle=_write_fifo_bundle(tmp_path, timed_domain="destination"),
        )
