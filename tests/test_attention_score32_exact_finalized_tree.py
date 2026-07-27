import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_score32_exact_finalized_tree import build_report
from npu.rtlgen.gen_attention_score32_exact_finalized_tree import generate as generate_tree
from npu.rtlgen.gen_attention_score32_exact_root_finalizer import generate as generate_finalizer
from npu.sim.perf.attention_exact_partial import (
    ExactPartialBeat,
    finalize_partial_beat,
    merge_partial_beats,
    pack_final_values,
    pack_numerators,
    unpack_final_values,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_RESULT_RE = re.compile(
    r"RESULT idx=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) value=([0-9a-fA-F]+)"
)
_SUMMARY_RE = re.compile(r"SUMMARY accepted=(\d+) completed=(\d+) cycle=(\d+) protocol_error=(\d+)")
_WRAP_SUMMARY_RE = re.compile(
    r"SUMMARY outputs=(\d+) protocol_error=(\d+) tree_protocol_error=(\d+) finalizer_protocol_error=(\d+) completed=(\d+)"
)


def _finalizer_config(divider_lanes: int) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_root_finalizer_l{divider_lanes}",
        "attention_score32_exact_root_finalizer": {
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
        },
    }


def _wrapper_config(clusters: int, divider_lanes: int) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_finalized_tree_c{clusters}_r2_l{divider_lanes}",
        "attention_score32_exact_finalized_tree": {
            "clusters": clusters,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
        },
    }


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


