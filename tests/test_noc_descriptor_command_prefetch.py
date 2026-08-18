from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not (shutil.which("iverilog") or Path("/oss-cad-suite/bin/iverilog").exists())
    or not (shutil.which("vvp") or Path("/oss-cad-suite/bin/vvp").exists()),
    reason="iverilog/vvp unavailable",
)
def test_noc_descriptor_command_prefetch_protocol(tmp_path: Path) -> None:
    iverilog = shutil.which("iverilog") or "/oss-cad-suite/bin/iverilog"
    vvp = shutil.which("vvp") or "/oss-cad-suite/bin/vvp"
    simulator = tmp_path / "prefetch.vvp"
    compile_result = subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "noc_descriptor_command_prefetch_tb",
            "-o",
            str(simulator),
            str(REPO_ROOT / "npu/sim/rtl/noc_descriptor_command_prefetch.sv"),
            str(REPO_ROOT / "tests/noc_descriptor_command_prefetch_tb.sv"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    simulation = subprocess.run(
        [vvp, str(simulator)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert simulation.returncode == 0, simulation.stderr
    assert "PASS prefetch commands=4" in simulation.stdout
