#!/usr/bin/env python3
"""Generate and measure output-projection ranker policy wrappers."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

try:
    from probe_llm_decoder_pipelined_ranker_architecture import _rank_config, _write_json
    from probe_llm_decoder_rank_tree_architecture import _write_rank_tree_wrapper
    from probe_llm_decoder_serial_ranker_architecture import _write_serial_wrapper
    from probe_llm_decoder_serial_ranker_producer_replay import _make_tile_values, _reference_top1
    from probe_llm_decoder_producer_ranker_physical_wrapper import (
        REPO_ROOT,
        _latest_metrics_row,
        _portable_metrics_row,
        _rel,
        _run_logged,
    )
    from probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _operation_options,
        _resolve_executable,
        _run,
        _sv_signed_literal,
    )
except ImportError:  # pragma: no cover - package-style imports in tests
    from npu.eval.probe_llm_decoder_pipelined_ranker_architecture import _rank_config, _write_json
    from npu.eval.probe_llm_decoder_rank_tree_architecture import _write_rank_tree_wrapper
    from npu.eval.probe_llm_decoder_serial_ranker_architecture import _write_serial_wrapper
    from npu.eval.probe_llm_decoder_serial_ranker_producer_replay import _make_tile_values, _reference_top1
    from npu.eval.probe_llm_decoder_producer_ranker_physical_wrapper import (
        REPO_ROOT,
        _latest_metrics_row,
        _portable_metrics_row,
        _rel,
        _run_logged,
    )
    from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
        _operation_options,
        _resolve_executable,
        _run,
        _sv_signed_literal,
    )


JsonDict = dict[str, Any]
R64_LANES = 64


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bus_range(index: int, width: int) -> str:
    return f"{index * width} +: {width}"


def _write_r64_policy_wrapper(path: Path, *, top: str, serial_top: str, tree_top: str, logit_bits: int, token_id_bits: int) -> None:
    logit_width = R64_LANES * logit_bits
    lines = [
        "`timescale 1ns/1ps",
        f"module {top}(",
        "  input clk,",
        "  input rst_n,",
        "  input use_ranktree,",
        "  input in_valid,",
        "  output in_ready,",
        "  input in_last,",
        f"  input [{token_id_bits - 1}:0] in_base_token_id,",
        f"  input [{R64_LANES - 1}:0] in_lane_valid,",
        f"  input signed [{logit_width - 1}:0] in_logits,",
        "  output out_valid,",
        "  input out_ready,",
        "  output out_valid_mask,",
        f"  output [{token_id_bits - 1}:0] out_token_ids,",
        f"  output signed [{logit_bits - 1}:0] out_logits,",
        "  output [31:0] accepted_group_count,",
        "  output [31:0] producer_stall_cycles,",
        "  output [31:0] fifo_max_occupancy,",
        "  output [31:0] final_completion_cycle",
        ");",
        "  wire serial_ready, tree_ready;",
        "  wire serial_valid, tree_valid;",
        "  wire serial_mask, tree_mask;",
        f"  wire [{token_id_bits - 1}:0] serial_token, tree_token;",
        f"  wire signed [{logit_bits - 1}:0] serial_logit, tree_logit;",
        "  wire [31:0] serial_accepted, tree_accepted, serial_stalls, tree_stalls;",
        "  wire [31:0] serial_fifo, tree_fifo, serial_final, tree_final;",
        "  assign in_ready = use_ranktree ? tree_ready : serial_ready;",
        "  assign out_valid = use_ranktree ? tree_valid : serial_valid;",
        "  assign out_valid_mask = use_ranktree ? tree_mask : serial_mask;",
        "  assign out_token_ids = use_ranktree ? tree_token : serial_token;",
        "  assign out_logits = use_ranktree ? tree_logit : serial_logit;",
        "  assign accepted_group_count = use_ranktree ? tree_accepted : serial_accepted;",
        "  assign producer_stall_cycles = use_ranktree ? tree_stalls : serial_stalls;",
        "  assign fifo_max_occupancy = use_ranktree ? tree_fifo : serial_fifo;",
        "  assign final_completion_cycle = use_ranktree ? tree_final : serial_final;",
        f"  {serial_top} serial_path (",
        "    .clk(clk), .rst_n(rst_n), .in_valid(in_valid && !use_ranktree), .in_ready(serial_ready),",
        "    .in_last(in_last), .in_base_token_id(in_base_token_id), .in_lane_valid(in_lane_valid), .in_logits(in_logits),",
        "    .out_valid(serial_valid), .out_ready(out_ready && !use_ranktree), .out_valid_mask(serial_mask),",
        "    .out_token_ids(serial_token), .out_logits(serial_logit), .accepted_group_count(serial_accepted),",
        "    .producer_stall_cycles(serial_stalls), .fifo_max_occupancy(serial_fifo), .final_completion_cycle(serial_final)",
        "  );",
        f"  {tree_top} tree_path (",
        "    .clk(clk), .rst_n(rst_n), .in_valid(in_valid && use_ranktree), .in_ready(tree_ready),",
        "    .in_last(in_last), .in_base_token_id(in_base_token_id), .in_lane_valid(in_lane_valid), .in_logits(in_logits),",
        "    .out_valid(tree_valid), .out_ready(out_ready && use_ranktree), .out_valid_mask(tree_mask),",
        "    .out_token_ids(tree_token), .out_logits(tree_logit), .accepted_group_count(tree_accepted),",
        "    .producer_stall_cycles(tree_stalls), .fifo_max_occupancy(tree_fifo), .final_completion_cycle(tree_final)",
        "  );",
        "endmodule",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _winner_expr(prefix: str) -> list[str]:
    return [
        f"  wire {prefix}_bank0_wins = ({prefix}0_logit > {prefix}1_logit) || "
        f"(({prefix}0_logit == {prefix}1_logit) && ({prefix}0_token <= {prefix}1_token));",
        f"  wire [{15}:0] {prefix}_token = {prefix}_bank0_wins ? {prefix}0_token : {prefix}1_token;",
        f"  wire signed [{15}:0] {prefix}_logit = {prefix}_bank0_wins ? {prefix}0_logit : {prefix}1_logit;",
    ]


def _write_r128_policy_wrapper(path: Path, *, top: str, serial_top: str, tree_top: str, logit_bits: int, token_id_bits: int) -> None:
    logit_width = 128 * logit_bits
    lines = [
        "`timescale 1ns/1ps",
        f"module {top}(",
        "  input clk,",
        "  input rst_n,",
        "  input use_ranktree,",
        "  input in_valid,",
        "  output in_ready,",
        "  input in_last,",
        f"  input [{token_id_bits - 1}:0] in_base_token_id,",
        "  input [127:0] in_lane_valid,",
        f"  input signed [{logit_width - 1}:0] in_logits,",
        "  output out_valid,",
        "  input out_ready,",
        "  output out_valid_mask,",
        f"  output [{token_id_bits - 1}:0] out_token_ids,",
        f"  output signed [{logit_bits - 1}:0] out_logits,",
        "  output [31:0] accepted_group_count,",
        "  output [31:0] producer_stall_cycles,",
        "  output [31:0] fifo_max_occupancy,",
        "  output [31:0] final_completion_cycle",
        ");",
    ]
    for prefix in ("serial", "tree"):
        lines.extend(
            [
                f"  wire {prefix}0_ready, {prefix}1_ready, {prefix}0_valid, {prefix}1_valid;",
                f"  wire {prefix}0_mask, {prefix}1_mask;",
                f"  wire [{token_id_bits - 1}:0] {prefix}0_token, {prefix}1_token;",
                f"  wire signed [{logit_bits - 1}:0] {prefix}0_logit, {prefix}1_logit;",
                f"  wire [31:0] {prefix}0_accepted, {prefix}1_accepted, {prefix}0_stalls, {prefix}1_stalls;",
                f"  wire [31:0] {prefix}0_fifo, {prefix}1_fifo, {prefix}0_final, {prefix}1_final;",
                f"  wire {prefix}_ready = {prefix}0_ready && {prefix}1_ready;",
                f"  wire {prefix}_valid = {prefix}0_valid && {prefix}1_valid;",
            ]
        )
        lines.extend(_winner_expr(prefix))
        lines.extend(
            [
                f"  wire {prefix}_mask = {prefix}0_mask && {prefix}1_mask;",
                f"  wire [31:0] {prefix}_accepted = {prefix}0_accepted + {prefix}1_accepted;",
                f"  wire [31:0] {prefix}_stalls = {prefix}0_stalls + {prefix}1_stalls;",
                f"  wire [31:0] {prefix}_fifo = ({prefix}0_fifo > {prefix}1_fifo) ? {prefix}0_fifo : {prefix}1_fifo;",
                f"  wire [31:0] {prefix}_final = ({prefix}0_final > {prefix}1_final) ? {prefix}0_final : {prefix}1_final;",
            ]
        )
    lines.extend(
        [
            "  assign in_ready = use_ranktree ? tree_ready : serial_ready;",
            "  assign out_valid = use_ranktree ? tree_valid : serial_valid;",
            "  assign out_valid_mask = use_ranktree ? tree_mask : serial_mask;",
            "  assign out_token_ids = use_ranktree ? tree_token : serial_token;",
            "  assign out_logits = use_ranktree ? tree_logit : serial_logit;",
            "  assign accepted_group_count = use_ranktree ? tree_accepted : serial_accepted;",
            "  assign producer_stall_cycles = use_ranktree ? tree_stalls : serial_stalls;",
            "  assign fifo_max_occupancy = use_ranktree ? tree_fifo : serial_fifo;",
            "  assign final_completion_cycle = use_ranktree ? tree_final : serial_final;",
        ]
    )
    for prefix, child, select_expr in (("serial", serial_top, "!use_ranktree"), ("tree", tree_top, "use_ranktree")):
        for bank in (0, 1):
            lane_base = bank * R64_LANES
            lines.extend(
                [
                    f"  {child} {prefix}{bank}_path (",
                    "    .clk(clk), .rst_n(rst_n),",
                    f"    .in_valid(in_valid && {select_expr} && {prefix}_ready), .in_ready({prefix}{bank}_ready),",
                    "    .in_last(in_last),",
                    f"    .in_base_token_id(in_base_token_id + {token_id_bits}'d{lane_base}),",
                    f"    .in_lane_valid(in_lane_valid[{lane_base} +: {R64_LANES}]),",
                    f"    .in_logits(in_logits[{lane_base * logit_bits} +: {R64_LANES * logit_bits}]),",
                    f"    .out_valid({prefix}{bank}_valid), .out_ready(out_ready && {select_expr} && {prefix}_valid),",
                    f"    .out_valid_mask({prefix}{bank}_mask), .out_token_ids({prefix}{bank}_token), .out_logits({prefix}{bank}_logit),",
                    f"    .accepted_group_count({prefix}{bank}_accepted), .producer_stall_cycles({prefix}{bank}_stalls),",
                    f"    .fifo_max_occupancy({prefix}{bank}_fifo), .final_completion_cycle({prefix}{bank}_final)",
                    "  );",
                ]
            )
    lines.extend(["endmodule", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _prepare_variant(
    *,
    rtlgen_binary: str,
    merge_config: Path,
    design_root: Path,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    top = f"decoder_output_ranker_policy_r{producer_lanes}_wrapper"
    design_dir = design_root / top
    verilog_dir = design_dir / "verilog"
    config_dir = design_dir / "generated_configs"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    for old in verilog_dir.glob("*.v"):
        old.unlink()
    rank1_config = config_dir / f"config_logit_rank_r1_l{logit_bits}_k1.json"
    rank4_config = config_dir / f"config_logit_rank_r4_l{logit_bits}_k1.json"
    _write_json(rank1_config, _rank_config(1, logit_bits))
    _write_json(rank4_config, _rank_config(4, logit_bits))
    commands = {
        "rank1": _run([rtlgen_binary, str(rank1_config.resolve())], cwd=verilog_dir),
        "rank4": _run([rtlgen_binary, str(rank4_config.resolve())], cwd=verilog_dir),
        "merge": _run([rtlgen_binary, str(merge_config.resolve())], cwd=verilog_dir),
    }
    serial_top = f"{top}_serial64"
    tree_top = f"{top}_ranktree64"
    if all(result.returncode == 0 for result in commands.values()):
        _write_serial_wrapper(
            verilog_dir / f"{serial_top}.v",
            top=serial_top,
            rank_module=f"logit_rank_r1_l{logit_bits}_k1",
            merge_module="candidate_stream_merge_fifo_k1_l16_t16_d16",
            producer_lanes=R64_LANES,
            lanes_per_cycle=1,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        )
        _write_rank_tree_wrapper(
            verilog_dir / f"{tree_top}.v",
            top=tree_top,
            rank_module=f"logit_rank_r4_l{logit_bits}_k1",
            merge_module="candidate_stream_merge_fifo_k1_l16_t16_d16",
            producer_lanes=R64_LANES,
            radix=4,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
        )
        if producer_lanes == R64_LANES:
            _write_r64_policy_wrapper(
                verilog_dir / f"{top}.v",
                top=top,
                serial_top=serial_top,
                tree_top=tree_top,
                logit_bits=logit_bits,
                token_id_bits=token_id_bits,
            )
        else:
            _write_r128_policy_wrapper(
                verilog_dir / f"{top}.v",
                top=top,
                serial_top=serial_top,
                tree_top=tree_top,
                logit_bits=logit_bits,
                token_id_bits=token_id_bits,
            )
    manifest = {
        "version": 0.1,
        "top": top,
        "producer_lanes": producer_lanes,
        "paths": ["serial_lpc1", "ranktree_radix4"],
        "ranktree_radix": 4,
        "serial_lanes_per_cycle": 1,
        "logit_bits": logit_bits,
        "token_id_bits": token_id_bits,
        "banking": "single_r64" if producer_lanes == R64_LANES else "banked_r64x2",
        "generated_configs": [_rel(rank1_config), _rel(rank4_config)],
    }
    _write_json(design_dir / f"config_{top}.json", manifest)
    return {
        "top": top,
        "design_dir": _rel(design_dir),
        "verilog_dir": _rel(verilog_dir),
        "producer_lanes": producer_lanes,
        "status": "ok" if all(result.returncode == 0 for result in commands.values()) else "rtlgen_failed",
        "returncodes": {name: result.returncode for name, result in commands.items()},
        "generated_verilog": sorted(_rel(path) for path in verilog_dir.glob("*.v")),
        "config_manifest": _rel(design_dir / f"config_{top}.json"),
    }


def _write_testbench(
    path: Path,
    *,
    top: str,
    producer_lanes: int,
    use_ranktree: bool,
    producer_ii_cycles: int,
    num_tiles: int,
    logit_bits: int,
    token_id_bits: int,
) -> JsonDict:
    tiles = _make_tile_values(num_tiles=num_tiles, producer_lanes=producer_lanes)
    expected = _reference_top1(tiles, producer_lanes=producer_lanes)
    logit_width = producer_lanes * logit_bits
    wait_limit = producer_ii_cycles * max(4, num_tiles * 2) + 512
    scenario = "ranktree" if use_ranktree else "serial"
    lines = [
        "`timescale 1ns/1ps",
        "module decoder_output_ranker_policy_tb;",
        "  reg clk;",
        "  reg rst_n;",
        "  reg use_ranktree;",
        "  reg in_valid;",
        "  wire in_ready;",
        "  reg in_last;",
        f"  reg [{token_id_bits - 1}:0] in_base_token_id;",
        f"  reg [{producer_lanes - 1}:0] in_lane_valid;",
        f"  reg signed [{logit_width - 1}:0] in_logits;",
        "  wire out_valid;",
        "  reg out_ready;",
        "  wire out_valid_mask;",
        f"  wire [{token_id_bits - 1}:0] out_token_ids;",
        f"  wire signed [{logit_bits - 1}:0] out_logits;",
        "  wire [31:0] accepted_group_count;",
        "  wire [31:0] producer_stall_cycles;",
        "  wire [31:0] fifo_max_occupancy;",
        "  wire [31:0] final_completion_cycle;",
        "  integer cycle, tile_id, wait_cycles, next_issue_cycle, tb_backpressure_cycles;",
        f"  {top} dut (",
        "    .clk(clk), .rst_n(rst_n), .use_ranktree(use_ranktree), .in_valid(in_valid), .in_ready(in_ready),",
        "    .in_last(in_last), .in_base_token_id(in_base_token_id), .in_lane_valid(in_lane_valid), .in_logits(in_logits),",
        "    .out_valid(out_valid), .out_ready(out_ready), .out_valid_mask(out_valid_mask), .out_token_ids(out_token_ids),",
        "    .out_logits(out_logits), .accepted_group_count(accepted_group_count), .producer_stall_cycles(producer_stall_cycles),",
        "    .fifo_max_occupancy(fifo_max_occupancy), .final_completion_cycle(final_completion_cycle)",
        "  );",
        "  always #5 clk = ~clk;",
        "  always @(posedge clk or negedge rst_n) begin if (!rst_n) cycle <= 0; else cycle <= cycle + 1; end",
        "  task clear_logits; integer i; begin",
        f"    for (i = 0; i < {producer_lanes}; i = i + 1) in_logits[i*{logit_bits} +: {logit_bits}] = {logit_bits}'sd0;",
        "  end endtask",
        "  task drive_tile; input [31:0] tid; input last; begin",
        "    in_valid = 1'b1; in_last = last;",
        f"    in_base_token_id = tid * {producer_lanes};",
        f"    in_lane_valid = {{{producer_lanes}{{1'b1}}}};",
        "    clear_logits();",
    ]
    for tile_id, logits in enumerate(tiles):
        lines.append(f"    if (tid == {tile_id}) begin")
        for lane, value in enumerate(logits):
            lines.append(
                f"      in_logits[{lane * logit_bits} +: {logit_bits}] = {_sv_signed_literal(logit_bits, value)};"
            )
        lines.append("    end")
    lines.extend(
        [
            "    while (!in_ready) begin tb_backpressure_cycles = tb_backpressure_cycles + 1; @(negedge clk); end",
            "    @(negedge clk);",
            "    in_valid = 1'b0; in_last = 1'b0; in_base_token_id = 0; in_lane_valid = 0; clear_logits();",
            "  end endtask",
            "  initial begin",
            "    clk = 1'b0; rst_n = 1'b0; use_ranktree = 1'b0; in_valid = 1'b0; in_last = 1'b0; in_base_token_id = 0; in_lane_valid = 0; out_ready = 1'b0; tb_backpressure_cycles = 0; next_issue_cycle = 0; clear_logits();",
            f"    use_ranktree = {1 if use_ranktree else 0};",
            "    repeat (3) @(negedge clk); rst_n = 1'b1;",
            f"    for (tile_id = 0; tile_id < {num_tiles}; tile_id = tile_id + 1) begin",
            "      while (cycle < next_issue_cycle) @(negedge clk);",
            f"      drive_tile(tile_id, tile_id == ({num_tiles} - 1));",
            f"      next_issue_cycle = next_issue_cycle + {producer_ii_cycles};",
            "    end",
            "    wait_cycles = 0;",
            f"    while (!out_valid && wait_cycles < {wait_limit}) begin wait_cycles = wait_cycles + 1; @(negedge clk); end",
            "    if (!out_valid) begin $display(\"FAIL no out_valid wait=%0d\", wait_cycles); $fatal; end",
            f"    if (out_valid_mask !== 1'b1 || out_token_ids !== {token_id_bits}'d{expected['token']} || $signed(out_logits) !== {_sv_signed_literal(logit_bits, int(expected['logit']))}) begin",
            "      $display(\"FAIL result token=%0d logit=%0d mask=%b\", out_token_ids, $signed(out_logits), out_valid_mask); $fatal;",
            "    end",
            f"    $display(\"RESULT scenario={scenario} lanes={producer_lanes} token=%0d logit=%0d accepted=%0d tb_backpressure=%0d dut_stalls=%0d fifo_max=%0d final_cycle=%0d\", out_token_ids, $signed(out_logits), accepted_group_count, tb_backpressure_cycles, producer_stall_cycles, fifo_max_occupancy, final_completion_cycle);",
            "    out_ready = 1'b1; @(negedge clk); out_ready = 1'b0; $finish;",
            "  end",
            "endmodule",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return expected


def _simulate_variant(variant: JsonDict, *, use_ranktree: bool, producer_ii_cycles: int, num_tiles: int) -> JsonDict:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        return {"status": "simulator_missing", "iverilog": iverilog, "vvp": vvp}
    design_dir = REPO_ROOT / str(variant["design_dir"])
    verilog_dir = design_dir / "verilog"
    top = str(variant["top"])
    scenario = "ranktree" if use_ranktree else "serial"
    tb = design_dir / f"tb_{top}_{scenario}.v"
    expected = _write_testbench(
        tb,
        top=top,
        producer_lanes=int(variant["producer_lanes"]),
        use_ranktree=use_ranktree,
        producer_ii_cycles=producer_ii_cycles,
        num_tiles=num_tiles,
        logit_bits=16,
        token_id_bits=16,
    )
    sim_path = design_dir / f"sim_{scenario}"
    sources = sorted(str(path) for path in verilog_dir.glob("*.v")) + [str(tb)]
    compile_cmd = _run(["iverilog", "-g2012", "-s", "decoder_output_ranker_policy_tb", "-o", str(sim_path), *sources], cwd=REPO_ROOT)
    if compile_cmd.returncode != 0:
        return {"status": "iverilog_failed", "returncode": compile_cmd.returncode, "log_tail": compile_cmd.stdout.splitlines()[-40:]}
    sim_cmd = _run(["vvp", str(sim_path)], cwd=REPO_ROOT)
    result: JsonDict = {
        "status": "ok" if sim_cmd.returncode == 0 else "vvp_failed",
        "returncode": sim_cmd.returncode,
        "expected": expected,
        "log_tail": sim_cmd.stdout.splitlines()[-40:],
    }
    match = re.search(
        r"RESULT scenario=(?P<scenario>\S+) lanes=(?P<lanes>\d+) token=(?P<token>\d+) "
        r"logit=(?P<logit>-?\d+) accepted=(?P<accepted>\d+) tb_backpressure=(?P<tb_backpressure>\d+) "
        r"dut_stalls=(?P<dut_stalls>\d+) fifo_max=(?P<fifo_max>\d+) final_cycle=(?P<final_cycle>\d+)",
        sim_cmd.stdout,
    )
    if match:
        result["observed"] = {key: int(value) if value.lstrip("-").isdigit() else value for key, value in match.groupdict().items()}
    return result


def _run_physical_variant(
    variant: JsonDict,
    *,
    sweep: str,
    platform: str,
    make_target: str,
    timeout_seconds: int,
    stall_timeout_seconds: int,
) -> tuple[JsonDict, JsonDict | None]:
    top = str(variant["top"])
    log_dir = REPO_ROOT / "control_plane/runtime_logs/decoder_output_ranker_policy_wrapper"
    cmd = [
        "python3",
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        str(variant["design_dir"]),
        "--platform",
        platform,
        "--top",
        top,
        "--sweep",
        sweep,
        "--make_target",
        make_target,
        "--out_root",
        "runs/designs/activations",
        "--force_copy",
    ]
    synthesis = _run_logged(
        cmd,
        cwd=REPO_ROOT,
        log_path=log_dir / f"{top}_{make_target}.log",
        timeout_seconds=timeout_seconds,
        stall_timeout_seconds=stall_timeout_seconds,
    )
    metrics = _portable_metrics_row(_latest_metrics_row(REPO_ROOT / str(variant["design_dir"]) / "metrics.csv"))
    return synthesis, metrics


def build_report(*, variants: list[JsonDict], sweep: str, make_target: str) -> JsonDict:
    measured = [row for row in variants if (row.get("metrics_row") or {}).get("status") == "ok"]
    sim_ok = [
        row
        for row in variants
        if all((sim.get("status") == "ok") for sim in (row.get("simulations") or {}).values())
    ]
    return {
        "version": 0.1,
        "model": "decoder_output_projection_ranker_wrapper_physical_v1",
        "target": {
            "producer_lanes": [row.get("producer_lanes") for row in variants],
            "paths": ["serial_lpc1", "ranktree_radix4"],
            "sweep": sweep,
            "make_target": make_target,
        },
        "variants": variants,
        "decision": {
            "decision": "output_projection_ranker_wrapper_physical_measured"
            if len(measured) == len(variants) and len(sim_ok) == len(variants)
            else "output_projection_ranker_wrapper_physical_incomplete",
            "next_step": (
                "Use the measured wrapper overhead to decide whether the policy wrapper can be integrated into the producer block or whether path-specific wrappers should be retained."
                if len(measured) == len(variants) and len(sim_ok) == len(variants)
                else "Inspect failed simulation or physical rows before promoting the final wrapper implementation."
            ),
        },
        "assumptions": [
            "The r64 wrapper contains both serial_lpc1 and radix-4 rank-tree paths selected by use_ranktree.",
            "The r128 wrapper banks both paths into two r64 instances and reduces the two bank outputs with lower-token tie-break.",
            "The physical sweep measures wrapper mux/control plus inactive path area; runtime policy may clock-gate inactive paths in a later refinement.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Ranker Physical Wrapper",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Variants",
        "",
        "| lanes | top | sim serial | sim ranktree | metrics | critical path ns | area | power mW |",
        "|---:|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["variants"]:
        metrics = row.get("metrics_row") or {}
        sims = row.get("simulations") or {}
        lines.append(
            "| {lanes} | `{top}` | `{serial}` | `{tree}` | `{met}` | {cp} | {area} | {power} |".format(
                lanes=row.get("producer_lanes"),
                top=row.get("top"),
                serial=(sims.get("serial") or {}).get("status"),
                tree=(sims.get("ranktree") or {}).get("status"),
                met=metrics.get("status"),
                cp=metrics.get("critical_path_ns", ""),
                area=metrics.get("die_area", ""),
                power=metrics.get("total_power_mw", ""),
            )
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--wrapper-contract", required=True)
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--design-root", default="runs/designs/activations")
    ap.add_argument("--producer-lanes", default="64,128")
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--platform", default="nangate45")
    ap.add_argument("--make-target", default="3_3_place_gp")
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    ap.add_argument("--stall-timeout-seconds", type=int, default=900)
    ap.add_argument("--skip-physical", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    _load_json(args.policy)
    _load_json(args.wrapper_contract)
    rtlgen_binary = _resolve_executable(args.rtlgen_binary)
    lanes_list = [int(item) for item in args.producer_lanes.split(",") if item.strip()]
    merge_opts = _operation_options(_load_json(args.merge_config))
    logit_bits = int(merge_opts.get("logit_bits", 16))
    token_id_bits = int(merge_opts.get("token_id_bits", 16))
    if rtlgen_binary is None:
        variants = [{"status": "rtlgen_binary_missing", "requested": args.rtlgen_binary, "producer_lanes": lanes} for lanes in lanes_list]
    else:
        variants = []
        for lanes in lanes_list:
            variant = _prepare_variant(
                rtlgen_binary=rtlgen_binary,
                merge_config=Path(args.merge_config),
                design_root=REPO_ROOT / args.design_root,
                producer_lanes=lanes,
                logit_bits=logit_bits,
                token_id_bits=token_id_bits,
            )
            if variant["status"] == "ok":
                serial_ii = 384
                tree_ii = 6 if lanes == 64 else 3
                variant["simulations"] = {
                    "serial": _simulate_variant(variant, use_ranktree=False, producer_ii_cycles=serial_ii, num_tiles=6),
                    "ranktree": _simulate_variant(variant, use_ranktree=True, producer_ii_cycles=tree_ii, num_tiles=6),
                }
            if (
                variant["status"] == "ok"
                and all((sim.get("status") == "ok") for sim in (variant.get("simulations") or {}).values())
                and not args.skip_physical
            ):
                synthesis, metrics = _run_physical_variant(
                    variant,
                    sweep=args.sweep,
                    platform=args.platform,
                    make_target=args.make_target,
                    timeout_seconds=args.timeout_seconds,
                    stall_timeout_seconds=args.stall_timeout_seconds,
                )
                variant["synthesis"] = synthesis
                variant["metrics_row"] = metrics
            variants.append(variant)

    payload = build_report(variants=variants, sweep=args.sweep, make_target=args.make_target)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
