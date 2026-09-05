"""RTL contract test for the macro-backed RMSNorm row/gamma store."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_banked_row_gamma_store_macro_inventory_and_behavior(tmp_path: Path) -> None:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog/vvp unavailable")
    rtl = REPO_ROOT / "npu/sim/rtl/llama7b_rmsnorm_banked_row_gamma_store.sv"
    text = rtl.read_text(encoding="utf-8")
    assert "localparam integer LANES = 16" in text
    assert "localparam integer SHARDS = 4" in text
    assert "fakeram45_64x32 u_row_gamma_mem" in text

    sim = tmp_path / "store_sim"
    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "llama7b_rmsnorm_banked_row_gamma_store_tb",
            "-o",
            str(sim),
            str(REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"),
            str(rtl),
            str(REPO_ROOT / "tests/llama7b_rmsnorm_banked_row_gamma_store_tb.sv"),
        ],
        check=True,
    )
    result = subprocess.run(["vvp", str(sim)], check=True, capture_output=True, text=True)
    assert "PASS" in result.stdout


def test_banked_row_gamma_store_elaborates_exactly_64_macros() -> None:
    if not shutil.which("yosys"):
        pytest.skip("yosys unavailable")
    result = subprocess.run(
        [
            "yosys",
            "-Q",
            "-p",
            "read_verilog -sv "
            "npu/rtl/fakeram45_64x32_blackbox.v "
            "npu/sim/rtl/llama7b_rmsnorm_banked_row_gamma_store.sv; "
            "hierarchy -top llama7b_rmsnorm_banked_row_gamma_store; proc; opt; stat",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "fakeram45_64x32                64" in result.stdout
    assert "Number of memories:               0" in result.stdout
