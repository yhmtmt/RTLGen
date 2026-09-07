"""Paired canonical K flits through a real transposer into every producer."""


def write_key_flits(path, *, fixture, cluster):
    """Command-major canonical memory; each command covers one head/tile."""
    with path.open("w") as output:
        for group in range(4):
            for wave in range(8):
                tile = cluster + 16 * wave
                for offset in range(0, 131072, 32):
                    data = fixture.memory_flit(tile=tile, address=group * 131072 + offset)
                    output.write(f"{int.from_bytes(data, 'little'):064x}\n")


def attach_cluster_key_ingress(tb, *, producers):
    for old, new in {
        ".key_write_valid(stage_kv)": ".key_write_valid(trans_valid)",
        ".key_write_kv_head(stage_head)": ".key_write_kv_head(trans_head)",
        ".key_write_producer(stage_producer)": ".key_write_producer(trans_producer)",
        ".key_write_producer_block(stage_block)": ".key_write_producer_block(trans_block)",
        ".key_write_dimension_pair(stage_pair)": ".key_write_dimension_pair(trans_pair)",
        ".key_write_data(stage_kdata)": ".key_write_data(trans_data)",
        ".key_write_last(stage_pair==63)": ".key_write_last(trans_last)",
    }.items():
        if tb.count(old) != 1:
            raise ValueError("cluster transpose anchor changed: " + old)
        tb = tb.replace(old, new)
    start = tb.index("      for(sp=0;sp<PRODUCERS;sp=sp+1)")
    end = tb.index("      wait(stage_complete);", start)
    tb = tb[:start] + """      schedule_head_valid=1;
      while(!schedule_head_ready) @(negedge clk);
      @(negedge clk); schedule_head_valid=0;
      wait(schedule_done); @(negedge clk);
""" + tb[end:]
    declarations = """
  reg [255:0] canonical_k[0:131071];
  reg schedule_head_valid=0;
  wire schedule_head_ready,schedule_valid,schedule_ready,schedule_done,schedule_error;
  wire [19:0] schedule_address,trans_address;
  reg [4:0] schedule_flit=0;
  wire trans_input_ready,trans_valid,trans_error,trans_last,trans_block;
  wire [255:0] trans_data;
  wire [1:0] trans_head;
  wire [5:0] trans_producer,trans_pair;
  integer schedule_spans=0,trans_inputs=0,trans_outputs=0;
"""
    anchor = "  reg stage_armed=0"
    if tb.count(anchor) != 1:
        raise ValueError("cluster stage declaration anchor changed")
    tb = tb.replace(anchor, declarations + anchor)
    body = f"""
  initial $readmemh("canonical_k_flits.memh",canonical_k);
  attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS({producers})) trans_dut (
    .clk(clk),.rst_n(rst_n),.ingress_valid(schedule_valid),.ingress_ready(trans_input_ready),
    .ingress_tile_byte_addr(trans_address),.ingress_data(canonical_k[sc*4096+trans_address[16:5]]),
    .ingress_byte_valid(32'hffffffff),.key_valid(trans_valid),.key_ready(stage_key_ready),
    .key_producer(trans_producer),.key_kv_head(trans_head),.key_producer_block(trans_block),
    .key_dimension_pair(trans_pair),.key_data(trans_data),.key_last(trans_last),.protocol_error(trans_error));
  attention_kv_paired_head_schedule schedule_dut (
    .clk(clk),.rst_n(rst_n),.head_valid(schedule_head_valid),.head_ready(schedule_head_ready),
    .head_kv_head(stage_head),.head_resident_prefix_bytes(18'd16384),
    .span_valid(schedule_valid),.span_ready(schedule_ready),.span_canonical_address(schedule_address),
    .span_head_byte_offset(),.span_resident(),.span_last(),.head_done(schedule_done),.protocol_error(schedule_error));
  assign trans_address=schedule_address+{{10'd0,schedule_flit,5'd0}};
  assign schedule_ready=trans_input_ready && schedule_flit==31;
  always @(posedge clk) begin
    if(!rst_n) schedule_flit<=0;
    else if(schedule_valid && trans_input_ready) schedule_flit<=schedule_flit+1'b1;
  end
  always @(posedge clk) if(rst_n) begin
    if(schedule_error || trans_error) $fatal(1,"cluster key ingress protocol error");
    if(schedule_valid && schedule_ready) schedule_spans=schedule_spans+1;
    if(schedule_valid && trans_input_ready) trans_inputs=trans_inputs+1;
    if(trans_valid && stage_key_ready) trans_outputs=trans_outputs+1;
    if(pending_summary && (schedule_spans!=4096 || trans_inputs!=131072 || trans_outputs!=131072))
      $fatal(1,"cluster key ingress coverage mismatch");
  end
"""
    anchor = "  always #5 clk = ~clk;"
    if tb.count(anchor) != 1:
        raise ValueError("cluster clock anchor changed")
    return tb.replace(anchor, body + "\n" + anchor)
