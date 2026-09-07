// Combinational source mapping for a paired 1-KiB K span. The enclosing
// scheduler owns valid/ready, stable coordinates, and completion ordering.
module attention_kv_paired_key_address (
  input wire [4:0] layer,
  input wire [6:0] tile,
  input wire [1:0] kv_head,
  input wire [16:0] head_byte_offset,
  output wire [19:0] canonical_address,
  output wire [33:0] source_byte_address,
  output wire source_hbm,
  output wire [3:0] source_endpoint,
  output wire [3:0] destination_cluster,
  output wire protocol_error
);
  wire resident = tile < 7'd2 ||
                  (tile == 7'd2 && head_byte_offset < 17'd16384);
  wire [33:0] layer_resident_base =
    {8'd0, layer, 21'd0} + {12'd0, layer, 17'd0};
  wire [33:0] resident_offset = tile < 7'd2 ?
    {7'd0, tile, 20'd0} + {14'd0, canonical_address} :
    34'd2097152 + {18'd0, kv_head, 14'd0} + {17'd0, head_byte_offset};
  wire [33:0] hbm_address = {2'd0, layer, 27'd0} +
    {7'd0, tile, 20'd0} + {14'd0, canonical_address};
  wire [1:0] corner_selector = layer[1:0] + tile[1:0] + kv_head;
  wire [3:0] corner = corner_selector == 2'd0 ? 4'd0 :
                      corner_selector == 2'd1 ? 4'd3 :
                      corner_selector == 2'd2 ? 4'd12 : 4'd15;
  assign canonical_address = {1'b0, kv_head, head_byte_offset};
  assign destination_cluster = {layer[2:0], 1'b0} + layer[3:0] + tile[3:0];
  assign source_hbm = !resident;
  assign source_byte_address = resident ? layer_resident_base + resident_offset : hbm_address;
  assign source_endpoint = resident ? destination_cluster : corner;
  assign protocol_error = |head_byte_offset[9:0];
endmodule
