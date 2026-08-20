`timescale 1ns/1ps

// One synchronous single-port physical bank for the shared-root storage
// fabric.  A write wins arbitration over a read in the same cycle.  The
// response register is held until the consumer accepts it.
module local_reducer_aggregate_stats_once_exact_shared_root_bank_memory #(
  parameter integer DATA_W = 256,
  parameter integer ADDR_W = 6,
  parameter integer DEPTH = 64,
  parameter integer USE_FAKERAM = 0
) (
  input wire clk,
  input wire rst_n,
  input wire write_valid,
  output wire write_ready,
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
  generate
    if (USE_FAKERAM == 0) begin : gen_inferred_memory
      reg [DATA_W-1:0] mem [0:DEPTH-1];
      reg read_rsp_valid_q;
      reg [ADDR_W-1:0] read_rsp_addr_q;
      reg [DATA_W-1:0] read_rsp_data_q;

      assign write_ready = 1'b1;
      assign read_req_ready = !write_valid &&
        (!read_rsp_valid_q || read_rsp_ready);
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
    end else begin : gen_fakeram_memory
      localparam integer MACRO_DEPTH = 64;
      localparam integer MACRO_WIDTH = 32;
      localparam integer DEPTH_MACROS =
        (DEPTH + MACRO_DEPTH - 1) / MACRO_DEPTH;
      localparam integer WIDTH_MACROS = DATA_W / MACRO_WIDTH;
      localparam integer PHYSICAL_BITS = WIDTH_MACROS * MACRO_WIDTH;
      localparam [1:0] S_IDLE = 2'd0;
      localparam [1:0] S_READ_WAIT = 2'd1;
      localparam [1:0] S_RESPONSE = 2'd2;

      reg [1:0] state_q;
      reg [ADDR_W-1:0] read_rsp_addr_q;
      wire response_replaced_w = state_q == S_RESPONSE && read_rsp_ready;
      wire operation_ready_w = state_q == S_IDLE || response_replaced_w;
      wire write_fire_w = write_valid && operation_ready_w;
      wire read_fire_w = read_req_valid && read_req_ready;
      wire [ADDR_W-1:0] operation_addr_w =
        write_fire_w ? write_addr : read_req_addr;
      wire [ADDR_W+5:0] extended_operation_addr_w =
        {{6{1'b0}}, operation_addr_w};
      wire [DEPTH_MACROS*PHYSICAL_BITS-1:0] macro_read_words_w;
      wire [PHYSICAL_BITS-1:0] selected_read_word_w =
        macro_read_words_w[
          (read_rsp_addr_q / MACRO_DEPTH) * PHYSICAL_BITS +: PHYSICAL_BITS];

      assign write_ready = operation_ready_w;
      assign read_req_ready = operation_ready_w && !write_valid;
      assign read_rsp_valid = state_q == S_RESPONSE;
      assign read_rsp_addr = read_rsp_addr_q;
      assign read_rsp_data = selected_read_word_w[DATA_W-1:0];

      genvar depth_g;
      genvar width_g;
      for (depth_g = 0; depth_g < DEPTH_MACROS; depth_g = depth_g + 1) begin : gen_depth
        for (width_g = 0; width_g < WIDTH_MACROS; width_g = width_g + 1) begin : gen_width
          fakeram45_64x32 u_packet_mem (
            .rd_out(macro_read_words_w[
              (depth_g * PHYSICAL_BITS) + (width_g * MACRO_WIDTH) +: MACRO_WIDTH]),
            .addr_in(extended_operation_addr_w[5:0]),
            .we_in(write_fire_w),
            .wd_in(write_data[width_g*MACRO_WIDTH +: MACRO_WIDTH]),
            .w_mask_in({MACRO_WIDTH{1'b1}}),
            .clk(clk),
            .ce_in((write_fire_w || read_fire_w) &&
              ((operation_addr_w / MACRO_DEPTH) == depth_g))
          );
        end
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state_q <= S_IDLE;
          read_rsp_addr_q <= {ADDR_W{1'b0}};
        end else begin
          case (state_q)
            S_IDLE: begin
              if (read_fire_w) begin
                read_rsp_addr_q <= read_req_addr;
                state_q <= S_READ_WAIT;
              end
            end
            S_READ_WAIT: state_q <= S_RESPONSE;
            S_RESPONSE: begin
              if (read_rsp_ready) begin
                if (read_fire_w) begin
                  read_rsp_addr_q <= read_req_addr;
                  state_q <= S_READ_WAIT;
                end else begin
                  state_q <= S_IDLE;
                end
              end
            end
            default: state_q <= S_IDLE;
          endcase
        end
      end
    end
  endgenerate

`ifndef SYNTHESIS
  initial begin
    if (DEPTH != (1 << ADDR_W)) begin
      $error("shared-root bank depth must match its address width");
      $finish(1);
    end
    if (USE_FAKERAM != 0 && (DATA_W % 32) != 0) begin
      $error("fakeram shared-root banks require 32-bit width granularity");
      $finish(1);
    end
  end
