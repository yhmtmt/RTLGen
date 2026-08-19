`timescale 1ns/1ps

module local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer ROOT_ID = 15;
  localparam integer BEAT_W = 419;
  localparam integer FLIT_W = 256;
  localparam integer GROUP_BEATS = 128;
  localparam integer GROUP_FLITS = 167;
  localparam integer GROUP_PACKETS = 21;
  localparam integer TOTAL_BEATS = SOURCE_COUNT * GROUP_BEATS;
  localparam integer TOTAL_FLITS = SOURCE_COUNT * GROUP_FLITS;
  localparam integer TOTAL_PACKETS = SOURCE_COUNT * GROUP_PACKETS;
`ifdef SHARED_ROOT_PHYSICAL_BANKS
  localparam integer ROOT_PHYSICAL_BANKS = `SHARED_ROOT_PHYSICAL_BANKS;
`else
  localparam integer ROOT_PHYSICAL_BANKS = SOURCE_COUNT;
`endif
  localparam integer SIM_TIMEOUT_CYCLES = 4000000;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg [SOURCE_COUNT-1:0] group_ctx_valid = {SOURCE_COUNT{1'b0}};
  wire [SOURCE_COUNT-1:0] root_group_ctx_ready;
  wire [SOURCE_COUNT-1:0] tx_group_ctx_ready;
  wire [SOURCE_COUNT-1:0] encoder_group_ctx_ready;
  wire [SOURCE_COUNT-1:0] decoder_group_ctx_ready;
  reg [SOURCE_COUNT*16-1:0] group_command_id = {SOURCE_COUNT*16{1'b0}};
  reg [SOURCE_COUNT*5-1:0] group_head_base = {SOURCE_COUNT*5{1'b0}};
  reg [SOURCE_COUNT*4-1:0] group_source = {SOURCE_COUNT*4{1'b0}};
  reg [SOURCE_COUNT*4-1:0] group_destination = {SOURCE_COUNT*4{1'b0}};
  reg [SOURCE_COUNT*2-1:0] group_vc = {SOURCE_COUNT*2{1'b0}};
  reg [SOURCE_COUNT*3-1:0] group_epoch = {SOURCE_COUNT*3{1'b0}};

  reg [SOURCE_COUNT-1:0] encoder_beat_valid = {SOURCE_COUNT{1'b0}};
  wire [SOURCE_COUNT-1:0] encoder_beat_ready;
  reg [SOURCE_COUNT*BEAT_W-1:0] encoder_beat_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_valid;
  wire [SOURCE_COUNT-1:0] encoder_flit_ready;
  wire [SOURCE_COUNT*FLIT_W-1:0] encoder_flit_data;
  wire [SOURCE_COUNT-1:0] encoder_flit_group_last;
  wire [SOURCE_COUNT-1:0] encoder_error;

  wire [SOURCE_COUNT-1:0] tx_release_valid;
  wire [SOURCE_COUNT-1:0] tx_release_ready;
  wire [SOURCE_COUNT-1:0] tx_adapter_error;
  wire [SOURCE_COUNT-1:0] tx_group_complete;

  wire [SOURCE_COUNT-1:0] root_codec_valid;
  wire [SOURCE_COUNT-1:0] root_codec_ready;
  wire [SOURCE_COUNT*FLIT_W-1:0] root_codec_data;
  wire [SOURCE_COUNT-1:0] root_codec_group_last;
  wire [SOURCE_COUNT-1:0] root_group_complete;
  wire [SOURCE_COUNT-1:0] root_descriptor_installed;
  wire [SOURCE_COUNT-1:0] root_source_error;
  wire root_protocol_error;
  wire [31:0] root_accepted_flit_count;
  wire [31:0] root_descriptor_install_count;
  wire [31:0] root_completion_count;
  wire [31:0] root_replay_packet_count;
  wire [5:0] root_max_occupied_slots;

  wire [SOURCE_COUNT-1:0] decoder_beat_valid;
  reg [SOURCE_COUNT-1:0] decoder_beat_ready = {SOURCE_COUNT{1'b0}};
  wire [SOURCE_COUNT*BEAT_W-1:0] decoder_beat_data;
  wire [SOURCE_COUNT-1:0] decoder_error;

  wire [SOURCE_COUNT-1:0] source_mesh_in_valid;
  wire [SOURCE_COUNT-1:0] source_mesh_in_ready;
  wire [SOURCE_COUNT*4-1:0] source_mesh_in_destination;
  wire [SOURCE_COUNT*4-1:0] source_mesh_in_source;
  wire [SOURCE_COUNT*8-1:0] source_mesh_in_tag;
  wire [SOURCE_COUNT*3-1:0] source_mesh_in_fragment;
  wire [SOURCE_COUNT-1:0] source_mesh_in_last;
  wire [SOURCE_COUNT*2-1:0] source_mesh_in_vc;
  wire [SOURCE_COUNT*FLIT_W-1:0] source_mesh_in_data;

  wire [SOURCE_COUNT-1:0] source_mesh_out_ready;
  wire [SOURCE_COUNT-1:0] source_mesh_out_valid = {SOURCE_COUNT{1'b0}};
  wire [SOURCE_COUNT*4-1:0] source_mesh_out_destination = {SOURCE_COUNT*4{1'b0}};
  wire [SOURCE_COUNT*4-1:0] source_mesh_out_source = {SOURCE_COUNT*4{1'b0}};
  wire [SOURCE_COUNT*8-1:0] source_mesh_out_tag = {SOURCE_COUNT*8{1'b0}};
  wire [SOURCE_COUNT*3-1:0] source_mesh_out_fragment = {SOURCE_COUNT*3{1'b0}};
  wire [SOURCE_COUNT-1:0] source_mesh_out_last = {SOURCE_COUNT{1'b0}};
  wire [SOURCE_COUNT*2-1:0] source_mesh_out_vc = {SOURCE_COUNT*2{1'b0}};
  wire [SOURCE_COUNT*FLIT_W-1:0] source_mesh_out_data = {SOURCE_COUNT*FLIT_W{1'b0}};

  wire [15:0] mesh_endpoint_in_valid;
  wire [15:0] mesh_endpoint_in_ready;
  wire [16*4-1:0] mesh_endpoint_in_dest;
  wire [16*4-1:0] mesh_endpoint_in_source;
  wire [16*8-1:0] mesh_endpoint_in_tag;
  wire [16*3-1:0] mesh_endpoint_in_fragment;
  wire [15:0] mesh_endpoint_in_last;
  wire [16*2-1:0] mesh_endpoint_in_vc;
  wire [16*FLIT_W-1:0] mesh_endpoint_in_data;
  wire [15:0] mesh_endpoint_out_valid;
  wire [15:0] mesh_endpoint_out_ready;
  wire [16*4-1:0] mesh_endpoint_out_dest;
  wire [16*4-1:0] mesh_endpoint_out_source;
  wire [16*8-1:0] mesh_endpoint_out_tag;
  wire [16*3-1:0] mesh_endpoint_out_fragment;
  wire [15:0] mesh_endpoint_out_last;
  wire [16*2-1:0] mesh_endpoint_out_vc;
  wire [16*FLIT_W-1:0] mesh_endpoint_out_data;

  wire root_mesh_in_ready = 1'b1;
  wire root_mesh_out_valid = mesh_endpoint_out_valid[ROOT_ID];
  wire root_mesh_out_ready;
  wire [3:0] root_mesh_out_destination = mesh_endpoint_out_dest[ROOT_ID*4 +: 4];
  wire [3:0] root_mesh_out_source = mesh_endpoint_out_source[ROOT_ID*4 +: 4];
  wire [7:0] root_mesh_out_tag = mesh_endpoint_out_tag[ROOT_ID*8 +: 8];
  wire [2:0] root_mesh_out_fragment = mesh_endpoint_out_fragment[ROOT_ID*3 +: 3];
  wire root_mesh_out_last = mesh_endpoint_out_last[ROOT_ID];
  wire [1:0] root_mesh_out_vc = mesh_endpoint_out_vc[ROOT_ID*2 +: 2];
  wire [FLIT_W-1:0] root_mesh_out_data = mesh_endpoint_out_data[ROOT_ID*FLIT_W +: FLIT_W];

  assign mesh_endpoint_in_valid[SOURCE_COUNT-1:0] = source_mesh_in_valid;
  assign mesh_endpoint_in_valid[ROOT_ID] = 1'b0;
  assign mesh_endpoint_in_dest[SOURCE_COUNT*4-1:0] = source_mesh_in_destination;
  assign mesh_endpoint_in_dest[ROOT_ID*4 +: 4] = 4'b0;
  assign mesh_endpoint_in_source[SOURCE_COUNT*4-1:0] = source_mesh_in_source;
  assign mesh_endpoint_in_source[ROOT_ID*4 +: 4] = 4'b0;
  assign mesh_endpoint_in_tag[SOURCE_COUNT*8-1:0] = source_mesh_in_tag;
  assign mesh_endpoint_in_tag[ROOT_ID*8 +: 8] = 8'b0;
  assign mesh_endpoint_in_fragment[SOURCE_COUNT*3-1:0] = source_mesh_in_fragment;
  assign mesh_endpoint_in_fragment[ROOT_ID*3 +: 3] = 3'b0;
  assign mesh_endpoint_in_last[SOURCE_COUNT-1:0] = source_mesh_in_last;
  assign mesh_endpoint_in_last[ROOT_ID] = 1'b0;
  assign mesh_endpoint_in_vc[SOURCE_COUNT*2-1:0] = source_mesh_in_vc;
  assign mesh_endpoint_in_vc[ROOT_ID*2 +: 2] = 2'b0;
  assign mesh_endpoint_in_data[SOURCE_COUNT*FLIT_W-1:0] = source_mesh_in_data;
  assign mesh_endpoint_in_data[ROOT_ID*FLIT_W +: FLIT_W] = {FLIT_W{1'b0}};
  assign source_mesh_in_ready = mesh_endpoint_in_ready[SOURCE_COUNT-1:0];

  assign mesh_endpoint_out_ready[SOURCE_COUNT-1:0] = {SOURCE_COUNT{1'b1}};
  assign mesh_endpoint_out_ready[ROOT_ID] = root_mesh_out_ready;

  noc_segmented_mesh4x4 #(
    .DATA_W(FLIT_W), .TAG_W(8), .FRAGMENT_W(3), .VC_W(2),
    .VC_COUNT(4), .FIFO_DEPTH(4)
  ) mesh (
    .clk(clk), .rst_n(rst_n),
    .endpoint_in_valid(mesh_endpoint_in_valid),
    .endpoint_in_ready(mesh_endpoint_in_ready),
    .endpoint_in_dest(mesh_endpoint_in_dest),
    .endpoint_in_source(mesh_endpoint_in_source),
    .endpoint_in_tag(mesh_endpoint_in_tag),
    .endpoint_in_fragment(mesh_endpoint_in_fragment),
    .endpoint_in_last(mesh_endpoint_in_last),
    .endpoint_in_vc(mesh_endpoint_in_vc),
    .endpoint_in_data(mesh_endpoint_in_data),
    .endpoint_out_valid(mesh_endpoint_out_valid),
    .endpoint_out_ready(mesh_endpoint_out_ready),
    .endpoint_out_dest(mesh_endpoint_out_dest),
    .endpoint_out_source(mesh_endpoint_out_source),
    .endpoint_out_tag(mesh_endpoint_out_tag),
    .endpoint_out_fragment(mesh_endpoint_out_fragment),
    .endpoint_out_last(mesh_endpoint_out_last),
    .endpoint_out_vc(mesh_endpoint_out_vc),
    .endpoint_out_data(mesh_endpoint_out_data),
    .router_accepted_flit_count(), .router_forwarded_flit_count(),
    .router_input_stall_cycles(), .router_output_stall_cycles(),
    .router_contention_cycles(), .router_current_input_occupancy(),
    .router_max_input_occupancy(), .router_route_flit_count()
  );

  local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter #(
    .PHYSICAL_BANKS(ROOT_PHYSICAL_BANKS)
  ) root (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(group_ctx_valid), .group_ctx_ready(root_group_ctx_ready),
    .group_command_id(group_command_id), .group_head_base(group_head_base),
    .group_source(group_source), .group_destination(group_destination),
    .group_vc(group_vc), .group_epoch(group_epoch),
    .tx_release_valid(tx_release_valid), .tx_release_ready(tx_release_ready),
    .codec_out_valid(root_codec_valid), .codec_out_ready(root_codec_ready),
    .codec_out_data(root_codec_data), .codec_out_group_last(root_codec_group_last),
    .group_complete(root_group_complete),
    .descriptor_installed(root_descriptor_installed),
    .source_protocol_error(root_source_error),
    .mesh_in_valid(), .mesh_in_ready(root_mesh_in_ready),
    .mesh_in_destination(), .mesh_in_source(), .mesh_in_tag(),
    .mesh_in_fragment(), .mesh_in_last(), .mesh_in_vc(), .mesh_in_data(),
    .mesh_out_valid(root_mesh_out_valid), .mesh_out_ready(root_mesh_out_ready),
    .mesh_out_destination(root_mesh_out_destination),
    .mesh_out_source(root_mesh_out_source), .mesh_out_tag(root_mesh_out_tag),
    .mesh_out_fragment(root_mesh_out_fragment), .mesh_out_last(root_mesh_out_last),
    .mesh_out_vc(root_mesh_out_vc), .mesh_out_data(root_mesh_out_data),
    .root_accepted_flit_count(root_accepted_flit_count),
    .root_descriptor_install_count(root_descriptor_install_count),
    .root_completion_count(root_completion_count),
    .root_replay_packet_count(root_replay_packet_count),
    .max_occupied_slots(root_max_occupied_slots),
    .protocol_error(root_protocol_error)
  );

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_source
      localparam integer SOURCE_ID = source_g;
      local_reducer_aggregate_stats_once_exact_encoder encoder (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(encoder_group_ctx_ready[SOURCE_ID]),
        .group_command_id(group_command_id[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base[SOURCE_ID*5 +: 5]),
        .beat_valid(encoder_beat_valid[SOURCE_ID]),
        .beat_ready(encoder_beat_ready[SOURCE_ID]),
        .beat_data(encoder_beat_data[SOURCE_ID*BEAT_W +: BEAT_W]),
        .flit_valid(encoder_flit_valid[SOURCE_ID]),
        .flit_ready(encoder_flit_ready[SOURCE_ID]),
        .flit_data(encoder_flit_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .flit_group_last(encoder_flit_group_last[SOURCE_ID]),
        .protocol_error(encoder_error[SOURCE_ID])
      );

      local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
        .LOCAL_ENDPOINT_ID(SOURCE_ID), .TX_ENABLE(1), .RX_ENABLE(0),
        .RX_WRITE_STALL_PERIOD(0)
      ) tx_adapter (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(tx_group_ctx_ready[SOURCE_ID]),
        .group_command_id(group_command_id[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base[SOURCE_ID*5 +: 5]),
        .group_source(group_source[SOURCE_ID*4 +: 4]),
        .group_destination(group_destination[SOURCE_ID*4 +: 4]),
        .group_vc(group_vc[SOURCE_ID*2 +: 2]),
        .group_epoch(group_epoch[SOURCE_ID*3 +: 3]),
        .codec_in_valid(encoder_flit_valid[SOURCE_ID]),
        .codec_in_ready(encoder_flit_ready[SOURCE_ID]),
        .codec_in_data(encoder_flit_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .codec_in_group_last(encoder_flit_group_last[SOURCE_ID]),
        .tx_release_valid(tx_release_valid[SOURCE_ID]),
        .tx_release_ready(tx_release_ready[SOURCE_ID]),
        .codec_out_valid(), .codec_out_ready(1'b0), .codec_out_data(),
        .codec_out_group_last(), .tx_group_complete(tx_group_complete[SOURCE_ID]),
        .rx_group_complete(), .rx_descriptor_installed(),
        .protocol_error(tx_adapter_error[SOURCE_ID]),
        .tx_descriptor_count(), .rx_completion_count(), .replay_packet_count(),
        .max_source_occupancy(), .max_destination_occupancy(),
        .mesh_in_valid(source_mesh_in_valid[SOURCE_ID]),
        .mesh_in_ready(source_mesh_in_ready[SOURCE_ID]),
        .mesh_in_destination(source_mesh_in_destination[SOURCE_ID*4 +: 4]),
        .mesh_in_source(source_mesh_in_source[SOURCE_ID*4 +: 4]),
        .mesh_in_tag(source_mesh_in_tag[SOURCE_ID*8 +: 8]),
        .mesh_in_fragment(source_mesh_in_fragment[SOURCE_ID*3 +: 3]),
        .mesh_in_last(source_mesh_in_last[SOURCE_ID]),
        .mesh_in_vc(source_mesh_in_vc[SOURCE_ID*2 +: 2]),
        .mesh_in_data(source_mesh_in_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .mesh_out_valid(source_mesh_out_valid[SOURCE_ID]),
        .mesh_out_ready(source_mesh_out_ready[SOURCE_ID]),
        .mesh_out_destination(source_mesh_out_destination[SOURCE_ID*4 +: 4]),
        .mesh_out_source(source_mesh_out_source[SOURCE_ID*4 +: 4]),
        .mesh_out_tag(source_mesh_out_tag[SOURCE_ID*8 +: 8]),
        .mesh_out_fragment(source_mesh_out_fragment[SOURCE_ID*3 +: 3]),
        .mesh_out_last(source_mesh_out_last[SOURCE_ID]),
        .mesh_out_vc(source_mesh_out_vc[SOURCE_ID*2 +: 2]),
        .mesh_out_data(source_mesh_out_data[SOURCE_ID*FLIT_W +: FLIT_W])
      );

      local_reducer_aggregate_stats_once_exact_decoder decoder (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(group_ctx_valid[SOURCE_ID]),
        .group_ctx_ready(decoder_group_ctx_ready[SOURCE_ID]),
        .group_command_id(group_command_id[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base[SOURCE_ID*5 +: 5]),
        .flit_valid(root_codec_valid[SOURCE_ID]),
        .flit_ready(root_codec_ready[SOURCE_ID]),
        .flit_data(root_codec_data[SOURCE_ID*FLIT_W +: FLIT_W]),
        .flit_group_last(root_codec_group_last[SOURCE_ID]),
        .beat_valid(decoder_beat_valid[SOURCE_ID]),
        .beat_ready(decoder_beat_ready[SOURCE_ID]),
        .beat_data(decoder_beat_data[SOURCE_ID*BEAT_W +: BEAT_W]),
        .protocol_error(decoder_error[SOURCE_ID])
      );
    end
  endgenerate

  function automatic [BEAT_W-1:0] make_beat;
    input integer source_id;
    input integer beat_index;
    reg [BEAT_W-1:0] value;
    integer head;
    integer slice;
    integer lane;
    begin
      value = {BEAT_W{1'b0}};
      head = beat_index / 16;
      slice = beat_index % 16;
      value[15:0] = 16'h7000 + source_id;
      value[20:16] = 8 + head;
      value[52:21] = 32'h2200_0000 + source_id * 32'h101 + head * 32'h31;
      value[85:53] = 33'h1 + source_id * 33'h11 + head * 33'h71;
      value[89:86] = slice[3:0];
      value[90] = (slice == 15);
      for (lane = 0; lane < 8; lane = lane + 1)
        value[91 + lane * 41 +: 41] =
          41'h30000 + source_id * 41'h101 + beat_index * 41'h13 + lane * 41'h7;
      make_beat = value;
    end
  endfunction

  integer beat_index [0:SOURCE_COUNT-1];
  integer input_count [0:SOURCE_COUNT-1];
  integer output_count [0:SOURCE_COUNT-1];
  integer tx_clean_count [0:SOURCE_COUNT-1];
  integer root_clean_count [0:SOURCE_COUNT-1];
  integer failures = 0;
  integer mesh_flit_count = 0;
  integer mesh_packet_count = 0;
  integer first_root_flit_cycle = -1;
  integer last_root_flit_cycle = -1;
  reg [SOURCE_COUNT-1:0] mesh_source_mask = {SOURCE_COUNT{1'b0}};
  integer monitor_i;

  always @* begin
    for (monitor_i = 0; monitor_i < SOURCE_COUNT; monitor_i = monitor_i + 1) begin
      encoder_beat_data[monitor_i*BEAT_W +: BEAT_W] =
        make_beat(monitor_i, beat_index[monitor_i]);
      decoder_beat_ready[monitor_i] =
        ((cycle + monitor_i * 3) % 13 != 5) &&
        ((cycle + monitor_i) % 7 != 2);
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      mesh_flit_count <= 0;
      mesh_packet_count <= 0;
      first_root_flit_cycle <= -1;
      last_root_flit_cycle <= -1;
      mesh_source_mask <= {SOURCE_COUNT{1'b0}};
      for (monitor_i = 0; monitor_i < SOURCE_COUNT; monitor_i = monitor_i + 1) begin
        beat_index[monitor_i] <= 0;
        input_count[monitor_i] <= 0;
        output_count[monitor_i] <= 0;
        tx_clean_count[monitor_i] <= 0;
        root_clean_count[monitor_i] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      if (cycle >= SIM_TIMEOUT_CYCLES)
        $fatal(1, "shared root simulation timeout at cycle=%0d", cycle);
      for (monitor_i = 0; monitor_i < SOURCE_COUNT; monitor_i = monitor_i + 1) begin
        if (encoder_beat_valid[monitor_i] && encoder_beat_ready[monitor_i]) begin
          beat_index[monitor_i] <= beat_index[monitor_i] + 1;
          input_count[monitor_i] <= input_count[monitor_i] + 1;
        end
        if (decoder_beat_valid[monitor_i] && decoder_beat_ready[monitor_i]) begin
          if (decoder_beat_data[monitor_i*BEAT_W +: BEAT_W] !==
              make_beat(monitor_i, output_count[monitor_i])) begin
            failures <= failures + 1;
          end
          output_count[monitor_i] <= output_count[monitor_i] + 1;
        end
        if (tx_group_complete[monitor_i])
          tx_clean_count[monitor_i] <= tx_clean_count[monitor_i] + 1;
        if (root_group_complete[monitor_i])
          root_clean_count[monitor_i] <= root_clean_count[monitor_i] + 1;
        if (encoder_error[monitor_i] || tx_adapter_error[monitor_i] ||
            root_source_error[monitor_i] || decoder_error[monitor_i])
          failures <= failures + 1;
      end

      if (root_mesh_out_valid && root_mesh_out_ready) begin
        if (first_root_flit_cycle < 0)
          first_root_flit_cycle <= cycle;
        last_root_flit_cycle <= cycle;
        mesh_flit_count <= mesh_flit_count + 1;
        if (root_mesh_out_source < SOURCE_COUNT)
          mesh_source_mask[root_mesh_out_source] <= 1'b1;
        if (root_mesh_out_last)
          mesh_packet_count <= mesh_packet_count + 1;
      end
    end
  end

  function automatic integer all_sources_complete;
    integer complete_i;
    begin
      all_sources_complete = 1;
      for (complete_i = 0; complete_i < SOURCE_COUNT; complete_i = complete_i + 1)
        if (input_count[complete_i] != GROUP_BEATS ||
            output_count[complete_i] != GROUP_BEATS ||
            tx_clean_count[complete_i] != 1 ||
            root_clean_count[complete_i] != 1)
          all_sources_complete = 0;
    end
  endfunction

  integer setup_i;
  initial begin
    for (setup_i = 0; setup_i < SOURCE_COUNT; setup_i = setup_i + 1) begin
      group_command_id[setup_i*16 +: 16] = 16'h7000 + setup_i;
      group_head_base[setup_i*5 +: 5] = 5'd8;
      group_source[setup_i*4 +: 4] = setup_i[3:0];
      group_destination[setup_i*4 +: 4] = ROOT_ID[3:0];
      group_vc[setup_i*2 +: 2] = 2'd2;
      group_epoch[setup_i*3 +: 3] = (setup_i + 1) % 8;
      beat_index[setup_i] = 0;
    end
    repeat (5) @(posedge clk);
    rst_n = 1'b1;

    // Wait for all four consumers to be able to accept a context before
    // asserting it.  This makes the context handshake atomic across the
    // source encoder, source TX adapter, shared root, and exact decoder.
    for (setup_i = 0; setup_i < SOURCE_COUNT; setup_i = setup_i + 1) begin
      while (!(root_group_ctx_ready[setup_i] &&
               tx_group_ctx_ready[setup_i] &&
               encoder_group_ctx_ready[setup_i] &&
               decoder_group_ctx_ready[setup_i])) @(posedge clk);
      @(negedge clk);
      group_ctx_valid[setup_i] = 1'b1;
      @(posedge clk);
      while (!(root_group_ctx_ready[setup_i] &&
               tx_group_ctx_ready[setup_i] &&
               encoder_group_ctx_ready[setup_i] &&
               decoder_group_ctx_ready[setup_i])) @(posedge clk);
      @(negedge clk);
      group_ctx_valid[setup_i] = 1'b0;
    end

    @(negedge clk);
    encoder_beat_valid = {SOURCE_COUNT{1'b1}};
    while (root_descriptor_install_count < TOTAL_PACKETS ||
           root_completion_count < TOTAL_PACKETS ||
           root_replay_packet_count < TOTAL_PACKETS ||
           mesh_flit_count < TOTAL_FLITS || !all_sources_complete())
      @(posedge clk);
    repeat (20) @(posedge clk);
    encoder_beat_valid = {SOURCE_COUNT{1'b0}};

    for (setup_i = 0; setup_i < SOURCE_COUNT; setup_i = setup_i + 1) begin
      if (input_count[setup_i] != GROUP_BEATS ||
          output_count[setup_i] != GROUP_BEATS ||
          tx_clean_count[setup_i] != 1 || root_clean_count[setup_i] != 1)
        failures = failures + 1;
    end
    if (failures != 0 || mesh_flit_count != TOTAL_FLITS ||
        mesh_packet_count != TOTAL_PACKETS ||
        root_accepted_flit_count != TOTAL_FLITS ||
        root_descriptor_install_count != TOTAL_PACKETS ||
        root_completion_count != TOTAL_PACKETS ||
        root_replay_packet_count != TOTAL_PACKETS ||
        (last_root_flit_cycle - first_root_flit_cycle + 1) < TOTAL_FLITS ||
        mesh_source_mask != {SOURCE_COUNT{1'b1}} || root_protocol_error ||
        (|encoder_error) || (|tx_adapter_error) || (|root_source_error) ||
        (|decoder_error) || root_max_occupied_slots == 0) begin
      $fatal(1, "shared root failed beats=%0d/%0d flits=%0d/%0d packets=%0d/%0d desc=%0d comp=%0d replay=%0d max_slots=%0d failures=%0d mask=%h errors=%b/%b/%b/%b/%b",
        input_count[0], TOTAL_BEATS, mesh_flit_count, TOTAL_FLITS,
        mesh_packet_count, TOTAL_PACKETS, root_descriptor_install_count,
        root_completion_count, root_replay_packet_count,
        root_max_occupied_slots, failures, mesh_source_mask, root_protocol_error,
        |encoder_error, |tx_adapter_error, |root_source_error, |decoder_error);
    end
    $display("PASS shared_root_stats_once sources=15 beats=%0d flits=%0d packets=%0d descriptors=%0d completions=%0d replays=%0d root_delivery_span=%0d max_occupied_slots=%0d source_mask=%h",
      TOTAL_BEATS, mesh_flit_count, mesh_packet_count,
      root_descriptor_install_count, root_completion_count,
      root_replay_packet_count,
      last_root_flit_cycle - first_root_flit_cycle + 1,
      root_max_occupied_slots, mesh_source_mask);
    $finish;
  end
endmodule
