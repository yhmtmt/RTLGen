"""Canonical paired-flit transpose through live K/Q stage and one producer."""
from pathlib import Path

from npu.eval.canonical_attention_staged_inputs import CanonicalStagedInputs


class CanonicalTransposedInputs(CanonicalStagedInputs):
    def identity(self):
        return {**super().identity(), "kind": "canonical_tensor_live_transpose_stage_producer",
                "live_key_transpose": True, "live_paired_head_schedule": True,
                "other_producer_keys": "canonical_tensor"}

    def rtl_sources(self):
        rtl = Path(__file__).resolve().parents[1] / "sim/rtl"
        return super().rtl_sources() + [str(rtl / name) for name in (
            "attention_score32_exact_kv_key_pingpong_transpose.sv",
            "attention_kv_paired_head_schedule.sv")]

    def transform_testbench(self, tb):
        tb = super().transform_testbench(tb)
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
                raise ValueError("transpose stage anchor changed: " + old)
            tb = tb.replace(old, new)
        start = tb.index(f"      for(sp=0;sp<{self.producers};sp=sp+1)")
        end = tb.index("      wait(stage_complete);", start)
        tb = tb[:start] + """      schedule_head_valid=1;
      while(!schedule_head_ready) @(negedge clk);
      @(negedge clk); schedule_head_valid=0;
      wait(schedule_done); @(negedge clk);
""" + tb[end:]
        memory_init = "\n".join(
            f"canonical_k[{a//32}]=256'h{int.from_bytes(self.fixture.memory_flit(tile=self.tile, address=a), 'little'):064x};"
            for a in range(0, 4*131072, 32))
        wiring = f"""
  reg [255:0] canonical_k[0:16383];
  wire trans_input_valid;
  wire trans_input_ready, trans_valid, trans_error, trans_last, trans_block;
  wire [19:0] trans_address;
  wire [255:0] trans_input_data;
  reg schedule_head_valid=0;
  wire schedule_head_ready, schedule_valid, schedule_ready, schedule_done, schedule_error;
  wire [19:0] schedule_address;
  reg [4:0] schedule_flit=0;
  integer schedule_spans=0;
  wire [255:0] trans_data;
  wire [1:0] trans_head;
  wire [5:0] trans_producer, trans_pair;
  integer trans_inputs=0, trans_outputs=0;
  attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS({self.producers})) trans_dut (
    .clk(clk), .rst_n(rst_n), .ingress_valid(trans_input_valid), .ingress_ready(trans_input_ready),
    .ingress_tile_byte_addr(trans_address), .ingress_data(trans_input_data), .ingress_byte_valid(32'hffffffff),
    .key_valid(trans_valid), .key_ready(stage_kready), .key_producer(trans_producer),
    .key_kv_head(trans_head), .key_producer_block(trans_block), .key_dimension_pair(trans_pair),
    .key_data(trans_data), .key_last(trans_last), .protocol_error(trans_error));
  attention_kv_paired_head_schedule schedule_dut (
    .clk(clk), .rst_n(rst_n), .head_valid(schedule_head_valid), .head_ready(schedule_head_ready),
    .head_kv_head(stage_head), .head_resident_prefix_bytes(18'd16384),
    .span_valid(schedule_valid), .span_ready(schedule_ready), .span_canonical_address(schedule_address),
    .span_head_byte_offset(), .span_resident(), .span_last(), .head_done(schedule_done),
    .protocol_error(schedule_error));
  assign trans_input_valid = schedule_valid;
  assign trans_address = schedule_address + {{10'd0,schedule_flit,5'd0}};
  assign trans_input_data = canonical_k[trans_address/32];
  assign schedule_ready = trans_input_ready && schedule_flit==31;
  always @(posedge clk) begin
    if(!rst_n) schedule_flit<=0;
    else if(trans_input_valid && trans_input_ready) schedule_flit<=schedule_flit+1'b1;
  end
  always @(posedge clk) if(rst_n) begin
    if(schedule_error) $fatal(1,"paired schedule protocol error");
    if(schedule_valid && schedule_ready) schedule_spans=schedule_spans+1;
    if(trans_error) $fatal(1,"live transpose protocol error");
    if(trans_input_valid && trans_input_ready) trans_inputs=trans_inputs+1;
    if(trans_valid && stage_kready) trans_outputs=trans_outputs+1;
    if(finish_pending && (trans_inputs!=16384 || trans_outputs!=16384 || schedule_spans!=512))
      $fatal(1,"live transpose coverage mismatch");
  end
  initial begin
    {memory_init}
  end
"""
        anchor = "  always #5 clk = ~clk;"
        if tb.count(anchor) != 1:
            raise ValueError("transpose clock anchor changed")
        declarations, body = wiring.split("  attention_score32_exact_kv_key_pingpong_transpose", 1)
        # Icarus requires procedural references to be declared before use.
        tb = tb.replace("module tb;", "module tb;\n" + declarations, 1)
        return tb.replace(anchor, "  attention_score32_exact_kv_key_pingpong_transpose" + body + "\n" + anchor)