`endif
endmodule

// Shared logical packet storage.  Source s maps to physical bank s modulo
// PHYSICAL_BANKS; its row is (s / PHYSICAL_BANKS) * 16 + slot * 8 + word.
// Each bank has one write/read port, so writes have priority and reads are
// selected fairly among the sources mapped to that bank.
module local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric #(
  parameter integer DATA_W = 256,
  parameter integer SOURCE_COUNT = 15,
  parameter integer PHYSICAL_BANKS = 15,
  parameter integer ADDR_W = 4,
  parameter integer USE_FAKERAM = 0
) (
  input wire clk,
  input wire rst_n,
  input wire [SOURCE_COUNT-1:0] write_valid,
  output wire [SOURCE_COUNT-1:0] write_ready,
  input wire [SOURCE_COUNT*ADDR_W-1:0] write_addr,
  input wire [SOURCE_COUNT*DATA_W-1:0] write_data,
  input wire [SOURCE_COUNT-1:0] read_req_valid,
  output wire [SOURCE_COUNT-1:0] read_req_ready,
  input wire [SOURCE_COUNT*ADDR_W-1:0] read_req_addr,
  output wire [SOURCE_COUNT-1:0] read_rsp_valid,
  input wire [SOURCE_COUNT-1:0] read_rsp_ready,
  output wire [SOURCE_COUNT*ADDR_W-1:0] read_rsp_addr,
  output wire [SOURCE_COUNT*DATA_W-1:0] read_rsp_data,
  output wire protocol_error
);
  localparam integer SLOT_WORDS = 8;
  localparam integer BANK_SOURCE_COUNT =
    (SOURCE_COUNT + PHYSICAL_BANKS - 1) / PHYSICAL_BANKS;
  localparam integer BANK_DEPTH = BANK_SOURCE_COUNT * 16;
  localparam integer BANK_ADDR_W = (BANK_DEPTH <= 1) ? 1 : $clog2(BANK_DEPTH);
  localparam integer BANK_PTR_W =
    (BANK_SOURCE_COUNT <= 1) ? 1 : $clog2(BANK_SOURCE_COUNT);
  localparam integer SOURCE_W =
    (SOURCE_COUNT <= 1) ? 1 : $clog2(SOURCE_COUNT);

  wire [PHYSICAL_BANKS-1:0] bank_write_valid_w;
  wire [PHYSICAL_BANKS-1:0] bank_write_ready_w;
  wire [PHYSICAL_BANKS-1:0] bank_read_req_valid_w;
  wire [PHYSICAL_BANKS-1:0] bank_read_req_ready_w;
  wire [PHYSICAL_BANKS-1:0] bank_read_rsp_valid_w;
  wire [PHYSICAL_BANKS-1:0] bank_read_rsp_ready_w;
  wire [PHYSICAL_BANKS*BANK_ADDR_W-1:0] bank_write_addr_w;
  wire [PHYSICAL_BANKS*BANK_ADDR_W-1:0] bank_read_req_addr_w;
  wire [PHYSICAL_BANKS*BANK_ADDR_W-1:0] bank_read_rsp_addr_w;
  wire [PHYSICAL_BANKS*DATA_W-1:0] bank_write_data_w;
  wire [PHYSICAL_BANKS*DATA_W-1:0] bank_read_rsp_data_w;
  wire [PHYSICAL_BANKS-1:0] bank_response_route_valid_w;
  wire [PHYSICAL_BANKS*SOURCE_W-1:0] bank_response_source_w;
  wire [PHYSICAL_BANKS*ADDR_W-1:0] bank_response_logical_addr_w;
  reg [SOURCE_COUNT-1:0] source_rsp_valid_q;
  reg [SOURCE_COUNT*ADDR_W-1:0] source_rsp_addr_q;
  reg [SOURCE_COUNT*DATA_W-1:0] source_rsp_data_q;
  wire [SOURCE_COUNT-1:0] source_rsp_slot_ready_w =
    ~source_rsp_valid_q | read_rsp_ready;

  assign read_rsp_valid = source_rsp_valid_q;
  assign read_rsp_addr = source_rsp_addr_q;
  assign read_rsp_data = source_rsp_data_q;

  genvar bank_g;
  generate
    for (bank_g = 0; bank_g < PHYSICAL_BANKS; bank_g = bank_g + 1) begin : gen_bank
      localparam integer BANK_ID = bank_g;
      integer source_i;
      integer offset_i;
      integer candidate_source_i;
      integer selected_source_i;
      integer selected_write_i;
      integer selected_offset_i;
      integer response_source_i;
      reg selected_write_r;
      reg selected_read_r;
      reg [BANK_PTR_W-1:0] rr_ptr_q;
      reg [BANK_PTR_W-1:0] rr_ptr_next;
      reg [BANK_ADDR_W-1:0] write_row_r;
      reg [BANK_ADDR_W-1:0] read_row_r;
      reg [DATA_W-1:0] write_data_r;
      reg [ADDR_W-1:0] read_logical_addr_r;
      reg [ADDR_W-1:0] write_logical_addr_r;
      reg [ADDR_W-1:0] response_logical_addr_r;
      reg response_source_valid_r;

      always @* begin
        response_logical_addr_r = bank_read_rsp_addr_w[
          BANK_ID*BANK_ADDR_W +: BANK_ADDR_W];
        response_source_valid_r = 1'b0;
        response_source_i = 0;
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
          if ((source_i % PHYSICAL_BANKS) == BANK_ID &&
              (bank_read_rsp_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W] / 16) ==
              (source_i / PHYSICAL_BANKS)) begin
            response_source_valid_r = 1'b1;
            response_source_i = source_i;
            response_logical_addr_r = bank_read_rsp_addr_w[
              BANK_ID*BANK_ADDR_W +: BANK_ADDR_W] % 16;
          end
        end

        selected_write_r = 1'b0;
        selected_write_i = 0;
        write_row_r = {BANK_ADDR_W{1'b0}};
        write_data_r = {DATA_W{1'b0}};
        write_logical_addr_r = {ADDR_W{1'b0}};
        for (source_i = 0; source_i < SOURCE_COUNT; source_i = source_i + 1) begin
          if (!selected_write_r && write_valid[source_i] &&
              ((source_i % PHYSICAL_BANKS) == BANK_ID)) begin
            selected_write_r = 1'b1;
            selected_write_i = source_i;
            write_logical_addr_r = write_addr[source_i*ADDR_W +: ADDR_W];
            write_row_r = (source_i / PHYSICAL_BANKS) * 16 +
              write_addr[source_i*ADDR_W +: ADDR_W];
            write_data_r = write_data[source_i*DATA_W +: DATA_W];
          end
        end

        selected_read_r = 1'b0;
        selected_source_i = 0;
        selected_offset_i = 0;
        read_row_r = {BANK_ADDR_W{1'b0}};
        read_logical_addr_r = {ADDR_W{1'b0}};
        for (offset_i = 0; offset_i < BANK_SOURCE_COUNT; offset_i = offset_i + 1) begin
          candidate_source_i = BANK_ID +
            ((rr_ptr_q + offset_i) % BANK_SOURCE_COUNT) * PHYSICAL_BANKS;
          if (!selected_read_r && candidate_source_i < SOURCE_COUNT &&
              read_req_valid[candidate_source_i] &&
              !source_rsp_valid_q[candidate_source_i] &&
              !(bank_read_rsp_valid_w[BANK_ID] &&
                response_source_valid_r &&
                response_source_i == candidate_source_i)) begin
            selected_read_r = 1'b1;
            selected_source_i = candidate_source_i;
            selected_offset_i = offset_i;
            read_logical_addr_r =
              read_req_addr[candidate_source_i*ADDR_W +: ADDR_W];
            read_row_r = (candidate_source_i / PHYSICAL_BANKS) * 16 +
              read_req_addr[candidate_source_i*ADDR_W +: ADDR_W];
          end
        end

        rr_ptr_next = rr_ptr_q;
        if (selected_read_r && bank_read_req_ready_w[BANK_ID]) begin
          if (selected_offset_i == BANK_SOURCE_COUNT - 1)
            rr_ptr_next = {BANK_PTR_W{1'b0}};
          else
            rr_ptr_next = rr_ptr_q + selected_offset_i + 1'b1;
        end

      end

      assign bank_write_valid_w[BANK_ID] = selected_write_r;
      assign bank_write_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W] = write_row_r;
      assign bank_write_data_w[BANK_ID*DATA_W +: DATA_W] = write_data_r;
      assign bank_read_req_valid_w[BANK_ID] = selected_read_r &&
        !selected_write_r;
      assign bank_read_req_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W] = read_row_r;
      assign bank_read_rsp_ready_w[BANK_ID] =
        bank_read_rsp_valid_w[BANK_ID] && response_source_valid_r &&
        source_rsp_slot_ready_w[response_source_i];
      assign bank_response_route_valid_w[BANK_ID] = response_source_valid_r;
      assign bank_response_source_w[BANK_ID*SOURCE_W +: SOURCE_W] =
        response_source_i[SOURCE_W-1:0];
      assign bank_response_logical_addr_w[BANK_ID*ADDR_W +: ADDR_W] =
        response_logical_addr_r;

      genvar source_route_g;
      for (source_route_g = 0; source_route_g < SOURCE_COUNT;
           source_route_g = source_route_g + 1) begin : gen_source_route
        if ((source_route_g % PHYSICAL_BANKS) == BANK_ID) begin : gen_mapped_source
          assign write_ready[source_route_g] = bank_write_ready_w[BANK_ID] &&
            (!selected_write_r || (selected_write_i == source_route_g));
          assign read_req_ready[source_route_g] = bank_read_req_ready_w[BANK_ID] &&
            !selected_write_r && selected_read_r &&
            (selected_source_i == source_route_g);
        end
      end

      local_reducer_aggregate_stats_once_exact_shared_root_bank_memory #(
        .DATA_W(DATA_W), .ADDR_W(BANK_ADDR_W), .DEPTH(BANK_DEPTH),
        .USE_FAKERAM(USE_FAKERAM)
      ) bank_memory (
        .clk(clk), .rst_n(rst_n),
        .write_valid(bank_write_valid_w[BANK_ID]),
        .write_ready(bank_write_ready_w[BANK_ID]),
        .write_addr(bank_write_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W]),
        .write_data(bank_write_data_w[BANK_ID*DATA_W +: DATA_W]),
        .read_req_valid(bank_read_req_valid_w[BANK_ID]),
        .read_req_ready(bank_read_req_ready_w[BANK_ID]),
        .read_req_addr(bank_read_req_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W]),
        .read_rsp_valid(bank_read_rsp_valid_w[BANK_ID]),
        .read_rsp_ready(bank_read_rsp_ready_w[BANK_ID]),
        .read_rsp_addr(bank_read_rsp_addr_w[BANK_ID*BANK_ADDR_W +: BANK_ADDR_W]),
        .read_rsp_data(bank_read_rsp_data_w[BANK_ID*DATA_W +: DATA_W])
      );

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
          rr_ptr_q <= {BANK_PTR_W{1'b0}};
        else
          rr_ptr_q <= rr_ptr_next;
      end
    end
  endgenerate

  integer response_source_i;
  integer response_bank_i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      source_rsp_valid_q <= {SOURCE_COUNT{1'b0}};
      source_rsp_addr_q <= {SOURCE_COUNT*ADDR_W{1'b0}};
      source_rsp_data_q <= {SOURCE_COUNT*DATA_W{1'b0}};
    end else begin
      for (response_source_i = 0;
           response_source_i < SOURCE_COUNT;
           response_source_i = response_source_i + 1) begin
        if (source_rsp_valid_q[response_source_i] &&
            read_rsp_ready[response_source_i])
          source_rsp_valid_q[response_source_i] <= 1'b0;
        for (response_bank_i = 0;
             response_bank_i < PHYSICAL_BANKS;
             response_bank_i = response_bank_i + 1) begin
          if (bank_read_rsp_valid_w[response_bank_i] &&
              bank_read_rsp_ready_w[response_bank_i] &&
              bank_response_route_valid_w[response_bank_i] &&
              bank_response_source_w[
                response_bank_i*SOURCE_W +: SOURCE_W] == response_source_i) begin
            source_rsp_valid_q[response_source_i] <= 1'b1;
            source_rsp_addr_q[response_source_i*ADDR_W +: ADDR_W] <=
              bank_response_logical_addr_w[
                response_bank_i*ADDR_W +: ADDR_W];
            source_rsp_data_q[response_source_i*DATA_W +: DATA_W] <=
              bank_read_rsp_data_w[response_bank_i*DATA_W +: DATA_W];
          end
        end
      end
    end
  end

  assign protocol_error = 1'b0;
endmodule

// Shared root receive adapter for the exact stats-once transport.
//
// The root owns one descriptor endpoint and demultiplexes its single memory
// write stream into one 16x256 packet SRAM per remote source.  Each source has
// two logical eight-word destination slots.  A completed slot is replayed in
// packet order through its own exact packet deframer; no source has a packet-
// sized register or a private NoC endpoint at the root.
module local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter #(
  parameter integer DATA_W = 256,
  parameter integer TAG_W = 8,
  parameter integer FRAGMENT_W = 3,
  parameter integer VC_W = 2,
  parameter integer ENDPOINT_W = 4,
  parameter integer ADDR_W = 16,
  parameter integer FLIT_COUNT_W = 4,
  parameter integer SOURCE_COUNT = 15,
  parameter integer ROOT_ENDPOINT_ID = 15,
  parameter integer PHYSICAL_BANKS = 15,
  parameter integer USE_FAKERAM = 0
) (
  input wire clk,
  input wire rst_n,

  input wire [SOURCE_COUNT-1:0] group_ctx_valid,
  output wire [SOURCE_COUNT-1:0] group_ctx_ready,
  input wire [SOURCE_COUNT*16-1:0] group_command_id,
  input wire [SOURCE_COUNT*5-1:0] group_head_base,
  input wire [SOURCE_COUNT*4-1:0] group_source,
  input wire [SOURCE_COUNT*4-1:0] group_destination,
  input wire [SOURCE_COUNT*VC_W-1:0] group_vc,
  input wire [SOURCE_COUNT*3-1:0] group_epoch,

  output wire [SOURCE_COUNT-1:0] tx_release_valid,
  input wire [SOURCE_COUNT-1:0] tx_release_ready,
  output wire [SOURCE_COUNT-1:0] codec_out_valid,
  input wire [SOURCE_COUNT-1:0] codec_out_ready,
  output wire [SOURCE_COUNT*DATA_W-1:0] codec_out_data,
  output wire [SOURCE_COUNT-1:0] codec_out_group_last,
  output wire [SOURCE_COUNT-1:0] group_complete,
  output wire [SOURCE_COUNT-1:0] descriptor_installed,
  output wire [SOURCE_COUNT-1:0] source_protocol_error,

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
  input wire [DATA_W-1:0] mesh_out_data,

  output reg [31:0] root_accepted_flit_count,
  output reg [31:0] root_descriptor_install_count,
  output reg [31:0] root_completion_count,
  output reg [31:0] root_replay_packet_count,
  output reg [5:0] max_occupied_slots,
  output wire protocol_error
);
  localparam integer DATA_BYTES = DATA_W / 8;
  localparam integer SLOT_WORDS = 8;
  localparam integer SLOT_BYTES = SLOT_WORDS * DATA_BYTES;
  localparam integer BANK_WORDS = 16;
  localparam integer BANK_BYTES = BANK_WORDS * DATA_BYTES;
  localparam integer SLOT_COUNT = 2;

  localparam [1:0] SLOT_FREE = 2'd0;
  localparam [1:0] SLOT_RESERVED = 2'd1;
  localparam [1:0] SLOT_ACTIVE = 2'd2;
  localparam [1:0] SLOT_COMPLETE = 2'd3;

  reg group_active_q [0:SOURCE_COUNT-1];
  reg [15:0] command_q [0:SOURCE_COUNT-1];
  reg [4:0] head_q [0:SOURCE_COUNT-1];
  reg [3:0] source_q [0:SOURCE_COUNT-1];
  reg [3:0] destination_q [0:SOURCE_COUNT-1];
  reg [VC_W-1:0] vc_q [0:SOURCE_COUNT-1];
  reg [2:0] epoch_q [0:SOURCE_COUNT-1];

  reg desc_pending_q [0:SOURCE_COUNT-1];
  reg desc_slot_q [0:SOURCE_COUNT-1];
  reg [4:0] desc_packet_q [0:SOURCE_COUNT-1];
  reg active_packet_q [0:SOURCE_COUNT-1];
  reg [4:0] active_packet_index_q [0:SOURCE_COUNT-1];
  reg [4:0] next_packet_q [0:SOURCE_COUNT-1];
  reg wait_next_q [0:SOURCE_COUNT-1];
  reg wait_slot_q [0:SOURCE_COUNT-1];
  reg [4:0] wait_packet_q [0:SOURCE_COUNT-1];
  reg release_pending_q [0:SOURCE_COUNT-1];
  reg local_error_q [0:SOURCE_COUNT-1];

  reg [1:0] slot_state [0:SOURCE_COUNT-1][0:SLOT_COUNT-1];
  reg [4:0] slot_packet [0:SOURCE_COUNT-1][0:SLOT_COUNT-1];
  reg [3:0] slot_flit_count [0:SOURCE_COUNT-1][0:SLOT_COUNT-1];
  reg replay_active_q [0:SOURCE_COUNT-1];
  reg replay_slot_q [0:SOURCE_COUNT-1];
  reg [3:0] replay_word_q [0:SOURCE_COUNT-1];

  integer active_group_i;
  reg all_groups_active;
  reg any_group_active;
  reg group_release_open_q;
  reg [4:0] release_round_q;
  reg [6:0] release_interval_q;
  always @* begin
    all_groups_active = 1'b1;
    any_group_active = 1'b0;
    for (active_group_i = 0;
         active_group_i < SOURCE_COUNT;
         active_group_i = active_group_i + 1) begin
      if (!group_active_q[active_group_i])
        all_groups_active = 1'b0;
      if (group_active_q[active_group_i])
        any_group_active = 1'b1;
    end
  end

  wire [SOURCE_COUNT-1:0] packet_sram_read_rsp_valid_w;
  wire [SOURCE_COUNT*4-1:0] packet_sram_read_rsp_addr_w;
  wire [SOURCE_COUNT-1:0] replay_response_fire_w;

  wire [SOURCE_COUNT-1:0] storage_write_valid_w;
  wire [SOURCE_COUNT-1:0] storage_write_ready_w;
  wire [SOURCE_COUNT*4-1:0] storage_write_addr_w;
  wire [SOURCE_COUNT*DATA_W-1:0] storage_write_data_w;
  wire [SOURCE_COUNT-1:0] storage_read_req_valid_w;
  wire [SOURCE_COUNT-1:0] storage_read_req_ready_w;
  wire [SOURCE_COUNT*4-1:0] storage_read_req_addr_w;
  wire [SOURCE_COUNT-1:0] storage_read_rsp_valid_w;
  wire [SOURCE_COUNT-1:0] storage_read_rsp_ready_w;
  wire [SOURCE_COUNT*4-1:0] storage_read_rsp_addr_w;
  wire [SOURCE_COUNT*DATA_W-1:0] storage_read_rsp_data_w;
  wire storage_protocol_error_w;

  wire [SOURCE_COUNT-1:0] deframer_ctx_ready_w;
  wire [SOURCE_COUNT-1:0] deframer_flit_valid_w;
  wire [SOURCE_COUNT-1:0] deframer_flit_ready_w;
  wire [SOURCE_COUNT-1:0] deframer_clean_w;
  wire [SOURCE_COUNT-1:0] deframer_error_w;
  wire [SOURCE_COUNT*DATA_W-1:0] deframer_data_w;

  wire ep_tx_desc_valid = 1'b0;
  wire ep_tx_mem_req_ready = 1'b0;
  wire ep_tx_mem_rsp_valid = 1'b0;
  wire ep_tx_flit_ready = 1'b0;
  wire ep_rx_desc_ready;
  wire ep_rx_flit_ready;
  wire ep_rx_mem_write_valid;
  wire ep_rx_mem_write_ready;
  wire [ADDR_W-1:0] ep_rx_mem_write_addr;
  wire [DATA_W-1:0] ep_rx_mem_write_data;
  wire ep_rx_completion_valid;
  wire ep_rx_completion_ready;
  wire [ENDPOINT_W-1:0] ep_rx_completion_source;
  wire [VC_W-1:0] ep_rx_completion_vc;
  wire [TAG_W-1:0] ep_rx_completion_tag;
  wire ep_protocol_error;

  wire [ENDPOINT_W-1:0] ep_rx_desc_source;
  wire [VC_W-1:0] ep_rx_desc_vc;
  wire [TAG_W-1:0] ep_rx_desc_tag;
  wire [ADDR_W-1:0] ep_rx_desc_base_addr;
  wire [FLIT_COUNT_W-1:0] ep_rx_desc_flit_count;

  wire ep_rx_desc_valid;
  wire ep_rx_desc_fire = ep_rx_desc_valid && ep_rx_desc_ready;
  wire ep_rx_mem_write_fire = ep_rx_mem_write_valid && ep_rx_mem_write_ready;
  wire ep_rx_completion_fire = ep_rx_completion_valid && ep_rx_completion_ready;

  integer descriptor_select_i;
  reg descriptor_select_valid;
  reg [ENDPOINT_W-1:0] descriptor_select_source;
  always @* begin
    descriptor_select_valid = 1'b0;
    descriptor_select_source = {ENDPOINT_W{1'b0}};
    for (descriptor_select_i = 0;
         descriptor_select_i < SOURCE_COUNT;
         descriptor_select_i = descriptor_select_i + 1) begin
      if (desc_pending_q[descriptor_select_i] && !descriptor_select_valid) begin
        descriptor_select_valid = 1'b1;
        descriptor_select_source = descriptor_select_i[ENDPOINT_W-1:0];
      end
    end
  end

  assign ep_rx_desc_valid = descriptor_select_valid;
  assign ep_rx_desc_source = descriptor_select_source;
  assign ep_rx_desc_vc = vc_q[descriptor_select_source];
  assign ep_rx_desc_tag = {
    epoch_q[descriptor_select_source],
    desc_packet_q[descriptor_select_source]
  };
  assign ep_rx_desc_base_addr =
    descriptor_select_source * BANK_BYTES +
    (desc_slot_q[descriptor_select_source] ? SLOT_BYTES : 0);
  assign ep_rx_desc_flit_count =
    (desc_packet_q[descriptor_select_source] == 5'd20) ? 4'd7 : 4'd8;

  noc_sram_packet_endpoint #(
    .DATA_W(DATA_W),
    .ENDPOINT_W(ENDPOINT_W),
    .VC_W(VC_W),
    .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W),
    .ADDR_W(ADDR_W),
    .FLIT_COUNT_W(FLIT_COUNT_W),
    .TX_DESC_DEPTH(1),
    .TX_OUTSTANDING(1),
    .RX_CONTEXTS(SOURCE_COUNT),
    .LOCAL_ENDPOINT_ID(ROOT_ENDPOINT_ID)
  ) shared_root_endpoint (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(ep_tx_desc_valid), .tx_desc_ready(),
    .tx_desc_destination(4'b0), .tx_desc_vc({VC_W{1'b0}}),
    .tx_desc_tag({TAG_W{1'b0}}), .tx_desc_base_addr({ADDR_W{1'b0}}),
    .tx_desc_flit_count({FLIT_COUNT_W{1'b0}}),
    .tx_mem_req_valid(), .tx_mem_req_ready(ep_tx_mem_req_ready),
    .tx_mem_req_addr(), .tx_mem_rsp_valid(ep_tx_mem_rsp_valid),
    .tx_mem_rsp_ready(), .tx_mem_rsp_data({DATA_W{1'b0}}),
    .tx_flit_valid(), .tx_flit_ready(ep_tx_flit_ready),
    .tx_flit_source(), .tx_flit_destination(), .tx_flit_vc(),
    .tx_flit_tag(), .tx_flit_fragment(), .tx_flit_last(), .tx_flit_data(),
    .rx_desc_valid(ep_rx_desc_valid), .rx_desc_ready(ep_rx_desc_ready),
    .rx_desc_source(ep_rx_desc_source), .rx_desc_vc(ep_rx_desc_vc),
    .rx_desc_tag(ep_rx_desc_tag), .rx_desc_base_addr(ep_rx_desc_base_addr),
    .rx_desc_flit_count(ep_rx_desc_flit_count),
    .rx_flit_valid(mesh_out_valid), .rx_flit_ready(ep_rx_flit_ready),
    .rx_flit_source(mesh_out_source), .rx_flit_destination(mesh_out_destination),
    .rx_flit_vc(mesh_out_vc), .rx_flit_tag(mesh_out_tag),
    .rx_flit_fragment(mesh_out_fragment), .rx_flit_last(mesh_out_last),
    .rx_flit_data(mesh_out_data),
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

  assign mesh_in_valid = 1'b0;
  assign mesh_in_destination = {ENDPOINT_W{1'b0}};
  assign mesh_in_source = {ENDPOINT_W{1'b0}};
  assign mesh_in_tag = {TAG_W{1'b0}};
  assign mesh_in_fragment = {FRAGMENT_W{1'b0}};
  assign mesh_in_last = 1'b0;
  assign mesh_in_vc = {VC_W{1'b0}};
  assign mesh_in_data = {DATA_W{1'b0}};
  assign mesh_out_ready = ep_rx_flit_ready;
  assign ep_rx_completion_ready = 1'b1;

  integer write_route_i;
  reg write_route_valid;
  reg [ENDPOINT_W-1:0] write_route_source;
  reg [3:0] write_route_addr;
  wire write_route_state_ok;
  always @* begin
    write_route_valid = 1'b0;
    write_route_source = {ENDPOINT_W{1'b0}};
    write_route_addr = 4'b0;
    for (write_route_i = 0;
         write_route_i < SOURCE_COUNT;
         write_route_i = write_route_i + 1) begin
      if (!write_route_valid &&
          ep_rx_mem_write_addr >= write_route_i * BANK_BYTES &&
          ep_rx_mem_write_addr < (write_route_i + 1) * BANK_BYTES) begin
        write_route_valid = 1'b1;
        write_route_source = write_route_i[ENDPOINT_W-1:0];
        write_route_addr =
          (ep_rx_mem_write_addr - write_route_i * BANK_BYTES) / DATA_BYTES;
      end
    end
  end
  // The endpoint writes one logical source lane at a time.  A valid active
  // slot is backpressured by the physical bank fabric; malformed or stale
  // writes are still consumed so the endpoint can report the protocol error.
  assign ep_rx_mem_write_ready = !ep_rx_mem_write_valid ||
    !write_route_valid || !write_route_state_ok ||
    storage_write_ready_w[write_route_source];

  assign write_route_state_ok = write_route_valid &&
    (slot_state[write_route_source][write_route_addr[3]] == SLOT_ACTIVE);

  // Keep the original fifteen top-level packet SRAM cells for the default
  // physical-bank configuration.  The shared fabric is selected for a
  // genuinely shared-bank configuration such as PHYSICAL_BANKS=4.
  genvar physical_bank_g;
  generate
    if (PHYSICAL_BANKS == SOURCE_COUNT && USE_FAKERAM == 0) begin : gen_compat_source_banks
      for (physical_bank_g = 0; physical_bank_g < SOURCE_COUNT;
           physical_bank_g = physical_bank_g + 1) begin : gen_source_bank
        localparam integer BANK_SOURCE_ID = physical_bank_g;
        local_reducer_aggregate_stats_once_exact_packet_sram #(
          .DATA_W(DATA_W), .ADDR_W(4)
        ) destination_packet_sram (
          .clk(clk), .rst_n(rst_n),
          .write_valid(storage_write_valid_w[BANK_SOURCE_ID]),
          .write_addr(storage_write_addr_w[BANK_SOURCE_ID*4 +: 4]),
          .write_data(storage_write_data_w[BANK_SOURCE_ID*DATA_W +: DATA_W]),
          .read_req_valid(storage_read_req_valid_w[BANK_SOURCE_ID]),
          .read_req_ready(storage_read_req_ready_w[BANK_SOURCE_ID]),
          .read_req_addr(storage_read_req_addr_w[BANK_SOURCE_ID*4 +: 4]),
          .read_rsp_valid(storage_read_rsp_valid_w[BANK_SOURCE_ID]),
          .read_rsp_ready(storage_read_rsp_ready_w[BANK_SOURCE_ID]),
          .read_rsp_addr(storage_read_rsp_addr_w[BANK_SOURCE_ID*4 +: 4]),
          .read_rsp_data(storage_read_rsp_data_w[BANK_SOURCE_ID*DATA_W +: DATA_W])
        );
        assign storage_write_ready_w[BANK_SOURCE_ID] = 1'b1;
      end
      assign storage_protocol_error_w = 1'b0;
    end else begin : gen_shared_physical_banks
      local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric #(
        .DATA_W(DATA_W), .SOURCE_COUNT(SOURCE_COUNT),
        .PHYSICAL_BANKS(PHYSICAL_BANKS), .ADDR_W(4),
        .USE_FAKERAM(USE_FAKERAM)
      ) storage_fabric (
        .clk(clk), .rst_n(rst_n),
        .write_valid(storage_write_valid_w),
        .write_ready(storage_write_ready_w),
        .write_addr(storage_write_addr_w),
        .write_data(storage_write_data_w),
        .read_req_valid(storage_read_req_valid_w),
        .read_req_ready(storage_read_req_ready_w),
        .read_req_addr(storage_read_req_addr_w),
        .read_rsp_valid(storage_read_rsp_valid_w),
        .read_rsp_ready(storage_read_rsp_ready_w),
        .read_rsp_addr(storage_read_rsp_addr_w),
        .read_rsp_data(storage_read_rsp_data_w),
        .protocol_error(storage_protocol_error_w)
      );
    end
  endgenerate

  assign packet_sram_read_rsp_valid_w = storage_read_rsp_valid_w;
  assign packet_sram_read_rsp_addr_w = storage_read_rsp_addr_w;

  genvar source_g;
  generate
    for (source_g = 0; source_g < SOURCE_COUNT; source_g = source_g + 1) begin : gen_source
      localparam integer SOURCE_ID = source_g;

      wire source_ctx_fire = group_ctx_valid[SOURCE_ID] &&
        group_ctx_ready[SOURCE_ID];
      wire descriptor_fire = ep_rx_desc_fire &&
        (descriptor_select_source == SOURCE_ID);
      wire completion_fire = ep_rx_completion_fire &&
        (ep_rx_completion_source == SOURCE_ID);
      wire release_fire = tx_release_valid[SOURCE_ID] &&
        tx_release_ready[SOURCE_ID];
      wire source_write_fire = ep_rx_mem_write_fire &&
        (write_route_source == SOURCE_ID);
      wire source_write_slot = write_route_addr[3];
      wire source_write_state_ok =
        slot_state[SOURCE_ID][source_write_slot] == SLOT_ACTIVE;

      wire replay_found;
      wire replay_found_slot;
      integer replay_scan_i;
      reg replay_found_r;
      reg replay_found_slot_r;
      always @* begin
        replay_found_r = 1'b0;
        replay_found_slot_r = 1'b0;
        for (replay_scan_i = 0;
             replay_scan_i < SLOT_COUNT;
             replay_scan_i = replay_scan_i + 1) begin
          if (!replay_found_r &&
              slot_state[SOURCE_ID][replay_scan_i] == SLOT_COMPLETE &&
              slot_packet[SOURCE_ID][replay_scan_i] == next_packet_q[SOURCE_ID]) begin
            replay_found_r = 1'b1;
            replay_found_slot_r = replay_scan_i[0:0];
          end
        end
      end
      assign replay_found = replay_found_r;
      assign replay_found_slot = replay_found_slot_r;

      wire replay_issue = replay_active_q[SOURCE_ID] &&
        (replay_word_q[SOURCE_ID] <
         slot_flit_count[SOURCE_ID][replay_slot_q[SOURCE_ID]]);
      wire packet_sram_read_req_ready;
      wire packet_sram_read_rsp_valid;
      wire [3:0] packet_sram_read_rsp_addr;
      wire [DATA_W-1:0] packet_sram_read_rsp_data;
      wire replay_request_fire = replay_issue &&
        packet_sram_read_req_ready;
      wire replay_response_fire = packet_sram_read_rsp_valid &&
        deframer_flit_ready_w[SOURCE_ID];
      wire replay_response_last = replay_response_fire &&
        (({1'b0, packet_sram_read_rsp_addr[2:0]} + 1'b1) ==
         {1'b0, slot_flit_count[SOURCE_ID][packet_sram_read_rsp_addr[3]]});

      wire packet_sram_read_rsp_ready = deframer_flit_ready_w[SOURCE_ID];

      assign storage_write_valid_w[SOURCE_ID] =
        ep_rx_mem_write_valid && write_route_valid &&
        (write_route_source == SOURCE_ID) && source_write_state_ok;
      assign storage_write_addr_w[SOURCE_ID*4 +: 4] = write_route_addr;
      assign storage_write_data_w[SOURCE_ID*DATA_W +: DATA_W] =
        ep_rx_mem_write_data;
      assign storage_read_req_valid_w[SOURCE_ID] = replay_issue;
      assign storage_read_req_addr_w[SOURCE_ID*4 +: 4] =
        {replay_slot_q[SOURCE_ID], replay_word_q[SOURCE_ID][2:0]};
      assign storage_read_rsp_ready_w[SOURCE_ID] = packet_sram_read_rsp_ready;
      assign packet_sram_read_rsp_valid = storage_read_rsp_valid_w[SOURCE_ID];
      assign packet_sram_read_rsp_addr =
        storage_read_rsp_addr_w[SOURCE_ID*4 +: 4];
      assign packet_sram_read_rsp_data =
        storage_read_rsp_data_w[SOURCE_ID*DATA_W +: DATA_W];
      assign packet_sram_read_req_ready = storage_read_req_ready_w[SOURCE_ID];

      wire deframer_ctx_valid = source_ctx_fire;
      wire [DATA_W-1:0] deframer_data = packet_sram_read_rsp_data;
      wire deframer_flit_last =
        (({1'b0, packet_sram_read_rsp_addr[2:0]} + 1'b1) ==
         {1'b0, slot_flit_count[SOURCE_ID][packet_sram_read_rsp_addr[3]]});

      local_reducer_aggregate_stats_once_exact_packet_rx_deframer deframer (
        .clk(clk), .rst_n(rst_n),
        .group_ctx_valid(deframer_ctx_valid),
        .group_ctx_ready(deframer_ctx_ready_w[SOURCE_ID]),
        .group_command_id(group_command_id[SOURCE_ID*16 +: 16]),
        .group_head_base(group_head_base[SOURCE_ID*5 +: 5]),
        .group_source(group_source[SOURCE_ID*4 +: 4]),
        .group_destination(group_destination[SOURCE_ID*4 +: 4]),
        .group_vc(group_vc[SOURCE_ID*VC_W +: VC_W]),
        .group_epoch(group_epoch[SOURCE_ID*3 +: 3]),
        .mesh_flit_valid(packet_sram_read_rsp_valid),
        .mesh_flit_ready(deframer_flit_ready_w[SOURCE_ID]),
        .mesh_flit_destination(ROOT_ENDPOINT_ID[ENDPOINT_W-1:0]),
        .mesh_flit_source(SOURCE_ID[ENDPOINT_W-1:0]),
        .mesh_flit_tag({epoch_q[SOURCE_ID], slot_packet[SOURCE_ID][packet_sram_read_rsp_addr[3]]}),
        .mesh_flit_fragment(packet_sram_read_rsp_addr[FRAGMENT_W-1:0]),
        .mesh_flit_last(deframer_flit_last),
        .mesh_flit_vc(vc_q[SOURCE_ID]),
        .mesh_flit_data(deframer_data),
        .codec_flit_valid(deframer_flit_valid_w[SOURCE_ID]),
        .codec_flit_ready(codec_out_ready[SOURCE_ID]),
        .codec_flit_data(deframer_data_w[SOURCE_ID*DATA_W +: DATA_W]),
        .codec_flit_group_last(codec_out_group_last[SOURCE_ID]),
        .codec_group_command_id(), .codec_group_head_base(),
        .protocol_error(deframer_error_w[SOURCE_ID]),
        .clean_group_complete(deframer_clean_w[SOURCE_ID])
      );

      assign codec_out_data[SOURCE_ID*DATA_W +: DATA_W] =
        deframer_data_w[SOURCE_ID*DATA_W +: DATA_W];

      assign group_ctx_ready[SOURCE_ID] =
        !group_active_q[SOURCE_ID] &&
        (!group_release_open_q || !any_group_active) &&
        !desc_pending_q[SOURCE_ID] &&
        !active_packet_q[SOURCE_ID] &&
        !wait_next_q[SOURCE_ID] &&
        !replay_active_q[SOURCE_ID] &&
        (slot_state[SOURCE_ID][0] == SLOT_FREE) &&
        (slot_state[SOURCE_ID][1] == SLOT_FREE) &&
        deframer_ctx_ready_w[SOURCE_ID];
      // A reduction group cannot make forward progress without every leaf.
      // Hold early sources until all remote contexts are latched so context
      // arrival skew cannot bias the fixed-priority descriptor scheduler.
      assign tx_release_valid[SOURCE_ID] =
        release_pending_q[SOURCE_ID] && group_release_open_q &&
        (active_packet_index_q[SOURCE_ID] <= release_round_q);
      assign codec_out_valid[SOURCE_ID] = deframer_flit_valid_w[SOURCE_ID];
      assign group_complete[SOURCE_ID] = deframer_clean_w[SOURCE_ID];
      assign descriptor_installed[SOURCE_ID] = descriptor_fire;
      assign source_protocol_error[SOURCE_ID] =
        local_error_q[SOURCE_ID] || deframer_error_w[SOURCE_ID];

      integer reset_slot_i;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          group_active_q[SOURCE_ID] <= 1'b0;
          command_q[SOURCE_ID] <= 16'b0;
          head_q[SOURCE_ID] <= 5'b0;
          source_q[SOURCE_ID] <= SOURCE_ID[3:0];
          destination_q[SOURCE_ID] <= ROOT_ENDPOINT_ID[3:0];
          vc_q[SOURCE_ID] <= {VC_W{1'b0}};
          epoch_q[SOURCE_ID] <= 3'b0;
          desc_pending_q[SOURCE_ID] <= 1'b0;
          desc_slot_q[SOURCE_ID] <= 1'b0;
          desc_packet_q[SOURCE_ID] <= 5'b0;
          active_packet_q[SOURCE_ID] <= 1'b0;
          active_packet_index_q[SOURCE_ID] <= 5'b0;
          next_packet_q[SOURCE_ID] <= 5'b0;
          wait_next_q[SOURCE_ID] <= 1'b0;
          wait_slot_q[SOURCE_ID] <= 1'b0;
          wait_packet_q[SOURCE_ID] <= 5'b0;
          release_pending_q[SOURCE_ID] <= 1'b0;
          local_error_q[SOURCE_ID] <= 1'b0;
          replay_active_q[SOURCE_ID] <= 1'b0;
          replay_slot_q[SOURCE_ID] <= 1'b0;
          replay_word_q[SOURCE_ID] <= 4'b0;
          for (reset_slot_i = 0; reset_slot_i < SLOT_COUNT; reset_slot_i = reset_slot_i + 1) begin
            slot_state[SOURCE_ID][reset_slot_i] <= SLOT_FREE;
            slot_packet[SOURCE_ID][reset_slot_i] <= 5'b0;
            slot_flit_count[SOURCE_ID][reset_slot_i] <= 4'b0;
          end
        end else begin
          if (source_ctx_fire) begin
            group_active_q[SOURCE_ID] <= 1'b1;
            command_q[SOURCE_ID] <= group_command_id[SOURCE_ID*16 +: 16];
            head_q[SOURCE_ID] <= group_head_base[SOURCE_ID*5 +: 5];
            source_q[SOURCE_ID] <= group_source[SOURCE_ID*4 +: 4];
            destination_q[SOURCE_ID] <= group_destination[SOURCE_ID*4 +: 4];
            vc_q[SOURCE_ID] <= group_vc[SOURCE_ID*VC_W +: VC_W];
            epoch_q[SOURCE_ID] <= group_epoch[SOURCE_ID*3 +: 3];
            desc_pending_q[SOURCE_ID] <= 1'b1;
            desc_slot_q[SOURCE_ID] <= 1'b0;
            desc_packet_q[SOURCE_ID] <= 5'd0;
            slot_state[SOURCE_ID][0] <= SLOT_RESERVED;
            next_packet_q[SOURCE_ID] <= 5'd0;
            wait_next_q[SOURCE_ID] <= 1'b0;
          end

          if (descriptor_fire) begin
            desc_pending_q[SOURCE_ID] <= 1'b0;
            active_packet_q[SOURCE_ID] <= 1'b1;
            active_packet_index_q[SOURCE_ID] <= desc_packet_q[SOURCE_ID];
            slot_state[SOURCE_ID][desc_slot_q[SOURCE_ID]] <= SLOT_ACTIVE;
            slot_packet[SOURCE_ID][desc_slot_q[SOURCE_ID]] <= desc_packet_q[SOURCE_ID];
            slot_flit_count[SOURCE_ID][desc_slot_q[SOURCE_ID]] <=
              (desc_packet_q[SOURCE_ID] == 5'd20) ? 4'd7 : 4'd8;
            release_pending_q[SOURCE_ID] <= 1'b1;
          end

          if (release_fire)
            release_pending_q[SOURCE_ID] <= 1'b0;

          if (source_write_fire && !source_write_state_ok)
            local_error_q[SOURCE_ID] <= 1'b1;

          if (completion_fire) begin
            if (!active_packet_q[SOURCE_ID] ||
                ep_rx_completion_vc != vc_q[SOURCE_ID] ||
                ep_rx_completion_tag !=
                  {epoch_q[SOURCE_ID], active_packet_index_q[SOURCE_ID]}) begin
              local_error_q[SOURCE_ID] <= 1'b1;
            end
            slot_state[SOURCE_ID][desc_slot_q[SOURCE_ID]] <= SLOT_COMPLETE;
            active_packet_q[SOURCE_ID] <= 1'b0;
            if (active_packet_index_q[SOURCE_ID] != 5'd20) begin
              wait_next_q[SOURCE_ID] <= 1'b1;
              wait_slot_q[SOURCE_ID] <= !desc_slot_q[SOURCE_ID];
              wait_packet_q[SOURCE_ID] <= active_packet_index_q[SOURCE_ID] + 1'b1;
            end
          end

          if (wait_next_q[SOURCE_ID] && !desc_pending_q[SOURCE_ID] &&
              !active_packet_q[SOURCE_ID] &&
              slot_state[SOURCE_ID][wait_slot_q[SOURCE_ID]] == SLOT_FREE) begin
            desc_pending_q[SOURCE_ID] <= 1'b1;
            desc_slot_q[SOURCE_ID] <= wait_slot_q[SOURCE_ID];
            desc_packet_q[SOURCE_ID] <= wait_packet_q[SOURCE_ID];
            slot_state[SOURCE_ID][wait_slot_q[SOURCE_ID]] <= SLOT_RESERVED;
            wait_next_q[SOURCE_ID] <= 1'b0;
          end

          if (!replay_active_q[SOURCE_ID] && replay_found) begin
            replay_active_q[SOURCE_ID] <= 1'b1;
            replay_slot_q[SOURCE_ID] <= replay_found_slot;
            replay_word_q[SOURCE_ID] <= 4'b0;
            slot_state[SOURCE_ID][replay_found_slot] <= SLOT_ACTIVE;
          end

          if (replay_request_fire)
            replay_word_q[SOURCE_ID] <= replay_word_q[SOURCE_ID] + 1'b1;

          if (replay_response_last) begin
            replay_active_q[SOURCE_ID] <= 1'b0;
            slot_state[SOURCE_ID][packet_sram_read_rsp_addr[3]] <= SLOT_FREE;
            next_packet_q[SOURCE_ID] <= next_packet_q[SOURCE_ID] + 1'b1;
          end

          if (deframer_clean_w[SOURCE_ID])
            group_active_q[SOURCE_ID] <= 1'b0;
        end
      end
    end
  endgenerate

  integer occupied_source_i;
  integer occupied_slot_i;
  reg [5:0] occupied_now;
  always @* begin
    occupied_now = 6'd0;
    for (occupied_source_i = 0;
         occupied_source_i < SOURCE_COUNT;
         occupied_source_i = occupied_source_i + 1) begin
      for (occupied_slot_i = 0;
           occupied_slot_i < SLOT_COUNT;
           occupied_slot_i = occupied_slot_i + 1) begin
        if (slot_state[occupied_source_i][occupied_slot_i] != SLOT_FREE)
          occupied_now = occupied_now + 1'b1;
      end
    end
  end

  reg root_error_q;

  reg [5:0] replay_fire_count_now;
  integer replay_count_i;
  always @* begin
    replay_fire_count_now = 6'd0;
    for (replay_count_i = 0;
         replay_count_i < SOURCE_COUNT;
         replay_count_i = replay_count_i + 1)
      if (replay_response_fire_w[replay_count_i])
        replay_fire_count_now = replay_fire_count_now + 1'b1;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      root_accepted_flit_count <= 32'b0;
      root_descriptor_install_count <= 32'b0;
      root_completion_count <= 32'b0;
      root_replay_packet_count <= 32'b0;
      max_occupied_slots <= 6'b0;
      root_error_q <= 1'b0;
      group_release_open_q <= 1'b0;
      release_round_q <= 5'b0;
      release_interval_q <= 7'b0;
    end else begin
      if (all_groups_active)
        group_release_open_q <= 1'b1;
      else if (!any_group_active)
        group_release_open_q <= 1'b0;
      if (!group_release_open_q) begin
        release_round_q <= 5'b0;
        release_interval_q <= 7'b0;
      end else if (release_interval_q == 7'd119) begin
        release_interval_q <= 7'b0;
        if (release_round_q != 5'd20)
          release_round_q <= release_round_q + 1'b1;
      end else begin
        release_interval_q <= release_interval_q + 1'b1;
      end
      if (ep_rx_mem_write_fire)
        root_accepted_flit_count <= root_accepted_flit_count + 1'b1;
      if (ep_rx_desc_fire)
        root_descriptor_install_count <= root_descriptor_install_count + 1'b1;
      if (ep_rx_completion_fire)
        root_completion_count <= root_completion_count + 1'b1;
      if (replay_fire_count_now != 0)
        root_replay_packet_count <=
          root_replay_packet_count + replay_fire_count_now;
      if (occupied_now > max_occupied_slots)
        max_occupied_slots <= occupied_now;
      if (ep_rx_mem_write_fire &&
          (!write_route_valid || mesh_out_source != write_route_source ||
           !write_route_state_ok))
        root_error_q <= 1'b1;
      if (ep_rx_completion_fire && ep_rx_completion_source >= SOURCE_COUNT)
        root_error_q <= 1'b1;
    end
  end

  genvar count_g;
  generate
    for (count_g = 0; count_g < SOURCE_COUNT; count_g = count_g + 1) begin : gen_count
      wire [3:0] count_response_addr =
        packet_sram_read_rsp_addr_w[count_g*4 +: 4];
      wire count_response_fire =
        replay_active_q[count_g] && packet_sram_read_rsp_valid_w[count_g] &&
        deframer_flit_ready_w[count_g] &&
        (({1'b0, count_response_addr[2:0]} + 1'b1) ==
         {1'b0, slot_flit_count[count_g][count_response_addr[3]]});
      assign replay_response_fire_w[count_g] = count_response_fire;
    end
  endgenerate

  assign protocol_error = root_error_q || ep_protocol_error ||
    storage_protocol_error_w ||
    (|source_protocol_error);

`ifndef SYNTHESIS
  initial begin
    if (DATA_W != 256 || TAG_W != 8 || FRAGMENT_W != 3 || VC_W != 2 ||
        SOURCE_COUNT != 15 || ROOT_ENDPOINT_ID != 15)
      $error("shared root exact adapter width/topology contract changed");
    if (BANK_WORDS != 16 || SLOT_WORDS != 8)
      $error("shared root packet SRAM geometry changed");
  end
`endif
endmodule
