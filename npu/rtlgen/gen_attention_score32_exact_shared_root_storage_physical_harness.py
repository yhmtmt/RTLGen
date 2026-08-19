#!/usr/bin/env python3
"""Generate a narrow-I/O physical harness for exact shared-root packet SRAM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_KEY = "attention_score32_exact_shared_root_storage_physical_harness"
_GENERATOR = (
    "npu/rtlgen/"
    "gen_attention_score32_exact_shared_root_storage_physical_harness.py"
)
_SOURCE = (
    REPO_ROOT
    / "npu/sim/rtl/"
    "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv"
)
_MANIFEST = "attention_score32_exact_shared_root_storage_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_attention_score32_exact_shared_root_storage_macro_ppa_v1"
_PROPOSAL_PATH = f"docs/proposals/{_PROPOSAL_ID}/proposal.json"
_VALID_BANKS = (2, 4, 8, 15)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to an object: {path}")
    return payload


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate(config: dict[str, Any]) -> tuple[str, int]:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")
    physical_banks = int(body.get("physical_banks", 0))
    if physical_banks not in _VALID_BANKS:
        raise SystemExit(f"physical_banks must be one of {_VALID_BANKS}")
    return top_name, physical_banks


def _storage_modules() -> str:
    source = _SOURCE.read_text(encoding="utf-8")
    marker = "// Shared root receive adapter for the exact stats-once transport."
    prefix, separator, _remainder = source.partition(marker)
    if not separator or "shared_root_storage_fabric" not in prefix:
        raise RuntimeError(f"unable to isolate shared-root storage modules from {_SOURCE}")
    return prefix.rstrip()


def _top(*, top_name: str, physical_banks: int) -> str:
    return f"""// Generated narrow-I/O shared-root packet-storage physical harness.
