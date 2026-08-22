#!/usr/bin/env python3
"""Generate a narrow-I/O activity harness for the shared-SRAM read adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_KEY = "attention_shared_sram_read_group_adapter_ppa_harness"
MANIFEST_NAME = "attention_shared_sram_read_group_adapter_ppa_harness_manifest.json"
PROPOSAL_ID = "prop_l1_attention_shared_sram_read_group_adapter_ppa_v1"
SOURCE = REPO_ROOT / "npu/sim/rtl/attention_shared_sram_read_group_adapter.sv"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to an object: {path}")
    return payload


def _validate(config: dict[str, Any]) -> tuple[str, int, int, int]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {CONFIG_KEY}")
    beat_width = int(body.get("beat_width", 0))
    group_slots = int(body.get("group_slots", 0))
    groups = int(body.get("groups", 64))
    if beat_width not in {256, 512}:
        raise SystemExit("beat_width must be 256 or 512")
    if group_slots not in {1, 2}:
        raise SystemExit("group_slots must be 1 or 2")
    if groups < 2:
        raise SystemExit("groups must be at least two")
    return top_name, beat_width, group_slots, groups


def _top(*, top_name: str, beat_width: int, group_slots: int, groups: int) -> str:
    return f"""// Generated shared-SRAM read-adapter physical/activity harness.
