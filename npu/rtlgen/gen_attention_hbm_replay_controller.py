#!/usr/bin/env python3
"""Generate a bounded score32 HBM replay-controller RTL measurement stub.

This block models only control timing for replay scheduling and does not
implement a full HBM datapath.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_int(cfg: dict[str, Any], key: str, default: int) -> int:
    return int(cfg.get(key, default))


def _clog2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def _validate(cfg: dict[str, Any]) -> dict[str, int | str]:
    top_name = str(cfg.get("top_name", "")).strip()
    if not top_name:
        raise SystemExit("config must contain non-empty top_name")

    ctrl = cfg.get("attention_hbm_replay_controller")
    if not isinstance(ctrl, dict):
        raise SystemExit("config must contain attention_hbm_replay_controller object")

    channel_count = _as_int(ctrl, "channel_count", 4)
    burst_bytes = _as_int(ctrl, "burst_bytes", 64)
    row_span_bursts = _as_int(ctrl, "row_span_bursts", 4)
    row_miss_penalty_cycles = _as_int(ctrl, "row_miss_penalty_cycles", 8)
    request_overhead_cycles = _as_int(ctrl, "request_overhead_cycles", 2)
    scheduler_gap_cycles = _as_int(ctrl, "scheduler_gap_cycles", 1)
    outstanding = _as_int(ctrl, "outstanding", 4)
    address_bits = _as_int(ctrl, "address_bits", 32)
    row_id_bits = _as_int(ctrl, "row_id_bits", 16)

    if channel_count < 1 or channel_count > 64:
        raise SystemExit("attention_hbm_replay_controller.channel_count must be in [1, 64]")
    if not _is_power_of_two(channel_count):
        raise SystemExit("attention_hbm_replay_controller.channel_count must be a power of two")
    if burst_bytes < 1 or burst_bytes > 4096:
        raise SystemExit("attention_hbm_replay_controller.burst_bytes must be in [1, 4096]")
    if row_span_bursts < 1 or row_span_bursts > 1024:
        raise SystemExit("attention_hbm_replay_controller.row_span_bursts must be in [1, 1024]")
    if not _is_power_of_two(row_span_bursts):
        raise SystemExit("attention_hbm_replay_controller.row_span_bursts must be a power of two")
    if row_miss_penalty_cycles < 0 or row_miss_penalty_cycles > 1024:
        raise SystemExit("attention_hbm_replay_controller.row_miss_penalty_cycles must be in [0, 1024]")
    if request_overhead_cycles < 0 or request_overhead_cycles > 1024:
        raise SystemExit("attention_hbm_replay_controller.request_overhead_cycles must be in [0, 1024]")
    if scheduler_gap_cycles < 0 or scheduler_gap_cycles > 1024:
        raise SystemExit("attention_hbm_replay_controller.scheduler_gap_cycles must be in [0, 1024]")
    if outstanding < 1 or outstanding > 128:
        raise SystemExit("attention_hbm_replay_controller.outstanding must be in [1, 128]")
    if address_bits < 1 or address_bits > 64:
        raise SystemExit("attention_hbm_replay_controller.address_bits must be in [1, 64]")
    if row_id_bits < 1 or row_id_bits > address_bits:
        raise SystemExit("attention_hbm_replay_controller.row_id_bits must be in [1, address_bits]")

    return {
        "top_name": top_name,
        "channel_count": channel_count,
        "burst_bytes": burst_bytes,
        "row_span_bursts": row_span_bursts,
        "row_miss_penalty_cycles": row_miss_penalty_cycles,
        "request_overhead_cycles": request_overhead_cycles,
        "scheduler_gap_cycles": scheduler_gap_cycles,
        "outstanding": outstanding,
        "address_bits": address_bits,
        "row_id_bits": row_id_bits,
    }


def _generate(params: dict[str, int | str]) -> str:
    top = str(params["top_name"])
    channel_count = int(params["channel_count"])
    burst_bytes = int(params["burst_bytes"])
    row_span_bursts = int(params["row_span_bursts"])
    row_miss_penalty_cycles = int(params["row_miss_penalty_cycles"])
    request_overhead_cycles = int(params["request_overhead_cycles"])
    scheduler_gap_cycles = int(params["scheduler_gap_cycles"])
    outstanding = int(params["outstanding"])
    address_bits = int(params["address_bits"])
    row_id_bits = int(params["row_id_bits"])

    channel_bits = _clog2(channel_count)
    row_span_shift = int(math.log2(row_span_bursts))
    row_window_expr = (
        "request_addr[ROW_ID_BITS-1:0]"
        if row_span_shift == 0
        else "{{"
        + str(row_span_shift)
        + "{1'b0}}, request_addr[ROW_ID_BITS-1:"
        + str(row_span_shift)
        + "]}"
    )
    outstanding_bits = _clog2(outstanding + 1)
    completion_bits = _clog2(channel_count + 1)
    queue_depth = 4
    queue_ptr_bits = _clog2(queue_depth)
    queue_count_bits = _clog2(queue_depth + 1)
    service_bits = _clog2(burst_bytes + request_overhead_cycles + scheduler_gap_cycles + row_miss_penalty_cycles + 1)

    template = """// Generated by npu/rtlgen/gen_attention_hbm_replay_controller.py
