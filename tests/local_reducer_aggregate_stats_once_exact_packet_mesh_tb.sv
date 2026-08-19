`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_packet_mesh_tb;
  localparam integer DATA_W = 256;
  localparam integer TAG_W = 8;
  localparam integer FRAGMENT_W = 3;
  localparam integer VC_W = 2;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  function automatic [DATA_W-1:0] payload_for;
    input integer group_id;
    input integer flit_id;
    reg [31:0] state;
    integer lane;
    begin
      payload_for = {DATA_W{1'b0}};
      for (lane = 0; lane < 8; lane = lane + 1) begin
        state = 32'h9e3779b9 ^ (group_id * 32'h45d9f3b) ^
          (flit_id * 32'h27d4eb2d) ^ (lane * 32'h165667b1);
        state = state ^ (state << 13);
        state = state ^ (state >> 17);
        state = state ^ (state << 5);
        payload_for[(lane * 32) +: 32] = state;
      end
    end
  endfunction

  function automatic [7:0] tag_for;
    input integer group_id;
    input integer flit_id;
    begin
      tag_for = ((3 + group_id) * 32) + (flit_id / 8);
    end
  endfunction

  function automatic [2:0] fragment_for;
    input integer flit_id;
    begin
      fragment_for = flit_id % 8;
    end
  endfunction

  // One source at endpoint 1, one sink at endpoint 0, and no traffic at the
  // other fourteen endpoints.  The actual segmented mesh and all router/FIFO
  // instances are therefore part of this equivalence test.
  reg good_ctx_valid;
  wire good_tx_ctx_ready;
  wire good_rx_ctx_ready;
  reg [15:0] good_command;
  reg [4:0] good_head;
  reg [3:0] good_source;
  reg [3:0] good_destination;
  reg [VC_W-1:0] good_vc;
  reg [2:0] good_epoch;

  reg good_codec_valid;
  wire good_codec_ready;
  reg [DATA_W-1:0] good_codec_data;
  reg good_codec_group_last;
  wire good_tx_mesh_valid;
  wire good_tx_mesh_ready;
  wire [3:0] good_tx_mesh_destination;
  wire [3:0] good_tx_mesh_source;
  wire [TAG_W-1:0] good_tx_mesh_tag;
  wire [FRAGMENT_W-1:0] good_tx_mesh_fragment;
  wire good_tx_mesh_last;
  wire [VC_W-1:0] good_tx_mesh_vc;
  wire [DATA_W-1:0] good_tx_mesh_data;
  wire good_tx_clean_complete;

  wire good_rx_mesh_valid;
  wire good_rx_mesh_ready;
  wire [3:0] good_rx_mesh_destination;
  wire [3:0] good_rx_mesh_source;
  wire [TAG_W-1:0] good_rx_mesh_tag;
  wire [FRAGMENT_W-1:0] good_rx_mesh_fragment;
  wire good_rx_mesh_last;
  wire [VC_W-1:0] good_rx_mesh_vc;
  wire [DATA_W-1:0] good_rx_mesh_data;
  wire good_rx_codec_valid;
  wire good_rx_codec_ready;
  wire [DATA_W-1:0] good_rx_codec_data;
  wire good_rx_codec_group_last;
  wire good_tx_error;
  wire good_rx_error;
  wire good_clean_complete;

  reg [15:0] mesh_in_valid;
  wire [15:0] mesh_in_ready;
  reg [16*4-1:0] mesh_in_dest;
  reg [16*4-1:0] mesh_in_source;
  reg [16*TAG_W-1:0] mesh_in_tag;
  reg [16*FRAGMENT_W-1:0] mesh_in_fragment;
  reg [15:0] mesh_in_last;
  reg [16*VC_W-1:0] mesh_in_vc;
  reg [16*DATA_W-1:0] mesh_in_data;
  wire [15:0] mesh_out_valid;
  reg [15:0] mesh_out_ready;
  wire [16*4-1:0] mesh_out_dest;
  wire [16*4-1:0] mesh_out_source;
  wire [16*TAG_W-1:0] mesh_out_tag;
  wire [16*FRAGMENT_W-1:0] mesh_out_fragment;
  wire [15:0] mesh_out_last;
  wire [16*VC_W-1:0] mesh_out_vc;
  wire [16*DATA_W-1:0] mesh_out_data;

  integer good_cycle;
  integer mesh_flit_count;
  integer output_flit_count;
  integer mesh_packet_count;
  integer mesh_group_packet_count;
  integer clean_count;
  integer tx_clean_count;
  integer good_failures;
  integer tx_stability_failures;
  integer rx_stability_failures;
  integer mesh_metadata_failures;
  integer output_last_failures;
  reg tx_hold_valid;
  reg [3:0] tx_hold_destination;
  reg [3:0] tx_hold_source;
  reg [TAG_W-1:0] tx_hold_tag;
  reg [FRAGMENT_W-1:0] tx_hold_fragment;
  reg tx_hold_last;
  reg [VC_W-1:0] tx_hold_vc;
  reg [DATA_W-1:0] tx_hold_data;
  reg rx_hold_valid;
  reg [DATA_W-1:0] rx_hold_data;
  reg rx_hold_group_last;

  assign good_tx_mesh_ready = mesh_in_ready[1];
  assign good_rx_codec_ready = !((good_cycle % 7) == 3) &&
    !((good_cycle % 13) == 6);
  assign good_rx_mesh_valid = mesh_out_valid[0];
  assign good_rx_mesh_destination = mesh_out_dest[0 +: 4];
  assign good_rx_mesh_source = mesh_out_source[0 +: 4];
  assign good_rx_mesh_tag = mesh_out_tag[0 +: TAG_W];
  assign good_rx_mesh_fragment = mesh_out_fragment[0 +: FRAGMENT_W];
  assign good_rx_mesh_last = mesh_out_last[0];
  assign good_rx_mesh_vc = mesh_out_vc[0 +: VC_W];
  assign good_rx_mesh_data = mesh_out_data[0 +: DATA_W];

  always @* begin
    mesh_in_valid = 16'b0;
    mesh_in_dest = {(16*4){1'b0}};
    mesh_in_source = {(16*4){1'b0}};
    mesh_in_tag = {(16*TAG_W){1'b0}};
    mesh_in_fragment = {(16*FRAGMENT_W){1'b0}};
    mesh_in_last = 16'b0;
    mesh_in_vc = {(16*VC_W){1'b0}};
    mesh_in_data = {(16*DATA_W){1'b0}};
    mesh_in_valid[1] = good_tx_mesh_valid;
    mesh_in_dest[1*4 +: 4] = good_tx_mesh_destination;
    mesh_in_source[1*4 +: 4] = good_tx_mesh_source;
    mesh_in_tag[1*TAG_W +: TAG_W] = good_tx_mesh_tag;
    mesh_in_fragment[1*FRAGMENT_W +: FRAGMENT_W] = good_tx_mesh_fragment;
    mesh_in_last[1] = good_tx_mesh_last;
    mesh_in_vc[1*VC_W +: VC_W] = good_tx_mesh_vc;
    mesh_in_data[1*DATA_W +: DATA_W] = good_tx_mesh_data;

    mesh_out_ready = 16'b0;
    mesh_out_ready[0] = good_rx_mesh_ready;
  end

  noc_segmented_mesh4x4 #(
    .DATA_W(DATA_W), .TAG_W(TAG_W), .FRAGMENT_W(FRAGMENT_W), .VC_W(VC_W),
    .VC_COUNT(4), .FIFO_DEPTH(4)
  ) u_mesh (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(mesh_in_valid), .endpoint_in_ready(mesh_in_ready),
    .endpoint_in_dest(mesh_in_dest), .endpoint_in_source(mesh_in_source),
    .endpoint_in_tag(mesh_in_tag), .endpoint_in_fragment(mesh_in_fragment),
    .endpoint_in_last(mesh_in_last), .endpoint_in_vc(mesh_in_vc),
    .endpoint_in_data(mesh_in_data),
    .endpoint_out_valid(mesh_out_valid), .endpoint_out_ready(mesh_out_ready),
    .endpoint_out_dest(mesh_out_dest), .endpoint_out_source(mesh_out_source),
    .endpoint_out_tag(mesh_out_tag), .endpoint_out_fragment(mesh_out_fragment),
    .endpoint_out_last(mesh_out_last), .endpoint_out_vc(mesh_out_vc),
    .endpoint_out_data(mesh_out_data),
    .router_accepted_flit_count(), .router_forwarded_flit_count(),
    .router_input_stall_cycles(), .router_output_stall_cycles(),
    .router_contention_cycles(), .router_current_input_occupancy(),
    .router_max_input_occupancy(), .router_route_flit_count()
  );

  local_reducer_aggregate_stats_once_exact_packet_tx_framer u_good_tx (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(good_ctx_valid), .group_ctx_ready(good_tx_ctx_ready),
    .group_command_id(good_command), .group_head_base(good_head),
    .group_source(good_source), .group_destination(good_destination),
    .group_vc(good_vc), .group_epoch(good_epoch),
    .codec_flit_valid(good_codec_valid), .codec_flit_ready(good_codec_ready),
    .codec_flit_data(good_codec_data),
    .codec_flit_group_last(good_codec_group_last),
    .mesh_flit_valid(good_tx_mesh_valid), .mesh_flit_ready(good_tx_mesh_ready),
    .mesh_flit_destination(good_tx_mesh_destination),
    .mesh_flit_source(good_tx_mesh_source), .mesh_flit_tag(good_tx_mesh_tag),
    .mesh_flit_fragment(good_tx_mesh_fragment),
    .mesh_flit_last(good_tx_mesh_last), .mesh_flit_vc(good_tx_mesh_vc),
    .mesh_flit_data(good_tx_mesh_data),
    .clean_group_complete(good_tx_clean_complete),
    .protocol_error(good_tx_error)
  );

  local_reducer_aggregate_stats_once_exact_packet_rx_deframer u_good_rx (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(good_ctx_valid), .group_ctx_ready(good_rx_ctx_ready),
    .group_command_id(good_command), .group_head_base(good_head),
    .group_source(good_source), .group_destination(good_destination),
    .group_vc(good_vc), .group_epoch(good_epoch),
    .mesh_flit_valid(good_rx_mesh_valid), .mesh_flit_ready(good_rx_mesh_ready),
    .mesh_flit_destination(good_rx_mesh_destination),
    .mesh_flit_source(good_rx_mesh_source), .mesh_flit_tag(good_rx_mesh_tag),
    .mesh_flit_fragment(good_rx_mesh_fragment),
    .mesh_flit_last(good_rx_mesh_last), .mesh_flit_vc(good_rx_mesh_vc),
    .mesh_flit_data(good_rx_mesh_data),
    .codec_flit_valid(good_rx_codec_valid),
    .codec_flit_ready(good_rx_codec_ready), .codec_flit_data(good_rx_codec_data),
    .codec_flit_group_last(good_rx_codec_group_last),
    .protocol_error(good_rx_error), .clean_group_complete(good_clean_complete)
  );

  always @(posedge clk) begin
    if (!rst_n) begin
      good_cycle <= 0;
      mesh_flit_count <= 0;
      output_flit_count <= 0;
      mesh_packet_count <= 0;
      mesh_group_packet_count <= 0;
      clean_count <= 0;
      tx_clean_count <= 0;
      good_failures <= 0;
      tx_stability_failures <= 0;
      rx_stability_failures <= 0;
      mesh_metadata_failures <= 0;
      output_last_failures <= 0;
      tx_hold_valid <= 1'b0;
      rx_hold_valid <= 1'b0;
    end else begin
      good_cycle <= good_cycle + 1;
      if (good_tx_error || good_rx_error)
        good_failures <= good_failures + 1;
      if (good_tx_clean_complete)
        tx_clean_count <= tx_clean_count + 1;

      if (tx_hold_valid) begin
        if (!good_tx_mesh_valid ||
            good_tx_mesh_destination !== tx_hold_destination ||
            good_tx_mesh_source !== tx_hold_source ||
            good_tx_mesh_tag !== tx_hold_tag ||
            good_tx_mesh_fragment !== tx_hold_fragment ||
            good_tx_mesh_last !== tx_hold_last ||
            good_tx_mesh_vc !== tx_hold_vc ||
            good_tx_mesh_data !== tx_hold_data) begin
          good_failures <= good_failures + 1;
          tx_stability_failures <= tx_stability_failures + 1;
        end
      end
      tx_hold_valid <= good_tx_mesh_valid && !good_tx_mesh_ready;
      if (good_tx_mesh_valid && !good_tx_mesh_ready) begin
        tx_hold_destination <= good_tx_mesh_destination;
        tx_hold_source <= good_tx_mesh_source;
        tx_hold_tag <= good_tx_mesh_tag;
        tx_hold_fragment <= good_tx_mesh_fragment;
        tx_hold_last <= good_tx_mesh_last;
        tx_hold_vc <= good_tx_mesh_vc;
        tx_hold_data <= good_tx_mesh_data;
      end

      if (rx_hold_valid) begin
        if (!good_rx_codec_valid || good_rx_codec_data !== rx_hold_data ||
            good_rx_codec_group_last !== rx_hold_group_last) begin
          good_failures <= good_failures + 1;
          rx_stability_failures <= rx_stability_failures + 1;
        end
      end
      rx_hold_valid <= good_rx_codec_valid && !good_rx_codec_ready;
      if (good_rx_codec_valid && !good_rx_codec_ready) begin
        rx_hold_data <= good_rx_codec_data;
        rx_hold_group_last <= good_rx_codec_group_last;
      end

      if (good_rx_mesh_valid && good_rx_mesh_ready) begin
        if (good_rx_mesh_destination !== 4'd0 ||
            good_rx_mesh_source !== 4'd1 || good_rx_mesh_vc !== 2'd2)
          begin good_failures <= good_failures + 1; mesh_metadata_failures <= mesh_metadata_failures + 1; end
        if (good_rx_mesh_tag !== tag_for(mesh_flit_count / 167,
                                         mesh_flit_count % 167))
          begin good_failures <= good_failures + 1; mesh_metadata_failures <= mesh_metadata_failures + 1; end
        if (good_rx_mesh_fragment !== fragment_for(mesh_flit_count % 167))
          begin good_failures <= good_failures + 1; mesh_metadata_failures <= mesh_metadata_failures + 1; end
        if (good_rx_mesh_last !== (((mesh_flit_count % 167) % 8) == 7 ||
                                   (mesh_flit_count % 167) == 166))
          begin good_failures <= good_failures + 1; mesh_metadata_failures <= mesh_metadata_failures + 1; end
        if (good_rx_mesh_data !== payload_for(mesh_flit_count / 167,
                                               mesh_flit_count % 167)) begin
          good_failures <= good_failures + 1;
          mesh_metadata_failures <= mesh_metadata_failures + 1;
        end
        mesh_flit_count <= mesh_flit_count + 1;
        if (good_rx_mesh_last) begin
          mesh_packet_count <= mesh_packet_count + 1;
          mesh_group_packet_count <= mesh_group_packet_count + 1;
          if ((mesh_flit_count % 167) == 166) begin
            if (mesh_group_packet_count != 20)
              good_failures <= good_failures + 1;
            mesh_group_packet_count <= 0;
          end
        end
      end

      if (good_rx_codec_valid && good_rx_codec_ready) begin
        if (good_rx_codec_data !== payload_for(output_flit_count / 167,
                                                output_flit_count % 167)) begin
          good_failures <= good_failures + 1;
        end
        if (good_rx_codec_group_last !==
            ((output_flit_count % 167) == 166))
          begin good_failures <= good_failures + 1; output_last_failures <= output_last_failures + 1; end
        output_flit_count <= output_flit_count + 1;
      end
      if (good_clean_complete)
        clean_count <= clean_count + 1;
    end
  end

  // Direct malformed TX: early group-last is rejected, but the fixed-size
  // group is drained so that context can be reused after recovery.
  reg bad_early_ctx_valid;
  wire bad_early_ctx_ready;
  reg [15:0] bad_early_command;
  reg [4:0] bad_early_head;
  reg [3:0] bad_early_source;
  reg [3:0] bad_early_destination;
  reg [1:0] bad_early_vc;
  reg [2:0] bad_early_epoch;
  reg bad_early_codec_valid;
  wire bad_early_codec_ready;
  reg [DATA_W-1:0] bad_early_data;
  reg bad_early_group_last;
  wire bad_early_mesh_valid;
  wire bad_early_clean;
  wire bad_early_error;
  integer bad_early_done;
  integer bad_early_clean_count;

  local_reducer_aggregate_stats_once_exact_packet_tx_framer u_bad_early (
    .clk(clk), .rst_n(rst_n), .group_ctx_valid(bad_early_ctx_valid),
    .group_ctx_ready(bad_early_ctx_ready), .group_command_id(bad_early_command),
    .group_head_base(bad_early_head), .group_source(bad_early_source),
    .group_destination(bad_early_destination), .group_vc(bad_early_vc),
    .group_epoch(bad_early_epoch), .codec_flit_valid(bad_early_codec_valid),
    .codec_flit_ready(bad_early_codec_ready), .codec_flit_data(bad_early_data),
    .codec_flit_group_last(bad_early_group_last),
    .mesh_flit_valid(bad_early_mesh_valid), .mesh_flit_ready(1'b1),
    .mesh_flit_destination(), .mesh_flit_source(), .mesh_flit_tag(),
    .mesh_flit_fragment(), .mesh_flit_last(), .mesh_flit_vc(),
    .mesh_flit_data(), .clean_group_complete(bad_early_clean),
    .protocol_error(bad_early_error)
  );

  // Direct malformed TX: the final codec beat omits group-last.
  reg bad_late_ctx_valid;
  wire bad_late_ctx_ready;
  reg [15:0] bad_late_command;
  reg [4:0] bad_late_head;
  reg [3:0] bad_late_source;
  reg [3:0] bad_late_destination;
  reg [1:0] bad_late_vc;
  reg [2:0] bad_late_epoch;
  reg bad_late_codec_valid;
  wire bad_late_codec_ready;
  reg [DATA_W-1:0] bad_late_data;
  reg bad_late_group_last;
  wire bad_late_mesh_valid;
  wire bad_late_clean;
  wire bad_late_error;
  integer bad_late_done;
  integer bad_late_clean_count;

  local_reducer_aggregate_stats_once_exact_packet_tx_framer u_bad_late (
    .clk(clk), .rst_n(rst_n), .group_ctx_valid(bad_late_ctx_valid),
    .group_ctx_ready(bad_late_ctx_ready), .group_command_id(bad_late_command),
    .group_head_base(bad_late_head), .group_source(bad_late_source),
    .group_destination(bad_late_destination), .group_vc(bad_late_vc),
    .group_epoch(bad_late_epoch), .codec_flit_valid(bad_late_codec_valid),
    .codec_flit_ready(bad_late_codec_ready), .codec_flit_data(bad_late_data),
    .codec_flit_group_last(bad_late_group_last),
    .mesh_flit_valid(bad_late_mesh_valid), .mesh_flit_ready(1'b1),
    .mesh_flit_destination(), .mesh_flit_source(), .mesh_flit_tag(),
    .mesh_flit_fragment(), .mesh_flit_last(), .mesh_flit_vc(),
    .mesh_flit_data(), .clean_group_complete(bad_late_clean),
    .protocol_error(bad_late_error)
  );

  // Direct malformed RX: one packet fragment is out of order.  All 167
  // flits are still supplied, so lack of clean completion is tested directly.
  reg bad_rx_ctx_valid;
  wire bad_rx_ctx_ready;
  reg [15:0] bad_rx_command;
  reg [4:0] bad_rx_head;
  reg [3:0] bad_rx_source;
  reg [3:0] bad_rx_destination;
  reg [1:0] bad_rx_vc;
  reg [2:0] bad_rx_epoch;
  reg bad_rx_mesh_valid;
  wire bad_rx_mesh_ready;
  reg [3:0] bad_rx_mesh_dest;
  reg [3:0] bad_rx_mesh_src;
  reg [7:0] bad_rx_mesh_tag;
  reg [2:0] bad_rx_mesh_fragment;
  reg bad_rx_mesh_last;
  reg [1:0] bad_rx_mesh_vc;
  reg [DATA_W-1:0] bad_rx_mesh_data;
  wire bad_rx_codec_valid;
  wire bad_rx_error;
  wire bad_rx_clean;
  integer bad_rx_output_count;
  integer bad_rx_clean_count;
  integer bad_rx_done;

  local_reducer_aggregate_stats_once_exact_packet_rx_deframer u_bad_rx (
    .clk(clk), .rst_n(rst_n), .group_ctx_valid(bad_rx_ctx_valid),
    .group_ctx_ready(bad_rx_ctx_ready), .group_command_id(bad_rx_command),
    .group_head_base(bad_rx_head), .group_source(bad_rx_source),
    .group_destination(bad_rx_destination), .group_vc(bad_rx_vc),
    .group_epoch(bad_rx_epoch), .mesh_flit_valid(bad_rx_mesh_valid),
    .mesh_flit_ready(bad_rx_mesh_ready), .mesh_flit_destination(bad_rx_mesh_dest),
    .mesh_flit_source(bad_rx_mesh_src), .mesh_flit_tag(bad_rx_mesh_tag),
    .mesh_flit_fragment(bad_rx_mesh_fragment), .mesh_flit_last(bad_rx_mesh_last),
    .mesh_flit_vc(bad_rx_mesh_vc), .mesh_flit_data(bad_rx_mesh_data),
    .codec_flit_valid(bad_rx_codec_valid), .codec_flit_ready(1'b1),
    .codec_flit_data(), .codec_flit_group_last(),
    .protocol_error(bad_rx_error), .clean_group_complete(bad_rx_clean)
  );

  initial begin
    good_ctx_valid = 0;
    good_command = 0;
    good_head = 0;
    good_source = 0;
    good_destination = 0;
    good_vc = 0;
    good_epoch = 0;
    good_codec_valid = 0;
    good_codec_data = 0;
    good_codec_group_last = 0;
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    for (integer group_i = 0; group_i < 2; group_i = group_i + 1) begin
      @(negedge clk);
      good_command = 16'h5200 + group_i;
      good_head = 5'd8;
      good_source = 4'd1;
      good_destination = 4'd0;
      good_vc = 2'd2;
      good_epoch = 3'd3 + group_i;
      good_ctx_valid = 1'b1;
      while (!(good_tx_ctx_ready && good_rx_ctx_ready)) @(posedge clk);
      @(negedge clk);
      good_ctx_valid = 1'b0;
      for (integer flit_i = 0; flit_i < 167; flit_i = flit_i + 1) begin
        good_codec_data = payload_for(group_i, flit_i);
        good_codec_group_last = (flit_i == 166);
        good_codec_valid = 1'b1;
        while (!(good_codec_valid && good_codec_ready)) @(posedge clk);
        @(negedge clk);
      end
      good_codec_valid = 1'b0;
      good_codec_group_last = 1'b0;
      good_codec_data = 0;
      while (clean_count <= group_i) @(posedge clk);
      @(negedge clk);
    end
    while (mesh_flit_count < 334 || output_flit_count < 334 || clean_count < 2)
      @(posedge clk);
    if (good_failures != 0 || mesh_flit_count != 334 ||
        output_flit_count != 334 || mesh_packet_count != 42 || clean_count != 2 ||
        tx_clean_count != 2 ||
        good_tx_error || good_rx_error)
      $fatal(1, "mesh equivalence failed mesh=%0d output=%0d packets=%0d clean=%0d failures=%0d txstable=%0d rxstable=%0d meta=%0d outlast=%0d errors=%b/%b",
        mesh_flit_count, output_flit_count, mesh_packet_count, clean_count,
        good_failures, tx_stability_failures, rx_stability_failures,
        mesh_metadata_failures, output_last_failures, good_tx_error, good_rx_error);
    bad_early_done = 1;
    bad_late_done = 1;
    bad_rx_done = 1;
    while (!(bad_early_done && bad_late_done && bad_rx_done)) @(posedge clk);
    $display("PASS local_reducer_aggregate_stats_once_exact_packet_mesh groups=2 flits=334 packets=42 outputs=334 tx_clean=2 rx_clean=2 clean=2");
    $finish;
  end

  initial begin
    bad_early_ctx_valid = 0;
    bad_early_command = 16'h6100;
    bad_early_head = 5'd8;
    bad_early_source = 4'd1;
    bad_early_destination = 4'd0;
    bad_early_vc = 2'd2;
    bad_early_epoch = 3'd1;
    bad_early_codec_valid = 0;
    bad_early_data = 0;
    bad_early_group_last = 0;
    bad_early_done = 0;
    bad_early_clean_count = 0;
    @(posedge rst_n);
    @(negedge clk);
    bad_early_ctx_valid = 1;
    while (!bad_early_ctx_ready) @(posedge clk);
    @(negedge clk);
    bad_early_ctx_valid = 0;
    for (integer i = 0; i < 167; i = i + 1) begin
      bad_early_data = payload_for(9, i);
      bad_early_group_last = (i == 10) || (i == 166);
      bad_early_codec_valid = 1;
      while (!(bad_early_codec_valid && bad_early_codec_ready)) @(posedge clk);
      @(negedge clk);
    end
    bad_early_codec_valid = 0;
    bad_early_group_last = 0;
    while (!bad_early_error) @(posedge clk);
    while (!bad_early_ctx_ready) @(posedge clk);
    if (bad_early_clean_count != 0)
      $fatal(1, "early malformed TX completed cleanly");
    bad_early_done = 1;
  end

  initial begin
    bad_late_ctx_valid = 0;
    bad_late_command = 16'h6200;
    bad_late_head = 5'd8;
    bad_late_source = 4'd1;
    bad_late_destination = 4'd0;
    bad_late_vc = 2'd2;
    bad_late_epoch = 3'd2;
    bad_late_codec_valid = 0;
    bad_late_data = 0;
    bad_late_group_last = 0;
    bad_late_done = 0;
    bad_late_clean_count = 0;
    @(posedge rst_n);
    @(negedge clk);
    bad_late_ctx_valid = 1;
    while (!bad_late_ctx_ready) @(posedge clk);
    @(negedge clk);
    bad_late_ctx_valid = 0;
    for (integer i = 0; i < 167; i = i + 1) begin
      bad_late_data = payload_for(10, i);
      bad_late_group_last = 1'b0;
      bad_late_codec_valid = 1;
      while (!(bad_late_codec_valid && bad_late_codec_ready)) @(posedge clk);
      @(negedge clk);
    end
    bad_late_codec_valid = 0;
    while (!bad_late_error) @(posedge clk);
    while (!bad_late_ctx_ready) @(posedge clk);
    if (bad_late_clean_count != 0)
      $fatal(1, "late malformed TX completed cleanly");
    bad_late_done = 1;
  end

  initial begin
    bad_rx_ctx_valid = 0;
    bad_rx_command = 16'h6300;
    bad_rx_head = 5'd8;
    bad_rx_source = 4'd1;
    bad_rx_destination = 4'd0;
    bad_rx_vc = 2'd2;
    bad_rx_epoch = 3'd7;
    bad_rx_mesh_valid = 0;
    bad_rx_mesh_dest = 0;
    bad_rx_mesh_src = 0;
    bad_rx_mesh_tag = 0;
    bad_rx_mesh_fragment = 0;
    bad_rx_mesh_last = 0;
    bad_rx_mesh_vc = 0;
    bad_rx_mesh_data = 0;
    bad_rx_output_count = 0;
    bad_rx_clean_count = 0;
    bad_rx_done = 0;
    @(posedge rst_n);
    @(negedge clk);
    bad_rx_ctx_valid = 1;
    while (!bad_rx_ctx_ready) @(posedge clk);
    @(negedge clk);
    bad_rx_ctx_valid = 0;
    for (integer i = 0; i < 167; i = i + 1) begin
      bad_rx_mesh_dest = 4'd0;
      bad_rx_mesh_src = 4'd1;
      bad_rx_mesh_tag = 8'he0 | (i / 8);
      bad_rx_mesh_fragment = (i == 166) ? 3'd5 : (i % 8);
      bad_rx_mesh_last = ((i % 8) == 7) || (i == 166);
      bad_rx_mesh_vc = 2'd2;
      bad_rx_mesh_data = payload_for(11, i);
      bad_rx_mesh_valid = 1;
      while (!(bad_rx_mesh_valid && bad_rx_mesh_ready)) @(posedge clk);
      @(negedge clk);
    end
    bad_rx_mesh_valid = 0;
    while (bad_rx_output_count < 167) @(posedge clk);
    if (!bad_rx_error || bad_rx_clean_count != 0)
      $fatal(1, "malformed RX was not rejected");
    bad_rx_done = 1;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (bad_rx_codec_valid)
        bad_rx_output_count <= bad_rx_output_count + 1;
      if (bad_rx_clean)
        bad_rx_clean_count <= bad_rx_clean_count + 1;
      if (bad_early_clean)
        bad_early_clean_count <= bad_early_clean_count + 1;
      if (bad_late_clean)
        bad_late_clean_count <= bad_late_clean_count + 1;
    end
  end

  initial begin
    #500000;
    $fatal(1, "simulation timeout");
  end
endmodule
