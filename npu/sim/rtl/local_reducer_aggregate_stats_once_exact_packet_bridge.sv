`timescale 1ns/1ps

// Packetizes one exact stats-once group for the segmented mesh.  The codec
// group stream and the mesh packet stream have independent last markers.
module local_reducer_aggregate_stats_once_exact_packet_tx_framer #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2
) (
  input  wire                         clk,
  input  wire                         rst_n,
  input  wire                         group_ctx_valid,
  output wire                         group_ctx_ready,
  input  wire [15:0]                  group_command_id,
  input  wire [4:0]                   group_head_base,
  input  wire [3:0]                   group_source,
  input  wire [3:0]                   group_destination,
  input  wire [VC_W-1:0]              group_vc,
  input  wire [2:0]                   group_epoch,
  input  wire                         codec_flit_valid,
  output wire                         codec_flit_ready,
  input  wire [DATA_W-1:0]             codec_flit_data,
  input  wire                         codec_flit_group_last,
  output wire                         mesh_flit_valid,
  input  wire                         mesh_flit_ready,
  output wire [3:0]                   mesh_flit_destination,
  output wire [3:0]                   mesh_flit_source,
  output wire [TAG_W-1:0]             mesh_flit_tag,
  output wire [FRAGMENT_W-1:0]        mesh_flit_fragment,
  output wire                         mesh_flit_last,
  output wire [VC_W-1:0]              mesh_flit_vc,
  output wire [DATA_W-1:0]             mesh_flit_data,
  output wire                         clean_group_complete,
  output wire                         protocol_error
);
  localparam integer GROUP_FLITS = 167;

  reg active_q;
  reg input_done_q;
  reg [7:0] flit_index_q;
  reg [3:0] source_q;
  reg [3:0] destination_q;
  reg [VC_W-1:0] vc_q;
  reg [2:0] epoch_q;
  reg output_valid_q;
  reg [3:0] output_destination_q;
  reg [3:0] output_source_q;
  reg [TAG_W-1:0] output_tag_q;
  reg [FRAGMENT_W-1:0] output_fragment_q;
  reg output_last_q;
  reg [VC_W-1:0] output_vc_q;
  reg [DATA_W-1:0] output_data_q;
  reg group_error_q;
  reg protocol_error_q;
  reg clean_group_complete_q;

  wire output_fire = output_valid_q && mesh_flit_ready;
  wire codec_fire = codec_flit_valid && codec_flit_ready;
  wire expected_group_last = (flit_index_q == 8'd166);
  wire valid_head_base = (group_head_base == 5'd0) ||
    (group_head_base == 5'd8) || (group_head_base == 5'd16) ||
    (group_head_base == 5'd24);

  assign group_ctx_ready = !active_q;
  assign codec_flit_ready = active_q && !input_done_q &&
    (!output_valid_q || mesh_flit_ready);
  assign mesh_flit_valid = output_valid_q;
  assign mesh_flit_destination = output_destination_q;
  assign mesh_flit_source = output_source_q;
  assign mesh_flit_tag = output_tag_q;
  assign mesh_flit_fragment = output_fragment_q;
  assign mesh_flit_last = output_last_q;
  assign mesh_flit_vc = output_vc_q;
  assign mesh_flit_data = output_data_q;
  assign clean_group_complete = clean_group_complete_q;
  assign protocol_error = protocol_error_q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_q <= 1'b0;
      input_done_q <= 1'b0;
      flit_index_q <= 8'b0;
      source_q <= 4'b0;
      destination_q <= 4'b0;
      vc_q <= {VC_W{1'b0}};
      epoch_q <= 3'b0;
      output_valid_q <= 1'b0;
      output_destination_q <= 4'b0;
      output_source_q <= 4'b0;
      output_tag_q <= {TAG_W{1'b0}};
      output_fragment_q <= {FRAGMENT_W{1'b0}};
      output_last_q <= 1'b0;
      output_vc_q <= {VC_W{1'b0}};
      output_data_q <= {DATA_W{1'b0}};
      group_error_q <= 1'b0;
      protocol_error_q <= 1'b0;
      clean_group_complete_q <= 1'b0;
    end else begin
      clean_group_complete_q <= 1'b0;
      if (group_ctx_valid && group_ctx_ready) begin
        active_q <= 1'b1;
        input_done_q <= 1'b0;
        flit_index_q <= 8'b0;
        source_q <= group_source;
        destination_q <= group_destination;
        vc_q <= group_vc;
        epoch_q <= group_epoch;
        output_valid_q <= 1'b0;
        group_error_q <= !valid_head_base;
        if (!valid_head_base)
          protocol_error_q <= 1'b1;
      end else begin
        if (codec_fire) begin
          output_valid_q <= 1'b1;
          output_destination_q <= destination_q;
          output_source_q <= source_q;
          output_tag_q <= {epoch_q, flit_index_q[7:3]};
          output_fragment_q <= flit_index_q[2:0];
          output_last_q <= (flit_index_q[2:0] == 3'd7) || expected_group_last;
          output_vc_q <= vc_q;
          output_data_q <= codec_flit_data;

          if (codec_flit_group_last != expected_group_last) begin
            group_error_q <= 1'b1;
            protocol_error_q <= 1'b1;
          end

          if (expected_group_last) begin
            input_done_q <= 1'b1;
          end else begin
            flit_index_q <= flit_index_q + 1'b1;
          end
        end else if (output_fire) begin
          output_valid_q <= 1'b0;
        end

        if (output_fire && input_done_q) begin
          if (!group_error_q)
            clean_group_complete_q <= 1'b1;
          active_q <= 1'b0;
          input_done_q <= 1'b0;
          output_valid_q <= 1'b0;
          flit_index_q <= 8'b0;
          group_error_q <= 1'b0;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || TAG_W != 8 || FRAGMENT_W != 3 || VC_W != 2) begin
      $error("packet TX bridge widths must be DATA=256 TAG=8 FRAGMENT=3 VC=2");
      $finish(1);
    end
    if (GROUP_FLITS != 167)
      $error("packet TX bridge group length changed");
  end
`endif
endmodule


