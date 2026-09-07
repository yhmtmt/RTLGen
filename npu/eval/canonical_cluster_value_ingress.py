"""Canonical V flits through the real ingress adapter into cluster SRAM."""


def attach_cluster_value_ingress(tb, *, producers):
    replacements = {
        "wire fill_valid = rst_n && (fill_command < COMMANDS) && (fill_row >= 0);":
            "wire fill_valid = vi_out_valid;",
        "wire [511:0] fill_data = (fill_row >= 0)\n      ? fill_mem[fill_drive_index * ROWS_PER_TARGET + fill_row] : '0;":
            "wire [511:0] fill_data = vi_out_data;",
        ".fill_target_valid(fill_target_valid), .fill_target_ready(fill_target_ready)":
            ".fill_target_valid(vi_endpoint_target), .fill_target_ready(vi_endpoint_ready)",
        ".fill_buffer_sel(wave_index_mem[fill_drive_index][0])": ".fill_buffer_sel(vi_out_buffer)",
        ".fill_stream(fill_row >= ROWS_PER_STREAM)": ".fill_stream(vi_out_stream)",
        ".fill_block_slot((fill_row >> 4) & 6'h3f), .fill_slice(fill_row & 4'hf)":
            ".fill_block_slot(vi_out_slot), .fill_slice(vi_out_slice)",
    }
    for old, new in replacements.items():
        if tb.count(old) != 1:
            raise ValueError("cluster V ingress anchor changed: " + old)
        tb = tb.replace(old, new)
    declarations = """
  reg [255:0] canonical_v[0:131071];
  reg vi_block_target=0,vi_valid=0;
  reg [6:0] vi_block=0;
  reg [19:0] vi_address=0;
  reg [255:0] vi_data=0;
  wire vi_endpoint_target,vi_endpoint_ready,vi_block_ready,vi_ready,vi_complete,vi_error;
  wire vi_out_valid,vi_out_buffer,vi_out_stream;
  wire [5:0] vi_out_slot;
  wire [3:0] vi_out_slice;
  wire [511:0] vi_out_data;
  integer vc,vb,vf,vi_inputs=0,vi_rows=0,vi_targets=0;
"""
    tb = tb.replace("  wire preload_complete", declarations + "  wire preload_complete", 1)
    body = f"""
  initial $readmemh("canonical_v_flits.memh",canonical_v);
  attention_score32_exact_kv_value_ingress #(.PRODUCERS({producers})) vi_dut (
    .clk(clk),.rst_n(rst_n),.fill_target_valid(fill_target_valid),.fill_target_ready(fill_target_ready),
    .fill_target_buffer_sel(wave_index_mem[fill_drive_index][0]),
    .fill_target_command_id(command_id_mem[fill_drive_index]),
    .fill_target_head_base(head_base_mem[fill_drive_index]),.fill_target_wave_index(wave_index_mem[fill_drive_index]),
    .endpoint_fill_target_valid(vi_endpoint_target),.endpoint_fill_target_ready(vi_endpoint_ready),
    .endpoint_fill_target_buffer_sel(),.endpoint_fill_target_command_id(),
    .endpoint_fill_target_head_base(),.endpoint_fill_target_wave_index(),
    .block_target_valid(vi_block_target),.block_target_ready(vi_block_ready),
    .block_target_kv_head(head_base_mem[fill_drive_index][4:3]),
    .block_target_stream(vi_block[6]),.block_target_slot(vi_block[5:0]),
    .ingress_valid(vi_valid),.ingress_ready(vi_ready),.ingress_tile_byte_addr(vi_address),
    .ingress_data(vi_data),.ingress_byte_valid(32'hffffffff),
    .endpoint_fill_valid(vi_out_valid),.endpoint_fill_ready(fill_ready),
    .endpoint_fill_buffer_sel(vi_out_buffer),.endpoint_fill_stream(vi_out_stream),
    .endpoint_fill_block_slot(vi_out_slot),.endpoint_fill_slice(vi_out_slice),
    .endpoint_fill_data(vi_out_data),.fill_complete(vi_complete),.fill_active(),
    .completed_block_count(),.protocol_error(vi_error));
  always @(posedge clk) if(rst_n) begin
    if(vi_error) $fatal(1,"cluster V ingress protocol error");
    if(vi_valid && vi_ready) vi_inputs=vi_inputs+1;
    if(fill_target_valid && fill_target_ready) vi_targets=vi_targets+1;
    if(fill_valid && fill_ready) begin
      vi_rows=vi_rows+1;
      if(fill_data !== fill_mem[fill_drive_index*ROWS_PER_TARGET+fill_row] ||
         vi_out_buffer !== wave_index_mem[fill_drive_index][0] ||
         vi_out_stream !== (fill_row>=ROWS_PER_STREAM) ||
         vi_out_slot !== ((fill_row>>4)&6'h3f) || vi_out_slice !== (fill_row&4'hf))
        $fatal(1,"cluster V ingress canonical row mismatch");
    end
    if(pending_summary && (vi_inputs!=131072 || vi_rows!=65536 || vi_targets!=32))
      $fatal(1,"cluster V ingress coverage mismatch");
  end
  initial begin
    wait(rst_n);
    for(vc=0;vc<COMMANDS;vc=vc+1) begin
      wait(fill_command==vc && fill_row>=0);
      for(vb=0;vb<128;vb=vb+1) begin
        @(negedge clk); vi_block=vb; vi_block_target=1;
        while(!vi_block_ready) @(negedge clk);
        @(negedge clk); vi_block_target=0;
        for(vf=0;vf<32;vf=vf+1) begin
          vi_valid=1;
          vi_address=524288+head_base_mem[vc][4:3]*131072+vb*1024+vf*32;
          vi_data=canonical_v[vc*4096+vb*32+vf];
          while(!vi_ready) @(negedge clk);
          @(negedge clk);
        end
        vi_valid=0;
      end
      wait(fill_command==vc+1);
    end
  end
"""
    return tb.replace("  always #5 clk = ~clk;", body + "\n  always #5 clk = ~clk;", 1)
