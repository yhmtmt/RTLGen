`timescale 1ns/1ps

// Two-source endpoint injection arbiter for the shared VC0/VC1 mesh.
// Each producer owns its ready/valid holding register. The arbiter stores the
// round-robin cursor and a stalled grant identity, but no flit payload.
module noc_endpoint_vc_injection_arbiter #(
  parameter integer DATA_W = 256,
  parameter integer ENDPOINT_W = 4,
  parameter integer VC_W = 2,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3
) (
  input wire clk,
  input wire rst_n,

  input wire vc0_valid,
  output wire vc0_ready,
  input wire [ENDPOINT_W-1:0] vc0_destination,
  input wire [ENDPOINT_W-1:0] vc0_source,
  input wire [TAG_W-1:0] vc0_tag,
  input wire [FRAGMENT_W-1:0] vc0_fragment,
  input wire vc0_last,
  input wire [VC_W-1:0] vc0_vc,
  input wire [DATA_W-1:0] vc0_data,

  input wire vc1_valid,
  output wire vc1_ready,
  input wire [ENDPOINT_W-1:0] vc1_destination,
  input wire [ENDPOINT_W-1:0] vc1_source,
  input wire [TAG_W-1:0] vc1_tag,
  input wire [FRAGMENT_W-1:0] vc1_fragment,
  input wire vc1_last,
  input wire [VC_W-1:0] vc1_vc,
  input wire [DATA_W-1:0] vc1_data,

  output reg out_valid,
  input wire out_ready,
  output reg [ENDPOINT_W-1:0] out_destination,
  output reg [ENDPOINT_W-1:0] out_source,
  output reg [TAG_W-1:0] out_tag,
  output reg [FRAGMENT_W-1:0] out_fragment,
  output reg out_last,
  output reg [VC_W-1:0] out_vc,
  output reg [DATA_W-1:0] out_data,

  output reg protocol_error
);
  reg preferred_vc_q;
  reg held_grant_valid_q;
  reg held_grant_vc_q;
  reg grant_vc_r;
  reg grant_valid_r;

  wire vc0_contract_valid = vc0_vc == {VC_W{1'b0}};
  wire [VC_W-1:0] vc1_expected = {{(VC_W-1){1'b0}}, 1'b1};
  wire vc1_contract_valid = vc1_vc == vc1_expected;
  wire vc0_eligible = vc0_valid && vc0_contract_valid;
  wire vc1_eligible = vc1_valid && vc1_contract_valid;
  wire vc0_drop = vc0_valid && !vc0_contract_valid;
  wire vc1_drop = vc1_valid && !vc1_contract_valid;
  wire out_fire = out_valid && out_ready;

  assign vc0_ready = vc0_drop || (grant_valid_r && !grant_vc_r && out_ready);
  assign vc1_ready = vc1_drop || (grant_valid_r && grant_vc_r && out_ready);

  always @(*) begin
    grant_valid_r = 1'b0;
    grant_vc_r = held_grant_valid_q ? held_grant_vc_q : preferred_vc_q;
    if (held_grant_valid_q) begin
      if (!held_grant_vc_q && vc0_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b0;
      end else if (held_grant_vc_q && vc1_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b1;
      end
    end else if (!preferred_vc_q) begin
      if (vc0_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b0;
      end else if (vc1_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b1;
      end
    end else begin
      if (vc1_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b1;
      end else if (vc0_eligible) begin
        grant_valid_r = 1'b1;
        grant_vc_r = 1'b0;
      end
    end

    out_valid = grant_valid_r;
    out_destination = {ENDPOINT_W{1'b0}};
    out_source = {ENDPOINT_W{1'b0}};
    out_tag = {TAG_W{1'b0}};
    out_fragment = {FRAGMENT_W{1'b0}};
    out_last = 1'b0;
    out_vc = {VC_W{1'b0}};
    out_data = {DATA_W{1'b0}};
    if (grant_valid_r && !grant_vc_r) begin
      out_destination = vc0_destination;
      out_source = vc0_source;
      out_tag = vc0_tag;
      out_fragment = vc0_fragment;
      out_last = vc0_last;
      out_vc = vc0_vc;
      out_data = vc0_data;
    end else if (grant_valid_r) begin
      out_destination = vc1_destination;
      out_source = vc1_source;
      out_tag = vc1_tag;
      out_fragment = vc1_fragment;
      out_last = vc1_last;
      out_vc = vc1_vc;
      out_data = vc1_data;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      preferred_vc_q <= 1'b0;
      held_grant_valid_q <= 1'b0;
      held_grant_vc_q <= 1'b0;
      protocol_error <= 1'b0;
    end else begin
      if (vc0_drop || vc1_drop)
        protocol_error <= 1'b1;
      if (held_grant_valid_q &&
          ((!held_grant_vc_q && vc0_drop) ||
           (held_grant_vc_q && vc1_drop))) begin
        held_grant_valid_q <= 1'b0;
      end else if (out_fire) begin
        held_grant_valid_q <= 1'b0;
        preferred_vc_q <= !grant_vc_r;
      end else if (grant_valid_r && !out_ready) begin
        held_grant_valid_q <= 1'b1;
        held_grant_vc_q <= grant_vc_r;
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (VC_W < 2) begin
      $error("noc_endpoint_vc_injection_arbiter requires VC_W >= 2");
      $finish(1);
    end
  end
`endif
endmodule
