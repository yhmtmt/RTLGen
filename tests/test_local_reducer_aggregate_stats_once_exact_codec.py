from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_codec.sv"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_codec_tb.sv"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    return None


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_stats_once_exact_codec_randomized_roundtrip_and_protocol_gate(
    tmp_path: Path,
) -> None:
    simv = tmp_path / "local_reducer_aggregate_stats_once_exact_codec.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_stats_once_exact_codec_tb",
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
    assert "PASS local_reducer_aggregate_stats_once_exact_codec" in run.stdout
    assert "input_beats_per_group=128" in run.stdout
    assert "flits_per_group=167" in run.stdout
    assert "beats_per_group=128" in run.stdout
    overlap = int(run.stdout.split("overlap=")[-1].split()[0])
    assert overlap >= 8


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_stats_once_exact_codec_yosys_import_process_check() -> None:
    yosys = str(_tool("yosys"))
    for top in (
        "local_reducer_aggregate_stats_once_exact_encoder",
        "local_reducer_aggregate_stats_once_exact_decoder",
    ):
        subprocess.run(
            [
                yosys,
                "-q",
                "-p",
                "read_verilog -DSYNTHESIS -sv "
                f"{RTL}; hierarchy -check -top {top}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