(* keep_hierarchy = 1 *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire start,
  input wire [31:0] seed,
  output wire done,
  output wire [31:0] folded_result,
  output wire [31:0] cycle_count,
  output wire [31:0] beat_request_count,
  output wire [31:0] macro_read_count,
  output wire [31:0] beat_response_count,
  output wire protocol_error,
  output wire access_reduction_proven
);
  localparam integer ADDR_W = 32;
  localparam integer BEAT_W = {beat_width};
  localparam integer GROUP_SLOTS = {group_slots};
  localparam integer GROUPS = {groups};
  localparam integer MACRO_W = 1024;
  localparam integer MACRO_BYTES = 128;
  localparam integer BEAT_BYTES = BEAT_W / 8;
  localparam integer SEGMENTS = MACRO_W / BEAT_W;
  localparam integer TOTAL_BEATS = GROUPS * SEGMENTS;
  localparam integer SLOT_W = (GROUP_SLOTS <= 1) ? 1 : $clog2(GROUP_SLOTS);

  reg running_q;
  reg done_q;
  reg [31:0] seed_q;
  reg [31:0] cycle_q;
  reg [31:0] issued_q;
  reg [31:0] received_q;
  reg [31:0] fold_q;

  wire req_valid = running_q && (issued_q < TOTAL_BEATS);
  wire req_ready;
  wire [ADDR_W-1:0] req_addr = 32'h0010_0000 + issued_q * BEAT_BYTES;
  wire rsp_valid;
  wire rsp_ready = running_q && (cycle_q[2:0] != 3'd5);
  (* keep = "true" *) wire [BEAT_W-1:0] rsp_data;
  wire [ADDR_W-1:0] rsp_addr;

  wire macro_req_valid;
  wire macro_req_ready = 1'b1;
  wire [ADDR_W-1:0] macro_req_addr;
  wire [SLOT_W-1:0] macro_req_slot;
  reg macro_rsp_valid_q;
  wire macro_rsp_ready;
  reg [ADDR_W-1:0] macro_rsp_addr_q;
  reg [SLOT_W-1:0] macro_rsp_slot_q;
  wire [63:0] beat_request_count_w;
  wire [63:0] macro_read_count_w;
  wire [63:0] beat_response_count_w;
  wire [63:0] unused_stalls_0;
  wire [63:0] unused_stalls_1;
  wire [63:0] unused_stalls_2;
  wire [63:0] unused_stalls_3;

  function automatic [1023:0] build_macro_word;
    input [31:0] address;
    input [31:0] seed_value;
    reg [31:0] lane;
    begin
      // Keep stimulus logic small; the retained DUT payload state, not the
      // synthetic macro response generator, is the physical target.
      lane = seed_value ^ address;
      build_macro_word = {{32{{lane}}}};
    end
  endfunction

  function automatic [31:0] fold_beat;
    input [BEAT_W-1:0] value;
    begin
      // rsp_data is kept in full; only endpoint lanes feed the narrow checksum.
      fold_beat = value[31:0] ^ value[BEAT_W-1 -: 32];
    end
  endfunction

  attention_shared_sram_read_group_adapter #(
    .ADDR_W(ADDR_W), .BEAT_W(BEAT_W), .GROUP_SLOTS(GROUP_SLOTS)
  ) adapter (
    .clk(clk), .rst_n(rst_n),
    .req_valid(req_valid), .req_ready(req_ready), .req_addr(req_addr),
    .rsp_valid(rsp_valid), .rsp_ready(rsp_ready), .rsp_data(rsp_data),
    .rsp_addr(rsp_addr),
    .macro_req_valid(macro_req_valid), .macro_req_ready(macro_req_ready),
    .macro_req_addr(macro_req_addr), .macro_req_slot(macro_req_slot),
    .macro_rsp_valid(macro_rsp_valid_q), .macro_rsp_ready(macro_rsp_ready),
    .macro_rsp_data(build_macro_word(macro_rsp_addr_q, seed_q)),
    .macro_rsp_addr(macro_rsp_addr_q), .macro_rsp_slot(macro_rsp_slot_q),
    .protocol_error(protocol_error),
    .beat_request_count(beat_request_count_w),
    .macro_read_count(macro_read_count_w),
    .beat_response_count(beat_response_count_w),
    .beat_request_stall_count(unused_stalls_0),
    .beat_response_stall_count(unused_stalls_1),
    .macro_request_stall_count(unused_stalls_2),
    .macro_response_stall_count(unused_stalls_3),
    .access_reduction_proven(access_reduction_proven)
  );

  assign done = done_q;
  assign folded_result = fold_q;
  assign cycle_count = cycle_q;
  assign beat_request_count = beat_request_count_w[31:0];
  assign macro_read_count = macro_read_count_w[31:0];
  assign beat_response_count = beat_response_count_w[31:0];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running_q <= 1'b0;
      done_q <= 1'b0;
      seed_q <= 32'd1;
      cycle_q <= 32'd0;
      issued_q <= 32'd0;
      received_q <= 32'd0;
      fold_q <= 32'd0;
      macro_rsp_valid_q <= 1'b0;
      macro_rsp_addr_q <= 32'd0;
      macro_rsp_slot_q <= {{SLOT_W{{1'b0}}}};
    end else begin
      if (start && !running_q && !done_q) begin
        running_q <= 1'b1;
        seed_q <= seed == 0 ? 32'd1 : seed;
      end
      if (running_q)
        cycle_q <= cycle_q + 1'b1;
      if (req_valid && req_ready)
        issued_q <= issued_q + 1'b1;

      if (macro_rsp_valid_q && macro_rsp_ready)
        macro_rsp_valid_q <= 1'b0;
      if (macro_req_valid && macro_req_ready) begin
        macro_rsp_valid_q <= 1'b1;
        macro_rsp_addr_q <= macro_req_addr;
        macro_rsp_slot_q <= macro_req_slot;
      end

      if (rsp_valid && rsp_ready) begin
        received_q <= received_q + 1'b1;
        fold_q <= fold_q ^ fold_beat(rsp_data) ^ rsp_addr;
        if (received_q + 1'b1 == TOTAL_BEATS) begin
          running_q <= 1'b0;
          done_q <= 1'b1;
        end
      end
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    top_name, beat_width, group_slots, groups = _validate(json.loads(json.dumps(config)))
    source = SOURCE.read_text(encoding="utf-8")
    rtl = source.rstrip() + "\n\n" + _top(
        top_name=top_name,
        beat_width=beat_width,
        group_slots=group_slots,
        groups=groups,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(rtl + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_shared_sram_read_group_adapter_ppa_harness.py",
        "top_name": top_name,
        "semantic_profile": "attention_shared_sram_read_group_adapter_logic_ppa_activity_v1",
        "beat_width": beat_width,
        "segments_per_macro_read": 1024 // beat_width,
        "group_slots": group_slots,
        "groups": groups,
        "shared_macro_width_bits": 1024,
        "buffer_payload_bits": 1024 * group_slots,
        "payload_reset_required": False,
        "full_capacity_macro_area_included": False,
        "synthetic_response_profile": "metadata_lane_replicated_v1",
        "synthetic_response_generator_is_dut": False,
        "narrow_io_harness_overhead_included": True,
        "response_bus_retention": "kept_full_bus_endpoint_lane_fold_v1",
        "linked_proposal_id": PROPOSAL_ID,
        "source_rtl": str(SOURCE.relative_to(REPO_ROOT)),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "generated_top_sha256": hashlib.sha256(rtl.encode("utf-8")).hexdigest(),
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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
