#!/usr/bin/env python3
"""Generate selected-domain narrow-IO physical diagnostics for the 464-bit CDC FIFO."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_decode_score_multivalue_service_temporal_cdc import (
    _PAYLOAD_BITS,
    _async_fifo,
)

JsonDict = dict[str, Any]
_CONFIG_KEY = "attention_exact_partial_async_fifo_physical_harness"
_MANIFEST = "attention_exact_partial_async_fifo_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_exact_partial_physical_calibration_v1"
_PROPOSAL_PATH = f"docs/proposals/{_PROPOSAL_ID}/proposal.json"
_TOP_PIN_BITS = 292


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"config must decode to a JSON object: {path}")
    return payload


def _validate(config: JsonDict) -> JsonDict:
    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config requires top_name and {_CONFIG_KEY}")
    domain = str(body.get("timed_domain", "")).strip().lower()
    if domain not in {"source", "destination"}:
        raise SystemExit("timed_domain must be source or destination")
    if int(body.get("depth", 4)) != 4:
        raise SystemExit("physical calibration FIFO depth must remain 4")
    return {"top_name": top_name, "timed_domain": domain}


def _top(*, top_name: str, fifo_top: str, timed_domain: str) -> str:
    source_clock = "clk" if timed_domain == "source" else "helper_clk_q"
    destination_clock = "helper_clk_q" if timed_domain == "source" else "clk"
    return f"""// Selected-domain CDC physical diagnostic; not a common-clock wrapper.
