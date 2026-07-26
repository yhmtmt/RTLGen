import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_score32_exact_partial_tree import build_report
from npu.rtlgen.gen_attention_score32_exact_partial_tree import generate as generate_tree
from npu.sim.perf.attention_exact_partial import ExactPartialBeat, merge_partial_beats, pack_numerators, unpack_numerators

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tree_config(clusters: int) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_partial_tree_c{clusters}_r2",
        "attention_score32_exact_partial_tree": {
            "clusters": clusters,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
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
    command_id: int,
    head_id: int,
    max_score: int,
    exp_sum: int,
    numerators: tuple[int, ...],
    slice_index: int = 0,
    last: bool = False,
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


def _run_protocol_vectors(tmp_path: Path) -> dict[str, object]:
    cases = [
        {
            "name": "metadata_mismatch",
            "canonical": [
                _beat(
                    command_id=0x4A21,
                    head_id=3,
                    max_score=15,
                    exp_sum=19,
                    numerators=(11, -9, 7, -5, 3, -1, 2, -2),
                ),
                _beat(
                    command_id=0x4A21,
                    head_id=3,
                    max_score=13,
                    exp_sum=17,
                    numerators=(-4, 6, -8, 10, -12, 14, -16, 18),
                ),
                _beat(
                    command_id=0x4A21,
                    head_id=3,
                    max_score=12,
                    exp_sum=11,
                    numerators=(5, -4, 3, -2, 1, -1, 2, -3),
                ),
                _beat(
                    command_id=0x4A21,
                    head_id=3,
                    max_score=9,
                    exp_sum=7,
                    numerators=(-7, 5, -3, 1, -2, 4, -6, 8),
                ),
            ],
            "overrides": [{}, {"command_id": 0x4A22}, {}, {}],
        },
        {
            "name": "invalid_last",
            "canonical": [
                _beat(
                    command_id=0x4A23,
                    head_id=7,
                    max_score=27,
                    exp_sum=23,
                    numerators=(9, -7, 5, -3, 1, -1, 2, -2),
                ),
                _beat(
                    command_id=0x4A23,
                    head_id=7,
                    max_score=22,
                    exp_sum=21,
                    numerators=(-8, 6, -4, 2, -1, 3, -5, 7),
                ),
                _beat(
                    command_id=0x4A23,
                    head_id=7,
                    max_score=25,
                    exp_sum=15,
                    numerators=(4, -3, 2, -1, 0, 1, -2, 3),
                ),
                _beat(
                    command_id=0x4A23,
                    head_id=7,
                    max_score=19,
                    exp_sum=13,
                    numerators=(-3, 4, -5, 6, -7, 8, -9, 10),
                ),
            ],
            "overrides": [{}, {"last": True}, {}, {}],
        },
    ]

    expected_rows = []
    for case in cases:
        left_stage = merge_partial_beats(case["canonical"][0], case["canonical"][1])
        right_stage = merge_partial_beats(case["canonical"][2], case["canonical"][3])
        merged = merge_partial_beats(left_stage, right_stage)
        expected_rows.append(
            {
                "command_id": merged.command_id,
                "head_id": merged.head_id,
                "slice": merged.slice_index,
                "last": merged.last,
                "global_max": merged.max_score,
                "exp_sum": merged.exp_sum,
                "value": list(merged.numerators),
            }
        )

    generate_tree(_tree_config(4), tmp_path / "rtl")
    tb_path = tmp_path / "tb.sv"
    leaf_init: list[str] = []
    for leaf in range(4):
        for case_index, case in enumerate(cases):
            beat = case["canonical"][leaf]
            override = case["overrides"][leaf]
            flat_index = (leaf * len(cases)) + case_index
            command_id = int(override.get("command_id", beat.command_id))
            last = bool(override.get("last", beat.last))
            leaf_init.append(
                f"    leaf_cmd_mem[{flat_index}] = 16'h{command_id:04x}; "
                f"leaf_head_mem[{flat_index}] = 5'd{beat.head_id}; "
                f"leaf_max_mem[{flat_index}] = {_signed_literal(beat.max_score, 32)}; "
                f"leaf_sum_mem[{flat_index}] = 33'd{beat.exp_sum}; "
                f"leaf_slice_mem[{flat_index}] = 4'd{beat.slice_index}; "
                f"leaf_last_mem[{flat_index}] = 1'b{1 if last else 0}; "
                f"leaf_value_mem[{flat_index}] = 328'h{pack_numerators(beat.numerators):082x};"
            )
    tb_path.write_text(
        f"""`timescale 1ns/1ps
module tb;
  localparam integer CLUSTERS = 4;
  localparam integer CASE_COUNT = {len(cases)};
  localparam integer MEM_DEPTH = CLUSTERS * CASE_COUNT;
  reg clk = 0, rst_n = 0;
  reg [CLUSTERS-1:0] leaf_valid;
  wire [CLUSTERS-1:0] leaf_ready;
  reg [(CLUSTERS*16)-1:0] leaf_command_id;
  reg [(CLUSTERS*5)-1:0] leaf_head_id;
  reg [(CLUSTERS*32)-1:0] leaf_global_max;
  reg [(CLUSTERS*33)-1:0] leaf_exp_sum;
  reg [(CLUSTERS*4)-1:0] leaf_slice;
  reg [CLUSTERS-1:0] leaf_last;
  reg [(CLUSTERS*328)-1:0] leaf_value;
  wire root_valid;
  reg root_ready;
  wire [15:0] root_command_id;
  wire [4:0] root_head_id;
  wire signed [31:0] root_global_max;
  wire [32:0] root_exp_sum;
  wire [3:0] root_slice;
  wire root_last;
  wire [327:0] root_value;
  wire [31:0] cycle_count;
  wire [31:0] root_completed_count;
  wire [95:0] node_completed_count;
  wire [63:0] stage_completed_count;
  wire [2:0] node_protocol_error;
  wire [1:0] stage_protocol_error;
  wire protocol_error;
  reg [15:0] leaf_cmd_mem [0:MEM_DEPTH-1];
  reg [4:0] leaf_head_mem [0:MEM_DEPTH-1];
  reg signed [31:0] leaf_max_mem [0:MEM_DEPTH-1];
  reg [32:0] leaf_sum_mem [0:MEM_DEPTH-1];
  reg [3:0] leaf_slice_mem [0:MEM_DEPTH-1];
  reg leaf_last_mem [0:MEM_DEPTH-1];
  reg [327:0] leaf_value_mem [0:MEM_DEPTH-1];
  reg [31:0] leaf_issue [0:CLUSTERS-1];
  reg [31:0] leaf_accept [0:CLUSTERS-1];
  integer cycle = 0;
  integer seen = 0;
  reg pending_summary = 0;
  integer leaf_index;
  integer init_index;

  always #5 clk = ~clk;

  attention_score32_exact_partial_tree_c4_r2 dut (
      .clk(clk),
      .rst_n(rst_n),
      .leaf_valid(leaf_valid),
      .leaf_ready(leaf_ready),
      .leaf_command_id(leaf_command_id),
      .leaf_head_id(leaf_head_id),
      .leaf_global_max(leaf_global_max),
      .leaf_exp_sum(leaf_exp_sum),
      .leaf_slice(leaf_slice),
      .leaf_last(leaf_last),
      .leaf_value(leaf_value),
      .root_valid(root_valid),
      .root_ready(root_ready),
      .root_command_id(root_command_id),
      .root_head_id(root_head_id),
      .root_global_max(root_global_max),
      .root_exp_sum(root_exp_sum),
      .root_slice(root_slice),
      .root_last(root_last),
      .root_value(root_value),
      .cycle_count(cycle_count),
      .root_completed_count(root_completed_count),
      .node_completed_count(node_completed_count),
      .stage_completed_count(stage_completed_count),
      .node_protocol_error(node_protocol_error),
      .stage_protocol_error(stage_protocol_error),
      .protocol_error(protocol_error)
  );

  always @* begin
    leaf_valid = 4'b0;
    leaf_command_id = 64'b0;
    leaf_head_id = 20'b0;
    leaf_global_max = 128'b0;
    leaf_exp_sum = 132'b0;
    leaf_slice = 16'b0;
    leaf_last = 4'b0;
    leaf_value = 1312'b0;
    root_ready = (cycle % 3) != 1;
    for (leaf_index = 0; leaf_index < CLUSTERS; leaf_index = leaf_index + 1) begin
      if (rst_n && leaf_issue[leaf_index] < CASE_COUNT) begin
        leaf_valid[leaf_index] = 1'b1;
        leaf_command_id[(leaf_index * 16) +: 16] =
            leaf_cmd_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_head_id[(leaf_index * 5) +: 5] =
            leaf_head_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_global_max[(leaf_index * 32) +: 32] =
            leaf_max_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_exp_sum[(leaf_index * 33) +: 33] =
            leaf_sum_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_slice[(leaf_index * 4) +: 4] =
            leaf_slice_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_last[leaf_index] =
            leaf_last_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
        leaf_value[(leaf_index * 328) +: 328] =
            leaf_value_mem[(leaf_index * CASE_COUNT) + leaf_issue[leaf_index]];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      seen <= 0;
      pending_summary <= 1'b0;
      for (leaf_index = 0; leaf_index < CLUSTERS; leaf_index = leaf_index + 1) begin
        leaf_issue[leaf_index] <= 0;
        leaf_accept[leaf_index] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      for (leaf_index = 0; leaf_index < CLUSTERS; leaf_index = leaf_index + 1) begin
        if (leaf_valid[leaf_index] && leaf_ready[leaf_index]) begin
          leaf_accept[leaf_index] <= leaf_accept[leaf_index] + 1;
          leaf_issue[leaf_index] <= leaf_issue[leaf_index] + 1;
        end
      end
      if (root_valid && root_ready) begin
        $display("RESULT idx=%0d cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x",
                 seen, root_command_id, root_head_id, root_slice, root_last, $signed(root_global_max), root_exp_sum, root_value);
        seen <= seen + 1;
        if (seen + 1 == CASE_COUNT) pending_summary <= 1'b1;
      end
      if (pending_summary) begin
        for (leaf_index = 0; leaf_index < CLUSTERS; leaf_index = leaf_index + 1) begin
          $display("LEAF leaf=%0d accepted=%0d", leaf_index, leaf_accept[leaf_index]);
        end
        $display("NODE node=0 count=%0d error=%0d", node_completed_count[0 +: 32], node_protocol_error[0]);
        $display("NODE node=1 count=%0d error=%0d", node_completed_count[32 +: 32], node_protocol_error[1]);
        $display("NODE node=2 count=%0d error=%0d", node_completed_count[64 +: 32], node_protocol_error[2]);
        $display("STAGE stage=0 count=%0d error=%0d", stage_completed_count[0 +: 32], stage_protocol_error[0]);
        $display("STAGE stage=1 count=%0d error=%0d", stage_completed_count[32 +: 32], stage_protocol_error[1]);
        $display("SUMMARY outputs=%0d protocol_error=%0d root_completed=%0d cycle=%0d", seen, protocol_error, root_completed_count, cycle_count);
        #1 $finish;
      end
      if (cycle > 200) $fatal(1, "timeout");
    end
  end

  initial begin
    for (init_index = 0; init_index < MEM_DEPTH; init_index = init_index + 1) begin
      leaf_cmd_mem[init_index] = 16'd0;
      leaf_head_mem[init_index] = 5'd0;
      leaf_max_mem[init_index] = 32'sd0;
      leaf_sum_mem[init_index] = 33'd0;
      leaf_slice_mem[init_index] = 4'd0;
      leaf_last_mem[init_index] = 1'b0;
      leaf_value_mem[init_index] = 328'd0;
    end
{chr(10).join(leaf_init)}
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
    if compiled.returncode:
        raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
    run = subprocess.run([_tool("vvp"), str(simv)], capture_output=True, text=True, timeout=60)
    if run.returncode:
        raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")

    result_re = re.compile(
        r"RESULT idx=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)"
    )
    leaf_re = re.compile(r"LEAF leaf=(\d+) accepted=(\d+)")
    node_re = re.compile(r"NODE node=(\d+) count=(\d+) error=(\d+)")
    stage_re = re.compile(r"STAGE stage=(\d+) count=(\d+) error=(\d+)")
    summary_re = re.compile(r"SUMMARY outputs=(\d+) protocol_error=(\d+) root_completed=(\d+) cycle=(\d+)")
    observed_rows = []
    leaf_accept = [0] * 4
    node_count = [0] * 3
    node_error = [False] * 3
    stage_count = [0] * 2
    stage_error = [False] * 2
    summary = None
    for line in run.stdout.splitlines():
        stripped = line.strip()
        if match := result_re.fullmatch(stripped):
            observed_rows.append(
                {
                    "command_id": int(match.group(2)),
                    "head_id": int(match.group(3)),
                    "slice": int(match.group(4)),
                    "last": bool(int(match.group(5))),
                    "global_max": int(match.group(6)),
                    "exp_sum": int(match.group(7)),
                    "value": list(unpack_numerators(int(match.group(8), 16))),
                }
            )
        elif match := leaf_re.fullmatch(stripped):
            leaf_accept[int(match.group(1))] = int(match.group(2))
        elif match := node_re.fullmatch(stripped):
            node = int(match.group(1))
            node_count[node] = int(match.group(2))
            node_error[node] = bool(int(match.group(3)))
        elif match := stage_re.fullmatch(stripped):
            stage = int(match.group(1))
            stage_count[stage] = int(match.group(2))
            stage_error[stage] = bool(int(match.group(3)))
        elif match := summary_re.fullmatch(stripped):
            summary = {
                "outputs": int(match.group(1)),
                "protocol_error": bool(int(match.group(2))),
                "root_completed": int(match.group(3)),
                "cycle": int(match.group(4)),
            }
    if summary is None:
        raise RuntimeError("protocol regression summary missing")
    return {
        "expected_rows": expected_rows,
        "observed_rows": observed_rows,
        "leaf_accept": leaf_accept,
        "node_count": node_count,
        "node_error": node_error,
        "stage_count": stage_count,
        "stage_error": stage_error,
        "summary": summary,
    }


def test_exact_partial_tree_manifest_and_ports(tmp_path: Path) -> None:
    generate_tree(_tree_config(16), tmp_path)

    manifest = json.loads((tmp_path / "attention_score32_exact_partial_tree_manifest.json").read_text(encoding="utf-8"))
    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == "score32_online_exact_partial_radix2_tree_v1"
    assert manifest["clusters"] == 16
    assert manifest["tree_stages"] == 4
    assert manifest["tree_nodes"] == 15
    assert manifest["partial_payload_bits_per_beat"] == 328
    assert manifest["theoretical_full_llama_service_manifest"]["heads"] == 32
    assert manifest["theoretical_full_llama_service_manifest"]["exact_state_bytes_per_cluster"] == 21252
    assert manifest["theoretical_full_llama_service_manifest"]["total_leaf_stream_bytes"] == 429056
    assert manifest["direct_328bit_links_unclosed"] is True
    assert manifest["final_divider_embodied"] is False
    assert "input  wire [15:0] leaf_valid" in rtl
    assert "output wire         root_valid" in rtl
    assert "output wire [479:0] node_protocol_error" not in rtl
    assert "output wire [14:0] node_protocol_error" in rtl


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_tree_protocol_errors_are_sticky_and_localized(tmp_path: Path) -> None:
    report = _run_protocol_vectors(tmp_path)

    assert report["observed_rows"] == report["expected_rows"]
    assert report["leaf_accept"] == [2, 2, 2, 2]
    assert report["node_count"] == [2, 2, 2]
    assert report["stage_count"] == [4, 2]
    assert report["node_error"] == [True, False, False]
    assert report["stage_error"] == [True, False]
    assert report["summary"]["outputs"] == 2
    assert report["summary"]["root_completed"] == 2
    assert report["summary"]["protocol_error"] is True


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
@pytest.mark.parametrize("clusters,heads,stage_counts", [(2, 3, [48]), (4, 3, [96, 48])])
def test_exact_partial_tree_probe_quick_passes(clusters: int, heads: int, stage_counts: list[int]) -> None:
    report = build_report(clusters=clusters, heads=heads)

    assert report["decision"] == "pass", json.dumps(report, indent=2)
    assert report["equivalence_pass"] is True
    assert report["heads"] == heads
    assert report["root_result_count"] == heads * 16
    assert report["leaf_accept_count"] == [heads * 16] * clusters
    assert report["leaf_total_accept_count"] == clusters * heads * 16
    assert report["node_completed_count"] == [heads * 16] * (clusters - 1)
    assert report["stage_completed_count"] == stage_counts
    assert report["node_protocol_error"] == [False] * (clusters - 1)
    assert report["stage_protocol_error"] == [False] * len(stage_counts)
    assert report["summary"]["protocol_error"] is False
    assert report["root_hash"] == report["expected_root_hash"]
    assert report["measured_workload_manifest"]["heads"] == heads
    assert report["measured_workload_manifest"]["root_outputs"] == heads * 16
    assert report["theoretical_full_llama_service_manifest"]["heads"] == 32
    assert report["theoretical_full_llama_service_manifest"]["total_leaf_stream_bytes"] == clusters * 26816
    assert report["measured_workload_manifest"]["first_output_cycle"] >= 0
    assert report["measured_workload_manifest"]["last_output_cycle"] >= report["measured_workload_manifest"]["first_output_cycle"]


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_tree_probe_c16_32_heads_passes() -> None:
    report = build_report(clusters=16, heads=32)

    assert report["decision"] == "pass", json.dumps(report, indent=2)
    assert report["equivalence_pass"] is True
    assert report["heads"] == 32
    assert report["root_result_count"] == 512
    assert report["leaf_accept_count"] == [512] * 16
    assert report["leaf_total_accept_count"] == 8192
    assert report["node_completed_count"] == [512] * 15
    assert report["stage_completed_count"] == [4096, 2048, 1024, 512]
    assert report["summary"]["protocol_error"] is False
    assert report["summary"]["root_completed_count"] == 512
    assert report["root_hash"] == report["expected_root_hash"]
    assert report["measured_workload_manifest"]["heads"] == 32
    assert report["measured_workload_manifest"]["leaf_accepts_per_leaf"] == 512
    assert report["measured_workload_manifest"]["total_leaf_beats"] == 8192
    assert report["measured_workload_manifest"]["root_outputs"] == 512
    assert report["measured_workload_manifest"]["root_sustained_beats_per_cycle"] > 0.0


@pytest.mark.skipif(not _rtl_tools_available(), reason="iverilog/vvp/verilator unavailable")
def test_exact_partial_tree_probe_cli_bootstraps_repo_root(tmp_path: Path) -> None:
    out_path = tmp_path / "probe.json"
    env = {
        "HOME": os.environ.get("HOME", str(tmp_path)),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PATH": os.environ.get("PATH", ""),
    }

    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_score32_exact_partial_tree.py",
            "--clusters",
            "2",
            "--heads",
            "3",
            "--out",
            str(out_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert run.returncode == 0, run.stderr or run.stdout
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["clusters"] == 2
    assert payload["heads"] == 3
    assert payload["decision"] == "pass"
    assert payload["equivalence_pass"] is True
