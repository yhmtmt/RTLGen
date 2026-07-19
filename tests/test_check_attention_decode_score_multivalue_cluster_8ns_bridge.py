#!/usr/bin/env python3

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _metrics_path(root: Path) -> Path:
    design_dir = root / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
    return design_dir / "metrics.csv"


def _write_metrics(metrics_path: Path, rows: list[tuple]) -> None:
    header = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "params_json",
        "result_path",
    ]
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def _write_row(*, status: str, critical_path_ns: float, params_json: str, result_path: str) -> tuple[str, ...]:
    return (
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
        "nangate45",
        "cfg",
        "param8",
        "tag",
        status,
        f"{critical_path_ns}",
        "0.2",
        "0.5",
        params_json,
        result_path,
    )


def _run_checker(metrics_path: Path) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "npu" / "eval" / "check_attention_decode_score_multivalue_cluster_8ns_bridge.py"
    return subprocess.run(
        [sys.executable, str(script), "--metrics-path", str(metrics_path)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_passes_with_exact_8ns_row() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8.0,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        assert _run_checker(metrics).returncode == 0


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_rejects_existing_10ns_ok_row() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.2189,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_proxy_die_2500","CLOCK_PERIOD":10,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        proc = _run_checker(metrics)
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_rejects_non_ok_status() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="flow_failed",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        proc = _run_checker(metrics)
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_rejects_clock_period_8p5() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8.5,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        proc = _run_checker(metrics)
        assert proc.returncode != 0


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_rejects_wrong_variant_area_or_path() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"other_variant","CLOCK_PERIOD":8,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8,"DIE_AREA":"0 0 3000 3000","CORE_AREA":"50 50 2950 2950"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="/tmp/other/design/metrics.json",
                ),
            ],
        )
        proc = _run_checker(metrics)
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_8ns_bridge_skips_malformed_rows() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json="not-json",
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    params_json='{"FLOW_VARIANT":"decode_score_multivalue_cluster_v1_8ns_bridge","CLOCK_PERIOD":8,"DIE_AREA":"0 0 2500 2500","CORE_AREA":"50 50 2450 2450"}',
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        assert _run_checker(metrics).returncode == 0
