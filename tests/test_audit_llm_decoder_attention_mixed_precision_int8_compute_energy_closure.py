#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_mixed_precision_int8_compute_energy_closure import (  # noqa: E402
    build_payload,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        hbm_command_calibrated_service_json=tmp_path / "hbm.json",
        mixed_precision_int8_compute_physical_feasibility_json=tmp_path / "feasibility.json",
        sram_profile_json=tmp_path / "sram.json",
        row_limit=16,
        pareto_row_limit=8,
        out=tmp_path / "out.json",
        out_md=tmp_path / "out.md",
    )


def _payload() -> dict:
    return {
        "diagnosis": {
            "physical_feasible_rows": 1,
            "source_rows_used": 2,
        },
        "best_requested": {
            "compute_mode": "dual_mac",
            "latency_us": 100.0,
            "adjusted_latency_us_if_feasible": 22.5,
            "substituted_compute_arch": "dense_gemm_int8_16x8_k1_p1",
            "substituted_compute_area_um2": 512_000.0,
            "substituted_compute_power_mw": 2.0,
            "substituted_compute_replica_count": 128,
            "compute_area_required_um2": 1_024_000.0,
        },
        "rows": [
            {
                "compute_mode": "dual_mac",
                "latency_us": 100.0,
                "adjusted_latency_us_if_feasible": 22.5,
                "substituted_compute_arch": "dense_gemm_int8_16x8_k1_p1",
                "substituted_compute_area_um2": 512_000.0,
                "substituted_compute_power_mw": 2.0,
                "substituted_compute_replica_count": 128,
                "die_area_mm2": 800.0,
            },
            {
                "compute_mode": "split_mac",
                "latency_us": 30.0,
                "adjusted_latency_us_if_feasible": 0.0,
                "substituted_compute_arch": "dense_gemm_fp16_16x16_k1_p1",
                "substituted_compute_area_um2": 800_000.0,
                "substituted_compute_power_mw": 1000.0,
                "substituted_compute_replica_count": 16,
                "die_area_mm2": 700.0,
            },
        ],
    }


def test_adjusted_latency_from_physical_feasibility_is_used(tmp_path: Path) -> None:
    args = _args(tmp_path)
    _write_json(args.hbm_command_calibrated_service_json, {
        "command_energy_calibration": {
            "source_hbm_energy_pj_per_byte": 1.0,
        }
    })
    _write_json(args.mixed_precision_int8_compute_physical_feasibility_json, _payload())
    _write_json(
        args.sram_profile_json,
        {
            "totals": {"allocated_sram_bytes": 4096},
            "sram_metrics_summary": {"total_read_energy_pj": 1024.0, "total_write_energy_pj": 512.0},
        },
    )

    payload = build_payload(args)
    best = payload["best"]
    assert best["latency_us"] == 22.5
    assert best["substituted_compute_arch"] == "dense_gemm_int8_16x8_k1_p1"
    assert payload["decision"].startswith("mixed_precision_int8_compute_energy_closure")


def test_substituted_compute_fields_are_preserved_in_energy_components(tmp_path: Path) -> None:
    args = _args(tmp_path)
    _write_json(args.hbm_command_calibrated_service_json, {
        "command_energy_calibration": {
            "source_hbm_energy_pj_per_byte": 2.5,
        }
    })
    _write_json(args.mixed_precision_int8_compute_physical_feasibility_json, _payload())
    _write_json(
        args.sram_profile_json,
        {
            "totals": {"allocated_sram_bytes": 4096},
            "sram_metrics_summary": {"total_read_energy_pj": 1024.0, "total_write_energy_pj": 512.0},
        },
    )

    payload = build_payload(args)
    best = payload["best"]
    assert best["substituted_compute_arch"] == "dense_gemm_int8_16x8_k1_p1"
    assert best["substituted_compute_power_mw"] == 2.0
    assert best["substituted_compute_replica_count"] == 128
    compute_component = best["energy_components"]["compute"]
    assert compute_component["compute_arch"] == "dense_gemm_int8_16x8_k1_p1"
    assert compute_component["replica_count"] == 128
