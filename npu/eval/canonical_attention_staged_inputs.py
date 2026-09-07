"""Bounded live wide-K/Q-stage to numerical producer testbench composition."""
from pathlib import Path

from npu.eval.canonical_attention_producer_inputs import CanonicalProducerInputs
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    exact_local_cluster_gqa8_command_block_counts,
)


class CanonicalStagedInputs(CanonicalProducerInputs):
    def identity(self):
        return {**super().identity(), "kind": "canonical_tensor_live_kq_stage_producer",
                "live_kq_stage": True, "other_producer_keys": "zero_fill",
                "live_mesh": False, "live_value_ingress": False}

    def rtl_sources(self):
        return [str(Path(__file__).resolve().parents[1] / "sim/rtl/attention_score32_exact_kv_key_stage_wide.sv")]

    def transform_testbench(self, tb):
        def replace_once(old, new):
            nonlocal tb
            if tb.count(old) != 1:
                raise ValueError("staged probe testbench anchor changed: " + old)
            tb = tb.replace(old, new)

        replace_once("command_valid = rst_n &&", "command_valid = stage_armed && stage_command_ready && rst_n &&")
        start = tb.index("    input_valid = rst_n &&")
        end = tb.index("    value_read_req_ready[0]", start)
        tb = tb[:start] + f"""    input_valid = stage_valid[{self.producer}];
    input_query = stage_query[{self.producer}*128+:128];
    input_key = stage_key[{self.producer}*128+:128];
    input_last = stage_last[{self.producer}];
""" + tb[end:]
        counts = "\n".join(f"stage_counts[{g*self.producers+p}]={n};"
            for g in range(4) for p, n in enumerate(exact_local_cluster_gqa8_command_block_counts(
                producers=self.producers, group_index=g)))
        stage = f"""
  reg stage_armed=0, stage_fill=0, stage_qv=0, stage_kv=0;
  wire stage_fill_ready, stage_qready, stage_kready, stage_complete;
  wire stage_command_ready, stage_done, stage_error;
  reg [1:0] stage_head=0;
  reg [6:0] stage_dim=0;
  reg [63:0] stage_qdata=0;
  reg [5:0] stage_producer=0, stage_pair=0;
  reg stage_block=0;
  reg [255:0] stage_kdata=0;
  wire [{self.producers-1}:0] stage_valid, stage_last;
  reg [{self.producers-1}:0] stage_ready;
  wire [{self.producers*128-1}:0] stage_query, stage_key;
  integer stage_counts[0:{4*self.producers-1}];
  integer sg, sp, sb, sd, stage_offset;
  integer stage_stalls=0;
  reg stage_held=0;
  reg [256:0] stage_previous;
  always @* begin
    stage_ready = '1;
    stage_ready[{self.producer}] = input_ready;
  end
  attention_score32_exact_kv_key_stage_wide #(.PRODUCERS({self.producers})) stage_dut (
    .clk(clk), .rst_n(rst_n), .fill_target_valid(stage_fill), .fill_target_ready(stage_fill_ready),
    .fill_target_kv_head(stage_head), .query_write_valid(stage_qv), .query_write_ready(stage_qready),
    .query_write_kv_head(stage_head), .query_write_dimension(stage_dim), .query_write_data(stage_qdata),
    .query_write_last(stage_dim==127), .key_write_valid(stage_kv), .key_write_ready(stage_kready),
    .key_write_kv_head(stage_head), .key_write_producer(stage_producer),
    .key_write_producer_block(stage_block), .key_write_dimension_pair(stage_pair),
    .key_write_data(stage_kdata), .key_write_last(stage_pair==63), .fill_complete(stage_complete),
    .command_valid(command_valid && command_ready), .command_ready(stage_command_ready),
    .command_kv_head(stage_head), .producer_valid(stage_valid), .producer_ready(stage_ready),
    .producer_last(stage_last), .producer_query(stage_query), .producer_key(stage_key),
    .command_done(stage_done), .protocol_error(stage_error));
  always @(posedge clk) if(rst_n) begin
    if(stage_error) $fatal(1,"live K/Q stage protocol error");
    if(stage_held && (!input_valid || {{input_query,input_key,input_last}} !== stage_previous))
      $fatal(1,"live K/Q stage changed a stalled beat");
    stage_held = input_valid && !input_ready;
    stage_previous = {{input_query,input_key,input_last}};
    if(stage_held) stage_stalls = stage_stalls + 1;
    if(finish_pending && stage_stalls==0) $fatal(1,"producer backpressure was not exercised");
    if(input_valid && input_ready &&
       (input_query !== query_mem[input_index] || input_key !== key_mem[input_index] ||
        input_last !== last_mem[input_index])) $fatal(1,"live K/Q stage input mismatch");
  end
  initial begin
    {counts}
    wait(rst_n);
    for(sg=0;sg<4;sg=sg+1) begin
      @(negedge clk); stage_head=sg; stage_fill=1;
      while(!stage_fill_ready) @(negedge clk);
      @(negedge clk); stage_fill=0;
      stage_offset=sg==0 ? 0 : cmd_beat_limit_mem[sg-1];
      for(sd=0;sd<128;sd=sd+1) begin
        stage_qv=1; stage_dim=sd; stage_qdata=query_mem[stage_offset+sd][63:0];
        @(negedge clk);
        if(!stage_qready && sd!=127) $fatal(1,"query fill unexpectedly blocked");
      end
      stage_qv=0;
      for(sp=0;sp<{self.producers};sp=sp+1)
        for(sb=0;sb<stage_counts[sg*{self.producers}+sp];sb=sb+1)
          for(sd=0;sd<64;sd=sd+1) begin
            stage_kv=1; stage_producer=sp; stage_block=sb; stage_pair=sd;
            stage_kdata=sp=={self.producer} ?
              {{key_mem[stage_offset+sb*128+sd*2+1],key_mem[stage_offset+sb*128+sd*2]}} : 256'd0;
            @(negedge clk);
          end
      stage_kv=0;
      wait(stage_complete); @(negedge clk); stage_armed=1;
      wait(issued_commands==sg+1); @(negedge clk); stage_armed=0;
      wait(stage_done);
      wait(command_completed_count==sg+1);
    end
  end
"""
        replace_once("  always #5 clk = ~clk;", stage + "\n  always #5 clk = ~clk;")
        return tb
