import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_operational_component_frontier import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _frontier_row() -> dict:
    return {
        "family": "score32_separated_two_pass",
        "candidate_id": "score32_candidate",
        "source_schedule_clock_ns": 5.0,
        "timing_ok": True,
        "latency_us": 123.0,
        "token_throughput_per_s": 8123.0,
        "energy_mj_per_token": 4.5,
        "logic_plus_service_area_mm2": 3.0,
        "retained_logic_area_mm2": 2.8,
        "embodied_logic_plus_score_macro_area_mm2": 3.4,
        "score_sram_macro_area_mm2": 0.2,
        "head_count": 32,
        "remaining_abstractions": [
            "dense compute proxy remains analytical",
            "schedule clock is already validated",
        ],
        "components": [
            {
                "component": "dense_int8_gemm_fabric",
                "area_um2": 1710000.0,
                "power_mw": 85.5,
                "critical_path_ns": 1.8,
                "energy_mj_per_token": 1.25,
            }
        ],
    }


def test_build_report_recosts_dense_area_and_timing_but_retains_energy_and_power_accounting(tmp_path: Path) -> None:
    frontier_json = tmp_path / "frontier.json"
    operational_csv = tmp_path / "operational.csv"
    old_tile_csv = tmp_path / "old_tile.csv"

    _write_json(frontier_json, {"rows": [_frontier_row()]})
    _write_csv(
        operational_csv,
        [
            {
                "status": "ok",
                "instance_area_um2": 880.0,
                "critical_path_ns": 6.0,
                "total_power_mw": 0.06,
            },
            {
                "status": "ok",
                "instance_area_um2": 900.0,
                "critical_path_ns": 4.0,
                "total_power_mw": 0.07,
            },
        ],
    )
    _write_csv(
        old_tile_csv,
        [
            {
                "status": "ok",
                "instance_area_um2": 1000.0,
                "critical_path_ns": 2.0,
                "total_power_mw": 0.05,
            }
        ],
    )

    report = build_report(
        frontier_json=frontier_json,
        operational_tile_metrics_csv=operational_csv,
        old_tile_metrics_csv=old_tile_csv,
    )

    row = report["rows"][0]
    dense = row["components"][0]

    assert report["selected_operational_tile"]["critical_path_ns"] == "4.0"
    assert report["selected_old_tile"]["instance_area_um2"] == "1000.0"
    assert dense["component"] == "operational_dense_int8_gemm_fabric"
    assert dense["area_replica_count"] == 1710
    assert dense["active_replica_count"] == 1710
    assert dense["per_tile_area_um2"] == 900.0
    assert dense["area_um2"] == 1539000.0
    assert dense["critical_path_ns"] == 4.0
    assert dense["clock_ok"] is True
    assert dense["power_mw"] == 85.5
    assert dense["energy_mj_per_token"] == 1.25
    assert dense["vectorless_power_mw_per_tile"] == 0.07
    assert dense["vectorless_power_mw_scaled_active"] == 119.7
    assert row["latency_us"] == 123.0
    assert row["energy_mj_per_token"] == 4.5
    assert row["logic_plus_service_area_mm2"] == 2.829
    assert row["retained_logic_area_mm2"] == 2.629
    assert row["embodied_logic_plus_score_macro_area_mm2"] == 3.229
    assert row["operational_dense_area_delta_mm2"] == -0.171
    assert row["energy_recost_status"] == "retained_activity_backed_energy_vectorless_power_not_substituted"
    assert "score-bank proxy PNR is pending" in row["remaining_abstractions"]


def test_build_report_optionally_replaces_score_bank_area_without_substituting_energy(tmp_path: Path) -> None:
    frontier_json = tmp_path / "frontier.json"
    operational_csv = tmp_path / "operational.csv"
    old_tile_csv = tmp_path / "old_tile.csv"
    score_bank_csv = tmp_path / "score_bank.csv"

    _write_json(frontier_json, {"rows": [_frontier_row()]})
    _write_csv(
        operational_csv,
        [
            {
                "status": "ok",
                "instance_area_um2": 900.0,
                "critical_path_ns": 4.0,
                "total_power_mw": 0.07,
            }
        ],
    )
    _write_csv(
        old_tile_csv,
        [
            {
                "status": "ok",
                "instance_area_um2": 1000.0,
                "critical_path_ns": 2.0,
                "total_power_mw": 0.05,
            }
        ],
    )
    _write_csv(
        score_bank_csv,
        [
            {
                "status": "ok",
                "instance_area_um2": 3200.0,
                "critical_path_ns": 4.5,
                "total_power_mw": 0.12,
            }
        ],
    )

    report = build_report(
        frontier_json=frontier_json,
        operational_tile_metrics_csv=operational_csv,
        old_tile_metrics_csv=old_tile_csv,
        score_bank_metrics_csv=score_bank_csv,
    )

    row = report["rows"][0]
    dense = row["components"][0]

    assert row["score_sram_macro_area_mm2"] == 0.1024
    assert row["score_bank_proxy_area_delta_mm2"] == -0.0976
    assert row["embodied_logic_plus_score_macro_area_mm2"] == 3.1314
    assert row["score_bank_proxy_metrics"] == {
        "metrics_csv": str(score_bank_csv),
        "critical_path_ns": 4.5,
        "instance_area_um2_per_bank": 3200.0,
        "vectorless_power_mw_per_bank": 0.12,
        "bank_count": 32,
        "fakeram_macro_count_per_bank": 56,
        "sram_signoff": False,
    }
    assert row["timing_ok"] is True
    assert row["latency_us"] == 123.0
    assert row["energy_mj_per_token"] == 4.5
    assert dense["power_mw"] == 85.5
    assert row["energy_recost_status"] == "retained_activity_backed_energy_vectorless_power_not_substituted"
    assert "score-bank FakeRAM LEF/LIB views have no SRAM GDS and are not signoff" in row["remaining_abstractions"]
    assert "score-bank proxy PNR is pending" not in row["remaining_abstractions"]
