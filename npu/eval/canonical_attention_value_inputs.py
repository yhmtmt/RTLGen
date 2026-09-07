"""Live K and V ingress with a testbench V response store, not physical SRAM."""
from pathlib import Path
import re

from npu.eval.canonical_attention_transposed_inputs import CanonicalTransposedInputs
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import exact_local_cluster_gqa8_slot_bases


class CanonicalValueIngressInputs(CanonicalTransposedInputs):
    def identity(self):
        return {**super().identity(), "kind": "canonical_tensor_kv_ingress_producer",
                "live_value_ingress": True, "value_response_store": "testbench_array",
                "physical_sram_service": False}

    def rtl_sources(self):
        rtl = Path(__file__).resolve().parents[1] / "sim/rtl"
        return super().rtl_sources() + [str(rtl / n) for n in (
            "attention_score32_exact_kv_value_ingress.sv", "attention_score32_exact_kv_ingress_transpose.sv")]

    def transform_testbench(self, tb):
        tb = super().transform_testbench(tb)
        tb, removed = re.subn(r"    value_mem\[\d+\] = 512'h[0-9a-f]+;", "", tb)
        if removed != sum(self.counts()) * 32:
            raise ValueError("V preload removal coverage mismatch")
        anchor = "      schedule_head_valid=1;"
        if tb.count(anchor) != 1:
            raise ValueError("V fill sequencing anchor changed")
        tb = tb.replace(anchor, """      vi_target=1;
      while(!vi_target_ready) @(negedge clk);
      @(negedge clk); vi_target=0;
      for(vs=0;vs<2;vs=vs+1) for(vb=0;vb<64;vb=vb+1) begin
        vi_stream=vs; vi_slot=vb; vi_block_target=1;
        while(!vi_block_ready) @(negedge clk);
        @(negedge clk); vi_block_target=0;
        for(vf=0;vf<32;vf=vf+1) begin
          vi_address=524288+sg*131072+vs*65536+vb*1024+vf*32;
          vi_data=canonical_v[(vi_address-524288)/32]; vi_valid=1;
          @(posedge clk); while(!vi_ready) @(posedge clk);
          @(negedge clk); vi_valid=0;
        end
      end
      wait(vi_complete); @(negedge clk);
""" + anchor)
        tb = tb.replace("if (cycle > 60000)", "if (cycle > 120000)")
        init = "\n".join(f"canonical_v[{a//32}]=256'h{int.from_bytes(self.fixture.memory_flit(tile=self.tile, address=524288+a), 'little'):064x};"
            for a in range(0, 524288, 32))
        bases = "\n".join(f"vi_bases[{g}]={exact_local_cluster_gqa8_slot_bases(producers=self.producers, group_index=g)[self.producer]};"
            for g in range(4))
        declarations = """
  reg [255:0] canonical_v[0:16383];
  reg vi_target=0,vi_block_target=0,vi_stream=0,vi_valid=0;
  reg [5:0] vi_slot=0;
  reg [19:0] vi_address=0;
  reg [255:0] vi_data=0;
  wire vi_target_ready,vi_block_ready,vi_ready,vi_complete,vi_error;
  wire vi_out_valid,vi_out_stream;
  wire [5:0] vi_out_slot;
  wire [3:0] vi_out_slice;
  wire [511:0] vi_out_data;
  wire vi_out_ready;
  integer vs,vb,vf,vi_rows=0,vi_inputs=0,vi_store_index;
  integer vi_bases[0:3];
  reg vi_written[0:2*TOTAL_BLOCKS*16-1];
  integer vi_init_index;
"""
        # TOTAL_BLOCKS is a localparam declared at the beginning of the base TB.
        decl_anchor = "  reg command_valid;"
        if tb.count(decl_anchor) != 1:
            raise ValueError("V declarations anchor changed")
        tb = tb.replace(decl_anchor, declarations + decl_anchor)
        body = f"""
  attention_score32_exact_kv_value_ingress #(.PRODUCERS({self.producers})) vi_dut (
    .clk(clk),.rst_n(rst_n),.fill_target_valid(vi_target),.fill_target_ready(vi_target_ready),
    .fill_target_buffer_sel(1'b0),.fill_target_command_id(cmd_id_mem[sg]),
    .fill_target_head_base(cmd_head_base_mem[sg]),.fill_target_wave_index(3'd0),
    .endpoint_fill_target_valid(),.endpoint_fill_target_ready(1'b1),
    .endpoint_fill_target_buffer_sel(),.endpoint_fill_target_command_id(),
    .endpoint_fill_target_head_base(),.endpoint_fill_target_wave_index(),
    .block_target_valid(vi_block_target),.block_target_ready(vi_block_ready),
    .block_target_kv_head(stage_head),.block_target_stream(vi_stream),.block_target_slot(vi_slot),
    .ingress_valid(vi_valid),.ingress_ready(vi_ready),.ingress_tile_byte_addr(vi_address),
    .ingress_data(vi_data),.ingress_byte_valid(32'hffffffff),
    .endpoint_fill_valid(vi_out_valid),.endpoint_fill_ready(vi_out_ready),
    .endpoint_fill_buffer_sel(),.endpoint_fill_stream(vi_out_stream),
    .endpoint_fill_block_slot(vi_out_slot),.endpoint_fill_slice(vi_out_slice),
    .endpoint_fill_data(vi_out_data),.fill_complete(vi_complete),.fill_active(),
    .completed_block_count(),.protocol_error(vi_error));
  assign vi_out_ready = cycle%5!=2;
  always @(posedge clk) if(rst_n) begin
    if(vi_error) $fatal(1,"live V ingress protocol error");
    if(vi_valid && vi_ready) vi_inputs=vi_inputs+1;
    if(vi_out_valid && vi_out_ready) begin
      vi_rows=vi_rows+1;
      if(vi_out_slot>=vi_bases[sg] && vi_out_slot<vi_bases[sg]+cmd_block_count_mem[sg]) begin
        vi_store_index=(vi_out_stream*TOTAL_BLOCKS+cmd_block_offset_mem[sg]+vi_out_slot-vi_bases[sg])*16+vi_out_slice;
        if(vi_written[vi_store_index]) $fatal(1,"duplicate V store row");
        value_mem[vi_store_index]=vi_out_data; vi_written[vi_store_index]=1;
      end
    end
    if(value_read_req_valid[0] && value_read_req_ready[0] &&
       !vi_written[(cmd_block_offset_mem[active_cmd0]+value_read_req_address[13:0])*16+value_read_req_slice[3:0]])
      $fatal(1,"V stream0 read before ingress fill");
    if(value_read_req_valid[1] && value_read_req_ready[1] &&
       !vi_written[(TOTAL_BLOCKS+cmd_block_offset_mem[active_cmd1]+value_read_req_address[27:14])*16+value_read_req_slice[7:4]])
      $fatal(1,"V stream1 read before ingress fill");
    if(finish_pending && (vi_rows!=8192 || vi_inputs!=16384)) $fatal(1,"V ingress coverage mismatch");
  end
  initial begin
    for(vi_init_index=0;vi_init_index<2*TOTAL_BLOCKS*16;vi_init_index=vi_init_index+1) begin
      vi_written[vi_init_index]=0; value_mem[vi_init_index]='x;
    end
    {bases}
    {init}
  end
"""
        return tb.replace("  always #5 clk = ~clk;", body + "\n  always #5 clk = ~clk;")
