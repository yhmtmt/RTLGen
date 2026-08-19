`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_sram_packet_adapter_tb;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer GROUP_FLITS = 167;
  localparam integer GROUP_PACKETS = 21;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg sink_ctx_valid = 1'b0;
  wire sink_ctx_ready;
  wire sink_decoder_ctx_ready;
  reg [15:0] sink_command = 16'h4a20;
  reg [4:0] sink_head = 5'd8;
  reg [3:0] sink_source = 4'd5;
  reg [3:0] sink_destination = 4'd0;
  reg [1:0] sink_vc = 2'd2;
  reg [2:0] sink_epoch = 3'd3;
  wire sink_codec_valid;
  wire sink_codec_ready;
  wire [FLIT_W-1:0] sink_codec_data;
  wire sink_codec_group_last;
  wire sink_group_complete;
  wire sink_rx_descriptor_installed;
  wire sink_protocol_error;
  wire [31:0] sink_completion_count;
  wire [31:0] sink_replay_count;
  wire [2:0] sink_max_slots;
  wire [2:0] sink_max_destination_slots;

  reg source_ctx_valid = 1'b0;
  wire source_ctx_ready;
  wire source_encoder_ctx_ready;
  reg [15:0] source_command = 16'h4a20;
  reg [4:0] source_head = 5'd8;
  reg [3:0] source_source = 4'd5;
  reg [3:0] source_destination = 4'd0;
  reg [1:0] source_vc = 2'd2;
  reg [2:0] source_epoch = 3'd3;
  reg source_beat_valid = 1'b0;
  wire source_beat_ready;
  reg [BEAT_W-1:0] source_beat_data = {BEAT_W{1'b0}};
  wire source_encoder_flit_valid;
  wire source_encoder_flit_ready;
  wire [FLIT_W-1:0] source_encoder_flit_data;
  wire source_encoder_flit_group_last;
  wire source_encoder_error;
  wire source_group_complete;
  wire source_protocol_error;
  wire [31:0] source_descriptor_count;
  wire [2:0] source_max_slots;
  reg source_release_valid = 1'b0;
  wire source_release_ready;

  reg [15:0] mesh_in_valid;
  wire [15:0] mesh_in_ready;
  reg [16*4-1:0] mesh_in_destination;
  reg [16*4-1:0] mesh_in_source;
  reg [16*8-1:0] mesh_in_tag;
  reg [16*3-1:0] mesh_in_fragment;
  reg [15:0] mesh_in_last;
  reg [16*2-1:0] mesh_in_vc;
  reg [16*FLIT_W-1:0] mesh_in_data;
  wire [15:0] mesh_out_valid;
  wire [15:0] mesh_out_ready;
  wire [16*4-1:0] mesh_out_destination;
  wire [16*4-1:0] mesh_out_source;
  wire [16*8-1:0] mesh_out_tag;
  wire [16*3-1:0] mesh_out_fragment;
  wire [15:0] mesh_out_last;
  wire [16*2-1:0] mesh_out_vc;
  wire [16*FLIT_W-1:0] mesh_out_data;

  wire source_mesh_in_valid;
  wire source_mesh_in_ready;
  wire [3:0] source_mesh_in_destination;
  wire [3:0] source_mesh_in_source;
  wire [7:0] source_mesh_in_tag;
  wire [2:0] source_mesh_in_fragment;
  wire source_mesh_in_last;
  wire [1:0] source_mesh_in_vc;
  wire [FLIT_W-1:0] source_mesh_in_data;
  wire source_mesh_out_ready;

  wire sink_mesh_in_valid;
  wire sink_mesh_in_ready;
  wire [3:0] sink_mesh_in_destination;
  wire [3:0] sink_mesh_in_source;
  wire [7:0] sink_mesh_in_tag;
  wire [2:0] sink_mesh_in_fragment;
  wire sink_mesh_in_last;
  wire [1:0] sink_mesh_in_vc;
  wire [FLIT_W-1:0] sink_mesh_in_data;
  wire sink_mesh_out_valid;
  wire sink_mesh_out_ready;
  wire [3:0] sink_mesh_out_destination;
  wire [3:0] sink_mesh_out_source;
  wire [7:0] sink_mesh_out_tag;
  wire [2:0] sink_mesh_out_fragment;
  wire sink_mesh_out_last;
  wire [1:0] sink_mesh_out_vc;
  wire [FLIT_W-1:0] sink_mesh_out_data;

  reg [BEAT_W-1:0] expected_beats [0:GROUP_BEATS-1];
  integer output_beat_count = 0;
  integer input_beat_count = 0;
  integer mesh_flit_count = 0;
  integer mesh_packet_count = 0;
  integer failures = 0;
  integer encoder_clean_count = 0;
  integer decoder_clean_count = 0;
  reg bad_rst_n = 1'b0;
  reg bad_rx_desc_valid = 1'b0;
  wire bad_rx_desc_ready;
  reg [3:0] bad_rx_desc_source = 4'd5;
  reg [1:0] bad_rx_desc_vc = 2'd1;
  reg [7:0] bad_rx_desc_tag = 8'ha1;
  reg [15:0] bad_rx_desc_base = 16'h2000;
  reg [3:0] bad_rx_desc_count = 4'd2;
  reg bad_rx_flit_valid = 1'b0;
  wire bad_rx_flit_ready;
  reg [3:0] bad_rx_flit_source = 4'd5;
  reg [3:0] bad_rx_flit_destination = 4'd0;
  reg [1:0] bad_rx_flit_vc = 2'd1;
  reg [7:0] bad_rx_flit_tag = 8'ha1;
  reg [2:0] bad_rx_flit_fragment = 3'd0;
  reg bad_rx_flit_last = 1'b0;
  reg [FLIT_W-1:0] bad_rx_flit_data = 0;
  wire bad_rx_mem_write_valid;
  wire bad_rx_completion_valid;
  wire bad_protocol_error;
  reg bad_done = 1'b0;

  wire decoder_beat_valid;
  wire decoder_protocol_error;
  wire [BEAT_W-1:0] decoder_beat_data;
  wire decoder_beat_ready = ((cycle % 11) != 4) && ((cycle % 17) != 3);

  local_reducer_aggregate_stats_once_exact_encoder encoder (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(source_ctx_valid), .group_ctx_ready(source_encoder_ctx_ready),
    .group_command_id(source_command), .group_head_base(source_head),
    .beat_valid(source_beat_valid), .beat_ready(source_beat_ready),
    .beat_data(source_beat_data), .flit_valid(source_encoder_flit_valid),
    .flit_ready(source_encoder_flit_ready), .flit_data(source_encoder_flit_data),
    .flit_group_last(source_encoder_flit_group_last),
    .protocol_error(source_encoder_error)
  );

  local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
    .LOCAL_ENDPOINT_ID(5), .TX_ENABLE(1), .RX_ENABLE(0),
    .RX_WRITE_STALL_PERIOD(0)
  ) source_adapter (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(source_ctx_valid), .group_ctx_ready(source_ctx_ready),
    .group_command_id(source_command), .group_head_base(source_head),
    .group_source(source_source), .group_destination(source_destination),
    .group_vc(source_vc), .group_epoch(source_epoch),
    .codec_in_valid(source_encoder_flit_valid),
    .codec_in_ready(source_encoder_flit_ready),
    .codec_in_data(source_encoder_flit_data),
    .codec_in_group_last(source_encoder_flit_group_last),
    .tx_release_valid(source_release_valid),
    .tx_release_ready(source_release_ready),
    .codec_out_valid(), .codec_out_ready(1'b0), .codec_out_data(),
    .codec_out_group_last(), .tx_group_complete(source_group_complete),
    .rx_group_complete(), .rx_descriptor_installed(),
    .protocol_error(source_protocol_error),
    .tx_descriptor_count(source_descriptor_count), .rx_completion_count(),
    .replay_packet_count(), .max_source_occupancy(source_max_slots),
    .max_destination_occupancy(),
    .mesh_in_valid(source_mesh_in_valid), .mesh_in_ready(source_mesh_in_ready),
    .mesh_in_destination(source_mesh_in_destination),
    .mesh_in_source(source_mesh_in_source), .mesh_in_tag(source_mesh_in_tag),
    .mesh_in_fragment(source_mesh_in_fragment), .mesh_in_last(source_mesh_in_last),
    .mesh_in_vc(source_mesh_in_vc), .mesh_in_data(source_mesh_in_data),
    .mesh_out_valid(1'b0), .mesh_out_ready(source_mesh_out_ready),
    .mesh_out_destination(4'b0), .mesh_out_source(4'b0), .mesh_out_tag(8'b0),
    .mesh_out_fragment(3'b0), .mesh_out_last(1'b0), .mesh_out_vc(2'b0),
    .mesh_out_data({FLIT_W{1'b0}})
  );

  local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
    .LOCAL_ENDPOINT_ID(0), .TX_ENABLE(0), .RX_ENABLE(1),
    .RX_WRITE_STALL_PERIOD(5)
  ) sink_adapter (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(sink_ctx_valid), .group_ctx_ready(sink_ctx_ready),
    .group_command_id(sink_command), .group_head_base(sink_head),
    .group_source(sink_source), .group_destination(sink_destination),
    .group_vc(sink_vc), .group_epoch(sink_epoch),
    .codec_in_valid(1'b0), .codec_in_ready(), .codec_in_data({FLIT_W{1'b0}}),
    .codec_in_group_last(1'b0), .codec_out_valid(sink_codec_valid),
    .tx_release_valid(1'b0), .tx_release_ready(),
    .codec_out_ready(sink_codec_ready), .codec_out_data(sink_codec_data),
    .codec_out_group_last(sink_codec_group_last),
    .tx_group_complete(), .rx_group_complete(sink_group_complete),
    .rx_descriptor_installed(sink_rx_descriptor_installed),
    .protocol_error(sink_protocol_error), .tx_descriptor_count(),
    .rx_completion_count(sink_completion_count),
    .replay_packet_count(sink_replay_count),
    .max_source_occupancy(sink_max_slots),
    .max_destination_occupancy(sink_max_destination_slots),
    .mesh_in_valid(sink_mesh_in_valid), .mesh_in_ready(sink_mesh_in_ready),
    .mesh_in_destination(sink_mesh_in_destination),
    .mesh_in_source(sink_mesh_in_source), .mesh_in_tag(sink_mesh_in_tag),
    .mesh_in_fragment(sink_mesh_in_fragment), .mesh_in_last(sink_mesh_in_last),
    .mesh_in_vc(sink_mesh_in_vc), .mesh_in_data(sink_mesh_in_data),
    .mesh_out_valid(sink_mesh_out_valid), .mesh_out_ready(sink_mesh_out_ready),
    .mesh_out_destination(sink_mesh_out_destination),
    .mesh_out_source(sink_mesh_out_source), .mesh_out_tag(sink_mesh_out_tag),
    .mesh_out_fragment(sink_mesh_out_fragment), .mesh_out_last(sink_mesh_out_last),
    .mesh_out_vc(sink_mesh_out_vc), .mesh_out_data(sink_mesh_out_data)
  );

  local_reducer_aggregate_stats_once_exact_decoder decoder (
    .clk(clk), .rst_n(rst_n), .group_ctx_valid(sink_ctx_valid),
    .group_ctx_ready(sink_decoder_ctx_ready),
    .group_command_id(sink_command), .group_head_base(sink_head),
    .flit_valid(sink_codec_valid), .flit_ready(sink_codec_ready),
    .flit_data(sink_codec_data), .flit_group_last(sink_codec_group_last),
    .beat_valid(decoder_beat_valid), .beat_ready(decoder_beat_ready),
    .beat_data(decoder_beat_data), .protocol_error(decoder_protocol_error)
  );

  noc_sram_packet_endpoint #(
    .ADDR_W(16), .TX_DESC_DEPTH(1), .TX_OUTSTANDING(1), .RX_CONTEXTS(1),
    .LOCAL_ENDPOINT_ID(0)
  ) malformed_endpoint (
    .clk(clk), .rst_n(bad_rst_n),
    .tx_desc_valid(1'b0), .tx_desc_ready(), .tx_desc_destination(4'b0),
    .tx_desc_vc(2'b0), .tx_desc_tag(8'b0), .tx_desc_base_addr(16'b0),
    .tx_desc_flit_count(4'b0), .tx_mem_req_valid(), .tx_mem_req_ready(1'b0),
    .tx_mem_req_addr(), .tx_mem_rsp_valid(1'b0), .tx_mem_rsp_ready(),
    .tx_mem_rsp_data(256'b0), .tx_flit_valid(), .tx_flit_ready(1'b0),
    .tx_flit_source(), .tx_flit_destination(), .tx_flit_vc(), .tx_flit_tag(),
    .tx_flit_fragment(), .tx_flit_last(), .tx_flit_data(),
    .rx_desc_valid(bad_rx_desc_valid), .rx_desc_ready(bad_rx_desc_ready),
    .rx_desc_source(bad_rx_desc_source), .rx_desc_vc(bad_rx_desc_vc),
    .rx_desc_tag(bad_rx_desc_tag), .rx_desc_base_addr(bad_rx_desc_base),
    .rx_desc_flit_count(bad_rx_desc_count), .rx_flit_valid(bad_rx_flit_valid),
    .rx_flit_ready(bad_rx_flit_ready), .rx_flit_source(bad_rx_flit_source),
    .rx_flit_destination(bad_rx_flit_destination), .rx_flit_vc(bad_rx_flit_vc),
    .rx_flit_tag(bad_rx_flit_tag), .rx_flit_fragment(bad_rx_flit_fragment),
    .rx_flit_last(bad_rx_flit_last), .rx_flit_data(bad_rx_flit_data),
    .rx_mem_write_valid(bad_rx_mem_write_valid), .rx_mem_write_ready(1'b1),
    .rx_mem_write_addr(), .rx_mem_write_data(),
    .rx_completion_valid(bad_rx_completion_valid), .rx_completion_ready(1'b1),
    .rx_completion_source(), .rx_completion_vc(), .rx_completion_tag(),
    .protocol_error(bad_protocol_error)
  );

  noc_segmented_mesh4x4 #(
    .DATA_W(FLIT_W), .TAG_W(8), .FRAGMENT_W(3), .VC_W(2),
    .VC_COUNT(4), .FIFO_DEPTH(4)
  ) mesh (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(mesh_in_valid), .endpoint_in_ready(mesh_in_ready),
    .endpoint_in_dest(mesh_in_destination), .endpoint_in_source(mesh_in_source),
    .endpoint_in_tag(mesh_in_tag), .endpoint_in_fragment(mesh_in_fragment),
    .endpoint_in_last(mesh_in_last), .endpoint_in_vc(mesh_in_vc),
    .endpoint_in_data(mesh_in_data), .endpoint_out_valid(mesh_out_valid),
    .endpoint_out_ready(mesh_out_ready), .endpoint_out_dest(mesh_out_destination),
    .endpoint_out_source(mesh_out_source), .endpoint_out_tag(mesh_out_tag),
    .endpoint_out_fragment(mesh_out_fragment), .endpoint_out_last(mesh_out_last),
    .endpoint_out_vc(mesh_out_vc), .endpoint_out_data(mesh_out_data),
    .router_accepted_flit_count(), .router_forwarded_flit_count(),
    .router_input_stall_cycles(), .router_output_stall_cycles(),
    .router_contention_cycles(), .router_current_input_occupancy(),
    .router_max_input_occupancy(), .router_route_flit_count()
  );

  always @* begin
    mesh_in_valid = 16'b0;
    mesh_in_destination = 64'b0;
    mesh_in_source = 64'b0;
    mesh_in_tag = 128'b0;
    mesh_in_fragment = 48'b0;
    mesh_in_last = 16'b0;
    mesh_in_vc = 32'b0;
    mesh_in_data = {(16*FLIT_W){1'b0}};
    mesh_in_valid[5] = source_mesh_in_valid;
    mesh_in_destination[5*4 +: 4] = source_mesh_in_destination;
    mesh_in_source[5*4 +: 4] = source_mesh_in_source;
    mesh_in_tag[5*8 +: 8] = source_mesh_in_tag;
    mesh_in_fragment[5*3 +: 3] = source_mesh_in_fragment;
    mesh_in_last[5] = source_mesh_in_last;
    mesh_in_vc[5*2 +: 2] = source_mesh_in_vc;
    mesh_in_data[5*FLIT_W +: FLIT_W] = source_mesh_in_data;
    mesh_in_valid[0] = sink_mesh_in_valid;
    mesh_in_destination[0 +: 4] = sink_mesh_in_destination;
    mesh_in_source[0 +: 4] = sink_mesh_in_source;
    mesh_in_tag[0 +: 8] = sink_mesh_in_tag;
    mesh_in_fragment[0 +: 3] = sink_mesh_in_fragment;
    mesh_in_last[0] = sink_mesh_in_last;
    mesh_in_vc[0 +: 2] = sink_mesh_in_vc;
    mesh_in_data[0 +: FLIT_W] = sink_mesh_in_data;
  end

  assign source_mesh_in_ready = mesh_in_ready[5];
  assign sink_mesh_in_ready = mesh_in_ready[0];
  assign mesh_out_ready = 16'b0 | (16'b1 << 0) & {16{sink_mesh_out_ready}};
  assign sink_mesh_out_valid = mesh_out_valid[0];
  assign sink_mesh_out_destination = mesh_out_destination[0 +: 4];
  assign sink_mesh_out_source = mesh_out_source[0 +: 4];
  assign sink_mesh_out_tag = mesh_out_tag[0 +: 8];
  assign sink_mesh_out_fragment = mesh_out_fragment[0 +: 3];
  assign sink_mesh_out_last = mesh_out_last[0];
  assign sink_mesh_out_vc = mesh_out_vc[0 +: 2];
  assign sink_mesh_out_data = mesh_out_data[0 +: FLIT_W];

  function automatic [BEAT_W-1:0] make_beat;
    input integer index;
    reg [BEAT_W-1:0] value;
    integer head;
    integer slice;
    integer lane;
    begin
      value = {BEAT_W{1'b0}};
      head = index / 16;
      slice = index % 16;
      value[15:0] = 16'h4a20;
      value[20:16] = 8 + head;
      value[52:21] = 32'h1200_0000 + head * 32'h31;
      value[85:53] = 33'h1 + head * 33'h71;
      value[89:86] = slice[3:0];
      value[90] = (slice == 15);
      for (lane = 0; lane < 8; lane = lane + 1)
        value[91 + lane * 41 +: 41] =
          41'h10000 + index * 41'h13 + lane * 41'h7;
      make_beat = value;
    end
  endfunction

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      mesh_flit_count <= 0;
      mesh_packet_count <= 0;
      output_beat_count <= 0;
    end else begin
      cycle <= cycle + 1;
      if (source_release_valid && source_release_ready)
        source_release_valid <= 1'b0;
      else if (sink_rx_descriptor_installed)
        source_release_valid <= 1'b1;
      if (source_mesh_in_valid && source_mesh_in_ready) begin
        mesh_flit_count <= mesh_flit_count + 1;
        if (source_mesh_in_last)
          mesh_packet_count <= mesh_packet_count + 1;
      end
      if (source_beat_valid && source_beat_ready)
        input_beat_count <= input_beat_count + 1;
      if (decoder_beat_valid && decoder_beat_ready) begin
        if (decoder_beat_data !== expected_beats[output_beat_count])
          failures <= failures + 1;
        output_beat_count <= output_beat_count + 1;
      end
      if (source_group_complete)
        encoder_clean_count <= encoder_clean_count + 1;
      if (sink_group_complete)
        decoder_clean_count <= decoder_clean_count + 1;
      if (source_protocol_error || sink_protocol_error || source_encoder_error ||
          decoder_protocol_error)
        failures <= failures + 1;
    end
  end

  integer i;
  initial begin
    for (i = 0; i < GROUP_BEATS; i = i + 1)
      expected_beats[i] = make_beat(i);
    repeat (4) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    sink_ctx_valid = 1'b1;
    while (!(sink_ctx_valid && sink_ctx_ready && sink_decoder_ctx_ready))
      @(posedge clk);
    @(negedge clk);
    sink_ctx_valid = 1'b0;
    while (!sink_rx_descriptor_installed)
      @(posedge clk);

    @(negedge clk);
    source_ctx_valid = 1'b1;
    while (!(source_ctx_valid && source_ctx_ready && source_encoder_ctx_ready))
      @(posedge clk);
    @(negedge clk);
    source_ctx_valid = 1'b0;

    for (i = 0; i < GROUP_BEATS; i = i + 1) begin
      @(negedge clk);
      source_beat_data = expected_beats[i];
      source_beat_valid = 1'b1;
      while (!(source_beat_valid && source_beat_ready))
        @(posedge clk);
      @(negedge clk);
      source_beat_valid = 1'b0;
    end

    while (output_beat_count < GROUP_BEATS || decoder_clean_count < 1 ||
           source_descriptor_count < GROUP_PACKETS ||
           sink_completion_count < GROUP_PACKETS ||
           sink_replay_count < GROUP_PACKETS || !bad_done)
      @(posedge clk);

    if (failures != 0 || input_beat_count != GROUP_BEATS ||
        output_beat_count != GROUP_BEATS || mesh_flit_count != GROUP_FLITS ||
        mesh_packet_count != GROUP_PACKETS || source_descriptor_count != GROUP_PACKETS ||
        sink_completion_count != GROUP_PACKETS || sink_replay_count != GROUP_PACKETS ||
        source_max_slots != 2 || sink_max_destination_slots != 2 ||
        source_protocol_error || sink_protocol_error || source_encoder_error ||
        decoder_protocol_error || !bad_done)
      $fatal(1, "adapter roundtrip failed beats=%0d/%0d flits=%0d packets=%0d desc=%0d completions=%0d replay=%0d failures=%0d slots=%0d/%0d errors=%b/%b/%b/%b",
        input_beat_count, output_beat_count, mesh_flit_count, mesh_packet_count,
        source_descriptor_count, sink_completion_count, sink_replay_count,
        failures, source_max_slots, sink_max_destination_slots,
        source_protocol_error, sink_protocol_error, source_encoder_error,
        decoder_protocol_error);
    $display("PASS stats_once_exact_sram_packet_adapter beats=128 flits=167 packets=21 source_max_slots=%0d destination_max_slots=%0d", source_max_slots, sink_max_destination_slots);
    $finish;
  end

  initial begin
    // First prove that a flit without an installed context is consumed as a
    // protocol violation.  Then reset the endpoint and send fragment 1 first
    // under a live two-fragment context to exercise ordering enforcement.
    repeat (2) @(posedge clk);
    bad_rst_n = 1'b1;
    @(negedge clk);
    bad_rx_flit_fragment = 3'd0;
    bad_rx_flit_last = 1'b0;
    bad_rx_flit_valid = 1'b1;
    while (!(bad_rx_flit_valid && bad_rx_flit_ready)) @(posedge clk);
    @(negedge clk);
    bad_rx_flit_valid = 1'b0;
    while (!bad_protocol_error) @(posedge clk);

    bad_rst_n = 1'b0;
    repeat (2) @(posedge clk);
    bad_rst_n = 1'b1;
    @(negedge clk);
    bad_rx_desc_valid = 1'b1;
    while (!(bad_rx_desc_valid && bad_rx_desc_ready)) @(posedge clk);
    @(negedge clk);
    bad_rx_desc_valid = 1'b0;
    bad_rx_flit_fragment = 3'd1;
    bad_rx_flit_last = 1'b1;
    bad_rx_flit_valid = 1'b1;
    while (!(bad_rx_flit_valid && bad_rx_flit_ready)) @(posedge clk);
    @(negedge clk);
    bad_rx_flit_valid = 1'b0;
    while (!bad_protocol_error) @(posedge clk);
    bad_done = 1'b1;
  end

endmodule
