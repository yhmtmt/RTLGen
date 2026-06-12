#!/usr/bin/env python3
"""Generate a composed dual-stream attention datapath PPA harness.

The generated top keeps the external boundary narrow while composing the local
datapath pieces used by the Llama7B mixed-precision dual-stream feasibility
model: two int8 dense compute streams, a shared int8 softmax-weight generator,
two q8/v6 full-value streams, stream buffers, and simple start/done control.
Every internal result is folded into a visible hash to prevent dead-code
elimination during synthesis.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    comp = cfg.get("attention_dual_stream_composed")
    if not isinstance(comp, dict):
        raise SystemExit("config must contain attention_dual_stream_composed object")
    streams = _as_int(comp, "streams", 2)
    array_m = _as_int(comp, "array_m", 16)
    array_n = _as_int(comp, "array_n", 8)
    k_unroll = _as_int(comp, "k_unroll", 1)
    row_elems = _as_int(comp, "softmax_row_elems", 8)
    value_lanes = _as_int(comp, "value_lanes", 16)
    partials = _as_int(comp, "partials", 8)
    partials_per_cycle = _as_int(comp, "partials_per_cycle", 2)
    stream_buffer_bits = _as_int(comp, "stream_buffer_bits", 1024)
    if streams != 2:
        raise SystemExit("attention_dual_stream_composed.streams must be 2 for the current dual-stream harness")
    if array_m < 1 or array_m > 16:
        raise SystemExit("attention_dual_stream_composed.array_m must be in [1, 16]")
    if array_n < 1 or array_n > 16:
        raise SystemExit("attention_dual_stream_composed.array_n must be in [1, 16]")
    if k_unroll < 1 or k_unroll > 4:
        raise SystemExit("attention_dual_stream_composed.k_unroll must be in [1, 4]")
    if row_elems < 1 or row_elems > 16:
        raise SystemExit("attention_dual_stream_composed.softmax_row_elems must be in [1, 16]")
    if value_lanes < 1 or value_lanes > 32:
        raise SystemExit("attention_dual_stream_composed.value_lanes must be in [1, 32]")
    if partials < 1 or partials > 16:
        raise SystemExit("attention_dual_stream_composed.partials must be in [1, 16]")
    if partials_per_cycle < 1 or partials_per_cycle > partials:
        raise SystemExit("attention_dual_stream_composed.partials_per_cycle must be in [1, partials]")
    if stream_buffer_bits < 128 or stream_buffer_bits > 4096:
        raise SystemExit("attention_dual_stream_composed.stream_buffer_bits must be in [128, 4096]")
    return comp


def _int8_mac_module() -> str:
    return """module int8_mac_s8s8_acc24 (
    input  wire signed [7:0]  A,
    input  wire signed [7:0]  B,
    input  wire signed [23:0] C,
    output wire signed [23:0] R
);
  wire signed [15:0] product = A * B;
  assign R = {{8{product[15]}}, product} + C;
endmodule
"""


def _softmax_module(*, module_name: str, row_elems: int, accum_bits: int, reciprocal_bits: int) -> str:
    data_width = row_elems * 8
    product_bits = accum_bits + 8
    return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{data_width - 1}:0] scores,
    output reg  [{data_width - 1}:0] weights,
    output reg  [31:0]          weight_hash
);
  localparam integer ROW_ELEMS = {row_elems};
  localparam integer ACCUM_BITS = {accum_bits};
  localparam integer PRODUCT_BITS = {product_bits};
  localparam integer MAX_SHIFT = 7;
  localparam integer OUTPUT_SCALE = 127;
  localparam integer RECIPROCAL_BITS = {reciprocal_bits};

  integer i;
  integer signed lane_val;
  integer signed row_max;
  integer delta;
  reg [ACCUM_BITS-1:0] exp_weight [0:ROW_ELEMS-1];
  reg [ACCUM_BITS-1:0] sum_weight;
  reg [PRODUCT_BITS-1:0] numer;
  reg [7:0] lane_out;
  reg [{data_width - 1}:0] next_weights;
  reg [31:0] next_hash;

  always @(*) begin
    row_max = -(1 << 7);
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*8) +: 8]);
      if (lane_val > row_max)
        row_max = lane_val;
    end

    sum_weight = {{ACCUM_BITS{{1'b0}}}};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      lane_val = $signed(scores[(i*8) +: 8]);
      delta = row_max - lane_val;
      if (delta < 0)
        delta = 0;
      if (delta > MAX_SHIFT)
        delta = MAX_SHIFT;
      exp_weight[i] = ({{{{(ACCUM_BITS-1){{1'b0}}}}, 1'b1}} << (MAX_SHIFT - delta));
      sum_weight = sum_weight + exp_weight[i];
    end

    next_weights = {{{data_width}{{1'b0}}}};
      next_hash = 32'h5a5a_0101 ^ 32'h{reciprocal_bits & 0xFFFF:04x};
    for (i = 0; i < ROW_ELEMS; i = i + 1) begin
      numer = (exp_weight[i] * OUTPUT_SCALE) + (sum_weight >> 1);
      if (sum_weight != 0)
        lane_out = numer / sum_weight;
      else
        lane_out = 8'h00;
      if (lane_out > 8'd127)
        lane_out = 8'd127;
      next_weights[(i*8) +: 8] = lane_out;
      next_hash = {{next_hash[23:0], next_hash[31:24]}} ^ {{24'h0, lane_out}};
    end
  end

  always @(posedge clk) begin
    weights <= next_weights;
    weight_hash <= next_hash;
  end
endmodule
"""