module __TOP__ (
    input  wire                          clk,
    input  wire                          rst_n,
    input  wire                          request_valid,
    output wire                          request_ready,
    input  wire [__ADDRESS_BITS__ - 1:0] request_addr,
    input  wire                          issue_ready,
    output wire                          issue_valid,
    output wire [__CHANNEL_BITS__ - 1:0] issue_channel,
    output wire [__ADDRESS_BITS__ - 1:0] issue_addr,
    output wire [__SERVICE_BITS__ - 1:0] issue_burst_countdown,
    output wire                          issue_row_miss,
    output reg                           response_valid,
    output reg  [__ADDRESS_BITS__ - 1:0] response_addr,
    output reg  [__CHANNEL_BITS__ - 1:0] response_channel,
    output reg                           response_row_miss,
    output wire [__OUTSTANDING_BITS__ - 1:0] outstanding_count,
    output wire [__OCCUPANCY_BITS__ - 1:0] channel_queue_occupancy,
    output wire [__SERVICE_STATUS_BITS__ - 1:0] channel_service_countdown
);
  localparam integer CHANNEL_COUNT = __CHANNEL_COUNT__;
  localparam integer ROW_SPAN_BURSTS = __ROW_SPAN_BURSTS__;
  localparam integer BURST_BYTES = __BURST_BYTES__;
  localparam integer ROW_MISS_PENALTY_CYCLES = __ROW_MISS_PENALTY_CYCLES__;
  localparam integer REQUEST_OVERHEAD_CYCLES = __REQUEST_OVERHEAD_CYCLES__;
  localparam integer SCHEDULER_GAP_CYCLES = __SCHEDULER_GAP_CYCLES__;
  localparam integer OUTSTANDING_MAX = __OUTSTANDING__;
  localparam integer ADDRESS_BITS = __ADDRESS_BITS__;
  localparam integer ROW_ID_BITS = __ROW_ID_BITS__;
  localparam integer CHANNEL_BITS = __CHANNEL_BITS__;
  localparam integer OUTSTANDING_BITS = __OUTSTANDING_BITS__;
  localparam integer COMPLETION_BITS = __COMPLETION_BITS__;
  localparam integer QUEUE_DEPTH = __QUEUE_DEPTH__;
  localparam integer QUEUE_PTR_BITS = __QUEUE_PTR_BITS__;
  localparam integer QUEUE_COUNT_BITS = __QUEUE_COUNT_BITS__;
  localparam integer SERVICE_BITS = __SERVICE_BITS__;
  localparam integer BASE_BURST_CYCLES = BURST_BYTES + REQUEST_OVERHEAD_CYCLES + SCHEDULER_GAP_CYCLES;
  localparam integer PTR_LAST = QUEUE_DEPTH - 1;

  reg [ADDRESS_BITS-1:0] q_addr [0:CHANNEL_COUNT-1][0:QUEUE_DEPTH-1];
  reg [ROW_ID_BITS-1:0] q_row_window [0:CHANNEL_COUNT-1][0:QUEUE_DEPTH-1];
  reg [QUEUE_PTR_BITS-1:0] q_head [0:CHANNEL_COUNT-1];
  reg [QUEUE_PTR_BITS-1:0] q_tail [0:CHANNEL_COUNT-1];
  reg [QUEUE_COUNT_BITS-1:0] q_count [0:CHANNEL_COUNT-1];

  reg [ROW_ID_BITS-1:0] last_row_window [0:CHANNEL_COUNT-1];
  reg last_row_valid [0:CHANNEL_COUNT-1];

  reg service_active [0:CHANNEL_COUNT-1];
  reg [SERVICE_BITS-1:0] service_countdown [0:CHANNEL_COUNT-1];
  reg [ADDRESS_BITS-1:0] service_addr [0:CHANNEL_COUNT-1];
  reg [ROW_ID_BITS-1:0] service_row_window [0:CHANNEL_COUNT-1];
  reg service_row_miss [0:CHANNEL_COUNT-1];

  reg [CHANNEL_BITS-1:0] rr_ptr;
  reg [OUTSTANDING_BITS-1:0] outstanding_count_r;

  reg [CHANNEL_BITS-1:0] selected_channel_r;
  reg selected_valid_r;
  reg selected_row_miss_r;
  reg [SERVICE_BITS-1:0] selected_burst_cycles_r;
  reg [ADDRESS_BITS-1:0] selected_addr_r;

  wire [ROW_ID_BITS-1:0] request_row_window = __REQUEST_ROW_WINDOW_EXPR__;
  wire [CHANNEL_BITS-1:0] request_channel = request_addr[CHANNEL_BITS-1:0];

  reg [COMPLETION_BITS-1:0] completion_count_r;
  reg completion_found_r;
  reg [CHANNEL_BITS-1:0] completion_channel_r;
  reg [ADDRESS_BITS-1:0] completion_addr_r;
  reg completion_row_miss_r;

  wire request_fire = request_valid && request_ready;
  wire issue_fire = issue_valid && issue_ready;
  wire pop_selected_channel = issue_fire && selected_valid_r;
  wire pop_from_request_channel = pop_selected_channel && (request_channel == selected_channel_r);

  integer scan;
  integer candidate;
  integer i;
  integer out_base;
  integer out_next;

  assign request_ready = (q_count[request_channel] < QUEUE_DEPTH) ||
    (pop_from_request_channel && q_count[request_channel] == QUEUE_DEPTH);
  assign issue_valid = selected_valid_r && (outstanding_count_r < OUTSTANDING_MAX);
  assign issue_channel = selected_channel_r;
  assign issue_addr = selected_addr_r;
  assign issue_burst_countdown = selected_burst_cycles_r;
  assign issue_row_miss = selected_row_miss_r;
  assign outstanding_count = outstanding_count_r;

  genvar g;
  generate
    for (g = 0; g < CHANNEL_COUNT; g = g + 1) begin : GEN_STATUS
      assign channel_queue_occupancy[(g + 1) * QUEUE_COUNT_BITS - 1 -: QUEUE_COUNT_BITS] = q_count[g];
      assign channel_service_countdown[(g + 1) * SERVICE_BITS - 1 -: SERVICE_BITS] = service_countdown[g];
    end
  endgenerate

  always @* begin
    selected_channel_r = {CHANNEL_BITS{1'b0}};
    selected_valid_r = 1'b0;
    selected_row_miss_r = 1'b0;
    selected_addr_r = {ADDRESS_BITS{1'b0}};
    selected_burst_cycles_r = {SERVICE_BITS{1'b0}};

    completion_count_r = {COMPLETION_BITS{1'b0}};
    completion_found_r = 1'b0;
    completion_channel_r = {CHANNEL_BITS{1'b0}};
    completion_addr_r = {ADDRESS_BITS{1'b0}};
    completion_row_miss_r = 1'b0;

    for (scan = 0; scan < CHANNEL_COUNT; scan = scan + 1) begin
      candidate = rr_ptr + scan;
      if (candidate >= CHANNEL_COUNT) begin
        candidate = candidate - CHANNEL_COUNT;
      end

      if (!selected_valid_r && !service_active[candidate] && (q_count[candidate] != 0)) begin
        selected_channel_r = candidate[CHANNEL_BITS-1:0];
        selected_valid_r = 1'b1;
        selected_addr_r = q_addr[candidate][q_head[candidate]];
        selected_row_miss_r =
          !last_row_valid[candidate] ||
          (q_row_window[candidate][q_head[candidate]] != last_row_window[candidate]);
        selected_burst_cycles_r = BASE_BURST_CYCLES;
        if (selected_row_miss_r) begin
          selected_burst_cycles_r = BASE_BURST_CYCLES + ROW_MISS_PENALTY_CYCLES;
        end
      end

      if (service_active[scan] && (service_countdown[scan] == 1'b1)) begin
        completion_count_r = completion_count_r + 1'b1;
        completion_found_r = 1'b1;
        completion_channel_r = scan[CHANNEL_BITS-1:0];
        completion_addr_r = service_addr[scan];
        completion_row_miss_r = service_row_miss[scan];
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < CHANNEL_COUNT; i = i + 1) begin
        q_head[i] <= {QUEUE_PTR_BITS{1'b0}};
        q_tail[i] <= {QUEUE_PTR_BITS{1'b0}};
        q_count[i] <= {QUEUE_COUNT_BITS{1'b0}};
        last_row_window[i] <= {ROW_ID_BITS{1'b0}};
        last_row_valid[i] <= 1'b0;
        service_active[i] <= 1'b0;
        service_countdown[i] <= {SERVICE_BITS{1'b0}};
        service_addr[i] <= {ADDRESS_BITS{1'b0}};
        service_row_window[i] <= {ROW_ID_BITS{1'b0}};
        service_row_miss[i] <= 1'b0;
      end
      rr_ptr <= {CHANNEL_BITS{1'b0}};
      outstanding_count_r <= {OUTSTANDING_BITS{1'b0}};
      response_valid <= 1'b0;
      response_addr <= {ADDRESS_BITS{1'b0}};
      response_channel <= {CHANNEL_BITS{1'b0}};
      response_row_miss <= 1'b0;
    end else begin
      response_valid <= 1'b0;

      for (i = 0; i < CHANNEL_COUNT; i = i + 1) begin
        if (service_active[i]) begin
          if (service_countdown[i] > 0) begin
            service_countdown[i] <= service_countdown[i] - 1'b1;
          end
          if (service_countdown[i] == 1'b1) begin
            service_active[i] <= 1'b0;
            service_countdown[i] <= {SERVICE_BITS{1'b0}};
            last_row_window[i] <= service_row_window[i];
            last_row_valid[i] <= 1'b1;
          end
        end

        if (request_fire && request_channel == i[CHANNEL_BITS-1:0]) begin
          q_addr[i][q_tail[i]] <= request_addr;
          q_row_window[i][q_tail[i]] <= request_row_window;
          if (q_tail[i] == PTR_LAST[QUEUE_PTR_BITS-1:0]) begin
            q_tail[i] <= {QUEUE_PTR_BITS{1'b0}};
          end else begin
            q_tail[i] <= q_tail[i] + 1'b1;
          end
        end

        if (pop_selected_channel && selected_channel_r == i[CHANNEL_BITS-1:0]) begin
          if (q_head[i] == PTR_LAST[QUEUE_PTR_BITS-1:0]) begin
            q_head[i] <= {QUEUE_PTR_BITS{1'b0}};
          end else begin
            q_head[i] <= q_head[i] + 1'b1;
          end
        end

        case ({request_fire && (request_channel == i[CHANNEL_BITS-1:0]), pop_selected_channel && (selected_channel_r == i[CHANNEL_BITS-1:0])})
          2'b10: q_count[i] <= q_count[i] + 1'b1;
          2'b01: q_count[i] <= q_count[i] - 1'b1;
          default: q_count[i] <= q_count[i];
        endcase
      end

      if (completion_found_r) begin
        response_valid <= 1'b1;
        response_addr <= completion_addr_r;
        response_channel <= completion_channel_r;
        response_row_miss <= completion_row_miss_r;
      end

      out_base = outstanding_count_r + (issue_fire ? 1 : 0);
      if (completion_count_r > out_base[COMPLETION_BITS-1:0]) begin
        out_next = 0;
      end else begin
        out_next = out_base - completion_count_r;
      end
      outstanding_count_r <= out_next[OUTSTANDING_BITS-1:0];

      if (issue_fire && selected_valid_r) begin
        service_active[selected_channel_r] <= 1'b1;
        service_addr[selected_channel_r] <= selected_addr_r;
        service_countdown[selected_channel_r] <= selected_burst_cycles_r;
        service_row_window[selected_channel_r] <= q_row_window[selected_channel_r][q_head[selected_channel_r]];
        service_row_miss[selected_channel_r] <= selected_row_miss_r;
        if (selected_channel_r == CHANNEL_COUNT - 1) begin
          rr_ptr <= {CHANNEL_BITS{1'b0}};
        end else begin
          rr_ptr <= selected_channel_r + 1'b1;
        end
      end
    end
  end
endmodule
"""

    return (
        template
        .replace("__TOP__", top)
        .replace("__CHANNEL_COUNT__", str(channel_count))
        .replace("__ROW_SPAN_BURSTS__", str(row_span_bursts))
        .replace("__REQUEST_ROW_WINDOW_EXPR__", row_window_expr)
        .replace("__BURST_BYTES__", str(burst_bytes))
        .replace("__ROW_MISS_PENALTY_CYCLES__", str(row_miss_penalty_cycles))
        .replace("__REQUEST_OVERHEAD_CYCLES__", str(request_overhead_cycles))
        .replace("__SCHEDULER_GAP_CYCLES__", str(scheduler_gap_cycles))
        .replace("__OUTSTANDING__", str(outstanding))
        .replace("__ADDRESS_BITS__", str(address_bits))
        .replace("__ROW_ID_BITS__", str(row_id_bits))
        .replace("__CHANNEL_BITS__", str(channel_bits))
        .replace("__OUTSTANDING_BITS__", str(outstanding_bits))
        .replace("__COMPLETION_BITS__", str(completion_bits))
        .replace("__QUEUE_DEPTH__", str(queue_depth))
        .replace("__QUEUE_PTR_BITS__", str(queue_ptr_bits))
        .replace("__QUEUE_COUNT_BITS__", str(queue_count_bits))
        .replace("__SERVICE_BITS__", str(service_bits))
        .replace("__OCCUPANCY_BITS__", str(channel_count * queue_count_bits))
        .replace("__SERVICE_STATUS_BITS__", str(channel_count * service_bits))
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    config_path = Path(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    params = _validate(_load_json(config_path))
    top_name = str(params["top_name"])
    (out_dir / f"{top_name}.v").write_text(_generate(params), encoding="utf-8")
    (out_dir / "config.json").write_text(json.dumps(_load_json(config_path), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