def _signed_literal(value: int, bits: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _beat(
    *,
    command_id: int = 0x4A21,
    head_id: int = 3,
    slice_index: int = 0,
    last: bool = False,
    max_score: int = 15,
    exp_sum: int = 19,
    numerators: tuple[int, ...] = (11, -9, 7, -5, 3, -1, 2, -2),
) -> ExactPartialBeat:
    return ExactPartialBeat(
        command_id=command_id,
        head_id=head_id,
        slice_index=slice_index,
        last=last,
        max_score=max_score,
        exp_sum=exp_sum,
        numerators=numerators,
    )


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_root_finalizer_and_wrapper_manifests(tmp_path: Path) -> None:
    generate_finalizer(_finalizer_config(4), tmp_path / "finalizer")
    generate_tree(_wrapper_config(16, 8), tmp_path / "wrapper")

    finalizer_manifest = json.loads(
        (tmp_path / "finalizer" / "attention_score32_exact_root_finalizer_manifest.json").read_text(encoding="utf-8")
    )
    wrapper_manifest = json.loads(
        (tmp_path / "wrapper" / "attention_score32_exact_finalized_tree_manifest.json").read_text(encoding="utf-8")
    )

    assert finalizer_manifest["divider_lanes"] == 4
    assert finalizer_manifest["divider_cycles_per_beat"] == 114
    assert finalizer_manifest["final_divider_embodied"] is True
    assert wrapper_manifest["clusters"] == 16
    assert wrapper_manifest["divider_lanes"] == 8
    assert wrapper_manifest["direct_328bit_links_unclosed"] is True
    assert wrapper_manifest["final_divider_embodied"] is True


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_root_finalizer_rtl_matches_reference_and_flags_exp_sum_zero(tmp_path: Path) -> None:
    beats = [
        _beat(
            command_id=0x4A31,
            head_id=5,
            slice_index=0,
            last=False,
            exp_sum=37,
            numerators=(91, -77, 63, -51, 39, -27, 15, -3),
        ),
        _beat(
            command_id=0x4A32,
            head_id=6,
            slice_index=15,
            last=True,
            exp_sum=91,
            numerators=(-255, 222, -189, 156, -123, 90, -57, 24),
        ),
        _beat(
            command_id=0x4A33,
            head_id=7,
            slice_index=15,
            last=True,
            exp_sum=0,
            numerators=(17, -15, 13, -11, 9, -7, 5, -3),
        ),
    ]
    expected_rows = [
        {
            "command_id": row.command_id,
            "head_id": row.head_id,
            "slice": row.slice_index,
            "last": row.last,
            "value": list(row.values),
        }
        for row in [finalize_partial_beat(beats[0]), finalize_partial_beat(beats[1])]
    ]
    expected_rows.append(
        {
            "command_id": beats[2].command_id,
            "head_id": beats[2].head_id,
            "slice": beats[2].slice_index,
            "last": beats[2].last,
            "value": [0] * 8,
        }
    )

    generate_finalizer(_finalizer_config(4), tmp_path / "rtl")
    tb_path = tmp_path / "tb.sv"
    beat_init = []
    for index, beat in enumerate(beats):
        beat_init.append(
            f"    cmd_mem[{index}] = 16'h{beat.command_id:04x}; "
            f"head_mem[{index}] = 5'd{beat.head_id}; "
            f"sum_mem[{index}] = 33'd{beat.exp_sum}; "
            f"slice_mem[{index}] = 4'd{beat.slice_index}; "
            f"last_mem[{index}] = 1'b{1 if beat.last else 0}; "
            f"value_mem[{index}] = 328'h{pack_numerators(beat.numerators):082x};"
        )
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer CASE_COUNT = {len(beats)};
  reg clk = 0, rst_n = 0;
  reg in_valid, out_ready;
  wire in_ready, out_valid, out_last, protocol_error;
  reg [15:0] cmd_mem [0:CASE_COUNT-1];
  reg [4:0] head_mem [0:CASE_COUNT-1];
  reg [32:0] sum_mem [0:CASE_COUNT-1];
  reg [3:0] slice_mem [0:CASE_COUNT-1];
  reg last_mem [0:CASE_COUNT-1];
  reg [327:0] value_mem [0:CASE_COUNT-1];
  wire [15:0] out_command_id;
  wire [4:0] out_head_id;
  wire [3:0] out_slice;
  wire [319:0] out_value;
  wire [31:0] accepted_count, completed_count, cycle_count;
  integer cycle = 0, issue = 0, seen = 0;
  reg pending_summary = 0;

  always #5 clk = ~clk;

  attention_score32_exact_root_finalizer_l4 dut (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(in_valid),
      .in_ready(in_ready),
      .in_command_id(cmd_mem[issue]),
      .in_head_id(head_mem[issue]),
      .in_exp_sum(sum_mem[issue]),
      .in_slice(slice_mem[issue]),
      .in_last(last_mem[issue]),
      .in_value(value_mem[issue]),
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

  always @* begin
    in_valid = rst_n && issue < CASE_COUNT;
    out_ready = (cycle % 4) != 1;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issue <= 0;
      seen <= 0;
      pending_summary <= 0;
    end else begin
      cycle <= cycle + 1;
      if (in_valid && in_ready) issue <= issue + 1;
      if (out_valid && out_ready) begin
        $display("RESULT idx=%0d cmd=%0d head=%0d slice=%0d last=%0d value=%080x",
                 seen, out_command_id, out_head_id, out_slice, out_last, out_value);
        seen <= seen + 1;
        if (seen + 1 == CASE_COUNT) pending_summary <= 1;
      end
      if (pending_summary) begin
        $display("SUMMARY accepted=%0d completed=%0d cycle=%0d protocol_error=%0d",
                 accepted_count, completed_count, cycle_count, protocol_error);
        #1 $finish;
      end
      if (cycle > 1200) $fatal(1, "timeout");
    end
  end

  initial begin
{chr(10).join(beat_init)}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
""",
        encoding="utf-8",
    )
    simv = tmp_path / "simv"
    compiled = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "rtl" / "top.v"),
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, f"{run.stdout}\n{run.stderr}"

    observed_rows = []
    summary = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _RESULT_RE.fullmatch(stripped):
            observed_rows.append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "value": list(unpack_final_values(int(match.group(6), 16))),
                }
            )
        elif match := _SUMMARY_RE.fullmatch(stripped):
            summary = {
                "accepted": int(match.group(1)),
                "completed": int(match.group(2)),
                "cycle": int(match.group(3)),
                "protocol_error": bool(int(match.group(4))),
            }

    assert observed_rows == expected_rows
    assert summary == {"accepted": 3, "completed": 3, "cycle": summary["cycle"], "protocol_error": True}
    assert summary["cycle"] >= (2 * 114)


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalized_tree_wrapper_preserves_tree_protocol_errors(tmp_path: Path) -> None:
    canonical_left = [
        _beat(
            command_id=0x4A41,
            head_id=9,
            max_score=15,
            exp_sum=23,
            numerators=(11, -9, 7, -5, 3, -1, 2, -2),
        ),
        _beat(
            command_id=0x4A42,
            head_id=9,
            max_score=27,
            exp_sum=31,
            numerators=(9, -7, 5, -3, 1, -1, 2, -2),
        ),
    ]
    canonical_right = [
        _beat(
            command_id=0x4A41,
            head_id=9,
            max_score=13,
            exp_sum=19,
            numerators=(-4, 6, -8, 10, -12, 14, -16, 18),
        ),
        _beat(
            command_id=0x4A42,
            head_id=9,
            max_score=21,
            exp_sum=17,
            numerators=(-8, 6, -4, 2, -1, 3, -5, 7),
        ),
    ]
    expected_rows = [
        finalize_partial_beat(merge_partial_beats(canonical_left[0], canonical_right[0])),
        finalize_partial_beat(merge_partial_beats(canonical_left[1], canonical_right[1])),
    ]

    generate_tree(_wrapper_config(2, 8), tmp_path / "rtl")
    tb_path = tmp_path / "tb.sv"
    left_cmd = [canonical_left[0].command_id, canonical_left[1].command_id]
    right_cmd = [canonical_right[0].command_id + 1, canonical_right[1].command_id]
    left_last = [int(canonical_left[0].last), 1]
    right_last = [int(canonical_right[0].last), 1]
    leaf0_init = []
    leaf1_init = []
    for index, beat in enumerate(canonical_left):
        leaf0_init.append(
            f"    l0_cmd[{index}] = 16'h{left_cmd[index]:04x}; l0_head[{index}] = 5'd{beat.head_id}; "
            f"l0_max[{index}] = {_signed_literal(beat.max_score, 32)}; l0_sum[{index}] = 33'd{beat.exp_sum}; "
            f"l0_slice[{index}] = 4'd{beat.slice_index}; l0_last[{index}] = 1'b{left_last[index]}; "
            f"l0_value[{index}] = 328'h{pack_numerators(beat.numerators):082x};"
        )
    for index, beat in enumerate(canonical_right):
        leaf1_init.append(
            f"    l1_cmd[{index}] = 16'h{right_cmd[index]:04x}; l1_head[{index}] = 5'd{beat.head_id}; "
            f"l1_max[{index}] = {_signed_literal(beat.max_score, 32)}; l1_sum[{index}] = 33'd{beat.exp_sum}; "
            f"l1_slice[{index}] = 4'd{beat.slice_index}; l1_last[{index}] = 1'b{right_last[index]}; "
            f"l1_value[{index}] = 328'h{pack_numerators(beat.numerators):082x};"
        )
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer CASE_COUNT = 2;
  reg clk = 0, rst_n = 0;
  reg [15:0] l0_cmd [0:CASE_COUNT-1];
  reg [4:0] l0_head [0:CASE_COUNT-1];
  reg signed [31:0] l0_max [0:CASE_COUNT-1];
  reg [32:0] l0_sum [0:CASE_COUNT-1];
  reg [3:0] l0_slice [0:CASE_COUNT-1];
  reg l0_last [0:CASE_COUNT-1];
  reg [327:0] l0_value [0:CASE_COUNT-1];
  reg [15:0] l1_cmd [0:CASE_COUNT-1];
  reg [4:0] l1_head [0:CASE_COUNT-1];
  reg signed [31:0] l1_max [0:CASE_COUNT-1];
  reg [32:0] l1_sum [0:CASE_COUNT-1];
  reg [3:0] l1_slice [0:CASE_COUNT-1];
  reg l1_last [0:CASE_COUNT-1];
  reg [327:0] l1_value [0:CASE_COUNT-1];
  reg [1:0] leaf_valid;
  wire [1:0] leaf_ready;
  wire root_valid, root_last, tree_protocol_error, finalizer_protocol_error, protocol_error;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire [3:0] root_slice;
  wire [319:0] root_value;
  wire [31:0] cycle_count, root_completed_count, finalizer_accepted_count, tree_root_completed_count;
  wire [31:0] node_completed_count;
  wire [31:0] stage_completed_count;
  wire node_protocol_error;
  wire stage_protocol_error;
  integer cycle = 0, issue = 0, seen = 0;
  reg pending_summary = 0;

  always #5 clk = ~clk;

  attention_score32_exact_finalized_tree_c2_r2_l8 dut (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid),
      .leaf_ready(leaf_ready),
      .leaf_command_id({{l1_cmd[issue], l0_cmd[issue]}}),
      .leaf_head_id({{l1_head[issue], l0_head[issue]}}),
      .leaf_global_max({{l1_max[issue], l0_max[issue]}}),
      .leaf_exp_sum({{l1_sum[issue], l0_sum[issue]}}),
      .leaf_slice({{l1_slice[issue], l0_slice[issue]}}),
      .leaf_last({{l1_last[issue], l0_last[issue]}}),
      .leaf_value({{l1_value[issue], l0_value[issue]}}),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(cycle_count),
      .root_completed_count(root_completed_count),
      .finalizer_accepted_count(finalizer_accepted_count),
      .tree_root_completed_count(tree_root_completed_count),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .tree_protocol_error(tree_protocol_error),
      .finalizer_protocol_error(finalizer_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    leaf_valid = (rst_n && issue < CASE_COUNT) ? 2'b11 : 2'b00;
    root_ready = (cycle % 5) != 2;
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      issue <= 0;
      seen <= 0;
      pending_summary <= 0;
    end else begin
      cycle <= cycle + 1;
      if (&leaf_ready && leaf_valid == 2'b11) issue <= issue + 1;
      if (root_valid && root_ready) begin
        $display("RESULT idx=%0d cmd=%0d head=%0d slice=%0d last=%0d value=%080x",
                 seen, root_command_id, root_head_id, root_slice, root_last, root_value);
        seen <= seen + 1;
        if (seen + 1 == CASE_COUNT) pending_summary <= 1;
      end
      if (pending_summary) begin
        $display("SUMMARY outputs=%0d protocol_error=%0d tree_protocol_error=%0d finalizer_protocol_error=%0d completed=%0d",
                 seen, protocol_error, tree_protocol_error, finalizer_protocol_error, root_completed_count);
        #1 $finish;
      end
      if (cycle > 400) $fatal(1, "timeout");
    end
  end

  initial begin
{chr(10).join(leaf0_init)}
{chr(10).join(leaf1_init)}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;
  end
endmodule
""",
        encoding="utf-8",
    )
    simv = tmp_path / "simv"
    compiled = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "rtl" / "top.v"),
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert compiled.returncode == 0, compiled.stderr
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, f"{run.stdout}\n{run.stderr}"

    observed_rows = []
    summary = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := _RESULT_RE.fullmatch(stripped):
            observed_rows.append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "value": list(unpack_final_values(int(match.group(6), 16))),
                }
            )
        elif match := _WRAP_SUMMARY_RE.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "protocol_error": bool(int(match.group(2))),
                "tree_protocol_error": bool(int(match.group(3))),
                "finalizer_protocol_error": bool(int(match.group(4))),
                "completed": int(match.group(5)),
            }

    assert observed_rows == [
        {
            "command_id": expected_rows[0].command_id,
            "head_id": expected_rows[0].head_id,
            "slice": expected_rows[0].slice_index,
            "last": expected_rows[0].last,
            "value": list(expected_rows[0].values),
        },
        {
            "command_id": expected_rows[1].command_id,
            "head_id": expected_rows[1].head_id,
            "slice": expected_rows[1].slice_index,
            "last": True,
            "value": list(expected_rows[1].values),
        },
    ]
    assert summary == {
        "outputs": 2,
        "protocol_error": True,
        "tree_protocol_error": True,
        "finalizer_protocol_error": True,
        "completed": 2,
    }


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("divider_lanes", [1, 2, 4, 8])
def test_exact_finalized_tree_probe_c2_lanes(divider_lanes: int) -> None:
    report = build_report(clusters=2, heads=1, divider_lanes=divider_lanes)

    assert report["passed"] is True
    assert report["outputs"] == 16
    assert report["finalizer_accepted_count"] == 16
    assert report["tree_root_completed_count"] == 16
    assert report["measured_workload_manifest"]["measured_heads"] == 1
    assert report["ideal_divider_cycles_per_beat"] == {1: 456, 2: 228, 4: 114, 8: 57}[divider_lanes]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_exact_finalized_tree_probe_c16_heads32_lane8() -> None:
    report = build_report(clusters=16, heads=32, divider_lanes=8)

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["finalizer_accepted_count"] == 512
    assert report["tree_root_completed_count"] == 512
    assert report["leaf_accept_count"] == [512] * 16
    assert report["measured_workload_manifest"]["measured_heads"] == 32
    assert report["measured_workload_manifest"]["total_leaf_beats"] == 8192
    assert report["observed_root_hash"] == "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_probe_script_runs_without_pythonpath() -> None:
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_score32_exact_finalized_tree.py",
            "--clusters",
            "2",
            "--heads",
            "1",
            "--divider-lanes",
            "4",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["passed"] is True
    assert payload["clusters"] == 2
    assert payload["divider_lanes"] == 4