def _value_stream_module(*, module_name: str, row_elems: int, value_lanes: int, stream_buffer_bits: int) -> str:
    acc_bits = 40
    product_bits = 16
    fold_terms = ["32'h0000_0000"]
    product_lines: list[str] = []
    for lane in range(value_lanes):
        product_lines.extend(
            [
                f"  wire signed [5:0] value_{lane:02d} = stream_data[{(lane * 6) % (stream_buffer_bits - 5)} +: 6];",
                f"  wire signed [7:0] weight_{lane:02d} = weights[{(lane % row_elems) * 8} +: 8];",
                f"  wire signed [{product_bits - 1}:0] product_{lane:02d} = value_{lane:02d} * weight_{lane:02d};",
            ]
        )
        fold_terms.append(f"{{16'h0, product_{lane:02d}}}")
    sum_terms = [
        f"{{{{{acc_bits - product_bits}{{product_{lane:02d}[{product_bits - 1}]}}}}, product_{lane:02d}}}"
        for lane in range(value_lanes)
    ]
    sum_expr = " +\n      ".join(sum_terms)
    fold_expr = " ^\n      ".join(fold_terms)
    score_ext = f"{{{{{acc_bits - 24}{{score_mix[23]}}}}, score_mix}}"
    return f"""(* keep_hierarchy = 1 *)
module {module_name} (
    input  wire                  clk,
    input  wire [{stream_buffer_bits - 1}:0] stream_data,
    input  wire [{row_elems * 8 - 1}:0] weights,
    input  wire [23:0]           score_mix,
    output reg  [{acc_bits - 1}:0] value_accum,
    output reg  [31:0]           value_hash
);
{chr(10).join(product_lines)}
  wire signed [{acc_bits - 1}:0] product_sum =
      {sum_expr};
  wire [31:0] product_fold =
      {fold_expr};

  always @(posedge clk) begin
    value_accum <= product_sum + {score_ext};
    value_hash <= product_fold ^ value_accum[31:0] ^ {{8'h0, score_mix}};
  end
endmodule
"""


