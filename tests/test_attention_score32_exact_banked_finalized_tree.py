import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_banked_finalized_tree import build_report
from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    exact_banked_finalized_tree_full_wave_saturated_service,
    merge_balanced_partial_streams,
    partial_stream_from_blocks,
    simulate_exact_banked_finalizer,
)


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


def _config(finalizer_banks: int, *, clusters: int = 16, divider_lanes: int = 8) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_banked_finalized_tree_c{clusters}_r2_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_banked_finalized_tree": {
            "clusters": clusters,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


def _commands(heads: int) -> tuple[dict[str, int], ...]:
    return tuple({"command_id": 0x5A00 + head_index, "head_id": head_index} for head_index in range(heads))


def _score_rows(leaf: int, command_index: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(
            ((leaf * 43 + command_index * 29 + block * 17 + lane * 11) % 255) - 127 + (14 if lane == block else 0)
            for lane in range(8)
        )
        for block in range(3)
    )


def _value_blocks(leaf: int, command_index: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]:
    return tuple(
        tuple(
            tuple(
                tuple(
                    ((leaf * 59 + command_index * 31 + block * 23 + value_slice * 13 + row * 7 + lane * 5) % 255)
                    - 127
                    for lane in range(8)
                )
                for row in range(8)
            )
            for value_slice in range(16)
        )
        for block in range(3)
    )


def _leaf_stream(leaf: int, *, heads: int) -> tuple[ExactPartialBeat, ...]:
    beats: list[ExactPartialBeat] = []
    for command_index, command in enumerate(_commands(heads)):
        beats.extend(
            partial_stream_from_blocks(
                command_id=int(command["command_id"]),
                head_id=int(command["head_id"]),
                score_rows=_score_rows(leaf, command_index),
                value_blocks=_value_blocks(leaf, command_index),
            )
        )
    return tuple(beats)


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_manifest_and_verilator_lint(tmp_path: Path) -> None:
    cfg = _config(59, clusters=16, divider_lanes=8)
    generate(cfg, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_banked_finalized_tree_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["finalizer_banks"] == 59
    assert manifest["order_fifo_depth"] == 59
    assert manifest["actual_finalizer_accept_interval_cycles"] == 59
    assert manifest["service_model"]["minimum_banks_for_wrap_free_lane8_service"] == 59
    assert manifest["direct_328bit_links_unclosed"] is True
    assert manifest["final_divider_embodied"] is True
    assert manifest["noc_closure"] is False
    assert manifest["sram_closure"] is False

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


def test_banked_finalized_tree_rejects_invalid_bank_counts(tmp_path: Path) -> None:
    for banks in (0, 65):
        with pytest.raises(SystemExit, match="finalizer_banks must be in \\[1, 64\\]"):
            generate(_config(banks), tmp_path / f"rtl_{banks}")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 16, 32, 57, 58, 59, 64])
