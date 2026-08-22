from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.rtlgen.gen_attention_shared_sram_read_group_adapter_ppa_harness import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS = (
    (256, 1),
    (256, 2),
    (512, 1),
    (512, 2),
)


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


@pytest.mark.parametrize(("beat_width", "group_slots"), CONFIGS)
def test_generator_manifest_and_rtl_compile(tmp_path: Path, beat_width: int, group_slots: int) -> None:
    top_name = f"attention_shared_sram_read_group_adapter_w{beat_width}_s{group_slots}"
    config_path = REPO_ROOT / "runs/designs/npu_blocks" / top_name / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    generate(config, tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_shared_sram_read_group_adapter_ppa_harness_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["top_name"] == top_name
    assert manifest["beat_width"] == beat_width
    assert manifest["group_slots"] == group_slots
    assert manifest["segments_per_macro_read"] == 1024 // beat_width
    assert manifest["buffer_payload_bits"] == 1024 * group_slots
    assert manifest["payload_reset_required"] is False
    assert manifest["full_capacity_macro_area_included"] is False
    assert manifest["synthetic_response_profile"] == "metadata_lane_replicated_v1"
    assert manifest["synthetic_response_generator_is_dut"] is False
    assert manifest["narrow_io_harness_overhead_included"] is True
    assert manifest["response_bus_retention"] == "kept_full_bus_endpoint_lane_fold_v1"
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    assert '(* keep = "true" *) reg [MACRO_W-1:0] slot_data' in rtl
    assert "slot_data[reset_i] <=" not in rtl
    assert "build_macro_word = {32{lane}};" in rtl
    assert '(* keep = "true" *) wire [BEAT_W-1:0] rsp_data;' in rtl
    assert "fold_beat = value[31:0] ^ value[BEAT_W-1 -: 32];" in rtl
    assert "32'h9e37_79b9 *" not in rtl

    if _tool("iverilog") is not None:
        subprocess.run(
            [_tool("iverilog"), "-g2012", "-s", top_name, "-o", str(tmp_path / "top.vvp"), str(tmp_path / "top.v")],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_generated_harness_completes_and_proves_four_to_one_access_reduction(tmp_path: Path) -> None:
    top_name = "attention_shared_sram_read_group_adapter_w256_s2"
    config = json.loads(
        (REPO_ROOT / "runs/designs/npu_blocks" / top_name / "config.json").read_text(encoding="utf-8")
    )
    generate(config, tmp_path)
    tb = f"""`timescale 1ns/1ps
module tb;
  reg clk = 0, rst_n = 0, start = 0;
  wire done, protocol_error, access_reduction_proven;
  wire [31:0] folded_result, cycle_count, beat_request_count, macro_read_count, beat_response_count;
  {top_name} dut(
    .clk(clk), .rst_n(rst_n), .start(start), .seed(32'h12345678),
    .done(done), .folded_result(folded_result), .cycle_count(cycle_count),
    .beat_request_count(beat_request_count), .macro_read_count(macro_read_count),
    .beat_response_count(beat_response_count), .protocol_error(protocol_error),
    .access_reduction_proven(access_reduction_proven));
  always #5 clk = ~clk;
  initial begin
    repeat (3) @(negedge clk); rst_n = 1; start = 1;
    @(negedge clk); start = 0;
    wait(done); @(posedge clk);
    if (protocol_error || !access_reduction_proven || beat_request_count != 256 ||
        macro_read_count != 64 || beat_response_count != 256) $fatal(1, "harness contract failed");
    $display("PASS harness cycles=%0d fold=%h", cycle_count, folded_result);
    $finish;
  end
  initial begin #200000; $fatal(1, "timeout"); end
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
        [_tool("vvp"), str(sim)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "PASS harness" in run.stdout
