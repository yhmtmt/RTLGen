#!/usr/bin/env python3
"""Generate narrow-I/O PPA harnesses for exact K ingress transpose variants."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_score32_exact_kv_key_ingress_ppa_harness"
MANIFEST_NAME = "attention_score32_exact_kv_key_ingress_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_score32_exact_kv_key_ingress_ppa_v1"
ONE_BUFFER_SOURCE = (
    REPO_ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_single_buffer_transpose.sv"
)
PINGPONG_SOURCE = (
    REPO_ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to an object: {path}")
    return payload


def _validate(config: dict[str, Any]) -> tuple[str, str, int, int]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    architecture = str(body.get("architecture") or "").strip()
    producers = int(body.get("producers", 53))
    kv_head = int(body.get("kv_head", 3))
    if architecture not in {"one_buffer_serial", "pingpong_wide_auto"}:
        raise SystemExit("architecture must be one_buffer_serial or pingpong_wide_auto")
    if producers not in {53, 54}:
        raise SystemExit("producers must be 53 or 54")
    if kv_head not in range(4):
        raise SystemExit("kv_head must be in [0, 3]")
    return top_name, architecture, producers, kv_head


def _common(*, top_name: str, producers: int, kv_head: int, body: str) -> str:
    return f"""(* keep_hierarchy = 1 *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire start,
  input wire [31:0] seed,
  output wire done,
  output wire [31:0] activity_checksum,
  output wire [31:0] cycle_count,
  output wire [31:0] ingress_accept_count,
  output wire [31:0] output_accept_count,
  output wire [31:0] ingress_stall_count,
  output wire protocol_error
);
  localparam integer PRODUCERS = {producers};
  localparam [1:0] KV_HEAD = 2'd{kv_head};
  reg running_q;
  reg done_q;
  reg [31:0] cycle_q;
  reg [31:0] ingress_count_q;
  reg [31:0] output_count_q;
  reg [31:0] ingress_stall_q;
  reg [31:0] checksum_q;
  reg [255:0] data_q;

  function automatic [31:0] fold_output;
    input [255:0] value;
    input [15:0] metadata;
    integer word;
    integer rotate;
    reg [31:0] slice;
    begin
      fold_output = {{16'd0, metadata}} ^ 32'h6d2b_79f5;
      for (word = 0; word < 8; word = word + 1) begin
        slice = value[word*32 +: 32];
        rotate = (word * 3 + 1) % 31;
        fold_output = fold_output ^ (slice << rotate) ^
          (slice >> (32-rotate)) ^ (32'h45d9_f3b * (word + 1));
      end
    end
  endfunction

  assign done = done_q;
  assign activity_checksum = checksum_q;
  assign cycle_count = cycle_q;
  assign ingress_accept_count = ingress_count_q;
  assign output_accept_count = output_count_q;
  assign ingress_stall_count = ingress_stall_q;

{body}

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running_q <= 1'b0;
      done_q <= 1'b0;
      cycle_q <= 32'd0;
      ingress_count_q <= 32'd0;
      output_count_q <= 32'd0;
      ingress_stall_q <= 32'd0;
      checksum_q <= 32'd0;
      data_q <= 256'd1;
    end else begin
      if (start && !running_q && !done_q) begin
        running_q <= 1'b1;
        data_q <= {{8{{seed == 0 ? 32'd1 : seed}}}};
      end
      if (running_q)
        cycle_q <= cycle_q + 1'b1;
      if (ingress_valid_w && !ingress_ready_w)
        ingress_stall_q <= ingress_stall_q + 1'b1;
      if (ingress_valid_w && ingress_ready_w) begin
        ingress_count_q <= ingress_count_q + 1'b1;
        data_q <= {{data_q[254:0], data_q[255] ^ data_q[253] ^ data_q[250] ^ data_q[245]}};
      end
      if (output_fire_w) begin
        output_count_q <= output_count_q + 1'b1;
        checksum_q <= checksum_q ^ fold_output(output_data_w, output_metadata_w);
      end
      if (run_complete_w) begin
        running_q <= 1'b0;
        done_q <= 1'b1;
      end
    end
  end
endmodule
"""


def _pingpong_body() -> str:
    return """  wire ingress_valid_w = running_q && ingress_count_q < 32'd4096;
  wire ingress_ready_w;
  wire [5:0] block_slot_w = ingress_count_q[11:6];
  wire stream_w = ingress_count_q[5];
  wire [2:0] token_lane_w = ingress_count_q[4:2];
  wire [1:0] chunk_w = ingress_count_q[1:0];
  wire [19:0] ingress_address_w = {1'b0, KV_HEAD, stream_w, block_slot_w,
    token_lane_w, chunk_w, 5'd0};
  wire key_valid_w;
  wire [5:0] key_producer_w;
  wire [1:0] key_kv_head_w;
  wire key_producer_block_w;
  wire [5:0] key_dimension_pair_w;
  wire [255:0] key_data_w;
  wire key_last_w;
  wire output_fire_w = key_valid_w && running_q;
  wire [255:0] output_data_w = key_data_w;
  wire [15:0] output_metadata_w = {key_producer_w, key_kv_head_w,
    key_producer_block_w, key_dimension_pair_w, key_last_w};
  wire run_complete_w = output_fire_w && output_count_q == 32'd4095;

  attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS(PRODUCERS)) dut (
    .clk(clk), .rst_n(rst_n),
    .ingress_valid(ingress_valid_w), .ingress_ready(ingress_ready_w),
    .ingress_tile_byte_addr(ingress_address_w), .ingress_data(data_q),
    .ingress_byte_valid(32'hffff_ffff),
    .key_valid(key_valid_w), .key_ready(running_q),
    .key_producer(key_producer_w), .key_kv_head(key_kv_head_w),
    .key_producer_block(key_producer_block_w),
    .key_dimension_pair(key_dimension_pair_w), .key_data(key_data_w),
    .key_last(key_last_w), .protocol_error(protocol_error)
  );"""


def _one_buffer_body() -> str:
    return """  reg target_pending_q;
  reg [5:0] target_slot_q;
  wire target_ready_w;
  wire target_fire_w = target_pending_q && target_ready_w;
  wire ingress_valid_w = running_q && !target_pending_q && ingress_count_q < 32'd4096;
  wire ingress_ready_w;
  wire [5:0] flit_in_block_w = ingress_count_q[5:0];
  wire stream_w = flit_in_block_w[5];
  wire [2:0] token_lane_w = flit_in_block_w[4:2];
  wire [1:0] chunk_w = flit_in_block_w[1:0];
  wire [19:0] ingress_address_w = {1'b0, KV_HEAD, stream_w, target_slot_q,
    token_lane_w, chunk_w, 5'd0};
  wire key_valid_w;
  wire [5:0] key_producer_w;
  wire [1:0] key_kv_head_w;
  wire key_producer_block_w;
  wire [6:0] key_dimension_w;
  wire [127:0] key_data_w;
  wire key_last_w;
  wire output_fire_w = key_valid_w && running_q;
  wire [255:0] output_data_w = {128'd0, key_data_w};
  wire [15:0] output_metadata_w = {key_producer_w, key_kv_head_w,
    key_producer_block_w, key_dimension_w};
  wire run_complete_w = output_fire_w && output_count_q == 32'd8191;
  attention_score32_exact_kv_key_single_buffer_transpose #(.PRODUCERS(PRODUCERS)) dut (
    .clk(clk), .rst_n(rst_n),
    .target_valid(target_pending_q), .target_ready(target_ready_w),
    .target_kv_head(KV_HEAD), .target_block_slot(target_slot_q),
    .ingress_valid(ingress_valid_w), .ingress_ready(ingress_ready_w),
    .ingress_tile_byte_addr(ingress_address_w), .ingress_data(data_q),
    .ingress_byte_valid(32'hffff_ffff),
    .key_valid(key_valid_w), .key_ready(running_q),
    .key_producer(key_producer_w), .key_kv_head(key_kv_head_w),
    .key_producer_block(key_producer_block_w), .key_dimension(key_dimension_w),
    .key_data(key_data_w), .key_last(key_last_w), .protocol_error(protocol_error)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      target_pending_q <= 1'b0;
      target_slot_q <= 6'd0;
    end else begin
      if (start && !running_q && !done_q) begin
        target_pending_q <= 1'b1;
        target_slot_q <= 6'd0;
      end
      if (target_fire_w)
        target_pending_q <= 1'b0;
      if (output_fire_w && key_last_w && target_slot_q != 6'd63) begin
        target_slot_q <= target_slot_q + 1'b1;
        target_pending_q <= 1'b1;
      end
    end
  end"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    top_name, architecture, producers, kv_head = _validate(json.loads(json.dumps(config)))
    source_path = ONE_BUFFER_SOURCE if architecture == "one_buffer_serial" else PINGPONG_SOURCE
    source = source_path.read_text(encoding="utf-8").rstrip()
    harness = _common(
        top_name=top_name,
        producers=producers,
        kv_head=kv_head,
        body=_one_buffer_body() if architecture == "one_buffer_serial" else _pingpong_body(),
    )
    generated_rtl = source + "\n\n" + harness + "\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(generated_rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_beats = 8192 if architecture == "one_buffer_serial" else 4096
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_kv_key_ingress_ppa_harness.py",
        "top_name": top_name,
        "semantic_profile": "attention_score32_exact_kv_key_ingress_logic_ppa_activity_v1",
        "architecture": architecture,
        "producers": producers,
        "kv_head": kv_head,
        "canonical_ingress_flits": 4096,
        "output_beats": output_beats,
        "transpose_storage_bits": 16384 if architecture == "one_buffer_serial" else 32768,
        "full_k_stage_macro_area_included": False,
        "full_k_stage_macro_energy_included": False,
        "external_hbm_dram_included": False,
        "activity_checksum_is_equivalence_proof": False,
        "narrow_io_harness_overhead_included": True,
        "linked_proposal_id": PROPOSAL_ID,
        "source_rtl": str(source_path.relative_to(REPO_ROOT)),
        "source_sha256": hashlib.sha256((source + "\n").encode("utf-8")).hexdigest(),
        "generated_top_sha256": hashlib.sha256(generated_rtl.encode("utf-8")).hexdigest(),
        "top_pin_bits": 197,
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(_load(args.config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
