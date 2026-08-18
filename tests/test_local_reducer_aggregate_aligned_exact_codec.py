from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RTL = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_aligned_exact_codec.sv"
TB = REPO_ROOT / "tests/local_reducer_aggregate_aligned_exact_codec_tb.sv"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    return None


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_local_reducer_aggregate_aligned_exact_codec_roundtrip_and_cadence(tmp_path: Path) -> None:
    simv = tmp_path / "local_reducer_aggregate_aligned_exact_codec.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_aligned_exact_codec_tb",
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
    assert (
        "PASS local_reducer_aggregate_aligned_exact_codec"
        in run.stdout
    )
    assert "encoder_flits=24" in run.stdout
    assert "loopback_beats=10" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_local_reducer_aggregate_aligned_exact_codec_yosys_import_process_check() -> None:
    for top in (
        "local_reducer_aggregate_aligned_exact_encoder",
        "local_reducer_aggregate_aligned_exact_decoder",
    ):
        subprocess.run(
            [
                str(_tool("yosys")),
                "-q",
                "-p",
                f"read_verilog -DSYNTHESIS -sv {RTL}; hierarchy -check -top {top}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
