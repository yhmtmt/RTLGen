#!/usr/bin/env python3
"""Generate a bounded dual-stream attention schedule/control wrapper.

This is an L1 PPA harness for the Llama7B attention frontier.  It composes the
existing central command dispatcher with a small bank of existing composed
dual-stream score/value datapaths and local ready/valid issue/done accounting.
The generated design intentionally measures a bounded 2/4-cluster slice, not
the full replicated Llama7B array.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_command_dispatch import _generate as _generate_dispatch
from npu.rtlgen.gen_attention_dual_stream_composed import _validate as _validate_datapath
from npu.rtlgen.gen_attention_dual_stream_composed import _write_top as _write_datapath_top


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    top_name = str(cfg.get("top_name", "")).strip()
    if not top_name:
        raise SystemExit("config top_name must not be empty")
    wrapper = cfg.get("attention_dual_stream_schedule_wrapper")
    if not isinstance(wrapper, dict):
        raise SystemExit("config must contain attention_dual_stream_schedule_wrapper object")
    datapath = wrapper.get("datapath")
    if not isinstance(datapath, dict):
        raise SystemExit("attention_dual_stream_schedule_wrapper.datapath must be an object")

    clusters = _as_int(wrapper, "clusters", 2)
    queue_depth = _as_int(wrapper, "queue_depth", 16)
    tile_id_bits = _as_int(wrapper, "tile_id_bits", 16)
    wave_id_bits = _as_int(wrapper, "wave_id_bits", 12)
    base_token_bits = _as_int(wrapper, "base_token_bits", 18)
    max_inflight = _as_int(wrapper, "max_inflight_per_cluster", 2)
    cluster_service_cycles = _as_int(wrapper, "cluster_service_cycles", 4)

    if clusters < 1 or clusters > 8:
        raise SystemExit("attention_dual_stream_schedule_wrapper.clusters must be in [1, 8]")
    if queue_depth < 2 or queue_depth > 64:
        raise SystemExit("attention_dual_stream_schedule_wrapper.queue_depth must be in [2, 64]")
    if max_inflight < 1 or max_inflight > 8:
        raise SystemExit("attention_dual_stream_schedule_wrapper.max_inflight_per_cluster must be in [1, 8]")
    if cluster_service_cycles < 1 or cluster_service_cycles > 64:
        raise SystemExit("attention_dual_stream_schedule_wrapper.cluster_service_cycles must be in [1, 64]")

    datapath_cfg = {
        "top_name": f"{top_name}_cluster_datapath",
        "attention_dual_stream_composed": dict(datapath),
    }
    datapath_params = _validate_datapath(datapath_cfg)
    return {
        "top_name": top_name,
        "clusters": clusters,
        "queue_depth": queue_depth,
        "tile_id_bits": tile_id_bits,
        "wave_id_bits": wave_id_bits,
        "base_token_bits": base_token_bits,
        "max_inflight_per_cluster": max_inflight,
        "cluster_service_cycles": cluster_service_cycles,
        "datapath_cfg": datapath_cfg,
        "datapath_params": datapath_params,
    }


def _datapath_seed_expr(*, cluster: int, tile_bits: int, wave_bits: int, base_bits: int) -> str:
    terms = [
        "dispatch_tile_id[31:0]" if tile_bits >= 32 else f"{{{{{32 - tile_bits}{{1'b0}}}}, dispatch_tile_id}}",
        "dispatch_wave_id[31:0]" if wave_bits >= 32 else f"{{{{{32 - wave_bits}{{1'b0}}}}, dispatch_wave_id}}",
        "dispatch_base_token[31:0]" if base_bits >= 32 else f"{{{{{32 - base_bits}{{1'b0}}}}, dispatch_base_token}}",
        f"32'h{0x9E3779B9 ^ (cluster * 0x01010101):08x}",
    ]
    return " ^ ".join(terms)


def _generate_wrapper_top(*, params: dict[str, Any], datapath_manifest: dict[str, Any]) -> str:
    top = str(params["top_name"])
    clusters = int(params["clusters"])
    tile_bits = int(params["tile_id_bits"])
    wave_bits = int(params["wave_id_bits"])
    base_bits = int(params["base_token_bits"])
    service_cycles = int(params["cluster_service_cycles"])
    cluster_bits = _clog2(clusters)
    service_bits = _clog2(service_cycles + 1)
    count_bits = 32
    datapath_top = f"{top}_cluster_datapath"
    dispatch_top = f"{top}_dispatch"
    weight_width = int(datapath_manifest["softmax_row_elems"]) * int(datapath_manifest["softmax_weight_bits"])
    score_mix_bits = int(datapath_manifest["score_mix_bits"])

    reg_lines: list[str] = []
    wire_lines: list[str] = []
    inst_lines: list[str] = []
    reset_lines: list[str] = []
    seq_lines: list[str] = []
    fold_terms: list[str] = ["32'h0000_0000"]
    done_priority: list[str] = []
    start_assigns: list[str] = []
    ready_terms: list[str] = []

    for idx in range(clusters):
        reg_lines.extend(
            [
                f"  reg cluster_{idx}_active;",
                f"  reg [{service_bits - 1}:0] cluster_{idx}_service_ctr;",
                f"  reg [31:0] cluster_{idx}_seed;",
            ]
        )
        wire_lines.extend(
            [
                f"  wire cluster_{idx}_start;",
                f"  wire cluster_{idx}_done;",
                f"  wire [{weight_width - 1}:0] cluster_{idx}_weights;",
                f"  wire [39:0] cluster_{idx}_value0;",
                f"  wire [39:0] cluster_{idx}_value1;",
                f"  wire [{score_mix_bits - 1}:0] cluster_{idx}_score0;",
                f"  wire [{score_mix_bits - 1}:0] cluster_{idx}_score1;",
                f"  wire cluster_{idx}_complete = cluster_{idx}_active && (cluster_{idx}_service_ctr == {service_bits}'d{service_cycles - 1});",
            ]
        )
        ready_terms.append(f"(external_cluster_ready[{idx}] && !cluster_{idx}_active)")
        start_assigns.append(
            f"  assign cluster_{idx}_start = local_issue_valid && (dispatch_cluster_id == {cluster_bits}'d{idx});"
        )
        inst_lines.append(
            f"""  {datapath_top} u_cluster_datapath_{idx} (
    .clk(clk),
    .rst_n(rst_n),
    .start(cluster_{idx}_start),
    .seed(cluster_{idx}_seed),
    .done(cluster_{idx}_done),
    .softmax_weights_out(cluster_{idx}_weights),
    .value_accum_0_out(cluster_{idx}_value0),
    .value_accum_1_out(cluster_{idx}_value1),
    .score_mix_0_out(cluster_{idx}_score0),
    .score_mix_1_out(cluster_{idx}_score1)
  );"""
        )
        reset_lines.extend(
            [
                f"      cluster_{idx}_active <= 1'b0;",
                f"      cluster_{idx}_service_ctr <= {service_bits}'h0;",
                f"      cluster_{idx}_seed <= 32'h{0x1000 + idx:08x};",
            ]
        )
        seq_lines.append(
            f"""      if (cluster_{idx}_start) begin
        cluster_{idx}_active <= 1'b1;
        cluster_{idx}_service_ctr <= {service_bits}'h0;
        cluster_{idx}_seed <= {_datapath_seed_expr(cluster=idx, tile_bits=tile_bits, wave_bits=wave_bits, base_bits=base_bits)};
      end else if (cluster_{idx}_complete) begin
        cluster_{idx}_active <= 1'b0;
        cluster_{idx}_service_ctr <= {service_bits}'h0;
      end else if (cluster_{idx}_active) begin
        cluster_{idx}_service_ctr <= cluster_{idx}_service_ctr + 1'b1;
      end"""
        )
        fold_terms.extend(
            [
                f"cluster_{idx}_weights[31:0]",
                f"cluster_{idx}_value0[31:0]",
                f"cluster_{idx}_value1[31:0]",
                f"cluster_{idx}_score0[31:0]",
                f"cluster_{idx}_score1[31:0]",
                f"{{31'h0, cluster_{idx}_done}}",
            ]
        )
        branch = "if" if idx == 0 else "end else if"
        done_priority.append(
            f"""    {branch} (cluster_{idx}_complete) begin
      done_valid_next = 1'b1;
      done_id_next = {cluster_bits}'d{idx};"""
        )

    ready_concat = ", ".join(reversed(ready_terms))
    fold_expr = " ^\n      ".join(fold_terms)
    done_priority_text = "\n".join(done_priority)
    return f"""// Generated by npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py
(* keep_hierarchy = 1 *)
module {top} (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         command_valid,
    output wire                         command_ready,
    input  wire [{tile_bits - 1}:0]     command_tile_id,
    input  wire [{wave_bits - 1}:0]     command_wave_id,
    input  wire [{base_bits - 1}:0]     command_base_token,
    input  wire [{clusters - 1}:0]      external_cluster_ready,
    output reg  [31:0]                  completed_count,
    output reg  [31:0]                  result_fold
);
  localparam integer CLUSTERS = {clusters};
  localparam integer CLUSTER_SERVICE_CYCLES = {service_cycles};

{chr(10).join(reg_lines)}
{chr(10).join(wire_lines)}

  wire [{clusters - 1}:0] cluster_ready = {{{ready_concat}}};
  wire dispatch_valid;
  wire dispatch_ready = 1'b1;
  wire [{cluster_bits - 1}:0] dispatch_cluster_id;
  wire [{tile_bits - 1}:0] dispatch_tile_id;
  wire [{wave_bits - 1}:0] dispatch_wave_id;
  wire [{base_bits - 1}:0] dispatch_base_token;
  wire queue_empty;
  wire queue_full;
  wire local_issue_valid = dispatch_valid && dispatch_ready;
  wire cluster_done_valid;
  wire [{cluster_bits - 1}:0] cluster_done_id;
  reg done_valid_next;
  reg [{cluster_bits - 1}:0] done_id_next;
  wire [31:0] datapath_result_fold =
      {fold_expr};

  assign cluster_done_valid = done_valid_next;
  assign cluster_done_id = done_id_next;

  {dispatch_top} u_dispatch (
    .clk(clk),
    .rst_n(rst_n),
    .command_valid(command_valid),
    .command_ready(command_ready),
    .command_tile_id(command_tile_id),
    .command_wave_id(command_wave_id),
    .command_base_token(command_base_token),
    .cluster_ready(cluster_ready),
    .cluster_done_valid(cluster_done_valid),
    .cluster_done_id(cluster_done_id),
    .dispatch_valid(dispatch_valid),
    .dispatch_ready(dispatch_ready),
    .dispatch_cluster_id(dispatch_cluster_id),
    .dispatch_tile_id(dispatch_tile_id),
    .dispatch_wave_id(dispatch_wave_id),
    .dispatch_base_token(dispatch_base_token),
    .queue_empty(queue_empty),
    .queue_full(queue_full),
    .queued_count()
  );

{chr(10).join(start_assigns)}

{chr(10).join(inst_lines)}

  always @* begin
    done_valid_next = 1'b0;
    done_id_next = {cluster_bits}'h0;
{done_priority_text}
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      completed_count <= {count_bits}'h0;
      result_fold <= 32'h0;
{chr(10).join(reset_lines)}
    end else begin
{chr(10).join(seq_lines)}
      if (cluster_done_valid) begin
        completed_count <= completed_count + 1'b1;
        result_fold <= result_fold ^ datapath_result_fold ^ {{16'h0, command_tile_id[15:0]}} ^ {{20'h0, cluster_done_id}};
      end
    end
  end
endmodule
"""


