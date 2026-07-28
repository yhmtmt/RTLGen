import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_partial_producer_tree import build_report
from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree import generate

_FAKERAM_MODEL = """
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  initial begin addr_q = 0; rd_out_q = 0; for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0; end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) for (idx = 0; idx < 39; idx = idx + 1)
        if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config_path(name: str = "config.json") -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_producer_tree_c2_r2_l8_b59"
        / name
    )


def _load_config(name: str = "config.json") -> dict[str, object]:
    return json.loads(_config_path(name).read_text(encoding="utf-8"))


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_producer_tree_manifest_and_verilator_lint(tmp_path: Path) -> None:
    config = _load_config()
    generate(config, tmp_path / "rtl")
    fakeram_path = tmp_path / "fakeram45_2048x39.sv"
    fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_partial_producer_tree_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["producers"] == 2
    assert manifest["clusters"] == 2
    assert manifest["divider_lanes"] == 8
    assert manifest["finalizer_banks"] == 59
    assert manifest["producer_result_mode"] == "exact_partial"
    assert manifest["llama_tile_cadence_unclosed"] is True
    assert manifest["service_model"]["per_bank_accept_interval_cycles"] == 59

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
            str(fakeram_path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


def test_exact_partial_producer_tree_rejects_non_b59_config(tmp_path: Path) -> None:
    config = _load_config()
    config["attention_score32_exact_partial_producer_tree"]["finalizer_banks"] = 58
    with pytest.raises(SystemExit, match="producer-coupled slice currently requires finalizer_banks=59"):
        generate(config, tmp_path / "rtl")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_producer_tree_small_native_overlap_probe() -> None:
    report = build_report(config=_load_config())

    assert report["passed"] is True
    assert report["outputs"] == 64
    assert report["command_accept_count"] == 4
    assert report["command_complete_count"] == 4
    assert report["finalizer_accepted_count"] == 64
    assert report["tree_root_completed_count"] == 64
    assert report["producer_parallel_then_reducer_bound_cycles"] == 1627
    assert report["producer_parallel_then_reducer_overlap_cycles_saved"] == 82
    assert report["producer_fully_serialized_then_reducer_diagnostic"]["drain_cycles"] == 3090
    assert report["protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_producer_tree_backpressure_and_skew_stress() -> None:
    report = build_report(
        config=_load_config(),
        heads=6,
        output_ready_pattern=(True, False, True, True, False, True, False, True, True, True, False, True),
    )

    assert report["passed"] is True
    assert report["outputs"] == 96
    assert report["tree_dispatch_stall_cycles"] >= 0
    assert report["producer_leaf_stall_cycles"][0] >= 0
    assert report["producer_leaf_stall_cycles"][1] >= 0
    assert report["order_protocol_error"] is False
    assert report["finalizer_protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_partial_producer_tree_full_heads32_native_probe() -> None:
    report = build_report(config=_load_config("config_heads32_native.json"))

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["command_accept_count"] == 32
    assert report["command_complete_count"] == 32
    assert report["finalizer_accepted_count"] == 512
    assert report["observed_root_hash"] == "f2573d701a6454ed4a4e12334560f2801cd941b33fd416ddea7c0492eacfdadf"
    assert report["integrated_drain_cycles"] == 11908
    assert report["producer_parallel_phase_drain_cycles"] == 12052
    assert report["producer_parallel_then_reducer_bound_cycles"] == 12623
    assert report["producer_parallel_then_reducer_overlap_cycles_saved"] == 715
    assert report["producer_fully_serialized_then_reducer_diagnostic"]["drain_cycles"] == 24352
