from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_score32_exact_kv_key_ingress_ppa_harness import (
    CONFIG_KEY,
    MANIFEST_NAME,
    generate,
)


ROOT = Path(__file__).resolve().parents[1]


def _config(*, architecture: str, producers: int) -> dict[str, object]:
    return {
        "top_name": f"kv_key_ingress_{architecture}_p{producers}",
        CONFIG_KEY: {
            "architecture": architecture,
            "producers": producers,
            "kv_head": 3,
        },
    }


@pytest.mark.parametrize("architecture", ["one_buffer_serial", "pingpong_wide_auto"])
@pytest.mark.parametrize("producers", [53, 54])
def test_harness_generation_is_manifested_and_lints(
    tmp_path: Path, architecture: str, producers: int
) -> None:
    out = tmp_path / f"{architecture}_p{producers}"
    config = _config(architecture=architecture, producers=producers)
    generate(config, out)
    manifest = json.loads((out / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["architecture"] == architecture
    assert manifest["producers"] == producers
    assert manifest["canonical_ingress_flits"] == 4096
    assert manifest["full_k_stage_macro_area_included"] is False
    assert manifest["narrow_io_harness_overhead_included"] is True
    assert manifest["top_pin_bits"] == 197
    rtl = (out / "top.v").read_text(encoding="utf-8")
    if architecture == "one_buffer_serial":
        assert "module attention_score32_exact_kv_key_single_buffer_transpose" in rtl
        assert "module attention_score32_exact_kv_ingress_transpose" not in rtl
        assert "value_data" not in rtl
    if shutil.which("verilator") is not None:
        completed = subprocess.run(
            [
                "verilator",
                "--lint-only",
                "-Wall",
                "--Wno-DECLFILENAME",
                "--top-module",
                str(config["top_name"]),
                str(out / "top.v"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.parametrize(
    ("architecture", "expected_cycles", "expected_outputs", "expected_stalls"),
    [
        ("one_buffer_serial", 12_352, 8_192, 8_064),
        ("pingpong_wide_auto", 4_160, 4_096, 0),
    ],
)
def test_harness_runs_complete_head_with_expected_service(
    tmp_path: Path,
    architecture: str,
    expected_cycles: int,
    expected_outputs: int,
    expected_stalls: int,
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    out = tmp_path / architecture
    config = _config(architecture=architecture, producers=53)
    generate(config, out)
    tb = tmp_path / f"tb_{architecture}.sv"
    tb.write_text(
        f"""`timescale 1ns/1ps
module tb;
  reg clk = 0;
  reg rst_n = 0;
  reg start = 0;
  reg [31:0] seed = 32'h1357_9bdf;
  wire done;
  wire [31:0] activity_checksum;
  wire [31:0] cycle_count;
  wire [31:0] ingress_accept_count;
  wire [31:0] output_accept_count;
  wire [31:0] ingress_stall_count;
  wire protocol_error;
  {config['top_name']} dut (.*);
  always #1 clk = ~clk;
  initial begin
    repeat (3) @(posedge clk);
    @(negedge clk); rst_n = 1; start = 1;
    @(posedge clk); @(negedge clk); start = 0;
    while (!done) @(posedge clk);
    @(negedge clk);
    if (cycle_count != 32'd{expected_cycles} ||
        ingress_accept_count != 32'd4096 ||
        output_accept_count != 32'd{expected_outputs} ||
        ingress_stall_count != 32'd{expected_stalls} ||
        protocol_error || activity_checksum == 0) begin
      $display("FAIL cycles=%0d ingress=%0d output=%0d stalls=%0d error=%0d checksum=%08x",
               cycle_count, ingress_accept_count, output_accept_count,
               ingress_stall_count, protocol_error, activity_checksum);
      $finish(1);
    end
    $display("PASS architecture={architecture} cycles=%0d", cycle_count);
    $finish(0);
  end
endmodule
""",
        encoding="utf-8",
    )
    binary = tmp_path / f"{architecture}.vvp"
    compiled = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(out / "top.v"), str(tb)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    completed = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"PASS architecture={architecture}" in completed.stdout
