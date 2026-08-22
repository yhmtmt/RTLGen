#!/usr/bin/env python3
"""Generate a narrow-I/O physical harness for the shared-SRAM K round scheduler."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_shared_sram_k_round_scheduler_ppa_harness"
MANIFEST_NAME = "attention_shared_sram_k_round_scheduler_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1"
SOURCES = (
    REPO_ROOT / "npu/sim/rtl/attention_shared_sram_k_round_bank.sv",
    REPO_ROOT / "npu/sim/rtl/attention_shared_sram_k_round_scheduler.sv",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to an object: {path}")
    return payload


def _validate(config: dict[str, Any]) -> str:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    expected = {"banks": 17, "words_per_group": 128, "dimension_groups": 8, "dimensions_per_group": 16}
    for key, value in expected.items():
        if int(body.get(key, value)) != value:
            raise SystemExit(f"{key} must be {value} for the checked Llama7B geometry")
    return top_name


def _top(*, top_name: str) -> str:
    return f"""// Generated K-round scheduler physical/activity harness.
(* keep_hierarchy = 1 *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire start,
  input wire [31:0] seed,
  output wire done,
  output wire [31:0] activity_checksum,
  output wire [31:0] cycle_count,
  output wire [31:0] bank_request_count,
  output wire [31:0] bank_response_count,
  output wire [31:0] compute_beat_count,
  output wire protocol_error
);
  localparam integer ADDR_W = 16;
  localparam integer BANKS = 17;

  reg running_q;
  reg done_q;
  reg [31:0] seed_q;
  reg [31:0] cycle_q;
  reg [31:0] checksum_q;

  wire command_ready;
  wire command_valid = start && !running_q && !done_q;
  wire [BANKS-1:0] bank_req_valid;
  wire [BANKS-1:0] bank_req_ready = {{BANKS{{1'b1}}}};
  wire [(BANKS*ADDR_W)-1:0] bank_req_word_addr;
  wire [BANKS-1:0] bank_req_buffer;
  wire [(BANKS*3)-1:0] bank_req_group;
  wire [(BANKS*3)-1:0] bank_req_round;
  wire [(BANKS*7)-1:0] bank_req_word_slot;

  reg [BANKS-1:0] bank_rsp_valid_q;
  wire [BANKS-1:0] bank_rsp_ready;
  wire [(BANKS*1024)-1:0] bank_rsp_data;
  reg [BANKS-1:0] bank_rsp_buffer_q;
  reg [(BANKS*3)-1:0] bank_rsp_group_q;
  reg [(BANKS*3)-1:0] bank_rsp_round_q;
  reg [(BANKS*7)-1:0] bank_rsp_word_slot_q;
  reg [(BANKS*ADDR_W)-1:0] bank_rsp_word_addr_q;

  wire compute_valid;
  wire compute_ready = running_q && cycle_q[3:0] != 4'd11;
  wire [2:0] compute_group;
  wire [2:0] compute_round;
  wire [3:0] compute_dimension;
  wire compute_last;
  wire [BANKS-1:0] compute_word_valid;
  wire [(BANKS*64)-1:0] compute_k_beats;
  wire scheduler_done;
  wire [63:0] bank_request_count_w;
  wire [63:0] bank_response_count_w;
  wire [63:0] compute_beat_count_w;
  wire [63:0] unused_stall_0;
  wire [63:0] unused_stall_1;
  wire [63:0] unused_stall_2;

  function automatic [1023:0] build_word;
    input [ADDR_W-1:0] address;
    input [2:0] group_value;
    input [2:0] round_value;
    input [6:0] slot_value;
    input [4:0] bank_value;
    input [31:0] seed_value;
    reg [31:0] lane;
    begin
      // The stimulus source is deliberately small: it exercises every stored
      // bit without adding seventeen wide arithmetic generators to DUT PPA.
      lane = seed_value ^ {{16'd0, address}} ^
        {{21'd0, bank_value, group_value, round_value}} ^
        {{25'd0, slot_value}};
      build_word = {{16{{{{lane ^ 32'ha5a5_5a5a, lane}}}}}};
    end
  endfunction

  function automatic [31:0] fold_compute;
    input [(BANKS*64)-1:0] value;
    integer lane;
    integer rotate;
    reg [31:0] slice;
    begin
      fold_compute = 32'h6d2b_79f5;
      for (lane = 0; lane < BANKS*2; lane = lane + 1) begin
        slice = value[lane*32 +: 32];
        rotate = (lane % 31) + 1;
        fold_compute = fold_compute ^ (slice << rotate) ^
          (slice >> (32-rotate)) ^ (32'h45d9_f3b * (lane + 1));
      end
    end
  endfunction

  genvar bank_g;
  generate
    for (bank_g = 0; bank_g < BANKS; bank_g = bank_g + 1) begin : gen_rsp_data
      assign bank_rsp_data[bank_g*1024 +: 1024] = build_word(
        bank_rsp_word_addr_q[bank_g*ADDR_W +: ADDR_W],
        bank_rsp_group_q[bank_g*3 +: 3],
        bank_rsp_round_q[bank_g*3 +: 3],
        bank_rsp_word_slot_q[bank_g*7 +: 7],
        5'(bank_g), seed_q
      );
    end
  endgenerate

  attention_shared_sram_k_round_scheduler #(
    .ADDR_W(ADDR_W), .BANKS(BANKS), .WORDS_PER_GROUP(128),
    .DIM_GROUPS(8), .DIMS_PER_GROUP(16)
  ) scheduler (
    .clk(clk), .rst_n(rst_n),
    .command_valid(command_valid), .command_ready(command_ready),
    .command_base_word_addr(ADDR_W'(16'h0100)),
    .bank_req_valid(bank_req_valid), .bank_req_ready(bank_req_ready),
    .bank_req_word_addr(bank_req_word_addr),
    .bank_req_buffer(bank_req_buffer), .bank_req_group(bank_req_group),
    .bank_req_round(bank_req_round), .bank_req_word_slot(bank_req_word_slot),
    .bank_rsp_valid(bank_rsp_valid_q), .bank_rsp_ready(bank_rsp_ready),
    .bank_rsp_data(bank_rsp_data), .bank_rsp_buffer(bank_rsp_buffer_q),
    .bank_rsp_group(bank_rsp_group_q), .bank_rsp_round(bank_rsp_round_q),
    .bank_rsp_word_slot(bank_rsp_word_slot_q),
    .compute_valid(compute_valid), .compute_ready(compute_ready),
    .compute_group(compute_group), .compute_round(compute_round),
    .compute_dimension(compute_dimension), .compute_last(compute_last),
    .compute_word_valid(compute_word_valid), .compute_k_beats(compute_k_beats),
    .done(scheduler_done), .protocol_error(protocol_error),
    .bank_request_count(bank_request_count_w),
    .bank_response_count(bank_response_count_w),
    .compute_beat_count(compute_beat_count_w),
    .bank_request_stall_count(unused_stall_0),
    .compute_output_stall_count(unused_stall_1),
    .compute_wait_for_window_count(unused_stall_2)
  );

  assign done = done_q;
  assign activity_checksum = checksum_q;
  assign cycle_count = cycle_q;
  assign bank_request_count = bank_request_count_w[31:0];
  assign bank_response_count = bank_response_count_w[31:0];
  assign compute_beat_count = compute_beat_count_w[31:0];

  integer bank_i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running_q <= 1'b0;
      done_q <= 1'b0;
      seed_q <= 32'd1;
      cycle_q <= 32'd0;
      checksum_q <= 32'd0;
      bank_rsp_valid_q <= {{BANKS{{1'b0}}}};
      bank_rsp_buffer_q <= {{BANKS{{1'b0}}}};
      bank_rsp_group_q <= {{(BANKS*3){{1'b0}}}};
      bank_rsp_round_q <= {{(BANKS*3){{1'b0}}}};
      bank_rsp_word_slot_q <= {{(BANKS*7){{1'b0}}}};
      bank_rsp_word_addr_q <= {{(BANKS*ADDR_W){{1'b0}}}};
    end else begin
      bank_rsp_valid_q <= bank_req_valid & bank_req_ready;
      for (bank_i = 0; bank_i < BANKS; bank_i = bank_i + 1) begin
        if (bank_req_valid[bank_i] && bank_req_ready[bank_i]) begin
          bank_rsp_buffer_q[bank_i] <= bank_req_buffer[bank_i];
          bank_rsp_group_q[bank_i*3 +: 3] <= bank_req_group[bank_i*3 +: 3];
          bank_rsp_round_q[bank_i*3 +: 3] <= bank_req_round[bank_i*3 +: 3];
          bank_rsp_word_slot_q[bank_i*7 +: 7] <= bank_req_word_slot[bank_i*7 +: 7];
          bank_rsp_word_addr_q[bank_i*ADDR_W +: ADDR_W] <=
            bank_req_word_addr[bank_i*ADDR_W +: ADDR_W];
        end
      end

      if (command_valid && command_ready) begin
        running_q <= 1'b1;
        seed_q <= seed == 0 ? 32'd1 : seed;
      end
      if (running_q)
        cycle_q <= cycle_q + 1'b1;
      if (compute_valid && compute_ready)
        checksum_q <= checksum_q ^ fold_compute(compute_k_beats) ^
          {{20'd0, compute_last, compute_word_valid[0],
            compute_group, compute_round, compute_dimension}};
      if (scheduler_done) begin
        running_q <= 1'b0;
        done_q <= 1'b1;
      end
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    top_name = _validate(json.loads(json.dumps(config)))
    source = "\n\n".join(path.read_text(encoding="utf-8").rstrip() for path in SOURCES) + "\n"
    rtl = source.rstrip() + "\n\n" + _top(top_name=top_name)
    generated_rtl = rtl + "\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(generated_rtl, encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_shared_sram_k_round_scheduler_ppa_harness.py",
        "top_name": top_name,
        "semantic_profile": "attention_shared_sram_k_round_scheduler_logic_ppa_activity_v1",
        "banks": 17,
        "words_per_group": 128,
        "dimension_groups": 8,
        "rounds_per_group": 8,
        "dimensions_per_group": 16,
        "requests_per_command": 1024,
        "compute_beats_per_command": 1024,
        "window_storage_bits": 34816,
        "compute_boundary_bits": 1088,
        "full_capacity_macro_area_included": False,
        "shared_sram_access_energy_included": False,
        "external_hbm_dram_included": False,
        "activity_checksum_is_equivalence_proof": False,
        "synthetic_response_profile": "metadata_lane_replicated_v1",
        "synthetic_response_generator_is_dut": False,
        "narrow_io_harness_overhead_included": True,
        "linked_proposal_id": PROPOSAL_ID,
        "source_rtl": [str(path.relative_to(REPO_ROOT)) for path in SOURCES],
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "generated_top_sha256": hashlib.sha256(generated_rtl.encode("utf-8")).hexdigest(),
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
