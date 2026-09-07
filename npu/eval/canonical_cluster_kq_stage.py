"""Connect the real wide K/Q stage to every producer in a cluster replay."""


def attach_cluster_kq_stage(tb: str, *, producers: int) -> str:
    if producers not in (53, 54):
        raise ValueError("invalid producer family")
    anchor = "wire command_valid = rst_n && preload_complete && (issued < COMMANDS);"
    if tb.count(anchor) != 1:
        raise ValueError("cluster command anchor changed")
    tb = tb.replace(anchor, "wire command_valid = stage_armed && stage_command_ready && rst_n && preload_complete && (issued < COMMANDS);")
    start = tb.index("    input_valid = '0; input_last = '0; input_query = '0; input_key = '0;")
    end = tb.index("  always @(posedge clk) begin", start)
    tb = tb[:start] + """    input_valid = stage_valid;
    input_last = stage_last;
    input_query = stage_query;
    input_key = stage_key;
  end
""" + tb[end:]
    decl = f"""
  reg stage_armed=0,stage_fill=0,stage_qv=0,stage_kv=0;
  reg [1:0] stage_head=0;
  reg [6:0] stage_dimension=0;
  reg [63:0] stage_qdata=0;
  reg [5:0] stage_producer=0,stage_pair=0;
  reg stage_block=0;
  reg [255:0] stage_kdata=0;
  wire stage_fill_ready,stage_query_ready,stage_key_ready,stage_complete;
  wire stage_command_ready,stage_done,stage_error;
  wire [{producers-1}:0] stage_valid,stage_last;
  wire [{producers*128-1}:0] stage_query,stage_key;
  integer sc,sp,sb,sd,stage_start,stage_blocks,check_p,check_flat;
  integer stage_stalls=0;
  reg [{producers-1}:0] stage_held=0;
  reg [256:0] stage_previous[0:{producers-1}];
"""
    tb = tb.replace("  wire preload_complete", decl + "\n  wire preload_complete", 1)
    body = f"""
  attention_score32_exact_kv_key_stage_wide #(.PRODUCERS({producers})) stage_dut (
    .clk(clk),.rst_n(rst_n),.fill_target_valid(stage_fill),.fill_target_ready(stage_fill_ready),
    .fill_target_kv_head(stage_head),.query_write_valid(stage_qv),.query_write_ready(stage_query_ready),
    .query_write_kv_head(stage_head),.query_write_dimension(stage_dimension),.query_write_data(stage_qdata),
    .query_write_last(stage_dimension==127),.key_write_valid(stage_kv),.key_write_ready(stage_key_ready),
    .key_write_kv_head(stage_head),.key_write_producer(stage_producer),.key_write_producer_block(stage_block),
    .key_write_dimension_pair(stage_pair),.key_write_data(stage_kdata),.key_write_last(stage_pair==63),
    .fill_complete(stage_complete),.command_valid(command_valid && command_ready),
    .command_ready(stage_command_ready),.command_kv_head(stage_head),.producer_valid(stage_valid),
    .producer_ready(input_ready),.producer_last(stage_last),.producer_query(stage_query),
    .producer_key(stage_key),.command_done(stage_done),.protocol_error(stage_error));
  always @(posedge clk) if(rst_n) begin
    if(stage_error) $fatal(1,"cluster K/Q stage protocol error");
    for(check_p=0;check_p<PRODUCERS;check_p=check_p+1) begin
      if(stage_held[check_p] && (!input_valid[check_p] ||
         {{input_query[check_p*128+:128],input_key[check_p*128+:128],input_last[check_p]}} !== stage_previous[check_p]))
        $fatal(1,"cluster stage changed stalled producer beat");
      stage_held[check_p]=input_valid[check_p] && !input_ready[check_p];
      stage_previous[check_p]={{input_query[check_p*128+:128],input_key[check_p*128+:128],input_last[check_p]}};
      if(stage_held[check_p]) stage_stalls=stage_stalls+1;
      if(input_valid[check_p] && input_ready[check_p]) begin
        check_flat=check_p*MAX_BEATS+beat_issue[check_p];
        if(input_query[check_p*128+:128] !== query_mem[check_flat] ||
           input_key[check_p*128+:128] !== key_mem[check_flat] || input_last[check_p] !== last_mem[check_flat])
          $fatal(1,"cluster stage canonical input mismatch");
      end
    end
    if(pending_summary && stage_stalls==0) $fatal(1,"cluster stage backpressure was not exercised");
  end
  initial begin
    wait(rst_n);
    for(sc=0;sc<COMMANDS;sc=sc+1) begin
      @(negedge clk); stage_head=head_base_mem[sc][4:3]; stage_fill=1;
      while(!stage_fill_ready) @(negedge clk);
      @(negedge clk); stage_fill=0;
      stage_start=sc==0 ? 0 : beat_limit_mem[sc-1][0];
      for(sd=0;sd<128;sd=sd+1) begin
        stage_qv=1; stage_dimension=sd; stage_qdata=query_mem[stage_start+sd][63:0];
        @(negedge clk);
      end
      stage_qv=0;
      for(sp=0;sp<PRODUCERS;sp=sp+1) begin
        stage_start=sc==0 ? 0 : beat_limit_mem[sc-1][sp];
        stage_blocks=(beat_limit_mem[sc][sp]-stage_start)/128;
        for(sb=0;sb<stage_blocks;sb=sb+1) for(sd=0;sd<64;sd=sd+1) begin
          stage_kv=1; stage_producer=sp; stage_block=sb; stage_pair=sd;
          stage_kdata={{key_mem[sp*MAX_BEATS+stage_start+sb*128+sd*2+1],key_mem[sp*MAX_BEATS+stage_start+sb*128+sd*2]}};
          @(negedge clk);
        end
      end
      stage_kv=0;
      wait(stage_complete); @(negedge clk); stage_armed=1;
      wait(issued==sc+1); @(negedge clk); stage_armed=0;
      wait(stage_done);
    end
  end
"""
    anchor = "  always #5 clk = ~clk;"
    if tb.count(anchor) != 1:
        raise ValueError("cluster clock anchor changed")
    return tb.replace(anchor, body + "\n" + anchor)
