from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_exact_codec_matched_ppa_harness.sv"
ALIGNED = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_aligned_exact_codec.sv"
STATS = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_codec.sv"
TB = REPO_ROOT / "tests/local_reducer_aggregate_exact_codec_matched_ppa_harness_tb.sv"


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
def test_matched_harness_roundtrip_and_transport_counts(tmp_path: Path) -> None:
    simv = tmp_path / "matched_ppa_harness.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_exact_codec_matched_ppa_harness_tb",
            "-o",
            str(simv),
            str(ALIGNED),
            str(STATS),
            str(HARNESS),
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
    assert "PASS local_reducer_aggregate_exact_codec_matched_ppa_harness" in run.stdout
    fields = dict(
        field.split("=", 1)
        for field in run.stdout.split()
        if "=" in field
    )
    assert int(fields["groups"]) >= 3
    assert int(fields["aligned_flits"]) >= int(fields["groups"]) * 256
    assert int(fields["stats_flits"]) >= 3 * 167


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_matched_harness_yosys_check_both_modes() -> None:
    yosys = str(_tool("yosys"))
    for mode in (0, 1):
        subprocess.run(
            [
                yosys,
                "-q",
                "-p",
                "read_verilog -DSYNTHESIS -sv "
                f"{ALIGNED} {STATS} {HARNESS}; "
                f"chparam -set MODE_STATS_ONCE {mode} "
                "local_reducer_aggregate_exact_codec_matched_ppa_harness; "
                "hierarchy -check -top local_reducer_aggregate_exact_codec_matched_ppa_harness; "
                "proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
