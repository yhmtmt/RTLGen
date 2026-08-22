from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.rtlgen.gen_attention_shared_sram_k_round_scheduler_ppa_harness import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
TOP_NAME = "attention_shared_sram_k_round_scheduler_b17_w17"
CONFIG_PATH = REPO_ROOT / "runs/designs/npu_blocks" / TOP_NAME / "config.json"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


def test_generator_manifest_and_rtl_compile(tmp_path: Path) -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_shared_sram_k_round_scheduler_ppa_harness_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["top_name"] == TOP_NAME
    assert manifest["window_storage_bits"] == 2 * 17 * 1024
    assert manifest["compute_beats_per_command"] == 1024
    assert manifest["full_capacity_macro_area_included"] is False
    assert manifest["activity_checksum_is_equivalence_proof"] is False
    assert manifest["synthetic_response_profile"] == "metadata_lane_replicated_v1"
    assert manifest["synthetic_response_generator_is_dut"] is False
    assert manifest["narrow_io_harness_overhead_included"] is True
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    assert "build_word = {16{{lane ^ 32'ha5a5_5a5a, lane}}};" in rtl
    assert "32'h9e37_79b9 *" not in rtl

    if _tool("iverilog") is not None:
        subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", TOP_NAME, "-o", str(tmp_path / "top.vvp"), str(tmp_path / "top.v")],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_generated_harness_completes_full_checked_schedule(tmp_path: Path) -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    generate(config, tmp_path)
    tb = f"""`timescale 1ns/1ps
module tb;
  reg clk = 0, rst_n = 0, start = 0;
  wire done, protocol_error;
  wire [31:0] activity_checksum, cycle_count;
  wire [31:0] bank_request_count, bank_response_count, compute_beat_count;
  {TOP_NAME} dut(
    .clk(clk), .rst_n(rst_n), .start(start), .seed(32'h12345678),
    .done(done), .activity_checksum(activity_checksum), .cycle_count(cycle_count),
    .bank_request_count(bank_request_count), .bank_response_count(bank_response_count),
    .compute_beat_count(compute_beat_count), .protocol_error(protocol_error));
  always #5 clk = ~clk;
  initial begin
    repeat (3) @(negedge clk); rst_n = 1; start = 1;
    @(negedge clk); start = 0;
    wait(done); @(posedge clk);
    if (protocol_error || bank_request_count != 1024 ||
        bank_response_count != 1024 || compute_beat_count != 1024)
      $fatal(1, "harness contract failed");
    $display("PASS harness cycles=%0d checksum=%h", cycle_count, activity_checksum);
    $finish;
  end
  initial begin #300000; $fatal(1, "timeout"); end
endmodule
"""
    (tmp_path / "tb.sv").write_text(tb, encoding="utf-8")
    sim = tmp_path / "harness.vvp"
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "tb", "-o", str(sim), str(tmp_path / "top.v"), str(tmp_path / "tb.sv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    run = subprocess.run(
        [_tool("vvp"), str(sim)], cwd=REPO_ROOT, check=True, capture_output=True, text=True, timeout=30
    )
    assert "PASS harness" in run.stdout