(* keep_hierarchy = 1 *)
module {top_name} (
  input wire clk,
  input wire rst_n,
  input wire start,
  input wire [31:0] seed,
  output wire done,
  output wire [31:0] folded_result,
  output wire [31:0] cycle_count,
  output wire [31:0] write_count,
  output wire [31:0] read_request_count,
  output wire [31:0] read_response_count,
  output wire [31:0] protocol_error_count
);
  localparam integer SOURCE_COUNT = 15;
  localparam integer PHYSICAL_BANKS = {physical_banks};
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 4;
  localparam [1:0] S_IDLE = 2'd0;
  localparam [1:0] S_WRITE = 2'd1;
  localparam [1:0] S_READ = 2'd2;
  localparam [SOURCE_COUNT-1:0] ALL_SOURCES = {{SOURCE_COUNT{{1'b1}}}};

  reg [1:0] state_q;
  reg done_q;
  reg [31:0] seed_q;
  reg [3:0] source_q;
  reg [3:0] logical_addr_q;
  reg [SOURCE_COUNT-1:0] read_pending_q;
  reg [SOURCE_COUNT-1:0] response_seen_q;
  reg [31:0] folded_result_q;
  reg [31:0] cycle_count_q;
  reg [31:0] write_count_q;
  reg [31:0] read_request_count_q;
  reg [31:0] read_response_count_q;
  reg [31:0] protocol_error_count_q;

  reg [SOURCE_COUNT-1:0] write_valid_r;
  wire [SOURCE_COUNT-1:0] write_ready_w;
  reg [SOURCE_COUNT*ADDR_W-1:0] write_addr_r;
  reg [SOURCE_COUNT*DATA_W-1:0] write_data_r;
  reg [SOURCE_COUNT-1:0] read_req_valid_r;
  wire [SOURCE_COUNT-1:0] read_req_ready_w;
  reg [SOURCE_COUNT*ADDR_W-1:0] read_req_addr_r;
  wire [SOURCE_COUNT-1:0] read_rsp_valid_w;
  reg [SOURCE_COUNT-1:0] read_rsp_ready_r;
  wire [SOURCE_COUNT*ADDR_W-1:0] read_rsp_addr_w;
  wire [SOURCE_COUNT*DATA_W-1:0] read_rsp_data_w;
  wire storage_protocol_error_w;
  wire [SOURCE_COUNT-1:0] write_fire_w = write_valid_r & write_ready_w;
  wire [SOURCE_COUNT-1:0] read_request_fire_w =
    read_req_valid_r & read_req_ready_w;
  wire [SOURCE_COUNT-1:0] read_response_fire_w =
    read_rsp_valid_w & read_rsp_ready_r;

  integer source_i;
  integer lane_i;
  integer request_count_now;
  integer response_count_now;
  reg [31:0] response_fold_now;
  reg [31:0] lane_word_r;
  always @* begin
    write_valid_r = {{SOURCE_COUNT{{1'b0}}}};
    write_addr_r = {{SOURCE_COUNT*ADDR_W{{1'b0}}}};
    write_data_r = {{SOURCE_COUNT*DATA_W{{1'b0}}}};
    read_req_valid_r = {{SOURCE_COUNT{{1'b0}}}};
    read_req_addr_r = {{SOURCE_COUNT*ADDR_W{{1'b0}}}};
    read_rsp_ready_r = {{SOURCE_COUNT{{1'b0}}}};
    if (state_q == S_WRITE) begin
      write_valid_r[source_q] = 1'b1;
      write_addr_r[source_q*ADDR_W +: ADDR_W] = logical_addr_q;
      for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1) begin
        lane_word_r = seed_q ^ {{24'd0, source_q, logical_addr_q}} ^
          (32'h9e3779b9 * (lane_i + 1));
        write_data_r[source_q*DATA_W + lane_i*32 +: 32] = lane_word_r;
      end
    end
    if (state_q == S_READ) begin
      read_req_valid_r = read_pending_q;
      read_rsp_ready_r = ALL_SOURCES;
      for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1)
        read_req_addr_r[source_i*ADDR_W +: ADDR_W] = logical_addr_q;
    end

    request_count_now = 0;
    response_count_now = 0;
    response_fold_now = 32'd0;
    for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
      if (read_request_fire_w[source_i])
        request_count_now = request_count_now + 1;
      if (read_response_fire_w[source_i]) begin
        response_count_now = response_count_now + 1;
        for (lane_i = 0; lane_i < 8; lane_i = lane_i + 1)
          response_fold_now = response_fold_now ^
            read_rsp_data_w[source_i*DATA_W + lane_i*32 +: 32];
      end
    end
  end

  local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric #(
    .DATA_W(DATA_W),
    .SOURCE_COUNT(SOURCE_COUNT),
    .PHYSICAL_BANKS(PHYSICAL_BANKS),
    .ADDR_W(ADDR_W),
    .USE_FAKERAM(1)
  ) storage (
    .clk(clk), .rst_n(rst_n),
    .write_valid(write_valid_r), .write_ready(write_ready_w),
    .write_addr(write_addr_r), .write_data(write_data_r),
    .read_req_valid(read_req_valid_r), .read_req_ready(read_req_ready_w),
    .read_req_addr(read_req_addr_r), .read_rsp_valid(read_rsp_valid_w),
    .read_rsp_ready(read_rsp_ready_r), .read_rsp_addr(read_rsp_addr_w),
    .read_rsp_data(read_rsp_data_w), .protocol_error(storage_protocol_error_w)
  );

  assign done = done_q;
  assign folded_result = folded_result_q;
  assign cycle_count = cycle_count_q;
  assign write_count = write_count_q;
  assign read_request_count = read_request_count_q;
  assign read_response_count = read_response_count_q;
  assign protocol_error_count = protocol_error_count_q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= S_IDLE;
      done_q <= 1'b0;
      seed_q <= 32'd0;
      source_q <= 4'd0;
      logical_addr_q <= 4'd0;
      read_pending_q <= {{SOURCE_COUNT{{1'b0}}}};
      response_seen_q <= {{SOURCE_COUNT{{1'b0}}}};
      folded_result_q <= 32'd0;
      cycle_count_q <= 32'd0;
      write_count_q <= 32'd0;
      read_request_count_q <= 32'd0;
      read_response_count_q <= 32'd0;
      protocol_error_count_q <= 32'd0;
    end else begin
      if (state_q != S_IDLE)
        cycle_count_q <= cycle_count_q + 1'b1;
      if (storage_protocol_error_w)
        protocol_error_count_q <= protocol_error_count_q + 1'b1;
      if (request_count_now != 0)
        read_request_count_q <= read_request_count_q + request_count_now;
      if (response_count_now != 0) begin
        read_response_count_q <= read_response_count_q + response_count_now;
        folded_result_q <= folded_result_q ^ response_fold_now;
      end

      case (state_q)
        S_IDLE: begin
          if (start && !done_q) begin
            state_q <= S_WRITE;
            seed_q <= seed == 0 ? 32'h1 : seed;
            source_q <= 4'd0;
            logical_addr_q <= 4'd0;
          end
        end
        S_WRITE: begin
          if (write_fire_w[source_q]) begin
            write_count_q <= write_count_q + 1'b1;
            if (logical_addr_q == 4'd15) begin
              logical_addr_q <= 4'd0;
              if (source_q == 4'd14) begin
                state_q <= S_READ;
                read_pending_q <= ALL_SOURCES;
                response_seen_q <= {{SOURCE_COUNT{{1'b0}}}};
              end else begin
                source_q <= source_q + 1'b1;
              end
            end else begin
              logical_addr_q <= logical_addr_q + 1'b1;
            end
          end
        end
        S_READ: begin
          read_pending_q <= read_pending_q & ~read_request_fire_w;
          response_seen_q <= response_seen_q | read_response_fire_w;
          if (((read_pending_q & ~read_request_fire_w) == 0) &&
              ((response_seen_q | read_response_fire_w) == ALL_SOURCES)) begin
            if (logical_addr_q == 4'd15) begin
              state_q <= S_IDLE;
              done_q <= 1'b1;
            end else begin
              logical_addr_q <= logical_addr_q + 1'b1;
              read_pending_q <= ALL_SOURCES;
              response_seen_q <= {{SOURCE_COUNT{{1'b0}}}};
            end
          end
        end
        default: state_q <= S_IDLE;
      endcase
    end
  end
endmodule
"""


def generate(config: dict[str, Any], out_dir: Path) -> None:
    top_name, physical_banks = _validate(json.loads(json.dumps(config)))
    storage_rtl = _storage_modules()
    top_rtl = _top(top_name=top_name, physical_banks=physical_banks)
    rtl = storage_rtl + "\n\n" + top_rtl
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "top.v").write_text(rtl + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    macro_count = {
        2: 32,
        4: 32,
        8: 64,
        15: 120,
    }[physical_banks]
    manifest = {
        "version": 1,
        "generator": _GENERATOR,
        "top_name": top_name,
        "semantic_profile": "score32_exact_shared_root_storage_macro_physical_v1",
        "physical_banks": physical_banks,
        "logical_sources": 15,
        "logical_words": 240,
        "word_bits": 256,
        "macro_type": "fakeram45_64x32",
        "macro_count": macro_count,
        "macro_area_um2": macro_count * 20.14 * 61.6,
        "top_pin_bits": 228,
        "traffic": {
            "writes": 240,
            "read_requests": 240,
            "read_responses": 240,
            "parallel_read_sources": 15,
            "observable_fold": True,
        },
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": _PROPOSAL_PATH,
        "source_rtl": str(_SOURCE.relative_to(REPO_ROOT)),
        "generated_top_sha256": _sha256_text(rtl),
    }
    (out_dir / _MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    macro_manifest = {
        "version": "0.1",
        "design_id": top_name,
        "module": top_name,
        "platform": "nangate45",
        "flow_variant": "score32_exact_shared_root_storage_macro_v1",
        "blackboxes": ["fakeram45_64x32"],
        "additional_lefs": [
            "/orfs/flow/platforms/nangate45/lef/fakeram45_64x32.lef"
        ],
        "additional_libs": [
            "/orfs/flow/platforms/nangate45/lib/fakeram45_64x32.lib"
        ],
        "additional_gds": [],
        "blackbox_verilog": ["npu/rtl/fakeram45_64x32_blackbox.v"],
        "source": {"mode": "generated_physical_harness", "generator": _GENERATOR},
        "manifest_params": {
            "physical_banks": physical_banks,
            "logical_sources": 15,
            "macro_count": macro_count,
            "macros_per_256_bit_row": 8,
        },
    }
    (out_dir / "macro_manifest.json").write_text(
        json.dumps(macro_manifest, indent=2, sort_keys=True) + "\n",
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
