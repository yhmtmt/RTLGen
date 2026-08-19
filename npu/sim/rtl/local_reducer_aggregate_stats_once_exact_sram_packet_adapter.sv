`timescale 1ns/1ps

// One-read/one-write 16x256 packet SRAM with a registered, backpressured read
// response.  The array has no reset and is kept in a dedicated module so
// synthesis retains a memory boundary instead of expanding packet payloads
// into resettable state registers.
module local_reducer_aggregate_stats_once_exact_packet_sram #(
  parameter integer DATA_W = 256,
  parameter integer ADDR_W = 4
) (
  input wire clk,
  input wire rst_n,
  input wire write_valid,
  input wire [ADDR_W-1:0] write_addr,
  input wire [DATA_W-1:0] write_data,
  input wire read_req_valid,
  output wire read_req_ready,
  input wire [ADDR_W-1:0] read_req_addr,
  output wire read_rsp_valid,
  input wire read_rsp_ready,
  output wire [ADDR_W-1:0] read_rsp_addr,
  output wire [DATA_W-1:0] read_rsp_data
);
  reg [DATA_W-1:0] mem [0:(1 << ADDR_W)-1];
  reg read_rsp_valid_q;
  reg [ADDR_W-1:0] read_rsp_addr_q;
  reg [DATA_W-1:0] read_rsp_data_q;

  assign read_req_ready = !read_rsp_valid_q || read_rsp_ready;
  assign read_rsp_valid = read_rsp_valid_q;
  assign read_rsp_addr = read_rsp_addr_q;
  assign read_rsp_data = read_rsp_data_q;

  always @(posedge clk) begin
    if (write_valid)
      mem[write_addr] <= write_data;
    if (read_req_valid && read_req_ready) begin
      read_rsp_addr_q <= read_req_addr;
      read_rsp_data_q <= mem[read_req_addr];
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      read_rsp_valid_q <= 1'b0;
    end else if (read_req_valid && read_req_ready) begin
      read_rsp_valid_q <= 1'b1;
    end else if (read_rsp_valid_q && read_rsp_ready) begin
      read_rsp_valid_q <= 1'b0;
    end
  end
endmodule

// Finite SRAM adapter for one exact stats-once group.  The packet framer and
// deframer retain the wire contract; this block owns only two source and two
// destination packet slots and the endpoint memory handshakes around them.
module local_reducer_aggregate_stats_once_exact_sram_packet_adapter #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer ENDPOINT_W = 4,
  parameter integer ADDR_W = 16,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer LOCAL_ENDPOINT_ID = 0,
  parameter integer TX_ENABLE = 1,
  parameter integer RX_ENABLE = 1,
  parameter integer SRC_BASE_ADDR = 0,
  parameter integer DST_BASE_ADDR = 4096,
  parameter integer RX_WRITE_STALL_PERIOD = 0
) (
  input wire clk,
  input wire rst_n,

  input wire group_ctx_valid,
  output wire group_ctx_ready,
  input wire [15:0] group_command_id,
  input wire [4:0] group_head_base,
  input wire [3:0] group_source,
  input wire [3:0] group_destination,
  input wire [VC_W-1:0] group_vc,
  input wire [2:0] group_epoch,

  input wire codec_in_valid,
  output wire codec_in_ready,
  input wire [DATA_W-1:0] codec_in_data,
  input wire codec_in_group_last,
  input wire tx_release_valid,
  output wire tx_release_ready,
  output wire codec_out_valid,
  input wire codec_out_ready,
  output wire [DATA_W-1:0] codec_out_data,
  output wire codec_out_group_last,

  output wire tx_group_complete,
  output wire rx_group_complete,
  output wire rx_descriptor_installed,
  output wire protocol_error,
  output reg [31:0] tx_descriptor_count,
  output reg [31:0] rx_completion_count,
  output reg [31:0] replay_packet_count,
  output reg [2:0] max_source_occupancy,
  output reg [2:0] max_destination_occupancy,

  output wire mesh_in_valid,
  input wire mesh_in_ready,
  output wire [ENDPOINT_W-1:0] mesh_in_destination,
  output wire [ENDPOINT_W-1:0] mesh_in_source,
  output wire [TAG_W-1:0] mesh_in_tag,
  output wire [FRAGMENT_W-1:0] mesh_in_fragment,
  output wire mesh_in_last,
  output wire [VC_W-1:0] mesh_in_vc,
  output wire [DATA_W-1:0] mesh_in_data,

  input wire mesh_out_valid,
  output wire mesh_out_ready,
  input wire [ENDPOINT_W-1:0] mesh_out_destination,
  input wire [ENDPOINT_W-1:0] mesh_out_source,
  input wire [TAG_W-1:0] mesh_out_tag,
  input wire [FRAGMENT_W-1:0] mesh_out_fragment,
  input wire mesh_out_last,
  input wire [VC_W-1:0] mesh_out_vc,
  input wire [DATA_W-1:0] mesh_out_data
);
  localparam integer SLOT_COUNT = 2;
  localparam integer SLOT_WORDS = 8;
  localparam integer DATA_BYTES = DATA_W / 8;
  localparam integer SLOT_BYTES = SLOT_WORDS * DATA_BYTES;
  localparam integer WORD_INDEX_W = 3;
  localparam integer RX_STALL_MOD =
    (RX_WRITE_STALL_PERIOD < 1) ? 1 : RX_WRITE_STALL_PERIOD;
  localparam [ADDR_W-1:0] SRC_SLOT0_BASE = SRC_BASE_ADDR;
  localparam [ADDR_W-1:0] SRC_SLOT1_BASE = SRC_BASE_ADDR + SLOT_BYTES;
  localparam [ADDR_W-1:0] DST_SLOT0_BASE = DST_BASE_ADDR;
  localparam [ADDR_W-1:0] DST_SLOT1_BASE = DST_BASE_ADDR + SLOT_BYTES;

  localparam [1:0] SLOT_FREE = 2'd0;
  localparam [1:0] SLOT_FILL = 2'd1;
  localparam [1:0] SLOT_READY = 2'd2;
  localparam [1:0] SLOT_IN_FLIGHT = 2'd3;
  localparam [2:0] DST_RESERVED = 3'd1;
  localparam [2:0] DST_ACTIVE = 3'd2;
  localparam [2:0] DST_COMPLETE = 3'd3;
  localparam [2:0] DST_REPLAY = 3'd4;

  wire tx_framer_ctx_ready;
  wire tx_framer_codec_ready;
  wire tx_framer_flit_valid;
  wire tx_framer_flit_ready;
  wire [DATA_W-1:0] tx_framer_flit_data;
  wire [ENDPOINT_W-1:0] tx_framer_destination;
  wire [ENDPOINT_W-1:0] tx_framer_source;
  wire [TAG_W-1:0] tx_framer_tag;
  wire [FRAGMENT_W-1:0] tx_framer_fragment;
  wire tx_framer_last;
  wire [VC_W-1:0] tx_framer_vc;
  wire tx_framer_clean;
  wire tx_framer_error;

  wire rx_deframer_ctx_ready;
  wire rx_deframer_flit_ready;
  wire rx_deframer_clean;
  wire rx_deframer_error;

  reg tx_group_active_q;
  reg [3:0] tx_group_source_q;
  reg [3:0] tx_group_destination_q;
  reg [VC_W-1:0] tx_group_vc_q;
  reg [2:0] tx_group_epoch_q;
  reg tx_fill_active_q;
  reg tx_fill_slot_q;
  reg [3:0] tx_fill_word_q;
  reg tx_desc_pending_q;
  reg tx_desc_slot_q;
  reg [ENDPOINT_W-1:0] tx_desc_destination_q;
  reg [VC_W-1:0] tx_desc_vc_q;
  reg [TAG_W-1:0] tx_desc_tag_q;
  reg [FLIT_COUNT_W-1:0] tx_desc_count_q;
  reg [4:0] tx_packet_index_q;
  reg tx_wait_fill_q;
  reg tx_wait_slot_q;
  reg [1:0] src_slot_state [0:SLOT_COUNT-1];
  reg [FLIT_COUNT_W-1:0] src_expected_count [0:SLOT_COUNT-1];
  reg [FLIT_COUNT_W-1:0] src_req_count [0:SLOT_COUNT-1];
  reg [FLIT_COUNT_W-1:0] src_rsp_count [0:SLOT_COUNT-1];
  reg source_error_q;

  reg rx_group_active_q;
  reg [3:0] rx_group_source_q;
  reg [3:0] rx_group_destination_q;
  reg [VC_W-1:0] rx_group_vc_q;
  reg [2:0] rx_group_epoch_q;
  reg rx_desc_pending_q;
  reg rx_desc_slot_q;
  reg [4:0] rx_desc_packet_q;
  reg rx_active_q;
  reg rx_active_slot_q;
  reg [4:0] rx_active_packet_q;
  reg rx_wait_next_desc_q;
  reg rx_wait_slot_q;
  reg [4:0] rx_wait_packet_q;
  reg [2:0] dst_slot_state [0:SLOT_COUNT-1];
  reg [4:0] dst_slot_packet [0:SLOT_COUNT-1];
  reg [ENDPOINT_W-1:0] dst_slot_source [0:SLOT_COUNT-1];
  reg [ENDPOINT_W-1:0] dst_slot_destination [0:SLOT_COUNT-1];
  reg [VC_W-1:0] dst_slot_vc [0:SLOT_COUNT-1];
  reg [TAG_W-1:0] dst_slot_tag [0:SLOT_COUNT-1];
  reg [FLIT_COUNT_W-1:0] dst_slot_count [0:SLOT_COUNT-1];
  reg [31:0] rx_write_cycle_q;
  reg rx_descriptor_installed_q;
  reg destination_error_q;
  reg replay_active_q;
  reg replay_slot_q;
  reg [3:0] replay_word_q;
  reg [4:0] replay_next_packet_q;

  wire src_mem_read_req_ready;
  wire src_mem_read_rsp_valid;
  wire [3:0] src_mem_read_rsp_addr;
  wire [DATA_W-1:0] src_mem_read_rsp_data;
  wire dst_mem_read_req_ready;
  wire dst_mem_read_rsp_valid;
  wire [3:0] dst_mem_read_rsp_addr;
  wire [DATA_W-1:0] dst_mem_read_rsp_data;

  wire [1:0] src_occupied_count =
    (src_slot_state[0] != SLOT_FREE) + (src_slot_state[1] != SLOT_FREE);
  wire [1:0] dst_occupied_count =
    (dst_slot_state[0] != 3'd0) + (dst_slot_state[1] != 3'd0);
  wire src_all_free = (src_occupied_count == 0);
  wire dst_all_free = (dst_occupied_count == 0);
  wire tx_ctx_fire = group_ctx_valid && group_ctx_ready && (TX_ENABLE != 0);
  wire rx_ctx_fire = group_ctx_valid && group_ctx_ready && (RX_ENABLE != 0);

  assign group_ctx_ready =
    ((TX_ENABLE == 0) ||
     (tx_framer_ctx_ready && !tx_group_active_q && src_all_free &&
      !tx_desc_pending_q)) &&
    ((RX_ENABLE == 0) ||
     (rx_deframer_ctx_ready && !rx_group_active_q && dst_all_free &&
      !rx_desc_pending_q));

  local_reducer_aggregate_stats_once_exact_packet_tx_framer tx_framer (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(tx_ctx_fire),
    .group_ctx_ready(tx_framer_ctx_ready),
    .group_command_id(group_command_id), .group_head_base(group_head_base),
    .group_source(group_source), .group_destination(group_destination),
    .group_vc(group_vc), .group_epoch(group_epoch),
    .codec_flit_valid(codec_in_valid && (TX_ENABLE != 0)),
    .codec_flit_ready(tx_framer_codec_ready), .codec_flit_data(codec_in_data),
    .codec_flit_group_last(codec_in_group_last),
    .mesh_flit_valid(tx_framer_flit_valid),
    .mesh_flit_ready(tx_framer_flit_ready),
    .mesh_flit_destination(tx_framer_destination),
    .mesh_flit_source(tx_framer_source), .mesh_flit_tag(tx_framer_tag),
    .mesh_flit_fragment(tx_framer_fragment), .mesh_flit_last(tx_framer_last),
    .mesh_flit_vc(tx_framer_vc), .mesh_flit_data(tx_framer_flit_data),
    .clean_group_complete(tx_framer_clean),
    .protocol_error(tx_framer_error)
  );

  local_reducer_aggregate_stats_once_exact_packet_rx_deframer rx_deframer (
    .clk(clk), .rst_n(rst_n),
    .group_ctx_valid(rx_ctx_fire),
    .group_ctx_ready(rx_deframer_ctx_ready),
    .group_command_id(group_command_id), .group_head_base(group_head_base),
    .group_source(group_source), .group_destination(group_destination),
    .group_vc(group_vc), .group_epoch(group_epoch),
    .mesh_flit_valid(dst_mem_read_rsp_valid && (RX_ENABLE != 0)),
    .mesh_flit_ready(rx_deframer_flit_ready),
    .mesh_flit_destination(dst_slot_destination[dst_mem_read_rsp_addr[3]]),
    .mesh_flit_source(dst_slot_source[dst_mem_read_rsp_addr[3]]),
    .mesh_flit_tag(dst_slot_tag[dst_mem_read_rsp_addr[3]]),
    .mesh_flit_fragment(dst_mem_read_rsp_addr[FRAGMENT_W-1:0]),
    .mesh_flit_last(dst_mem_read_rsp_addr[WORD_INDEX_W-1:0] + 1'b1 ==
                    dst_slot_count[dst_mem_read_rsp_addr[3]]),
    .mesh_flit_vc(dst_slot_vc[dst_mem_read_rsp_addr[3]]),
    .mesh_flit_data(dst_mem_read_rsp_data),
    .codec_flit_valid(codec_out_valid), .codec_flit_ready(codec_out_ready),
    .codec_flit_data(codec_out_data),
    .codec_flit_group_last(codec_out_group_last),
    .codec_group_command_id(), .codec_group_head_base(),
    .protocol_error(rx_deframer_error),
    .clean_group_complete(rx_deframer_clean)
  );

  assign codec_in_ready = (TX_ENABLE != 0) && tx_framer_codec_ready;
  assign tx_framer_flit_ready =
    (TX_ENABLE != 0) && tx_fill_active_q && !tx_desc_pending_q &&
    (src_slot_state[tx_fill_slot_q] == SLOT_FILL) &&
    (tx_fill_word_q < 4'd8);

  wire ep_tx_desc_valid = tx_desc_pending_q && tx_release_valid &&
    (TX_ENABLE != 0);
  wire ep_tx_desc_ready;
  wire [ENDPOINT_W-1:0] ep_tx_desc_destination = tx_desc_destination_q;
  wire [VC_W-1:0] ep_tx_desc_vc = tx_desc_vc_q;
  wire [TAG_W-1:0] ep_tx_desc_tag = tx_desc_tag_q;
  wire [ADDR_W-1:0] ep_tx_desc_base_addr =
    tx_desc_slot_q ? SRC_SLOT1_BASE : SRC_SLOT0_BASE;
  wire [FLIT_COUNT_W-1:0] ep_tx_desc_flit_count = tx_desc_count_q;
  wire ep_tx_desc_fire = ep_tx_desc_valid && ep_tx_desc_ready;
  assign tx_release_ready = (TX_ENABLE != 0) && tx_desc_pending_q &&
    ep_tx_desc_ready;

  wire ep_tx_mem_req_valid;
  wire ep_tx_mem_req_ready;
  wire [ADDR_W-1:0] ep_tx_mem_req_addr;
  wire ep_tx_mem_rsp_valid;
  wire ep_tx_mem_rsp_ready;
  wire [DATA_W-1:0] ep_tx_mem_rsp_data;
  wire ep_tx_flit_valid;
  wire ep_tx_flit_ready = mesh_in_ready;
  wire [ENDPOINT_W-1:0] ep_tx_flit_source;
  wire [ENDPOINT_W-1:0] ep_tx_flit_destination;
  wire [VC_W-1:0] ep_tx_flit_vc;
  wire [TAG_W-1:0] ep_tx_flit_tag;
  wire [FRAGMENT_W-1:0] ep_tx_flit_fragment;
  wire ep_tx_flit_last;
  wire [DATA_W-1:0] ep_tx_flit_data;

  wire ep_rx_desc_valid = rx_desc_pending_q && (RX_ENABLE != 0);
  wire ep_rx_desc_ready;
  wire [ENDPOINT_W-1:0] ep_rx_desc_source = rx_group_source_q;
  wire [VC_W-1:0] ep_rx_desc_vc = rx_group_vc_q;
  wire [TAG_W-1:0] ep_rx_desc_tag =
    {rx_group_epoch_q, rx_desc_packet_q};
  wire [ADDR_W-1:0] ep_rx_desc_base_addr =
    rx_desc_slot_q ? DST_SLOT1_BASE : DST_SLOT0_BASE;
  wire [FLIT_COUNT_W-1:0] ep_rx_desc_flit_count =
    (rx_desc_packet_q == 5'd20) ? 4'd7 : 4'd8;
  wire ep_rx_desc_fire = ep_rx_desc_valid && ep_rx_desc_ready;

  wire ep_rx_mem_write_valid;
  wire ep_rx_mem_write_ready;
  wire [ADDR_W-1:0] ep_rx_mem_write_addr;
  wire [DATA_W-1:0] ep_rx_mem_write_data;
  wire ep_rx_flit_ready;
  wire ep_rx_completion_valid;
  wire ep_rx_completion_ready;
  wire [ENDPOINT_W-1:0] ep_rx_completion_source;
  wire [VC_W-1:0] ep_rx_completion_vc;
  wire [TAG_W-1:0] ep_rx_completion_tag;
  wire ep_protocol_error;

  noc_sram_packet_endpoint #(
    .DATA_W(DATA_W), .ENDPOINT_W(ENDPOINT_W), .VC_W(VC_W), .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W), .ADDR_W(ADDR_W), .FLIT_COUNT_W(FLIT_COUNT_W),
    .TX_DESC_DEPTH(2), .TX_OUTSTANDING(1), .RX_CONTEXTS(1),
    .LOCAL_ENDPOINT_ID(LOCAL_ENDPOINT_ID)
  ) endpoint (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(ep_tx_desc_valid), .tx_desc_ready(ep_tx_desc_ready),
    .tx_desc_destination(ep_tx_desc_destination), .tx_desc_vc(ep_tx_desc_vc),
    .tx_desc_tag(ep_tx_desc_tag), .tx_desc_base_addr(ep_tx_desc_base_addr),
    .tx_desc_flit_count(ep_tx_desc_flit_count),
    .tx_mem_req_valid(ep_tx_mem_req_valid),
    .tx_mem_req_ready(ep_tx_mem_req_ready), .tx_mem_req_addr(ep_tx_mem_req_addr),
    .tx_mem_rsp_valid(ep_tx_mem_rsp_valid), .tx_mem_rsp_ready(ep_tx_mem_rsp_ready),
    .tx_mem_rsp_data(ep_tx_mem_rsp_data), .tx_flit_valid(ep_tx_flit_valid),
    .tx_flit_ready(ep_tx_flit_ready), .tx_flit_source(ep_tx_flit_source),
    .tx_flit_destination(ep_tx_flit_destination), .tx_flit_vc(ep_tx_flit_vc),
    .tx_flit_tag(ep_tx_flit_tag), .tx_flit_fragment(ep_tx_flit_fragment),
    .tx_flit_last(ep_tx_flit_last), .tx_flit_data(ep_tx_flit_data),
    .rx_desc_valid(ep_rx_desc_valid), .rx_desc_ready(ep_rx_desc_ready),
    .rx_desc_source(ep_rx_desc_source), .rx_desc_vc(ep_rx_desc_vc),
    .rx_desc_tag(ep_rx_desc_tag), .rx_desc_base_addr(ep_rx_desc_base_addr),
    .rx_desc_flit_count(ep_rx_desc_flit_count), .rx_flit_valid(mesh_out_valid),
    .rx_flit_ready(ep_rx_flit_ready), .rx_flit_source(mesh_out_source),
    .rx_flit_destination(mesh_out_destination), .rx_flit_vc(mesh_out_vc),
    .rx_flit_tag(mesh_out_tag), .rx_flit_fragment(mesh_out_fragment),
    .rx_flit_last(mesh_out_last), .rx_flit_data(mesh_out_data),
    .rx_mem_write_valid(ep_rx_mem_write_valid),
    .rx_mem_write_ready(ep_rx_mem_write_ready),
    .rx_mem_write_addr(ep_rx_mem_write_addr),
    .rx_mem_write_data(ep_rx_mem_write_data),
    .rx_completion_valid(ep_rx_completion_valid),
    .rx_completion_ready(ep_rx_completion_ready),
    .rx_completion_source(ep_rx_completion_source),
    .rx_completion_vc(ep_rx_completion_vc),
    .rx_completion_tag(ep_rx_completion_tag),
    .protocol_error(ep_protocol_error)
  );

  assign mesh_in_valid = ep_tx_flit_valid && (TX_ENABLE != 0);
  assign mesh_in_destination = ep_tx_flit_destination;
  assign mesh_in_source = ep_tx_flit_source;
  assign mesh_in_tag = ep_tx_flit_tag;
  assign mesh_in_fragment = ep_tx_flit_fragment;
  assign mesh_in_last = ep_tx_flit_last;
  assign mesh_in_vc = ep_tx_flit_vc;
  assign mesh_in_data = ep_tx_flit_data;
  assign mesh_out_ready = ep_rx_flit_ready;

  assign ep_tx_mem_req_ready = (TX_ENABLE != 0) && src_mem_read_req_ready;
  assign ep_tx_mem_rsp_valid = src_mem_read_rsp_valid && (TX_ENABLE != 0);
  assign ep_tx_mem_rsp_data = src_mem_read_rsp_data;
  wire ep_tx_mem_req_fire = ep_tx_mem_req_valid && ep_tx_mem_req_ready;
  wire ep_tx_mem_rsp_fire = ep_tx_mem_rsp_valid && ep_tx_mem_rsp_ready;

  integer tx_addr_slot_i;
  integer tx_addr_word_i;
  reg tx_addr_valid_r;
  always @* begin
    tx_addr_valid_r = 1'b0;
    tx_addr_slot_i = 0;
    tx_addr_word_i = 0;
    if ((ep_tx_mem_req_addr >= SRC_SLOT0_BASE) &&
        (ep_tx_mem_req_addr < SRC_SLOT1_BASE)) begin
      tx_addr_valid_r = 1'b1;
      tx_addr_slot_i = 0;
      tx_addr_word_i = (ep_tx_mem_req_addr - SRC_SLOT0_BASE) / DATA_BYTES;
    end else if ((ep_tx_mem_req_addr >= SRC_SLOT1_BASE) &&
                 (ep_tx_mem_req_addr < SRC_SLOT1_BASE + SLOT_BYTES)) begin
      tx_addr_valid_r = 1'b1;
      tx_addr_slot_i = 1;
      tx_addr_word_i =
        (ep_tx_mem_req_addr - SRC_SLOT1_BASE) / DATA_BYTES;
    end
  end

  integer rx_addr_slot_i;
  integer rx_addr_word_i;
  reg rx_addr_valid_r;
  always @* begin
    rx_addr_valid_r = 1'b0;
    rx_addr_slot_i = 0;
    rx_addr_word_i = 0;
    if ((ep_rx_mem_write_addr >= DST_SLOT0_BASE) &&
        (ep_rx_mem_write_addr < DST_SLOT1_BASE)) begin
      rx_addr_valid_r = 1'b1;
      rx_addr_slot_i = 0;
      rx_addr_word_i = (ep_rx_mem_write_addr - DST_SLOT0_BASE) / DATA_BYTES;
    end else if ((ep_rx_mem_write_addr >= DST_SLOT1_BASE) &&
                 (ep_rx_mem_write_addr < DST_SLOT1_BASE + SLOT_BYTES)) begin
      rx_addr_valid_r = 1'b1;
      rx_addr_slot_i = 1;
      rx_addr_word_i =
        (ep_rx_mem_write_addr - DST_SLOT1_BASE) / DATA_BYTES;
    end
  end

  wire rx_write_stall = (RX_WRITE_STALL_PERIOD != 0) &&
    ((rx_write_cycle_q % RX_STALL_MOD) == 0);
  assign ep_rx_mem_write_ready = (RX_ENABLE != 0) && !rx_write_stall;
  assign ep_rx_completion_ready = (RX_ENABLE != 0) && rx_active_q;
  wire ep_rx_mem_write_fire =
    ep_rx_mem_write_valid && ep_rx_mem_write_ready;
  wire ep_rx_completion_fire =
    ep_rx_completion_valid && ep_rx_completion_ready;
  assign rx_descriptor_installed = rx_descriptor_installed_q;
  assign tx_group_complete = tx_framer_clean;
  assign rx_group_complete = rx_deframer_clean;
  assign protocol_error = tx_framer_error || rx_deframer_error ||
    ep_protocol_error || source_error_q || destination_error_q;

  integer reset_i;
  integer replay_found_i;
  reg replay_found_r;
  reg replay_found_slot_r;
  wire replay_issue_available = replay_active_q &&
    (replay_word_q < dst_slot_count[replay_slot_q]);
  wire [3:0] src_fill_mem_addr =
    {tx_fill_slot_q, tx_fill_word_q[WORD_INDEX_W-1:0]};
  wire [3:0] src_read_mem_addr =
    {tx_addr_slot_i[0], tx_addr_word_i[WORD_INDEX_W-1:0]};
  wire [3:0] dst_write_mem_addr =
    {rx_addr_slot_i[0], rx_addr_word_i[WORD_INDEX_W-1:0]};
  wire [3:0] dst_read_mem_addr =
    {replay_slot_q, replay_word_q[WORD_INDEX_W-1:0]};
  wire dst_mem_read_req_valid = replay_issue_available && (RX_ENABLE != 0);
  wire dst_mem_read_req_fire = dst_mem_read_req_valid &&
    dst_mem_read_req_ready;
  wire dst_mem_read_rsp_fire = dst_mem_read_rsp_valid &&
    rx_deframer_flit_ready;

  local_reducer_aggregate_stats_once_exact_packet_sram #(
    .DATA_W(DATA_W), .ADDR_W(4)
  ) source_packet_sram (
    .clk(clk), .rst_n(rst_n),
    .write_valid(tx_framer_flit_valid && tx_framer_flit_ready),
    .write_addr(src_fill_mem_addr), .write_data(tx_framer_flit_data),
    .read_req_valid(ep_tx_mem_req_valid && (TX_ENABLE != 0)),
    .read_req_ready(src_mem_read_req_ready),
    .read_req_addr(src_read_mem_addr),
    .read_rsp_valid(src_mem_read_rsp_valid),
    .read_rsp_ready(ep_tx_mem_rsp_ready && (TX_ENABLE != 0)),
    .read_rsp_addr(src_mem_read_rsp_addr),
    .read_rsp_data(src_mem_read_rsp_data)
  );

  local_reducer_aggregate_stats_once_exact_packet_sram #(
    .DATA_W(DATA_W), .ADDR_W(4)
  ) destination_packet_sram (
    .clk(clk), .rst_n(rst_n), .write_valid(ep_rx_mem_write_fire),
    .write_addr(dst_write_mem_addr), .write_data(ep_rx_mem_write_data),
    .read_req_valid(dst_mem_read_req_valid),
    .read_req_ready(dst_mem_read_req_ready),
    .read_req_addr(dst_read_mem_addr),
    .read_rsp_valid(dst_mem_read_rsp_valid),
    .read_rsp_ready(rx_deframer_flit_ready),
    .read_rsp_addr(dst_mem_read_rsp_addr),
    .read_rsp_data(dst_mem_read_rsp_data)
  );
  always @* begin
    replay_found_r = 1'b0;
    replay_found_slot_r = 1'b0;
    for (replay_found_i = 0; replay_found_i < SLOT_COUNT; replay_found_i = replay_found_i + 1) begin
      if (!replay_found_r &&
          (dst_slot_state[replay_found_i] == DST_COMPLETE) &&
          (dst_slot_packet[replay_found_i] == replay_next_packet_q)) begin
        replay_found_r = 1'b1;
        replay_found_slot_r = replay_found_i[0:0];
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tx_group_active_q <= 1'b0;
      tx_group_source_q <= 0;
      tx_group_destination_q <= 0;
      tx_group_vc_q <= 0;
      tx_group_epoch_q <= 0;
      tx_fill_active_q <= 1'b0;
      tx_fill_slot_q <= 1'b0;
      tx_fill_word_q <= 4'd0;
      tx_desc_pending_q <= 1'b0;
      tx_desc_slot_q <= 1'b0;
      tx_desc_destination_q <= 0;
      tx_desc_vc_q <= 0;
      tx_desc_tag_q <= 0;
      tx_desc_count_q <= 0;
      tx_packet_index_q <= 0;
      tx_wait_fill_q <= 1'b0;
      tx_wait_slot_q <= 1'b0;
      source_error_q <= 1'b0;
      rx_group_active_q <= 1'b0;
      rx_group_source_q <= 0;
      rx_group_destination_q <= 0;
      rx_group_vc_q <= 0;
      rx_group_epoch_q <= 0;
      rx_desc_pending_q <= 1'b0;
      rx_desc_slot_q <= 1'b0;
      rx_desc_packet_q <= 0;
      rx_active_q <= 1'b0;
      rx_active_slot_q <= 1'b0;
      rx_active_packet_q <= 0;
      rx_wait_next_desc_q <= 1'b0;
      rx_wait_slot_q <= 1'b0;
      rx_wait_packet_q <= 0;
      rx_write_cycle_q <= 0;
      rx_descriptor_installed_q <= 1'b0;
      destination_error_q <= 1'b0;
      replay_active_q <= 1'b0;
      replay_slot_q <= 1'b0;
      replay_word_q <= 0;
      replay_next_packet_q <= 0;
      tx_descriptor_count <= 0;
      rx_completion_count <= 0;
      replay_packet_count <= 0;
      for (reset_i = 0; reset_i < SLOT_COUNT; reset_i = reset_i + 1) begin
        src_slot_state[reset_i] <= SLOT_FREE;
        src_expected_count[reset_i] <= 0;
        src_req_count[reset_i] <= 0;
        src_rsp_count[reset_i] <= 0;
        dst_slot_state[reset_i] <= 3'd0;
        dst_slot_packet[reset_i] <= 0;
        dst_slot_source[reset_i] <= 0;
        dst_slot_destination[reset_i] <= 0;
        dst_slot_vc[reset_i] <= 0;
        dst_slot_tag[reset_i] <= 0;
        dst_slot_count[reset_i] <= 0;
      end
    end else begin
      rx_write_cycle_q <= rx_write_cycle_q + 1'b1;
      rx_descriptor_installed_q <= 1'b0;

      if (tx_ctx_fire) begin
        tx_group_active_q <= 1'b1;
        tx_group_source_q <= group_source;
        tx_group_destination_q <= group_destination;
        tx_group_vc_q <= group_vc;
        tx_group_epoch_q <= group_epoch;
        tx_fill_active_q <= 1'b1;
        tx_fill_slot_q <= 1'b0;
        tx_fill_word_q <= 0;
        tx_desc_pending_q <= 1'b0;
        tx_packet_index_q <= 0;
        tx_wait_fill_q <= 1'b0;
        src_slot_state[0] <= SLOT_FILL;
      end
      if (tx_framer_clean)
        tx_group_active_q <= 1'b0;

      if (tx_framer_flit_valid && tx_framer_flit_ready) begin
        if (tx_framer_fragment != tx_fill_word_q[FRAGMENT_W-1:0] ||
            tx_framer_source != tx_group_source_q ||
            tx_framer_destination != tx_group_destination_q ||
            tx_framer_vc != tx_group_vc_q ||
            tx_framer_tag != {tx_group_epoch_q, tx_packet_index_q})
          source_error_q <= 1'b1;
        if (tx_framer_last) begin
          if ((tx_packet_index_q < 5'd20 && tx_fill_word_q != 4'd7) ||
              (tx_packet_index_q == 5'd20 && tx_fill_word_q != 4'd6))
            source_error_q <= 1'b1;
          src_slot_state[tx_fill_slot_q] <= SLOT_READY;
          src_expected_count[tx_fill_slot_q] <= tx_fill_word_q + 1'b1;
          tx_desc_pending_q <= 1'b1;
          tx_desc_slot_q <= tx_fill_slot_q;
          tx_desc_destination_q <= tx_framer_destination;
          tx_desc_vc_q <= tx_framer_vc;
          tx_desc_tag_q <= tx_framer_tag;
          tx_desc_count_q <= tx_fill_word_q + 1'b1;
          tx_fill_active_q <= 1'b0;
          tx_wait_fill_q <= (tx_packet_index_q != 5'd20);
          tx_wait_slot_q <= !tx_fill_slot_q;
          if (tx_packet_index_q != 5'd20)
            tx_packet_index_q <= tx_packet_index_q + 1'b1;
        end else begin
          tx_fill_word_q <= tx_fill_word_q + 1'b1;
        end
      end

      if (ep_tx_desc_fire) begin
        tx_desc_pending_q <= 1'b0;
        src_slot_state[tx_desc_slot_q] <= SLOT_IN_FLIGHT;
        src_req_count[tx_desc_slot_q] <= 0;
        src_rsp_count[tx_desc_slot_q] <= 0;
        tx_descriptor_count <= tx_descriptor_count + 1'b1;
      end

      if (tx_wait_fill_q && !tx_fill_active_q && !tx_desc_pending_q &&
          (src_slot_state[tx_wait_slot_q] == SLOT_FREE)) begin
        tx_fill_active_q <= 1'b1;
        tx_fill_slot_q <= tx_wait_slot_q;
        tx_fill_word_q <= 0;
        src_slot_state[tx_wait_slot_q] <= SLOT_FILL;
        tx_wait_fill_q <= 1'b0;
      end

      if (ep_tx_mem_req_fire) begin
        if (!tx_addr_valid_r || tx_addr_word_i >= SLOT_WORDS ||
            src_slot_state[tx_addr_slot_i] != SLOT_IN_FLIGHT ||
            src_req_count[tx_addr_slot_i] >= src_expected_count[tx_addr_slot_i]) begin
          source_error_q <= 1'b1;
        end else begin
          src_req_count[tx_addr_slot_i] <=
            src_req_count[tx_addr_slot_i] + 1'b1;
        end
      end
      if (ep_tx_mem_rsp_fire) begin
        if (src_slot_state[src_mem_read_rsp_addr[3]] != SLOT_IN_FLIGHT ||
            src_rsp_count[src_mem_read_rsp_addr[3]] >=
            src_expected_count[src_mem_read_rsp_addr[3]]) begin
          source_error_q <= 1'b1;
        end else begin
          src_rsp_count[src_mem_read_rsp_addr[3]] <=
            src_rsp_count[src_mem_read_rsp_addr[3]] + 1'b1;
          if (src_rsp_count[src_mem_read_rsp_addr[3]] + 1'b1 ==
              src_expected_count[src_mem_read_rsp_addr[3]])
            src_slot_state[src_mem_read_rsp_addr[3]] <= SLOT_FREE;
        end
      end

      if (rx_ctx_fire) begin
        rx_group_active_q <= 1'b1;
        rx_group_source_q <= group_source;
        rx_group_destination_q <= group_destination;
        rx_group_vc_q <= group_vc;
        rx_group_epoch_q <= group_epoch;
        rx_desc_pending_q <= 1'b1;
        rx_desc_slot_q <= 1'b0;
        rx_desc_packet_q <= 0;
        dst_slot_state[0] <= DST_RESERVED;
        rx_wait_next_desc_q <= 1'b0;
        replay_next_packet_q <= 0;
      end
      if (rx_deframer_clean)
        rx_group_active_q <= 1'b0;

      if (ep_rx_desc_fire) begin
        dst_slot_state[rx_desc_slot_q] <= DST_ACTIVE;
        dst_slot_packet[rx_desc_slot_q] <= rx_desc_packet_q;
        dst_slot_source[rx_desc_slot_q] <= rx_group_source_q;
        dst_slot_destination[rx_desc_slot_q] <= rx_group_destination_q;
        dst_slot_vc[rx_desc_slot_q] <= rx_group_vc_q;
        dst_slot_tag[rx_desc_slot_q] <= {rx_group_epoch_q, rx_desc_packet_q};
        dst_slot_count[rx_desc_slot_q] <= ep_rx_desc_flit_count;
        rx_desc_pending_q <= 1'b0;
        rx_active_q <= 1'b1;
        rx_active_slot_q <= rx_desc_slot_q;
        rx_active_packet_q <= rx_desc_packet_q;
        rx_descriptor_installed_q <= 1'b1;
      end

      if (ep_rx_mem_write_fire) begin
        if (!rx_addr_valid_r || rx_addr_word_i >= SLOT_WORDS || !rx_active_q ||
            rx_addr_slot_i[0:0] != rx_active_slot_q ||
            rx_addr_word_i >= dst_slot_count[rx_active_slot_q]) begin
          destination_error_q <= 1'b1;
        end else begin
        end
      end

      if (ep_rx_completion_fire) begin
        if (!rx_active_q ||
            ep_rx_completion_tag != dst_slot_tag[rx_active_slot_q] ||
            ep_rx_completion_source != dst_slot_source[rx_active_slot_q] ||
            ep_rx_completion_vc != dst_slot_vc[rx_active_slot_q]) begin
          destination_error_q <= 1'b1;
        end
        dst_slot_state[rx_active_slot_q] <= DST_COMPLETE;
        rx_active_q <= 1'b0;
        rx_completion_count <= rx_completion_count + 1'b1;
        if (rx_active_packet_q == 5'd20) begin
          rx_wait_next_desc_q <= 1'b0;
        end else begin
          rx_wait_next_desc_q <= 1'b1;
          rx_wait_slot_q <= !rx_active_slot_q;
          rx_wait_packet_q <= rx_active_packet_q + 1'b1;
        end
      end

      if (rx_wait_next_desc_q && !rx_desc_pending_q && !rx_active_q &&
          (dst_slot_state[rx_wait_slot_q] == 3'd0)) begin
        rx_desc_pending_q <= 1'b1;
        rx_desc_slot_q <= rx_wait_slot_q;
        rx_desc_packet_q <= rx_wait_packet_q;
        dst_slot_state[rx_wait_slot_q] <= DST_RESERVED;
        rx_wait_next_desc_q <= 1'b0;
      end

      if (!replay_active_q && replay_found_r) begin
        replay_active_q <= 1'b1;
        replay_slot_q <= replay_found_slot_r;
        replay_word_q <= 0;
        dst_slot_state[replay_found_slot_r] <= DST_REPLAY;
      end

      if (dst_mem_read_req_fire)
        replay_word_q <= replay_word_q + 1'b1;

      if (dst_mem_read_rsp_fire) begin
        if (dst_mem_read_rsp_addr[WORD_INDEX_W-1:0] + 1'b1 ==
            dst_slot_count[dst_mem_read_rsp_addr[3]]) begin
          replay_active_q <= 1'b0;
          dst_slot_state[dst_mem_read_rsp_addr[3]] <= 3'd0;
          replay_next_packet_q <= replay_next_packet_q + 1'b1;
          replay_packet_count <= replay_packet_count + 1'b1;
        end else if (!replay_active_q ||
                     dst_mem_read_rsp_addr[3] != replay_slot_q) begin
          destination_error_q <= 1'b1;
        end
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      max_source_occupancy <= 0;
      max_destination_occupancy <= 0;
    end else begin
      if ({1'b0, src_occupied_count} > max_source_occupancy)
        max_source_occupancy <= {1'b0, src_occupied_count};
      if ({1'b0, dst_occupied_count} > max_destination_occupancy)
        max_destination_occupancy <= {1'b0, dst_occupied_count};
    end
  end

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || TAG_W != 8 || FRAGMENT_W != 3 || VC_W != 2) begin
      $error("stats-once SRAM adapter widths must match the packet bridge");
      $finish(1);
    end
    if (SLOT_COUNT != 2 || SLOT_WORDS != 8)
      $error("stats-once SRAM adapter must retain the two-by-eight minimum");
  end
`endif
endmodule