// Deframes checked segmented-mesh packets back into the exact codec group
// stream.  It accepts the expected context atomically before accepting data.
module local_reducer_aggregate_stats_once_exact_packet_rx_deframer #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2
) (
  input  wire                         clk,
  input  wire                         rst_n,
  input  wire                         group_ctx_valid,
  output wire                         group_ctx_ready,
  input  wire [15:0]                  group_command_id,
  input  wire [4:0]                   group_head_base,
  input  wire [3:0]                   group_source,
  input  wire [3:0]                   group_destination,
  input  wire [VC_W-1:0]              group_vc,
  input  wire [2:0]                   group_epoch,
  input  wire                         mesh_flit_valid,
  output wire                         mesh_flit_ready,
  input  wire [3:0]                   mesh_flit_destination,
  input  wire [3:0]                   mesh_flit_source,
  input  wire [TAG_W-1:0]             mesh_flit_tag,
  input  wire [FRAGMENT_W-1:0]        mesh_flit_fragment,
  input  wire                         mesh_flit_last,
  input  wire [VC_W-1:0]              mesh_flit_vc,
  input  wire [DATA_W-1:0]             mesh_flit_data,
  output wire                         codec_flit_valid,
  input  wire                         codec_flit_ready,
  output wire [DATA_W-1:0]             codec_flit_data,
  output wire                         codec_flit_group_last,
  output wire [15:0]                  codec_group_command_id,
  output wire [4:0]                   codec_group_head_base,
  output wire                         protocol_error,
  output wire                         clean_group_complete
);
  localparam integer GROUP_FLITS = 167;

  reg active_q;
  reg input_done_q;
  reg [7:0] flit_index_q;
  reg [15:0] command_q;
  reg [4:0] head_base_q;
  reg [3:0] source_q;
  reg [3:0] destination_q;
  reg [VC_W-1:0] vc_q;
  reg [2:0] epoch_q;
  reg output_valid_q;
  reg [DATA_W-1:0] output_data_q;
  reg output_group_last_q;
  reg group_error_q;
  reg protocol_error_q;
  reg clean_group_complete_q;

  wire output_fire = output_valid_q && codec_flit_ready;
  wire mesh_fire = mesh_flit_valid && mesh_flit_ready;
  wire expected_group_last = (flit_index_q == 8'd166);
  wire expected_packet_last = (flit_index_q[2:0] == 3'd7) ||
    expected_group_last;
  wire [4:0] expected_packet = flit_index_q[7:3];
  wire [TAG_W-1:0] expected_tag = {epoch_q, expected_packet};
  wire valid_head_base = (group_head_base == 5'd0) ||
    (group_head_base == 5'd8) || (group_head_base == 5'd16) ||
    (group_head_base == 5'd24);
  wire metadata_ok =
    (mesh_flit_destination == destination_q) &&
    (mesh_flit_source == source_q) &&
    (mesh_flit_vc == vc_q) &&
    (mesh_flit_tag == expected_tag) &&
    (mesh_flit_fragment == flit_index_q[2:0]) &&
    (mesh_flit_last == expected_packet_last);

  assign group_ctx_ready = !active_q;
  assign mesh_flit_ready = active_q && !input_done_q &&
    (!output_valid_q || codec_flit_ready);
  assign codec_flit_valid = output_valid_q;
  assign codec_flit_data = output_data_q;
  assign codec_flit_group_last = output_group_last_q;
  assign codec_group_command_id = command_q;
  assign codec_group_head_base = head_base_q;
  assign protocol_error = protocol_error_q;
  assign clean_group_complete = clean_group_complete_q;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active_q <= 1'b0;
      input_done_q <= 1'b0;
      flit_index_q <= 8'b0;
      command_q <= 16'b0;
      head_base_q <= 5'b0;
      source_q <= 4'b0;
      destination_q <= 4'b0;
      vc_q <= {VC_W{1'b0}};
      epoch_q <= 3'b0;
      output_valid_q <= 1'b0;
      output_data_q <= {DATA_W{1'b0}};
      output_group_last_q <= 1'b0;
      group_error_q <= 1'b0;
      protocol_error_q <= 1'b0;
      clean_group_complete_q <= 1'b0;
    end else begin
      clean_group_complete_q <= 1'b0;

      if (group_ctx_valid && group_ctx_ready) begin
        active_q <= 1'b1;
        input_done_q <= 1'b0;
        flit_index_q <= 8'b0;
        command_q <= group_command_id;
        head_base_q <= group_head_base;
        source_q <= group_source;
        destination_q <= group_destination;
        vc_q <= group_vc;
        epoch_q <= group_epoch;
        output_valid_q <= 1'b0;
        group_error_q <= !valid_head_base;
        if (!valid_head_base)
          protocol_error_q <= 1'b1;
      end else begin
        if (mesh_fire) begin
          output_valid_q <= 1'b1;
          output_data_q <= mesh_flit_data;
          output_group_last_q <= expected_group_last;

          if (!metadata_ok) begin
            group_error_q <= 1'b1;
            protocol_error_q <= 1'b1;
          end

          if (expected_group_last)
            input_done_q <= 1'b1;
          else
            flit_index_q <= flit_index_q + 1'b1;
        end else if (output_fire) begin
          output_valid_q <= 1'b0;
        end

        if (output_fire && output_group_last_q) begin
          active_q <= 1'b0;
          input_done_q <= 1'b0;
          output_valid_q <= 1'b0;
          flit_index_q <= 8'b0;
          if (!group_error_q)
            clean_group_complete_q <= 1'b1;
          group_error_q <= 1'b0;
        end
      end
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || TAG_W != 8 || FRAGMENT_W != 3 || VC_W != 2) begin
      $error("packet RX bridge widths must be DATA=256 TAG=8 FRAGMENT=3 VC=2");
      $finish(1);
    end
    if (GROUP_FLITS != 167)
      $error("packet RX bridge group length changed");
  end
`endif
endmodule