(* keep_hierarchy = 1 *)
module {top_name} (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [31:0] seed,
    output wire        done,
    output wire [31:0] folded_result,
    output wire [31:0] accepted_count,
    output wire [31:0] emitted_count,
    output wire [31:0] full_cycles,
    output wire [31:0] empty_cycles,
    output wire [31:0] source_occupancy,
    output wire [31:0] destination_occupancy,
    output wire [31:0] protocol_error_count
);
  localparam integer TRANSFERS = 32;
  localparam integer PAYLOAD_BITS = {_PAYLOAD_BITS};

  reg helper_clk_q;
  reg source_running_q;
  reg destination_running_q;
  reg source_done_q;
  reg destination_done_q;
  reg [5:0] source_index_q;
  reg [31:0] source_lfsr_q;
  reg [31:0] destination_fold_q;
  reg [31:0] destination_cycle_q;
  reg [31:0] protocol_error_count_q;

  wire source_clk_w = {source_clock};
  wire destination_clk_w = {destination_clock};
  wire wr_valid_w = source_running_q && source_index_q < TRANSFERS;
  wire wr_ready_w;
  wire wr_fire_w = wr_valid_w && wr_ready_w;
  wire [PAYLOAD_BITS-1:0] wr_data_w = {{
      16'h5100,
      16'h6200,
      14'd0,
      15'd2,
      5'd1,
      source_lfsr_q,
      {{1'b0, source_lfsr_q}},
      source_index_q[3:0],
      source_index_q[3:0] == 4'd15,
      {{10{{source_lfsr_q}}}},
      source_lfsr_q[7:0]
  }};
  wire [31:0] source_lfsr_next_w = {{
      source_lfsr_q[30:0],
      source_lfsr_q[31] ^ source_lfsr_q[21]
          ^ source_lfsr_q[1] ^ source_lfsr_q[0]
  }};
  wire rd_valid_w;
  wire rd_ready_w =
      destination_running_q && destination_cycle_q[2:0] != 3'b000;
  wire rd_fire_w = rd_valid_w && rd_ready_w;
  wire [PAYLOAD_BITS-1:0] rd_data_w;
  wire overflow_error_w;
  wire underflow_error_w;
  wire wr_protocol_error_w;
  wire rd_protocol_error_w;
  wire [31:0] emitted_count_w;
  wire [31:0] rd_fold_w =
      rd_data_w[31:0] ^ rd_data_w[63:32] ^ rd_data_w[95:64]
      ^ rd_data_w[127:96] ^ rd_data_w[159:128]
      ^ rd_data_w[191:160] ^ rd_data_w[223:192]
      ^ rd_data_w[255:224] ^ rd_data_w[287:256]
      ^ rd_data_w[319:288] ^ rd_data_w[351:320]
      ^ rd_data_w[383:352] ^ rd_data_w[415:384]
      ^ rd_data_w[447:416] ^ {{16'd0, rd_data_w[463:448]}};

  assign done = destination_done_q;
  assign folded_result = destination_fold_q;
  assign protocol_error_count = protocol_error_count_q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      helper_clk_q <= 1'b0;
    else
      helper_clk_q <= ~helper_clk_q;
  end

  always @(posedge source_clk_w or negedge rst_n) begin
    if (!rst_n) begin
      source_running_q <= 1'b0;
      source_done_q <= 1'b0;
      source_index_q <= 6'd0;
      source_lfsr_q <= 32'h1;
    end else begin
      if (start && !source_running_q && !source_done_q) begin
        source_running_q <= 1'b1;
        source_lfsr_q <= seed == 0 ? 32'h1 : seed;
      end
      if (wr_fire_w) begin
        source_index_q <= source_index_q + 1'b1;
        source_lfsr_q <= source_lfsr_next_w;
        if (source_index_q == TRANSFERS - 1) begin
          source_running_q <= 1'b0;
          source_done_q <= 1'b1;
        end
      end
    end
  end

  always @(posedge destination_clk_w or negedge rst_n) begin
    if (!rst_n) begin
      destination_running_q <= 1'b0;
      destination_done_q <= 1'b0;
      destination_fold_q <= 32'd0;
      destination_cycle_q <= 32'd0;
      protocol_error_count_q <= 32'd0;
    end else begin
      if (start && !destination_running_q && !destination_done_q)
        destination_running_q <= 1'b1;
      if (destination_running_q)
        destination_cycle_q <= destination_cycle_q + 1'b1;
      if (rd_fire_w) begin
        destination_fold_q <= destination_fold_q ^ rd_fold_w;
        if (emitted_count_w == TRANSFERS - 1) begin
          destination_running_q <= 1'b0;
          destination_done_q <= 1'b1;
        end
      end
      if (overflow_error_w || underflow_error_w
          || wr_protocol_error_w || rd_protocol_error_w)
        protocol_error_count_q <= protocol_error_count_q + 1'b1;
    end
  end

  {fifo_top} u_async_fifo (
      .wr_clk(source_clk_w),
      .wr_rst_n(rst_n),
      .wr_valid(wr_valid_w),
      .wr_ready(wr_ready_w),
      .wr_data(wr_data_w),
      .rd_clk(destination_clk_w),
      .rd_rst_n(rst_n),
      .rd_valid(rd_valid_w),
      .rd_ready(rd_ready_w),
      .rd_data(rd_data_w),
      .wr_occupancy(source_occupancy),
      .rd_occupancy(destination_occupancy),
      .accepted_count(accepted_count),
      .emitted_count(emitted_count_w),
      .full_cycles(full_cycles),
      .empty_cycles(empty_cycles),
      .overflow_error(overflow_error_w),
      .underflow_error(underflow_error_w),
      .wr_protocol_error(wr_protocol_error_w),
      .rd_protocol_error(rd_protocol_error_w)
  );
  assign emitted_count = emitted_count_w;
endmodule
"""


def generate(config: JsonDict, out_dir: Path) -> None:
    params = _validate(json.loads(json.dumps(config)))
    top_name = str(params["top_name"])
    fifo_top = f"{top_name}__async_fifo"
    out_dir.mkdir(parents=True, exist_ok=True)
    rtl = "\n\n".join(
        (
            _async_fifo(module_name=fifo_top, depth=4),
            _top(
                top_name=top_name,
                fifo_top=fifo_top,
                timed_domain=str(params["timed_domain"]),
            ),
        )
    )
    (out_dir / "top.v").write_text(rtl + "\n", encoding="utf-8")
    (out_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": 1,
        "generator": (
            "npu/rtlgen/gen_attention_exact_partial_async_fifo_physical_harness.py"
        ),
        "top_name": top_name,
        "semantic_profile": "exact_partial_async_fifo_selected_domain_physical_diagnostic_v1",
        "payload_bits": _PAYLOAD_BITS,
        "depth": 4,
        "timed_domain": str(params["timed_domain"]),
        "timed_clock_port": "clk",
        "inactive_domain_clock": "protocol_safe_divide_by_two_generated_clock",
        "external_interface": "clk_reset_start_seed_done_folded_result_and_counters_only",
        "top_pin_bits": _TOP_PIN_BITS,
        "macro_count": 0,
        "physical_timing_claim": f"{params['timed_domain']}_domain_diagnostic_only",
        "whole_dual_clock_common_delay_claim": False,
        "cross_domain_paths_are_signoff_timing": False,
        "cdc_correctness_evidence": (
            "separate non_harmonic_functional_probe_not_this_openroad_harness"
        ),
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": _PROPOSAL_PATH,
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
        "flow_variant": "exact_partial_async_fifo_selected_domain_diagnostic_v1",
        "blackboxes": [],
        "additional_lefs": [],
        "additional_libs": [],
        "additional_gds": [],
        "blackbox_verilog": [],
        "source": {
            "mode": "generated_physical_harness",
            "generator": (
                "npu/rtlgen/"
                "gen_attention_exact_partial_async_fifo_physical_harness.py"
            ),
        },
        "manifest_params": {"macro_count": 0},
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
