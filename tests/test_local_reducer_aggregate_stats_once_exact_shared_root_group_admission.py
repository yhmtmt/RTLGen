from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / (
    "npu/sim/rtl/"
    "local_reducer_aggregate_stats_once_exact_shared_root_group_admission.sv"
)
TB = REPO_ROOT / (
    "tests/"
    "local_reducer_aggregate_stats_once_exact_shared_root_group_admission_tb.sv"
)


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_exact_shared_root_group_admission(tmp_path: Path) -> None:
    simv = tmp_path / "exact_shared_root_group_admission.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_stats_once_exact_shared_root_group_admission_tb",
            "-o",
            str(simv),
            str(RTL),
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert "PASS group_admission four_groups=4 exact_done=1 exact_error=0" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_exact_shared_root_group_admission_yosys_import() -> None:
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            f"{RTL}; hierarchy -check -top "
            "local_reducer_aggregate_stats_once_exact_shared_root_group_admission; "
            "proc; check",
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
