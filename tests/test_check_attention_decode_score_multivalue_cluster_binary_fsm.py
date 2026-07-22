#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


EXPECTED_TAG = "decode_score_multivalue_cluster_v1_8ns_binary_fsm"
EXPECTED_VARIANT = "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
EXPECTED_SYNTH_ARGS = "-nofsm"

VALID_PACKED_NETLIST_DECLARATIONS = """\
module top;
  wire [2:0] \\state_q ;
  wire [3:0] \\reducer.state ;
endmodule
"""

VALID_BITBLASTED_NETLIST_DECLARATIONS = """\
module top;
  wire \\state_q[0] ;
  wire \\state_q[1] ;
  wire \\state_q[2] ;
  wire \\reducer.state[0] ;
  wire \\reducer.state[1] ;
  wire \\reducer.state[2] ;
  wire \\reducer.state[3] ;
endmodule
"""

INVALID_REDUCER_STATE = """\
module top;
  wire [2:0] \\state_q ;
  wire [6:0] \\reducer.state ;
endmodule
"""

INVALID_STATE_Q = """\
module top;
  wire [3:0] \\state_q ;
  wire [3:0] \\reducer.state ;
endmodule
"""

INVALID_REDUCER_STATE_BIT = """\
module top;
  wire \\state_q[0] ;
  wire \\state_q[1] ;
  wire \\state_q[2] ;
  wire \\reducer.state[0] ;
  wire \\reducer.state[1] ;
  wire \\reducer.state[2] ;
  wire \\reducer.state[3] ;
  wire \\reducer.state[6] ;
endmodule
"""

INVALID_STATE_Q_BIT = """\
module top;
  wire \\state_q[0] ;
  wire \\state_q[1] ;
  wire \\state_q[2] ;
  wire \\state_q[3] ;
  wire \\reducer.state[0] ;
  wire \\reducer.state[1] ;
  wire \\reducer.state[2] ;
  wire \\reducer.state[3] ;
endmodule
"""


def _synth_results_dir(root: Path) -> Path:
    return root / "orfs" / "flow" / "results"


def _write_netlist(
    root: Path,
    *,
    platform: str = "nangate45",
    design: str = "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
    flow_variant: str = EXPECTED_VARIANT,
    body: str = VALID_PACKED_NETLIST_DECLARATIONS,
) -> Path:
    netlist = (
        _synth_results_dir(root)
        / platform
        / design
        / flow_variant
        / "1_synth.v"
    )
    netlist.parent.mkdir(parents=True, exist_ok=True)
    netlist.write_text(body, encoding="utf-8")
    return netlist


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


def _write_row(
    *,
    status: str,
    critical_path_ns: float,
    result_path: str,
    tag: str = EXPECTED_TAG,
    flow_variant: str = EXPECTED_VARIANT,
    synth_args: str | None = EXPECTED_SYNTH_ARGS,
    clock_period: float = 8,
    die_area: str = "0 0 2500 2500",
    core_area: str = "50 50 2450 2450",
    place_density: object | None = 0.4,
    synth_hierarchical: object | None = 1,
    synth_memory_max_bits: object | None = 65536,
) -> tuple[str, ...]:
    params = {
        "FLOW_VARIANT": flow_variant,
        "CLOCK_PERIOD": clock_period,
        "DIE_AREA": die_area,
        "CORE_AREA": core_area,
    }
    if place_density is not None:
        params["PLACE_DENSITY"] = place_density
    if synth_hierarchical is not None:
        params["SYNTH_HIERARCHICAL"] = synth_hierarchical
    if synth_memory_max_bits is not None:
        params["SYNTH_MEMORY_MAX_BITS"] = synth_memory_max_bits
    if synth_args is not None:
        params["SYNTH_ARGS"] = synth_args
    return (
        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv",
        "nangate45",
        "cfg",
        "param8",
        tag,
        status,
        f"{critical_path_ns}",
        "0.2",
        "0.5",
        json.dumps(params),
        result_path,
    )


def _run_checker(
    metrics_path: Path,
    *,
    synth_results_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "npu" / "eval" / "check_attention_decode_score_multivalue_cluster_binary_fsm.py"
    command = [sys.executable, str(script), "--metrics-path", str(metrics_path)]
    if synth_results_dir is not None:
        command.extend(["--synth-results-dir", str(synth_results_dir)])
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_passes_with_exact_8ns_row() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                )
            ],
        )
        assert _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td))).returncode == 0


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_passes_with_mode_suffixed_tag() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    tag=f"{EXPECTED_TAG}_proxy_die_2500",
                )
            ],
        )
        assert _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td))).returncode == 0


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_old_bridge_flow() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    flow_variant="decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500",
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_missing_synth_args() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    synth_args=None,
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_wrong_synth_args() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    synth_args="-nofsm -D DEBUG",
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


@pytest.mark.parametrize(
    "architecture_params",
    [
        {"place_density": None},
        {"place_density": 0.41},
        {"synth_hierarchical": None},
        {"synth_hierarchical": 0},
        {"synth_memory_max_bits": None},
        {"synth_memory_max_bits": 32768},
    ],
)
def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_missing_or_wrong_architecture_params(
    architecture_params: dict[str, object | None],
) -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    **architecture_params,
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_bad_status_or_timing() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_netlist(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="flow_failed",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
                _write_row(
                    status="ok",
                    critical_path_ns=8.2,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                ),
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing required 8ns" in proc.stderr


@pytest.mark.parametrize(
    "declaration",
    [VALID_PACKED_NETLIST_DECLARATIONS, VALID_BITBLASTED_NETLIST_DECLARATIONS],
)
def test_check_attention_decode_score_multivalue_cluster_binary_fsm_accepts_valid_signal_declarations(
    declaration: str,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, body=declaration)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                )
            ],
        )
        assert _run_checker(metrics, synth_results_dir=_synth_results_dir(root)).returncode == 0


@pytest.mark.parametrize(
    "declaration",
    [INVALID_REDUCER_STATE, INVALID_REDUCER_STATE_BIT],
    ids=["reducer_state_packed", "reducer_state_bit"],
)
def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_reducer_state_oob(
    declaration: str,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, body=declaration)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(root))
        assert proc.returncode != 0
        assert "invalid width for reducer.state" in proc.stderr
        assert "details" in proc.stderr


@pytest.mark.parametrize(
    "declaration",
    [INVALID_STATE_Q, INVALID_STATE_Q_BIT],
    ids=["state_q_packed", "state_q_bit"],
)
def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_state_q_oob(
    declaration: str,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, body=declaration)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(root))
        assert proc.returncode != 0
        assert "invalid width for state_q" in proc.stderr
        assert "details" in proc.stderr


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_when_synth_netlist_is_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        metrics = _metrics_path(Path(td))
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(Path(td)))
        assert proc.returncode != 0
        assert "missing exact netlist" in proc.stderr
