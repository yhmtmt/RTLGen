// Exact macro-backed storage boundary for one 4096-element RMSNorm row.
//
// Mapping: 16 lanes x 256 beats x {row BF16, gamma BF16}.  Each lane uses
// four depth shards of the available 64x32 FakeRAM macro, for 64 macros total.
// Reads have a fixed two-cycle request-to-response latency matching the
// registered FakeRAM model.  Read and write requests are mutually exclusive.
module llama7b_rmsnorm_banked_row_gamma_store (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         write_en,
    input  wire [7:0]   write_beat,
    input  wire [255:0] write_row,
    input  wire [255:0] write_gamma,
    input  wire         read_en,
    input  wire [7:0]   read_beat,
    output wire         read_valid,
    output wire [255:0] read_row,
    output wire [255:0] read_gamma,
    output reg          request_collision
);
  localparam integer LANES = 16;
  localparam integer SHARDS = 4;

  wire [2047:0] macro_read_bus;
  wire [1:0] request_shard = write_en ? write_beat[7:6] : read_beat[7:6];
  wire [5:0] request_addr = write_en ? write_beat[5:0] : read_beat[5:0];

  reg read_valid_q1;
  reg read_valid_q2;
  reg [1:0] read_shard_q1;
  reg [1:0] read_shard_q2;

  assign read_valid = read_valid_q2;

  genvar shard;
  genvar lane;
  generate
    for (shard = 0; shard < SHARDS; shard = shard + 1) begin : gen_shard
      for (lane = 0; lane < LANES; lane = lane + 1) begin : gen_lane
        wire selected = request_shard == shard[1:0];
        fakeram45_64x32 u_row_gamma_mem (
            .rd_out(macro_read_bus[((shard * LANES + lane) * 32) +: 32]),
            .addr_in(request_addr),
            .we_in(write_en && selected && !read_en),
            .wd_in({write_gamma[(lane * 16) +: 16], write_row[(lane * 16) +: 16]}),
            .w_mask_in({32{write_en && selected && !read_en}}),
            .clk(clk),
            .ce_in(selected && (write_en ^ read_en))
        );
      end
    end
  endgenerate

  generate
    for (lane = 0; lane < LANES; lane = lane + 1) begin : gen_read_mux
      wire [31:0] selected_word =
          macro_read_bus[((read_shard_q2 * LANES + lane) * 32) +: 32];
      assign read_row[(lane * 16) +: 16] = selected_word[15:0];
      assign read_gamma[(lane * 16) +: 16] = selected_word[31:16];
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      read_valid_q1 <= 1'b0;
      read_valid_q2 <= 1'b0;
      read_shard_q1 <= 2'd0;
      read_shard_q2 <= 2'd0;
      request_collision <= 1'b0;
    end else begin
      read_valid_q1 <= read_en && !write_en;
      read_valid_q2 <= read_valid_q1;
      if (read_en && !write_en)
        read_shard_q1 <= read_beat[7:6];
      if (read_valid_q1)
        read_shard_q2 <= read_shard_q1;
      if (read_en && write_en)
        request_collision <= 1'b1;
    end
  end
endmodule