def test_banked_finalized_tree_small_probe_all_checked_in_bank_counts(finalizer_banks: int) -> None:
    report = build_report(clusters=2, heads=1, divider_lanes=8, finalizer_banks=finalizer_banks)

    assert report["passed"] is True
    assert report["outputs"] == 16
    assert report["finalizer_accepted_count"] == 16
    assert report["tree_root_completed_count"] == 16
    assert report["per_bank_accept_interval_cycles"] == 59
    assert report["measured_workload_manifest"]["minimum_banks_for_wrap_free_lane8_service"] == 59


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 59])
def test_banked_finalized_tree_full_c16_heads32_exact_regression(finalizer_banks: int) -> None:
    report = build_report(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=finalizer_banks,
        saturated=True,
        output_ready_pattern=(True,),
    )

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["finalizer_accepted_count"] == 512
    assert report["tree_root_completed_count"] == 512
    assert report["leaf_accept_count"] == [512] * 16
    assert report["measured_workload_manifest"]["measured_heads"] == 32
    assert report["measured_workload_manifest"]["total_leaf_beats"] == 8192
    assert report["observed_root_hash"] == "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_root_backpressure_order_stress() -> None:
    report = build_report(
        clusters=4,
        heads=4,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True, False, True, True, False, True, False, True, True, True),
    )

    assert report["passed"] is True
    assert report["protocol_error"] is False
    assert report["order_protocol_error"] is False
    assert report["finalizer_protocol_error"] is False


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_non_power_of_two_pointer_wrap() -> None:
    report = build_report(
        clusters=4,
        heads=4,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True,),
    )

    assert report["passed"] is True
    assert report["outputs"] == 64
    assert report["order_fifo_high_watermark"] <= 57


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_bank59_is_first_wrap_free_lane8_point_under_saturated_no_stall() -> None:
    bank57 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=57,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank58 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=58,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank59 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=59,
        saturated=True,
        output_ready_pattern=(True,),
    )
    bank64 = build_report(
        clusters=2,
        heads=5,
        divider_lanes=8,
        finalizer_banks=64,
        saturated=True,
        output_ready_pattern=(True,),
    )

    for report in (bank57, bank58, bank59, bank64):
        assert report["passed"] is True

    interval57 = bank57["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval58 = bank58["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval59 = bank59["measured_workload_manifest"]["measured_root_output_interval_cycles"]
    interval64 = bank64["measured_workload_manifest"]["measured_root_output_interval_cycles"]

    assert interval57 > interval58 > interval59
    assert interval59 == interval64


def test_bank_wrap_boundary_full_wave_perf_model() -> None:
    merged = merge_balanced_partial_streams([_leaf_stream(leaf, heads=32) for leaf in range(16)])
    bank57 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=57, output_ready_pattern=(True,))
    bank58 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=58, output_ready_pattern=(True,))
    bank59 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=59, output_ready_pattern=(True,))
    bank64 = simulate_exact_banked_finalizer(merged, divider_lanes=8, finalizer_banks=64, output_ready_pattern=(True,))

    assert bank57["completed_count"] == 512
    assert bank58["completed_count"] == 512
    assert bank59["completed_count"] == 512
    assert bank64["completed_count"] == 512
    assert bank57["result_events"][-1]["cycle"] - bank57["result_events"][0]["cycle"] == 527
    assert bank58["result_events"][-1]["cycle"] - bank58["result_events"][0]["cycle"] == 519
    assert bank59["result_events"][-1]["cycle"] - bank59["result_events"][0]["cycle"] == 511
    assert bank64["result_events"][-1]["cycle"] - bank64["result_events"][0]["cycle"] == 511


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_finalized_tree_embedded_finalizer_rejects_same_cycle_replace_attempt(tmp_path: Path) -> None:
    cfg = _config(1, clusters=2, divider_lanes=8)
    rtl_dir = tmp_path / "rtl"
    generate(cfg, rtl_dir)
    finalizer_name = f"{cfg['top_name']}__root_finalizer"
    tb_path = tmp_path / "tb.sv"
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg in_valid = 1'b0;
  wire in_ready;
  reg [15:0] in_command_id = 16'd0;
  reg [4:0] in_head_id = 5'd0;
  reg [32:0] in_exp_sum = 33'd1;
  reg [3:0] in_slice = 4'd0;
  reg in_last = 1'b0;
  reg [327:0] in_value = 328'd0;
  wire out_valid;
  reg out_ready = 1'b0;
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire [3:0] out_slice;
  wire out_last;
  wire [319:0] out_value;
  wire [31:0] accepted_count;
  wire [31:0] completed_count;
  wire [31:0] cycle_count;
  wire protocol_error;
  integer wait_cycles;

  always #5 clk = ~clk;

  {finalizer_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(in_valid),
      .in_ready(in_ready),
      .in_command_id(in_command_id),
      .in_head_id(in_head_id),
      .in_exp_sum(in_exp_sum),
      .in_slice(in_slice),
      .in_last(in_last),
      .in_value(in_value),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_command_id(out_command_id),
      .out_head_id(out_head_id),
      .out_slice(out_slice),
      .out_last(out_last),
      .out_value(out_value),
      .accepted_count(accepted_count),
      .completed_count(completed_count),
      .cycle_count(cycle_count),
      .protocol_error(protocol_error)
  );

  initial begin
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
    in_valid = 1'b1;
    in_command_id = 16'h2001;
    #1;
    if (in_ready !== 1'b1) $fatal(1, "finalizer should accept first beat from idle");
    @(posedge clk);
    #1;
    if (accepted_count !== 32'd1) $fatal(1, "first beat was not accepted");
    @(negedge clk);
    in_valid = 1'b0;

    wait_cycles = 0;
    while (out_valid !== 1'b1 && wait_cycles < 600) begin
      @(negedge clk);
      wait_cycles = wait_cycles + 1;
    end
    if (out_valid !== 1'b1) $fatal(1, "timed out waiting for finalizer output");

    in_valid = 1'b1;
    in_command_id = 16'h2002;
    out_ready = 1'b1;
    #1;
    if (in_ready !== 1'b0) $fatal(1, "embedded finalizer must reject same-cycle replacement");
    @(posedge clk);
    #1;
    if (accepted_count !== 32'd1) $fatal(1, "replacement should not be accepted");
    if (completed_count !== 32'd1) $fatal(1, "output should retire exactly once");
    if (protocol_error !== 1'b0) $fatal(1, "unexpected protocol error");
    @(negedge clk);
    in_valid = 1'b0;
    out_ready = 1'b0;
    #1;
    if (out_valid !== 1'b0) $fatal(1, "output valid should clear after retirement");
    $display("PASS embedded finalizer rejects same-cycle replace");
    #1 $finish;
  end
endmodule
""",
        encoding="utf-8",
    )
    run = _compile_and_run(rtl_dir / "top.v", tb_path, timeout=240)
    assert "PASS embedded finalizer rejects same-cycle replace" in run.stdout


def test_banked_finalized_tree_does_not_emit_unreachable_same_bank_replace_guard(tmp_path: Path) -> None:
    cfg = _config(1, clusters=2, divider_lanes=8)
    generate(cfg, tmp_path / "rtl")
    rtl_text = (tmp_path / "rtl" / "top.v").read_text(encoding="utf-8")
    assert "wire same_bank_replace_w =" not in rtl_text
    assert "if (bank_outstanding_q[dispatch_bank_q]) begin" in rtl_text
    assert "bank_outstanding_q[order_fifo_head_bank_id_w] <= 1'b0;" in rtl_text


def test_banked_finalized_tree_full_wave_saturated_service_matches_recorded_contract() -> None:
    bank1 = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=1,
    )
    bank57 = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=57,
    )
    bank58 = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=58,
    )
    bank59 = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=59,
    )
    bank64 = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=32,
        divider_lanes=8,
        finalizer_banks=64,
    )

    assert bank1["divider_iterations_per_group"] == 57
    assert bank1["per_bank_output_latency_cycles"] == 58
    assert bank1["per_bank_accept_interval_cycles"] == 59
    assert bank1["first_output_cycle"] == 62
    assert bank1["last_output_cycle"] == 30211
    assert bank1["drain_cycles"] == 30212
    assert bank1["interval_cycles"] == 30149
    assert bank1["cycles_per_beat"] == pytest.approx(59.0)
    assert bank1["dispatch_stall_cycles"] == 29638
    assert bank1["exact_no_stall_full_wave_service"] is False

    assert bank57["first_output_cycle"] == 62
    assert bank57["last_output_cycle"] == 589
    assert bank57["drain_cycles"] == 590
    assert bank57["interval_cycles"] == 527
    assert bank57["cycles_per_beat"] == pytest.approx(527 / 511)
    assert bank57["dispatch_stall_cycles"] == 16
    assert bank57["exact_no_stall_full_wave_service"] is False

    assert bank58["first_output_cycle"] == 62
    assert bank58["last_output_cycle"] == 581
    assert bank58["drain_cycles"] == 582
    assert bank58["interval_cycles"] == 519
    assert bank58["cycles_per_beat"] == pytest.approx(519 / 511)
    assert bank58["dispatch_stall_cycles"] == 8
    assert bank58["exact_no_stall_full_wave_service"] is False

    assert bank59["first_output_cycle"] == 62
    assert bank59["last_output_cycle"] == 573
    assert bank59["drain_cycles"] == 574
    assert bank59["interval_cycles"] == 511
    assert bank59["cycles_per_beat"] == pytest.approx(1.0)
    assert bank59["dispatch_stall_cycles"] == 0
    assert bank59["exact_no_stall_full_wave_service"] is True

    assert bank64["first_output_cycle"] == 62
    assert bank64["last_output_cycle"] == 573
    assert bank64["drain_cycles"] == 574
    assert bank64["interval_cycles"] == 511
    assert bank64["cycles_per_beat"] == pytest.approx(1.0)
    assert bank64["dispatch_stall_cycles"] == 0
    assert bank64["exact_no_stall_full_wave_service"] is True


def test_banked_finalized_tree_short_wave_no_stall_without_bank_reuse_wrap() -> None:
    short_wave = exact_banked_finalized_tree_full_wave_saturated_service(
        clusters=16,
        heads=1,
        divider_lanes=8,
        finalizer_banks=16,
    )

    assert short_wave["root_beats"] == 16
    assert short_wave["wrap_event_count"] == 0
    assert short_wave["wrap_shortage_cycles_per_bank_reuse"] == 43
    assert short_wave["dispatch_stall_cycles"] == 0
    assert short_wave["first_output_cycle"] == 62
    assert short_wave["last_output_cycle"] == 77
    assert short_wave["drain_cycles"] == 78
    assert short_wave["cycles_per_beat"] == pytest.approx(1.0)
    assert short_wave["exact_no_stall_full_wave_service"] is True


def test_banked_finalized_tree_full_wave_saturated_service_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="clusters must be a power of two in \\[2, 16\\]"):
        exact_banked_finalized_tree_full_wave_saturated_service(
            clusters=3,
            heads=32,
            divider_lanes=8,
            finalizer_banks=59,
        )
    with pytest.raises(ValueError, match="heads must be in \\[1, 32\\]"):
        exact_banked_finalized_tree_full_wave_saturated_service(
            clusters=16,
            heads=0,
            divider_lanes=8,
            finalizer_banks=59,
        )
    with pytest.raises(ValueError, match="divider_lanes must be one of 1, 2, 4, 8"):
        exact_banked_finalized_tree_full_wave_saturated_service(
            clusters=16,
            heads=32,
            divider_lanes=3,
            finalizer_banks=59,
        )
    with pytest.raises(ValueError, match="finalizer_banks must be in \\[1, 64\\]"):
        exact_banked_finalized_tree_full_wave_saturated_service(
            clusters=16,
            heads=32,
            divider_lanes=8,
            finalizer_banks=65,
        )
    with pytest.raises(ValueError, match="clusters must be an integer"):
        exact_banked_finalized_tree_full_wave_saturated_service(
            clusters=16.0,
            heads=32,
            divider_lanes=8,
            finalizer_banks=59,
        )


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_banked_probe_script_runs_without_pythonpath() -> None:
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_score32_exact_banked_finalized_tree.py",
            "--clusters",
            "2",
            "--heads",
            "1",
            "--divider-lanes",
            "8",
            "--finalizer-banks",
            "59",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["passed"] is True
    assert payload["finalizer_banks"] == 59
