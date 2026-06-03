#!/usr/bin/env python3
"""Generate a dense FP16 GEMM-tile PPA harness.

The generated top is intentionally narrow at the boundary. It self-stimulates a
regular array of exact RTLGen FP16 MAC primitives from a small seed register and
folds all MAC outputs into a visible result register. This measures the dense
compute tile without replicating the current NPU dynamic dispatcher or vector
tail, while keeping every MAC output connected to the datapath.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen import generate_cpp_fp16_mac_module


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _validate_tile(tile: dict[str, Any]) -> None:
    array_m = _as_int(tile, "array_m", 4)
    array_n = _as_int(tile, "array_n", 4)
    k_unroll = _as_int(tile, "k_unroll", 1)
    pipeline_stages = _as_int(tile, "pipeline_stages", 1)
    if array_m < 1 or array_m > 16:
        raise SystemExit("dense_gemm_tile.array_m must be in [1, 16]")
    if array_n < 1 or array_n > 16:
        raise SystemExit("dense_gemm_tile.array_n must be in [1, 16]")
    if k_unroll < 1 or k_unroll > 4:
        raise SystemExit("dense_gemm_tile.k_unroll must be in [1, 4]")
    if pipeline_stages < 0 or pipeline_stages > 2:
        raise SystemExit("dense_gemm_tile.pipeline_stages must be in [0, 2]")
    if str(tile.get("precision", "fp16")).lower() != "fp16":
        raise SystemExit("dense_gemm_tile.precision currently supports only fp16")


def _signal_name(prefix: str, index: int) -> str:
    return f"{prefix}_{index:04d}"


def _write_top(*, cfg: dict[str, Any], out_path: Path, mac_module_name: str, mac_module_text: str) -> None:
    tile = cfg["dense_gemm_tile"]
    top_name = str(cfg.get("top_name", tile.get("module_name", "dense_gemm_tile_top"))).strip()
    array_m = _as_int(tile, "array_m", 4)
    array_n = _as_int(tile, "array_n", 4)
    k_unroll = _as_int(tile, "k_unroll", 1)
    pipeline_stages = _as_int(tile, "pipeline_stages", 1)
    mac_count = array_m * array_n * k_unroll

    wire_lines: list[str] = []
    input_reg_lines: list[str] = []
    input_reset_lines: list[str] = []
    input_update_lines: list[str] = []
    inst_lines: list[str] = []
    result_terms: list[str] = ["32'h0000_0000"]
    output_reg_lines: list[str] = []
    output_reset_lines: list[str] = []
    output_update_lines: list[str] = []
    output_terms: list[str] = ["32'h0000_0000"]

    for idx in range(mac_count):
        row = idx // (array_n * k_unroll)
        col = (idx // k_unroll) % array_n
        ku = idx % k_unroll
        const_a = (0x3C00 ^ ((row + 1) * 0x0131) ^ ((col + 1) * 0x0027) ^ (ku * 0x0041)) & 0xFFFF
        const_b = (0x4000 ^ ((row + 1) * 0x001D) ^ ((col + 1) * 0x00A3) ^ (ku * 0x0055)) & 0xFFFF
        const_c = (0x0000 ^ ((row + 1) * 0x0007) ^ ((col + 1) * 0x000B) ^ (ku * 0x0013)) & 0xFFFF
        a_src = f"(seed_state[15:0] ^ 16'h{const_a:04x} ^ cycle_ctr[15:0])"
        b_src = f"(seed_state[31:16] ^ 16'h{const_b:04x} ^ {{cycle_ctr[7:0], cycle_ctr[15:8]}})"
        c_src = f"(result_hash[15:0] ^ 16'h{const_c:04x})"
        a_name = _signal_name("mac_a", idx)
        b_name = _signal_name("mac_b", idx)
        c_name = _signal_name("mac_c", idx)
        r_name = _signal_name("mac_r", idx)
        if pipeline_stages >= 1:
            input_reg_lines.extend(
                [
                    f"  reg [15:0] {a_name}_q;",
                    f"  reg [15:0] {b_name}_q;",
                    f"  reg [15:0] {c_name}_q;",
                ]
            )
            input_reset_lines.extend(
                [
                    f"      {a_name}_q <= 16'h0000;",
                    f"      {b_name}_q <= 16'h0000;",
                    f"      {c_name}_q <= 16'h0000;",
                ]
            )
            input_update_lines.extend(
                [
                    f"      {a_name}_q <= {a_src};",
                    f"      {b_name}_q <= {b_src};",
                    f"      {c_name}_q <= {c_src};",
                ]
            )
            a_expr = f"{a_name}_q"
            b_expr = f"{b_name}_q"
            c_expr = f"{c_name}_q"
        else:
            wire_lines.extend(
                [
                    f"  wire [15:0] {a_name} = {a_src};",
                    f"  wire [15:0] {b_name} = {b_src};",
                    f"  wire [15:0] {c_name} = {c_src};",
                ]
            )
            a_expr = a_name
            b_expr = b_name
            c_expr = c_name

        wire_lines.append(f"  wire [15:0] {r_name};")
        inst_lines.append(
            f"""  {mac_module_name} u_mac_{idx:04d} (
    .A({a_expr}),
    .B({b_expr}),
    .C({c_expr}),
    .negateAB(1'b0),
    .negateC(1'b0),
    .RndMode(2'b00),
    .R({r_name})
  );"""
        )
        if pipeline_stages >= 2:
            rq_name = f"{r_name}_q"
            output_reg_lines.append(f"  reg [15:0] {rq_name};")
            output_reset_lines.append(f"      {rq_name} <= 16'h0000;")
            output_update_lines.append(f"      {rq_name} <= {r_name};")
            output_terms.append(f"{{16'h0000, {rq_name}}}")
        else:
            result_terms.append(f"{{16'h0000, {r_name}}}")

    if pipeline_stages >= 2:
        folded_expr = "\n      ^ ".join(output_terms)
    else:
        folded_expr = "\n      ^ ".join(result_terms)

    top_text = f"""// Auto-generated by npu/rtlgen/gen_dense_gemm_tile.py
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [31:0] seed,
    output reg         done,
    output reg  [31:0] result_hash
);
  localparam integer ARRAY_M = {array_m};
  localparam integer ARRAY_N = {array_n};
  localparam integer K_UNROLL = {k_unroll};
  localparam integer MACS_PER_CYCLE = {mac_count};
  localparam integer PIPELINE_STAGES = {pipeline_stages};

  reg [31:0] seed_state;
  reg [15:0] cycle_ctr;
  wire [31:0] folded_result;

{chr(10).join(wire_lines)}
{chr(10).join(input_reg_lines)}
{chr(10).join(output_reg_lines)}

{chr(10).join(inst_lines)}

  assign folded_result =
      {folded_expr};

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      seed_state <= 32'h1;
      cycle_ctr <= 16'h0;
      result_hash <= 32'h0;
      done <= 1'b0;
{chr(10).join(input_reset_lines)}
{chr(10).join(output_reset_lines)}
    end else begin
      seed_state <= {{seed_state[30:0], seed_state[31] ^ seed_state[21] ^ seed_state[1] ^ seed_state[0]}} ^ seed;
      cycle_ctr <= cycle_ctr + 16'h1;
      done <= start;
{chr(10).join(input_update_lines)}
{chr(10).join(output_update_lines)}
      if (start) begin
        result_hash <= result_hash ^ folded_result ^ seed_state ^ {{16'h0, cycle_ctr}};
      end
    end
  end
endmodule
"""

    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "top.v").write_text(mac_module_text + "\n\n" + top_text, encoding="utf-8")
    manifest = {
        "version": 0.1,
        "generator": "npu/rtlgen/gen_dense_gemm_tile.py",
        "top_name": top_name,
        "precision": "fp16",
        "array_m": array_m,
        "array_n": array_n,
        "k_unroll": k_unroll,
        "pipeline_stages": pipeline_stages,
        "mac_primitive": mac_module_name,
        "macs_per_cycle": mac_count,
        "external_io_policy": "narrow_self_stimulating_hash",
        "datapath_guard": "all MAC outputs fold into result_hash",
    }
    (out_path / "dense_gemm_tile_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out_path / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = _load_json(Path(args.config))
    tile = cfg.get("dense_gemm_tile")
    if not isinstance(tile, dict):
        raise SystemExit("config must contain dense_gemm_tile object")
    _validate_tile(tile)

    out_path = Path(args.out)
    gemm_cfg = {
        "rtlgen_cpp": tile.get(
            "rtlgen_cpp",
            {
                "binary_path": "build/rtlgen",
                "module_name": "gemm_mac_fp16_ieee",
                "total_width": 16,
                "mantissa_width": 10,
            },
        )
    }
    mac_module_name, mac_module_text = generate_cpp_fp16_mac_module(gemm_cfg, out_path)
    _write_top(cfg=cfg, out_path=out_path, mac_module_name=mac_module_name, mac_module_text=mac_module_text)
    print(f"dense-gemm-tile: wrote RTL to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