def _write_top(*, cfg: dict[str, Any], comp: dict[str, Any], out_path: Path) -> None:
    top_name = str(cfg.get("top_name", "attention_dual_stream_composed_top")).strip()
    array_m = _as_int(comp, "array_m", 16)
    array_n = _as_int(comp, "array_n", 8)
    k_unroll = _as_int(comp, "k_unroll", 1)
    row_elems = _as_int(comp, "softmax_row_elems", 8)
    value_lanes = _as_int(comp, "value_lanes", 16)
    partials = _as_int(comp, "partials", 8)
    partials_per_cycle = _as_int(comp, "partials_per_cycle", 2)
    reciprocal_bits = _as_int(comp, "reciprocal_bits", 10)
    accum_bits = _as_int(comp, "softmax_accum_bits", 24)
    stream_buffer_bits = _as_int(comp, "stream_buffer_bits", 1024)
    macs_per_stream = array_m * array_n * k_unroll
    streams = 2
    total_macs = streams * macs_per_stream
    softmax_name = "attention_softmax_weight_int8_r8_acc24_recip_q10_like"
    value_name = "attention_full_value_stream_q8v6_p8_ppc2"

    stream_regs = [f"  reg [{stream_buffer_bits - 1}:0] stream_buf_{stream};" for stream in range(streams)]
    stream_reset = [f"      stream_buf_{stream} <= {{{stream_buffer_bits}{{1'b0}}}};" for stream in range(streams)]
    stream_update = [
        (
            f"      stream_buf_{stream} <= {{stream_buf_{stream}[{stream_buffer_bits - 33}:0], "
            f"seed_state ^ result_hash ^ 32'h{0x13572468 ^ stream:08x}}};"
        )
        for stream in range(streams)
    ]

    mac_wires: list[str] = []
    mac_insts: list[str] = []
    score_lane_terms: list[list[str]] = [[] for _ in range(row_elems)]
    score_mix_terms = [["24'h000000"] for _ in range(streams)]
    compute_fold_terms = ["32'h0000_0000"]
    for stream in range(streams):
        for idx in range(macs_per_stream):
            row = idx // (array_n * k_unroll)
            col = (idx // k_unroll) % array_n
            ku = idx % k_unroll
            flat = stream * macs_per_stream + idx
            const_a = (0x3D ^ ((stream + 1) * 0x17) ^ ((row + 1) * 0x13) ^ ((col + 1) * 0x27) ^ (ku * 0x41)) & 0xFF
            const_b = (0x21 ^ ((stream + 1) * 0x2B) ^ ((row + 1) * 0x1D) ^ ((col + 1) * 0xA3) ^ (ku * 0x55)) & 0xFF
            const_c = (0x001011 ^ ((stream + 1) * 0x0101) ^ ((row + 1) * 0x0007) ^ ((col + 1) * 0x000B) ^ (ku * 0x0013)) & 0xFFFFFF
            mac_wires.extend(
                [
                    f"  wire signed [7:0] mac_a_{flat:04d} = seed_state[7:0] ^ stream_buf_{stream}[{(idx * 7) % (stream_buffer_bits - 7)} +: 8] ^ 8'h{const_a:02x} ^ cycle_ctr[7:0];",
                    f"  wire signed [7:0] mac_b_{flat:04d} = seed_state[15:8] ^ stream_buf_{stream}[{(idx * 11) % (stream_buffer_bits - 7)} +: 8] ^ 8'h{const_b:02x} ^ cycle_ctr[15:8];",
                    f"  wire signed [23:0] mac_c_{flat:04d} = {{8'h00, result_hash[15:0]}} ^ stream_buf_{stream}[{(idx * 13) % (stream_buffer_bits - 23)} +: 24] ^ 24'h{const_c:06x};",
                    f"  wire signed [23:0] mac_r_{flat:04d};",
                ]
            )
            mac_insts.append(
                f"""  int8_mac_s8s8_acc24 u_mac_{flat:04d} (
    .A(mac_a_{flat:04d}),
    .B(mac_b_{flat:04d}),
    .C(mac_c_{flat:04d}),
    .R(mac_r_{flat:04d})
  );"""
            )
            score_lane_terms[idx % row_elems].append(f"mac_r_{flat:04d}[7:0]")
            score_mix_terms[stream].append(f"mac_r_{flat:04d}")
            compute_fold_terms.append(f"{{8'h00, mac_r_{flat:04d}}}")

    score_assigns = []
    for lane, terms in enumerate(score_lane_terms):
        expr = " ^ ".join(terms or ["8'h00"])
        score_assigns.append(f"  wire [7:0] score_lane_{lane:02d} = {expr};")
    score_row_concat = ", ".join(f"score_lane_{lane:02d}" for lane in reversed(range(row_elems)))
    compute_fold_expr = " ^\n      ".join(compute_fold_terms)
    score_mix_exprs = [" ^\n      ".join(terms) for terms in score_mix_terms]

    top_text = f"""// Auto-generated by npu/rtlgen/gen_attention_dual_stream_composed.py
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [31:0] seed,
    output reg         done,
    output reg  [31:0] result_hash
);
  localparam integer STREAMS = {streams};
  localparam integer ARRAY_M = {array_m};
  localparam integer ARRAY_N = {array_n};
  localparam integer K_UNROLL = {k_unroll};
  localparam integer MACS_PER_STREAM = {macs_per_stream};
  localparam integer TOTAL_MACS = {total_macs};
  localparam integer SOFTMAX_ROW_ELEMS = {row_elems};
  localparam integer VALUE_LANES = {value_lanes};
  localparam integer PARTIALS = {partials};
  localparam integer PARTIALS_PER_CYCLE = {partials_per_cycle};
  localparam integer STREAM_BUFFER_BITS = {stream_buffer_bits};

  reg [31:0] seed_state;
  reg [15:0] cycle_ctr;
{chr(10).join(stream_regs)}

{chr(10).join(mac_wires)}

{chr(10).join(mac_insts)}

{chr(10).join(score_assigns)}
  wire [{row_elems * 8 - 1}:0] softmax_scores = {{{score_row_concat}}};
  wire [{row_elems * 8 - 1}:0] softmax_weights;
  wire [31:0] softmax_weight_hash;
  wire [31:0] compute_fold =
      {compute_fold_expr};
  wire [23:0] score_mix_0 =
      {score_mix_exprs[0]};
  wire [23:0] score_mix_1 =
      {score_mix_exprs[1]};
  wire [39:0] value_accum_0;
  wire [39:0] value_accum_1;
  wire [31:0] value_hash_0;
  wire [31:0] value_hash_1;

  {softmax_name} u_softmax (
    .clk(clk),
    .scores(softmax_scores),
    .weights(softmax_weights),
    .weight_hash(softmax_weight_hash)
  );

  {value_name} u_value_stream_0 (
    .clk(clk),
    .stream_data(stream_buf_0),
    .weights(softmax_weights),
    .score_mix(score_mix_0),
    .value_accum(value_accum_0),
    .value_hash(value_hash_0)
  );

  {value_name} u_value_stream_1 (
    .clk(clk),
    .stream_data(stream_buf_1),
    .weights(softmax_weights),
    .score_mix(score_mix_1),
    .value_accum(value_accum_1),
    .value_hash(value_hash_1)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      seed_state <= 32'h0000_0001;
      cycle_ctr <= 16'h0;
      result_hash <= 32'h0;
      done <= 1'b0;
{chr(10).join(stream_reset)}
    end else begin
      seed_state <= {{seed_state[30:0], seed_state[31] ^ seed_state[21] ^ seed_state[1] ^ seed_state[0]}} ^ seed;
      cycle_ctr <= cycle_ctr + 16'h1;
      done <= start;
{chr(10).join(stream_update)}
      if (start) begin
        result_hash <= result_hash ^ compute_fold ^ softmax_weight_hash ^ value_hash_0 ^ value_hash_1 ^
                       value_accum_0[31:0] ^ value_accum_1[31:0] ^ {{16'h0, cycle_ctr}};
      end
    end
  end
endmodule
"""

    out_path.mkdir(parents=True, exist_ok=True)
    rtl = "\n\n".join(
        [
            _int8_mac_module(),
            _softmax_module(module_name=softmax_name, row_elems=row_elems, accum_bits=accum_bits, reciprocal_bits=reciprocal_bits),
            _value_stream_module(module_name=value_name, row_elems=row_elems, value_lanes=value_lanes, stream_buffer_bits=stream_buffer_bits),
            top_text,
        ]
    )
    (out_path / "top.v").write_text(rtl, encoding="utf-8")
    manifest = {
        "version": 0.1,
        "generator": "npu/rtlgen/gen_attention_dual_stream_composed.py",
        "top_name": top_name,
        "streams": streams,
        "array_m": array_m,
        "array_n": array_n,
        "k_unroll": k_unroll,
        "macs_per_stream": macs_per_stream,
        "total_macs": total_macs,
        "softmax_row_elems": row_elems,
        "softmax_accum_bits": accum_bits,
        "reciprocal_bits": reciprocal_bits,
        "value_bits": 6,
        "value_lanes_per_stream": value_lanes,
        "partials": partials,
        "partials_per_cycle": partials_per_cycle,
        "stream_buffer_bits_per_stream": stream_buffer_bits,
        "components": {
            "compute": "two signed-int8 dense GEMM streams",
            "softmax_weight": "one shared rowwise int8 shift-exp reciprocal-normalized generator",
            "full_value": "two q8/v6 weighted-value streams",
            "control": "start/done, seed LFSR, per-stream buffer registers, result hash",
        },
        "datapath_guard": "all MAC, softmax, and value stream outputs fold into result_hash",
    }
    (out_path / "attention_dual_stream_composed_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_path / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = _load_json(Path(args.config))
    comp = _validate(cfg)
    _write_top(cfg=cfg, comp=comp, out_path=Path(args.out))
    print(f"attention-dual-stream-composed: wrote RTL to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
