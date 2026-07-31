import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_finalizer_bank_control import build_report
from npu.rtlgen.gen_attention_score32_exact_finalizer_bank_control import generate


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


def _compile_and_run(top_v: Path, tb_v: Path, *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    simv = tb_v.with_suffix(".out")
    compiled = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(top_v),
            str(tb_v),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert compiled.returncode == 0, compiled.stderr
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=timeout)
    assert run.returncode == 0, f"{run.stdout}\n{run.stderr}"
    return run


def _config(finalizer_banks: int, *, divider_lanes: int = 8) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_finalizer_bank_control_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_finalizer_bank_control": {
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalizer_bank_control_manifest_and_verilator_lint(tmp_path: Path) -> None:
    cfg = _config(59)
    generate(cfg, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_finalizer_bank_control_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["finalizer_banks"] == 59
    assert manifest["divider_lanes"] == 8
    assert manifest["order_fifo_depth"] == 59
    assert manifest["transaction_id_bits"] == 16
    assert manifest["control_only_embodied"] is True
    assert manifest["bank_arithmetic_embodied"] is False
    assert manifest["tree_payload_fanout_embodied"] is False
    assert manifest["root_payload_mux_embodied"] is False
    assert manifest["exact_service_model_cycle_equivalence"] is True
    assert manifest["service_model"]["per_bank_accept_interval_cycles"] == 59
    assert manifest["top_pin_estimate_bits"] == 2543

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "--top-module",
            str(cfg["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


def test_finalizer_bank_control_rejects_invalid_bank_counts(tmp_path: Path) -> None:
    for banks in (0, 65):
        with pytest.raises(SystemExit, match="finalizer_banks must be in \\[1, 64\\]"):
            generate(_config(banks), tmp_path / f"rtl_{banks}")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 4, 8, 16, 32, 59])
def test_finalizer_bank_control_probe_matches_service_model(finalizer_banks: int) -> None:
    report = build_report(clusters=2, heads=2, divider_lanes=8, finalizer_banks=finalizer_banks)
    assert report["passed"] is True
    assert report["outputs"] == 32
    assert report["service_contract"]["finalizer_banks"] == finalizer_banks
    assert report["service_contract"]["per_bank_accept_interval_cycles"] == 59
    assert report["observed_transaction_hash"] == report["expected_transaction_hash"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalizer_bank_control_full_wave_b59_matches_transaction_order() -> None:
    report = build_report(clusters=16, heads=32, divider_lanes=8, finalizer_banks=59)
    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["dispatch_stall_cycles"] == 0
    assert report["observed_transaction_hash"] == report["expected_transaction_hash"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalizer_bank_control_same_cycle_same_bank_replace_keeps_outstanding(tmp_path: Path) -> None:
    cfg = _config(1)
    rtl_dir = tmp_path / "rtl"
    tb_path = tmp_path / "tb.sv"
    generate(cfg, rtl_dir)
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer TRANSACTION_ID_BITS = 16;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg tree_valid = 1'b0;
  wire tree_ready;
  reg [TRANSACTION_ID_BITS-1:0] tree_transaction_id = {{TRANSACTION_ID_BITS{{1'b0}}}};
  wire [0:0] bank_in_valid;
  reg [0:0] bank_in_ready = 1'b0;
  wire [TRANSACTION_ID_BITS-1:0] bank_in_transaction_id;
  reg [0:0] bank_out_valid = 1'b0;
  wire [0:0] bank_out_ready;
  reg [TRANSACTION_ID_BITS-1:0] bank_out_transaction_id = {{TRANSACTION_ID_BITS{{1'b0}}}};
  wire root_valid;
  reg root_ready = 1'b0;
  wire [TRANSACTION_ID_BITS-1:0] root_transaction_id;
  wire [31:0] cycle_count;
  wire [31:0] tree_accepted_count;
  wire [31:0] root_completed_count;
  wire [31:0] order_fifo_occupancy;
  wire [31:0] order_fifo_high_watermark;
  wire [31:0] order_enqueued_count;
  wire [31:0] order_dequeued_count;
  wire [31:0] dispatch_stall_cycles;
  wire [31:0] dispatch_bank_id;
  wire [31:0] head_bank_id;
  wire [0:0] bank_outstanding;
  wire order_protocol_error;
  wire protocol_error;

  always #5 clk = ~clk;

  {cfg["top_name"]} dut (
      .clk(clk),
      .rst_n(rst_n),
      .tree_valid(tree_valid),
      .tree_ready(tree_ready),
      .tree_transaction_id(tree_transaction_id),
      .bank_in_valid(bank_in_valid),
      .bank_in_ready(bank_in_ready),
      .bank_in_transaction_id(bank_in_transaction_id),
      .bank_out_valid(bank_out_valid),
      .bank_out_ready(bank_out_ready),
      .bank_out_transaction_id(bank_out_transaction_id),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_transaction_id(root_transaction_id),
      .cycle_count(cycle_count),
      .tree_accepted_count(tree_accepted_count),
      .root_completed_count(root_completed_count),
      .order_fifo_occupancy(order_fifo_occupancy),
      .order_fifo_high_watermark(order_fifo_high_watermark),
      .order_enqueued_count(order_enqueued_count),
      .order_dequeued_count(order_dequeued_count),
      .dispatch_stall_cycles(dispatch_stall_cycles),
      .dispatch_bank_id(dispatch_bank_id),
      .head_bank_id(head_bank_id),
      .bank_outstanding(bank_outstanding),
      .order_protocol_error(order_protocol_error),
      .protocol_error(protocol_error)
  );

  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    tree_valid = 1'b1;
    tree_transaction_id = 16'h1001;
    bank_in_ready = 1'b1;
    #1;
    if (tree_ready !== 1'b1) $fatal(1, "first issue should be accepted");
    @(posedge clk);
    #1;
    if (tree_accepted_count !== 32'd1) $fatal(1, "first issue missing");
    if (order_fifo_occupancy !== 32'd1) $fatal(1, "fifo occupancy should be 1 after first issue");
    if (bank_outstanding !== 1'b1) $fatal(1, "bank should be outstanding after first issue");

    @(negedge clk);
    tree_transaction_id = 16'h1002;
    bank_out_valid = 1'b1;
    bank_out_transaction_id = 16'h1001;
    root_ready = 1'b1;
    #1;
    if (root_valid !== 1'b1) $fatal(1, "root should see the retiring bank");
    if (root_transaction_id !== 16'h1001) $fatal(1, "root transaction id should come from fifo head");
    if (tree_ready !== 1'b1) $fatal(1, "same-cycle replacement should be admitted by generic bank control");
    @(posedge clk);
    #1;
    if (tree_accepted_count !== 32'd2) $fatal(1, "replacement issue missing");
    if (root_completed_count !== 32'd1) $fatal(1, "dequeue count missing");
    if (order_fifo_occupancy !== 32'd1) $fatal(1, "fifo occupancy should remain 1 on replace");
    if (bank_outstanding !== 1'b1) $fatal(1, "same-bank replace must keep outstanding asserted");
    if (order_protocol_error !== 1'b0 || protocol_error !== 1'b0) $fatal(1, "unexpected protocol error");
    $display("PASS same-cycle same-bank replace keeps outstanding");
    #1 $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    run = _compile_and_run(rtl_dir / "top.v", tb_path)
    assert "PASS same-cycle same-bank replace keeps outstanding" in run.stdout
