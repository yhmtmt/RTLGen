// Emit 128 paired 1-KiB K spans for one head. Source bases and descriptor
// completion ordering are owned by the enclosing gather scheduler.
module attention_kv_paired_head_schedule (
  input wire clk, input wire rst_n,
  input wire head_valid, output wire head_ready,
  input wire [1:0] head_kv_head,
  input wire [17:0] head_resident_prefix_bytes,
  output wire span_valid, input wire span_ready,
  output wire [19:0] span_canonical_address,
  output wire [16:0] span_head_byte_offset,
  output wire span_resident,
  output wire span_last,
  output reg head_done,
  output reg protocol_error
);
  reg active;
  reg [6:0] index_q;
  reg [1:0] head_q;
  reg [17:0] prefix_q;
  wire [16:0] offset = {index_q[0], index_q[6:1], 10'd0};
  assign head_ready = !active && !protocol_error;
  assign span_valid = active && !protocol_error;
  assign span_head_byte_offset = offset;
  assign span_canonical_address = {1'b0, head_q, offset};
  assign span_resident = {1'b0, offset} < prefix_q;
  assign span_last = index_q == 7'd127;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active <= 0; index_q <= 0; head_q <= 0; prefix_q <= 0;
      head_done <= 0; protocol_error <= 0;
    end else begin
      head_done <= 0;
      if (head_valid && head_ready) begin
        if (head_resident_prefix_bytes > 18'd131072 ||
            head_resident_prefix_bytes[9:0] != 0)
          protocol_error <= 1;
        else begin
          active <= 1; index_q <= 0; head_q <= head_kv_head;
          prefix_q <= head_resident_prefix_bytes;
        end
      end
      if (span_valid && span_ready) begin
        if (span_last) begin active <= 0; head_done <= 1; end
        else index_q <= index_q + 1'b1;
      end
    end
  end
endmodule
