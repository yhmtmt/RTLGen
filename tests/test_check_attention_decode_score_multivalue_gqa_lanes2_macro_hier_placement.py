#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


FLOW_VARIANT_PREFIX = "decode_score_multivalue_gqa_lanes2_macro_hier_placement_compare_3550_v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _metrics_path(root: Path) -> Path:
    design_dir = root / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv"
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
        "mode_name",
        "mode_use_macro",
        "failure_stage",
        "failure_signature",
        "params_json",
        "result_path",
    ]
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def _write_row(
    *,
    status: str,
    mode_name: str,
    mode_use_macro: bool,
    critical_path_ns: float,
    hierarchical: int,
    result_path: str,
    failure_stage: str = "",
    failure_signature: str = "",
    flow_variant: str | None = None,
    place_density: float = 0.4,
    synth_memory_max_bits: int = 65536,
) -> tuple[str, ...]:
    params = {
        "CLOCK_PERIOD": 10,
        "FLOW_VARIANT": flow_variant or f"{FLOW_VARIANT_PREFIX}_{mode_name}",
        "PLACE_DENSITY": place_density,
        "SYNTH_HIERARCHICAL": hierarchical,
        "SYNTH_MEMORY_MAX_BITS": synth_memory_max_bits,
        "DIE_AREA": "0 0 3550 3550",
        "CORE_AREA": "50 50 3500 3500",
    }
    return (
        "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv",
        "nangate45",
        "cfg",
        "param10",
        f"tag_{mode_name}",
        status,
        f"{critical_path_ns}",
        "0.2",
        "0.5",
        mode_name,
        str(mode_use_macro),
        failure_stage,
        failure_signature,
        json.dumps(params),
        result_path,
    )


def _run_checker(metrics_path: Path, out_path: Path) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "npu" / "eval" / "check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement.py"
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-path",
            str(metrics_path),
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_passes_with_one_failed_mode() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        metrics = _metrics_path(tmp)
        report = tmp / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv" / "mode_compare_lanes2_placement_diag.json"
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    mode_name="flattened_wrapper",
                    mode_use_macro=True,
                    critical_path_ns=10.1,
                    hierarchical=0,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
                _write_row(
                    status="flow_failed",
                    mode_name="hierarchical_macro",
                    mode_use_macro=True,
                    critical_path_ns=0,
                    hierarchical=1,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                    failure_stage="place",
                    failure_signature="exit_code=13",
                ),
            ],
        )

        proc = _run_checker(metrics, report)
        assert proc.returncode == 0
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["status"] == "ok"
        modes = {entry["mode"] for entry in payload["status_mode_rows"]}
        assert modes == {"flattened_wrapper", "hierarchical_macro"}
        assert payload["status_mode_rows"][0]["mode_use_macro"] in {"True", "true"}


def test_check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_rejects_missing_mode() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        metrics = _metrics_path(tmp)
        report = tmp / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv" / "mode_compare_lanes2_placement_diag.json"
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    mode_name="flattened_wrapper",
                    mode_use_macro=True,
                    critical_path_ns=10.1,
                    hierarchical=0,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
            ],
        )

        proc = _run_checker(metrics, report)
        assert proc.returncode != 0
        assert "missing required mode" in proc.stderr


def test_check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_rejects_non_macro_mode() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        metrics = _metrics_path(tmp)
        report = tmp / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv" / "mode_compare_lanes2_placement_diag.json"
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    mode_name="flattened_wrapper",
                    mode_use_macro=False,
                    critical_path_ns=9.9,
                    hierarchical=0,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
                _write_row(
                    status="ok",
                    mode_name="hierarchical_macro",
                    mode_use_macro=True,
                    critical_path_ns=9.6,
                    hierarchical=1,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
            ],
        )

        proc = _run_checker(metrics, report)
        assert proc.returncode != 0
        assert "missing required mode" in proc.stderr


def test_check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_rejects_malformed_hier_setting() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        metrics = _metrics_path(tmp)
        report = tmp / "runs" / "designs" / "npu_blocks" / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv" / "mode_compare_lanes2_placement_diag.json"
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    mode_name="flattened_wrapper",
                    mode_use_macro=True,
                    critical_path_ns=9.9,
                    hierarchical=1,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
                _write_row(
                    status="ok",
                    mode_name="hierarchical_macro",
                    mode_use_macro=True,
                    critical_path_ns=9.6,
                    hierarchical=1,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                ),
            ],
        )

        proc = _run_checker(metrics, report)
        assert proc.returncode != 0
        assert "missing required mode" in proc.stderr


@pytest.mark.parametrize(
    "bad_param",
    [
        {"flow_variant": f"{FLOW_VARIANT_PREFIX}_wrong_mode"},
        {"place_density": 0.41},
        {"synth_memory_max_bits": 32768},
    ],
    ids=["wrong-flow-variant", "wrong-place-density", "wrong-memory-threshold"],
)
def test_check_attention_decode_score_multivalue_gqa_lanes2_macro_hier_placement_rejects_changed_fixed_param(
    bad_param: dict[str, object],
) -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        metrics = _metrics_path(tmp)
        report = (
            tmp
            / "runs"
            / "designs"
            / "npu_blocks"
            / "attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv"
            / "mode_compare_lanes2_placement_diag.json"
        )
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    mode_name="flattened_wrapper",
                    mode_use_macro=True,
                    critical_path_ns=9.9,
                    hierarchical=0,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                    **bad_param,
                ),
                _write_row(
                    status="flow_failed",
                    mode_name="hierarchical_macro",
                    mode_use_macro=True,
                    critical_path_ns=0,
                    hierarchical=1,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes2_int8_m1x8_iterdiv/3_5_place_dp/base/params.json",
                    failure_stage="place",
                    failure_signature="exit_code=13",
                ),
            ],
        )

        proc = _run_checker(metrics, report)
        assert proc.returncode != 0
        assert "missing required mode: flattened_wrapper" in proc.stderr
