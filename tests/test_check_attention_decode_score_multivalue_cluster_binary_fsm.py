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
EXPECTED_VARIANT = "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4_proxy_die_2500"
EXPECTED_SYNTH_ARGS = "-nofsm"
STALE_VARIANT = "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
TARGETED_TAG = "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm"
TARGETED_VARIANT = (
    "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
)
EXPLICIT_ONEHOT_TAG = "decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm"
EXPLICIT_ONEHOT_VARIANT = (
    "decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm_v1_proxy_die_2500"
)

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

VALID_EXPLICIT_ONEHOT_PACKED_NETLIST_DECLARATIONS = """\
module top;
  wire [6:0] \\state_q ;
  wire [10:0] \\reducer.state ;
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
        "failure_stage",
        "failure_returncode",
        "failure_signature",
    ]
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def _write_row(
    *,
    status: str,
    critical_path_ns: float | None,
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
    failure_stage: str = "",
    failure_returncode: int | str = "",
    failure_signature: str = "",
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
        "" if critical_path_ns is None else f"{critical_path_ns}",
        "0.2",
        "0.5",
        json.dumps(params),
        result_path,
        failure_stage,
        str(failure_returncode),
        failure_signature,
    )


def _run_checker(
    metrics_path: Path,
    *,
    synth_results_dir: Path | None = None,
    diagnostic_out: Path | None = None,
    profile: str = "v4_nofsm",
) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "npu" / "eval" / "check_attention_decode_score_multivalue_cluster_binary_fsm.py"
    diagnostic_out = diagnostic_out or metrics_path.parent / "binary_fsm_diagnostic.json"
    command = [
        sys.executable,
        str(script),
        "--metrics-path",
        str(metrics_path),
        "--diagnostic-out",
        str(diagnostic_out),
        "--profile",
        profile,
    ]
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
        diagnostic_out = metrics.parent / "binary_fsm_diagnostic.json"
        assert (
            _run_checker(
                metrics,
                synth_results_dir=_synth_results_dir(Path(td)),
                diagnostic_out=diagnostic_out,
            ).returncode
            == 0
        )
        diagnostic = json.loads(diagnostic_out.read_text(encoding="utf-8"))
        assert diagnostic["promotion_valid"] is True
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_reasons"] == []
        assert diagnostic["selected_exact_row"]["status"] == "ok"


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_records_valid_widths_for_flow_failure() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="flow_failed",
                    critical_path_ns=None,
                    result_path=(
                        "/orfs/flow/logs/nangate45/"
                        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.log"
                    ),
                    failure_stage="global_route",
                    failure_returncode=2,
                    failure_signature="error in /tmp/evaluator/work/5_2_route.log",
                )
            ],
        )
        diagnostic_out = metrics.parent / "binary_fsm_diagnostic.json"

        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            diagnostic_out=diagnostic_out,
        )

        assert proc.returncode != 0
        diagnostic_text = diagnostic_out.read_text(encoding="utf-8")
        diagnostic = json.loads(diagnostic_text)
        assert diagnostic["selected_exact_row"]["status"] == "flow_failed"
        assert diagnostic["selected_exact_row"]["failure_stage"] == "global_route"
        assert diagnostic["selected_exact_row"]["failure_returncode"] == 2
        assert diagnostic["selected_exact_row"]["failure_signature"] == (
            "error in <absolute-path>"
        )
        assert diagnostic["expected_logical_netlist_path"] == (
            "results/nangate45/"
            "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
            f"{EXPECTED_VARIANT}/1_synth.v"
        )
        assert diagnostic["netlist_exists"] is True
        assert diagnostic["signals"]["state_q"]["observed_packed_ranges"] == [
            {"msb": 2, "lsb": 0}
        ]
        assert diagnostic["signals"]["reducer.state"]["observed_packed_ranges"] == [
            {"msb": 3, "lsb": 0}
        ]
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_valid"] is False
        assert "status is flow_failed, not ok" in diagnostic["promotion_reasons"]
        assert "critical path is missing or invalid" in diagnostic["promotion_reasons"]
        assert str(root) not in diagnostic_text


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_records_one_hot_width_failure() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, body=INVALID_REDUCER_STATE)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path=(
                        "runs/designs/npu_blocks/"
                        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json"
                    ),
                )
            ],
        )
        diagnostic_out = metrics.parent / "binary_fsm_diagnostic.json"

        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            diagnostic_out=diagnostic_out,
        )

        assert proc.returncode != 0
        diagnostic = json.loads(diagnostic_out.read_text(encoding="utf-8"))
        assert diagnostic["signals"]["reducer.state"]["observed_packed_ranges"] == [
            {"msb": 6, "lsb": 0}
        ]
        assert diagnostic["width_valid"] is False
        assert diagnostic["promotion_valid"] is False
        assert any(
            "invalid width for reducer.state" in reason
            for reason in diagnostic["promotion_reasons"]
        )


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_accepts_targeted_profile_without_nofsm() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, flow_variant=TARGETED_VARIANT)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path=(
                        "runs/designs/npu_blocks/"
                        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json"
                    ),
                    tag=TARGETED_TAG,
                    flow_variant=TARGETED_VARIANT,
                    synth_args=None,
                )
            ],
        )
        diagnostic_out = metrics.parent / "targeted_binary_fsm_diagnostic.json"

        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            diagnostic_out=diagnostic_out,
            profile="targeted_binary",
        )

        assert proc.returncode == 0, proc.stderr
        diagnostic = json.loads(diagnostic_out.read_text(encoding="utf-8"))
        assert diagnostic["profile"] == "targeted_binary"
        assert diagnostic["selected_exact_row"]["synth_args"] == ""
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_valid"] is True


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_accepts_explicit_onehot_profile() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(
            root,
            flow_variant=EXPLICIT_ONEHOT_VARIANT,
            body=VALID_EXPLICIT_ONEHOT_PACKED_NETLIST_DECLARATIONS,
        )
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.2,
                    result_path=(
                        "runs/designs/npu_blocks/"
                        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json"
                    ),
                    tag=EXPLICIT_ONEHOT_TAG,
                    flow_variant=EXPLICIT_ONEHOT_VARIANT,
                    synth_args=None,
                )
            ],
        )
        diagnostic_out = metrics.parent / "explicit_onehot_fsm_diagnostic.json"

        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            diagnostic_out=diagnostic_out,
            profile="explicit_onehot",
        )

        assert proc.returncode == 0, proc.stderr
        diagnostic = json.loads(diagnostic_out.read_text(encoding="utf-8"))
        assert diagnostic["profile"] == "explicit_onehot"
        assert diagnostic["checker"] == "attention_decode_score_multivalue_cluster_explicit_onehot_fsm_v1"
        assert diagnostic["selected_exact_row"]["flow_variant"] == EXPLICIT_ONEHOT_VARIANT
        assert diagnostic["selected_exact_row"]["synth_args"] == ""
        assert diagnostic["config_fsm_encoding"] == "explicit_onehot"
        assert diagnostic["width_valid"] is True
        assert diagnostic["promotion_valid"] is True


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_targeted_profile_relies_on_post_synth_widths() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(
            root,
            flow_variant=TARGETED_VARIANT,
            body=INVALID_REDUCER_STATE,
        )
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path=(
                        "runs/designs/npu_blocks/"
                        "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json"
                    ),
                    tag=TARGETED_TAG,
                    flow_variant=TARGETED_VARIANT,
                    synth_args=None,
                )
            ],
        )

        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            profile="targeted_binary",
        )

        assert proc.returncode != 0
        assert "invalid width for reducer.state" in proc.stderr
        assert "SYNTH_ARGS" not in proc.stderr.split("details:", 1)[-1]


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


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_stale_v3_exact_netlist_for_v4_checker() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, flow_variant=STALE_VARIANT)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.5,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    flow_variant=EXPECTED_VARIANT,
                    tag=f"{EXPECTED_TAG}_proxy_die_2500",
                    synth_args=EXPECTED_SYNTH_ARGS,
                )
            ],
        )
        proc = _run_checker(metrics, synth_results_dir=_synth_results_dir(root))
        assert proc.returncode != 0
        assert "missing exact netlist" in proc.stderr
        assert EXPECTED_VARIANT in proc.stderr
        diagnostic = json.loads(
            (metrics.parent / "binary_fsm_diagnostic.json").read_text(encoding="utf-8")
        )
        assert EXPECTED_VARIANT in diagnostic["expected_logical_netlist_path"]
        assert STALE_VARIANT not in json.dumps(diagnostic)


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


def test_check_attention_decode_score_multivalue_cluster_binary_fsm_rejects_explicit_onehot_width_mismatch() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = _metrics_path(root)
        _write_netlist(root, flow_variant=EXPLICIT_ONEHOT_VARIANT, body=INVALID_REDUCER_STATE)
        _write_metrics(
            metrics,
            [
                _write_row(
                    status="ok",
                    critical_path_ns=7.2,
                    result_path="runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/result.json",
                    tag=EXPLICIT_ONEHOT_TAG,
                    flow_variant=EXPLICIT_ONEHOT_VARIANT,
                    synth_args=None,
                )
            ],
        )
        proc = _run_checker(
            metrics,
            synth_results_dir=_synth_results_dir(root),
            profile="explicit_onehot",
        )
        assert proc.returncode != 0
        assert "invalid width for reducer.state" in proc.stderr


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