def _write_wrapper(*, cfg: dict[str, Any], params: dict[str, Any], out_path: Path) -> None:
    out_path.mkdir(parents=True, exist_ok=True)
    top = str(params["top_name"])
    dispatch_top = f"{top}_dispatch"
    dispatch_params = {
        "top_name": dispatch_top,
        "clusters": params["clusters"],
        "queue_depth": params["queue_depth"],
        "tile_id_bits": params["tile_id_bits"],
        "wave_id_bits": params["wave_id_bits"],
        "base_token_bits": params["base_token_bits"],
        "max_inflight_per_cluster": params["max_inflight_per_cluster"],
    }
    with tempfile.TemporaryDirectory() as td:
        tmp_out = Path(td) / "datapath"
        _write_datapath_top(
            cfg=params["datapath_cfg"],
            comp=params["datapath_params"],
            out_path=tmp_out,
        )
        datapath_rtl = (tmp_out / "top.v").read_text(encoding="utf-8")
        datapath_manifest = json.loads(
            (tmp_out / "attention_dual_stream_composed_manifest.json").read_text(encoding="utf-8")
        )

    dispatch_rtl = _generate_dispatch(dispatch_params)
    wrapper_rtl = _generate_wrapper_top(params=params, datapath_manifest=datapath_manifest)
    (out_path / "top.v").write_text(
        "\n\n".join([dispatch_rtl, datapath_rtl, wrapper_rtl]),
        encoding="utf-8",
    )
    manifest = {
        "version": 0.1,
        "generator": "npu/rtlgen/gen_attention_dual_stream_schedule_wrapper.py",
        "top_name": top,
        "clusters": int(params["clusters"]),
        "queue_depth": int(params["queue_depth"]),
        "max_inflight_per_cluster": int(params["max_inflight_per_cluster"]),
        "cluster_service_cycles": int(params["cluster_service_cycles"]),
        "datapath_top_name": params["datapath_cfg"]["top_name"],
        "dispatch_top_name": dispatch_top,
        "datapath_total_macs_per_cluster": int(datapath_manifest["total_macs"]),
        "total_macs": int(datapath_manifest["total_macs"]) * int(params["clusters"]),
        "datapath_manifest": datapath_manifest,
        "remaining_abstractions": [
            "bounded cluster slice must still be scaled to the full Llama7B replica count",
            "external SRAM, NoC, HBM/DRAM service, and distributed clock/reset signoff remain outside this wrapper",
            "local datapath stimulus is deterministic PPA/equivalence stimulus, not full token data replay",
        ],
    }
    (out_path / "attention_dual_stream_schedule_wrapper_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_path / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    cfg = _load_json(Path(args.config))
    params = _validate(cfg)
    _write_wrapper(cfg=cfg, params=params, out_path=Path(args.out))
    print(f"attention-dual-stream-schedule-wrapper: wrote RTL to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
