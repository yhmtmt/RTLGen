#!/usr/bin/env python3
"""Probe producer-to-ranker ready/valid equivalence for the first decoder target."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ceil_log2_at_least_one(value: int) -> int:
    if value <= 1:
        return 1
    return (value - 1).bit_length()


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sv_signed_literal(bits: int, value: int) -> str:
    return f"-{bits}'sd{abs(value)}" if value < 0 else f"{bits}'sd{value}"


def _producer_summary(config: JsonDict) -> JsonDict:
    gemm = config.get("compute", {}).get("gemm", {})
    num_modules = _as_int(gemm.get("num_modules"), 1)
    lanes_per_module = _as_int(gemm.get("lanes_per_module", gemm.get("lanes")), 1)
    return {
        "num_modules": num_modules,
        "lanes_per_module": lanes_per_module,
        "mac_lanes_per_cycle": num_modules * lanes_per_module,
        "mac_type": gemm.get("mac_type"),
    }


def _operation_options(config: JsonDict) -> JsonDict:
    operations = config.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("expected config.operations[0]")
    options = operations[0].get("options")
    if not isinstance(options, dict):
        raise ValueError("expected config.operations[0].options")
    return options


def _module_name(config: JsonDict) -> str:
    operations = config.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("expected config.operations[0]")
    module_name = operations[0].get("module_name")
    if not isinstance(module_name, str) or not module_name:
        raise ValueError("expected module_name")
    return module_name


def _make_tile_values() -> list[list[int]]:
    tiles: list[list[int]] = []
    for tile in range(3):
        row = []
        for lane in range(64):
            row.append(((tile + 1) * 17 + lane * 5) % 257 - 128)
        tiles.append(row)
    tiles[0][5] = 500
    tiles[1][2] = 499
    tiles[2][7] = 500
    return tiles


def _reference_top1(tiles: list[list[int]], *, producer_lanes: int) -> JsonDict:
    best_token = None
    best_logit = None
    for tile_id, logits in enumerate(tiles):
        for lane, logit in enumerate(logits):
            token = tile_id * producer_lanes + lane
            if best_logit is None or logit > best_logit or (
                logit == best_logit and token < int(best_token)
            ):
                best_token = token
                best_logit = logit
    return {"token": best_token, "logit": best_logit}


def _write_ready_valid_wrapper(
    path: Path,
    *,
    wrapper_name: str,
    rank_module: str,
    merge_module: str,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
    top_k: int,
) -> None:
    index_bits = _ceil_log2_at_least_one(producer_lanes)
    logit_width = producer_lanes * logit_bits
    min_logit = -(2 ** (logit_bits - 1))
    lines = [
        "`timescale 1ns/1ps",
        f"module {wrapper_name}(",
        "  input clk,",
        "  input rst_n,",
        "  input in_valid,",
        "  output in_ready,",
        "  input in_last,",
        f"  input [{token_id_bits - 1}:0] in_base_token_id,",
        f"  input [{producer_lanes - 1}:0] in_lane_valid,",
        f"  input signed [{logit_width - 1}:0] in_logits,",
        "  output out_valid,",
        "  input out_ready,",
        f"  output [{top_k - 1}:0] out_valid_mask,",
        f"  output [{token_id_bits * top_k - 1}:0] out_token_ids,",
        f"  output signed [{logit_bits * top_k - 1}:0] out_logits,",
        "  output [31:0] accepted_group_count,",
        "  output [31:0] producer_stall_cycles,",
        "  output [31:0] fifo_max_occupancy,",
        "  output [31:0] final_completion_cycle",
        ");",
        f"  wire signed [{logit_width - 1}:0] masked_logits;",
    ]
    for lane in range(producer_lanes):
        lines.append(
            f"  assign masked_logits[{lane * logit_bits} +: {logit_bits}] = "
            f"in_lane_valid[{lane}] ? in_logits[{lane * logit_bits} +: {logit_bits}] : {_sv_signed_literal(logit_bits, min_logit)};"
        )
    lines.extend(
        [
            f"  wire [{index_bits * top_k - 1}:0] local_top_indices;",
            f"  wire signed [{logit_bits * top_k - 1}:0] local_top_logits;",
            f"  wire [{token_id_bits * top_k - 1}:0] local_token_ids;",
            f"  {rank_module} ranker (",
            "    .logits(masked_logits),",
            "    .top_indices(local_top_indices),",
            "    .top_logits(local_top_logits)",
            "  );",
        ]
    )
    for k in range(top_k):
        lines.append(
            f"  assign local_token_ids[{k * token_id_bits} +: {token_id_bits}] = "
            f"in_base_token_id + {{ {token_id_bits - index_bits}'d0, local_top_indices[{k * index_bits} +: {index_bits}] }};"
        )
    lines.extend(
        [
            f"  {merge_module} merger (",
            "    .clk(clk),",
            "    .rst_n(rst_n),",
            "    .in_valid(in_valid),",
            "    .in_ready(in_ready),",
            "    .in_last(in_last),",
            f"    .in_valid_mask({top_k}'b1),",
            "    .in_token_ids(local_token_ids),",
            "    .in_logits(local_top_logits),",
            "    .out_valid(out_valid),",
            "    .out_ready(out_ready),",
            "    .out_valid_mask(out_valid_mask),",
            "    .out_token_ids(out_token_ids),",
            "    .out_logits(out_logits),",
            "    .accepted_group_count(accepted_group_count),",
            "    .producer_stall_cycles(producer_stall_cycles),",
            "    .fifo_max_occupancy(fifo_max_occupancy),",
            "    .final_completion_cycle(final_completion_cycle)",
            "  );",
            "endmodule",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_testbench(
    path: Path,
    *,
    wrapper_name: str,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
    tiles: list[list[int]],
    expected: JsonDict,
) -> None:
    logit_width = producer_lanes * logit_bits
    lines = [
        "`timescale 1ns/1ps",
        "module decoder_ranker_ready_valid_tb;",
        "  reg clk;",
        "  reg rst_n;",
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
        f"  {wrapper_name} dut (",
        "    .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_ready(in_ready),",
        "    .in_last(in_last), .in_base_token_id(in_base_token_id),",
        "    .in_lane_valid(in_lane_valid), .in_logits(in_logits),",
        "    .out_valid(out_valid), .out_ready(out_ready), .out_valid_mask(out_valid_mask),",
        "    .out_token_ids(out_token_ids), .out_logits(out_logits),",
        "    .accepted_group_count(accepted_group_count),",
        "    .producer_stall_cycles(producer_stall_cycles),",
        "    .fifo_max_occupancy(fifo_max_occupancy),",
        "    .final_completion_cycle(final_completion_cycle)",
        "  );",
        "  always #5 clk = ~clk;",
        "  task clear_logits;",
        "    integer i;",
        "    begin",
        f"      for (i = 0; i < {producer_lanes}; i = i + 1) begin",
        f"        in_logits[i*{logit_bits} +: {logit_bits}] = {logit_bits}'sd0;",
        "      end",
        "    end",
        "  endtask",
        "  task send_tile;",
        "    input [31:0] tile_id;",
        "    input last;",
        "    begin",
        "      @(negedge clk);",
        "      in_valid = 1'b1;",
        "      in_last = last;",
        f"      in_base_token_id = tile_id * {producer_lanes};",
        f"      in_lane_valid = {{{producer_lanes}{{1'b1}}}};",
        "      clear_logits();",
    ]
    for tile_id, logits in enumerate(tiles):
        lines.append(f"      if (tile_id == {tile_id}) begin")
        for lane, value in enumerate(logits):
            lines.append(
                f"        in_logits[{lane * logit_bits} +: {logit_bits}] = {_sv_signed_literal(logit_bits, value)};"
            )
        lines.append("      end")
    lines.extend(
        [
            "      while (!in_ready) begin",
            "        @(negedge clk);",
            "      end",
            "      @(negedge clk);",
            "      in_valid = 1'b0;",
            "      in_last = 1'b0;",
            "      in_base_token_id = 0;",
            "      in_lane_valid = 0;",
            "      clear_logits();",
            "    end",
            "  endtask",
            "  integer wait_cycles;",
            "  initial begin",
            "    clk = 1'b0;",
            "    rst_n = 1'b0;",
            "    in_valid = 1'b0;",
            "    in_last = 1'b0;",
            "    in_base_token_id = 0;",
            "    in_lane_valid = 0;",
            "    out_ready = 1'b0;",
            "    clear_logits();",
            "    repeat (3) @(negedge clk);",
            "    rst_n = 1'b1;",
            "    send_tile(0, 1'b0);",
            "    send_tile(1, 1'b0);",
            "    send_tile(2, 1'b1);",
            "    wait_cycles = 0;",
            "    while (!out_valid && wait_cycles < 80) begin",
            "      wait_cycles = wait_cycles + 1;",
            "      @(negedge clk);",
            "    end",
            "    if (!out_valid) begin",
            "      $display(\"FAIL no out_valid\");",
            "      $fatal;",
            "    end",
            f"    if (out_valid_mask !== 1'b1 || out_token_ids !== {token_id_bits}'d{expected['token']} || $signed(out_logits) !== {_sv_signed_literal(logit_bits, int(expected['logit']))}) begin",
            "      $display(\"FAIL result token=%0d logit=%0d mask=%b\", out_token_ids, $signed(out_logits), out_valid_mask);",
            "      $fatal;",
            "    end",
            "    $display(\"RESULT token=%0d logit=%0d accepted=%0d stalls=%0d fifo_max=%0d final_cycle=%0d\",",
            "      out_token_ids, $signed(out_logits), accepted_group_count, producer_stall_cycles,",
            "      fifo_max_occupancy, final_completion_cycle);",
            "    out_ready = 1'b1;",
            "    @(negedge clk);",
            "    out_ready = 1'b0;",
            "    $finish;",
            "  end",
            "endmodule",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(cmd, 127, stdout=str(exc))


def _resolve_executable(requested: str) -> str | None:
    candidate_paths: list[Path] = []
    requested_path = Path(requested)
    if requested_path.is_absolute():
        candidate_paths.append(requested_path)
    elif "/" in requested or "\\" in requested:
        candidate_paths.append((Path.cwd() / requested_path).resolve())
    else:
        found = shutil.which(requested)
        if found is not None:
            candidate_paths.append(Path(found))

    env_path = os.environ.get("RTLGEN_BINARY")
    if env_path:
        candidate_paths.append(Path(env_path).expanduser())

    repo_root = Path(__file__).resolve().parents[2]
    candidate_paths.extend(
        [
            Path.cwd() / "build" / "rtlgen",
            repo_root / "build" / "rtlgen",
            Path("/workspaces/RTLGen/build/rtlgen"),
        ]
    )
    for candidate in candidate_paths:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
    return None


def _run_rtl_sim(
    *,
    rtlgen_binary: str,
    iverilog_binary: str,
    vvp_binary: str,
    logit_rank_config: Path,
    merge_config: Path,
    producer_lanes: int,
    logit_bits: int,
    token_id_bits: int,
    top_k: int,
) -> JsonDict:
    rank_module = _module_name(_load_json(logit_rank_config))
    merge_module = _module_name(_load_json(merge_config))
    wrapper_name = "decoder_r64_k1_ready_valid_wrapper"
    tiles = _make_tile_values()
    expected = _reference_top1(tiles, producer_lanes=producer_lanes)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        rank_cmd = _run([rtlgen_binary, str(logit_rank_config)], cwd=work)
        merge_cmd = _run([rtlgen_binary, str(merge_config)], cwd=work)
        if rank_cmd.returncode != 0 or merge_cmd.returncode != 0:
            return {
                "status": "rtlgen_failed",
                "rank_returncode": rank_cmd.returncode,
                "merge_returncode": merge_cmd.returncode,
                "rank_log_tail": rank_cmd.stdout.splitlines()[-20:],
                "merge_log_tail": merge_cmd.stdout.splitlines()[-20:],
            }
        wrapper = work / f"{wrapper_name}.v"
        testbench = work / "decoder_ranker_ready_valid_tb.v"
        _write_ready_valid_wrapper(
            wrapper,
            wrapper_name=wrapper_name,
            rank_module=rank_module,
            merge_module=merge_module,
            producer_lanes=producer_lanes,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
            top_k=top_k,
        )
        _write_testbench(
            testbench,
            wrapper_name=wrapper_name,
            producer_lanes=producer_lanes,
            logit_bits=logit_bits,
            token_id_bits=token_id_bits,
            tiles=tiles,
            expected=expected,
        )
        sim_path = work / "sim"
        compile_cmd = _run(
            [
                iverilog_binary,
                "-g2012",
                "-s",
                "decoder_ranker_ready_valid_tb",
                "-o",
                str(sim_path),
                f"{rank_module}.v",
                f"{merge_module}.v",
                str(wrapper),
                str(testbench),
            ],
            cwd=work,
        )
        if compile_cmd.returncode != 0:
            return {
                "status": "iverilog_failed",
                "returncode": compile_cmd.returncode,
                "log_tail": compile_cmd.stdout.splitlines()[-40:],
            }
        sim_cmd = _run([vvp_binary, str(sim_path)], cwd=work)
        result = {
            "status": "ok" if sim_cmd.returncode == 0 else "vvp_failed",
            "returncode": sim_cmd.returncode,
            "expected": expected,
            "log_tail": sim_cmd.stdout.splitlines()[-40:],
        }
        match = re.search(
            r"RESULT token=(?P<token>\d+) logit=(?P<logit>-?\d+) accepted=(?P<accepted>\d+) "
            r"stalls=(?P<stalls>\d+) fifo_max=(?P<fifo>\d+) final_cycle=(?P<cycle>\d+)",
            sim_cmd.stdout,
        )
        if match:
            result["observed"] = {key: int(value) for key, value in match.groupdict().items()}
        return result


def build_report(
    *,
    producer_config: JsonDict,
    logit_rank_config: JsonDict,
    merge_config: JsonDict,
    integration_plan: JsonDict | None,
    rtl_sim: JsonDict | None,
) -> JsonDict:
    rank_opts = _operation_options(logit_rank_config)
    merge_opts = _operation_options(merge_config)
    producer_lanes = _as_int(rank_opts.get("row_elems"))
    top_k = _as_int(rank_opts.get("top_k"))
    checks = [
        {
            "name": "producer_lanes_match_r64_target",
            "passed": producer_lanes == 64,
            "observed": producer_lanes,
        },
        {
            "name": "top_k_matches_first_target",
            "passed": top_k == 1 and _as_int(merge_opts.get("top_k")) == top_k,
            "observed": {"rank_top_k": top_k, "merge_top_k": _as_int(merge_opts.get("top_k"))},
        },
        {
            "name": "token_id_width_covers_gpt2_vocab",
            "passed": _as_int(merge_opts.get("token_id_bits")) >= 16,
            "observed": _as_int(merge_opts.get("token_id_bits")),
        },
    ]
    if rtl_sim is not None:
        observed = rtl_sim.get("observed") if isinstance(rtl_sim.get("observed"), dict) else {}
        expected = rtl_sim.get("expected") if isinstance(rtl_sim.get("expected"), dict) else {}
        checks.append(
            {
                "name": "rtl_stream_matches_full_vocab_reference",
                "passed": (
                    rtl_sim.get("status") == "ok"
                    and observed.get("token") == expected.get("token")
                    and observed.get("logit") == expected.get("logit")
                    and observed.get("accepted") == 3
                ),
                "observed": observed,
                "expected": expected,
            }
        )
    return {
        "version": 0.1,
        "model": "decoder_producer_ranker_ready_valid_equivalence_v1",
        "target": {
            "name": "r64_k1_nm16_ready_valid_equivalence",
            "producer_lanes": producer_lanes,
            "top_k": top_k,
            "logit_bits": _as_int(rank_opts.get("logit_bits")),
            "token_id_bits": _as_int(merge_opts.get("token_id_bits")),
            "fifo_depth_groups": _as_int(merge_opts.get("fifo_depth_groups")),
        },
        "producer_config_summary": _producer_summary(producer_config),
        "integration_plan_next_target": (
            integration_plan.get("recommendation", {}).get("next_target")
            if integration_plan is not None
            else None
        ),
        "rtl_sim": rtl_sim,
        "equivalence_checks": checks,
        "decision": {
            "decision": "ready_valid_equivalence_passed"
            if all(bool(check["passed"]) for check in checks)
            else "ready_valid_equivalence_blocked",
            "next_step": (
                "Queue a bounded macro-style r64/k1 producer-to-ranker physical wrapper."
                if all(bool(check["passed"]) for check in checks)
                else "Fix stream contract or RTL simulation failures before physical measurement."
            ),
        },
        "assumptions": [
            "The harness validates stream ordering, lower-token tie-break, final last-beat completion, and merge observables for the first r64/k1 target.",
            "The current wrapper is a functional ready-valid harness, not the final physical macro implementation.",
            "nm16 producer config is used as measured MAC-context metadata; the harness feeds deterministic logit tiles directly.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Producer/Ranker Ready-Valid Equivalence",
        "",
        f"- model: `{payload['model']}`",
        f"- target: `{payload['target']['name']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Checks",
        "",
        "| check | passed | observed |",
        "|---|---|---|",
    ]
    for check in payload["equivalence_checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    if payload.get("rtl_sim"):
        lines.extend(["", "## RTL Simulation", ""])
        sim = payload["rtl_sim"]
        lines.append(f"- status: `{sim.get('status')}`")
        lines.append(f"- expected: `{sim.get('expected')}`")
        lines.append(f"- observed: `{sim.get('observed')}`")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe decoder producer/ranker ready-valid equivalence")
    ap.add_argument("--producer-config", required=True)
    ap.add_argument("--logit-rank-config", required=True)
    ap.add_argument("--merge-config", required=True)
    ap.add_argument("--integration-plan")
    ap.add_argument("--rtlgen-binary", default="build/rtlgen")
    ap.add_argument("--run-rtl-sim", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    producer_config = _load_json(args.producer_config)
    logit_rank_config = _load_json(args.logit_rank_config)
    merge_config = _load_json(args.merge_config)
    integration_plan = _load_json(args.integration_plan) if args.integration_plan else None
    rank_opts = _operation_options(logit_rank_config)
    merge_opts = _operation_options(merge_config)
    rtl_sim = None
    if args.run_rtl_sim:
        iverilog = shutil.which("iverilog")
        vvp = shutil.which("vvp")
        if iverilog is None or vvp is None:
            rtl_sim = {"status": "simulator_missing", "iverilog": iverilog, "vvp": vvp}
        else:
            rtlgen_binary = _resolve_executable(args.rtlgen_binary)
            if rtlgen_binary is None:
                rtl_sim = {
                    "status": "rtlgen_binary_missing",
                    "requested": args.rtlgen_binary,
                    "rtlgen_binary_env": os.environ.get("RTLGEN_BINARY"),
                }
            else:
                rtl_sim = _run_rtl_sim(
                    rtlgen_binary=rtlgen_binary,
                    iverilog_binary=iverilog,
                    vvp_binary=vvp,
                    logit_rank_config=Path(args.logit_rank_config).resolve(),
                    merge_config=Path(args.merge_config).resolve(),
                    producer_lanes=_as_int(rank_opts.get("row_elems")),
                    logit_bits=_as_int(rank_opts.get("logit_bits")),
                    token_id_bits=_as_int(merge_opts.get("token_id_bits")),
                    top_k=_as_int(rank_opts.get("top_k")),
                )
                rtl_sim["rtlgen_binary"] = rtlgen_binary
    payload = build_report(
        producer_config=producer_config,
        logit_rank_config=logit_rank_config,
        merge_config=merge_config,
        integration_plan=integration_plan,
        rtl_sim=rtl_sim,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
