"""Canonical ingress and selected producer using generated banked SRAM RTL."""
import re

from npu.eval.canonical_attention_value_inputs import CanonicalValueIngressInputs
from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import _top


class CanonicalSramInputs(CanonicalValueIngressInputs):
    def identity(self):
        return {**super().identity(), "kind": "canonical_tensor_ingress_sram_producer",
                "value_response_store": "generated_banked_sram_rtl",
                "physical_sram_service": False, "technology_macros": False}

    def transform_testbench(self, tb):
        tb = super().transform_testbench(tb)
        start = tb.index("      if (value_read_req_valid[0] && value_read_req_ready[0]) begin")
        end = tb.index("      if (result_valid && result_ready) begin", start)
        tb = tb[:start] + tb[end:]
        tb = re.sub(r"^\s*value_response_(?:valid|address|slice|matrix)\s*(?:<=|=)\s*0;\n", "\n", tb, flags=re.M)
        tb = re.sub(r"reg(\s+(?:\[[^\]]+\]\s+)?value_response_(?:valid|address|slice|matrix);)", r"wire\1", tb)
        tb = re.sub(r"reg(\s+\[1:0\]\s+value_read_req_ready;)", r"wire\1", tb)
        tb = re.sub(r"^    value_read_req_ready\[[01]\] = .*;\n", "", tb, flags=re.M)
        tb = tb.replace("command_valid = stage_armed &&", "command_valid = sram_command_ready && stage_armed &&")
        tb = tb.replace(".endpoint_fill_target_valid(),.endpoint_fill_target_ready(1'b1)",
                        ".endpoint_fill_target_valid(sram_target_valid),.endpoint_fill_target_ready(sram_target_ready)")
        tb = tb.replace("assign vi_out_ready = cycle%5!=2;", "assign vi_out_ready = sram_fill_ready && cycle%5!=2;")
        tb = tb.replace("      wait(command_completed_count==sg+1);", """      wait(command_completed_count==sg+1);
      @(negedge clk); sram_release=1;
      @(negedge clk); sram_release=0;""")
        lanes = self.producers * 2
        lane = self.producer * 2
        decl = f"""
  wire sram_target_valid,sram_target_ready,sram_fill_ready,sram_command_ready,sram_error;
  reg sram_release=0;
  wire [{lanes-1}:0] sr_req_ready,sr_rsp_valid;
  reg [{lanes-1}:0] sr_req_valid,sr_rsp_ready;
  reg [{lanes*14-1}:0] sr_req_addr;
  reg [{lanes*4-1}:0] sr_req_slice;
  wire [{lanes*14-1}:0] sr_rsp_addr;
  wire [{lanes*4-1}:0] sr_rsp_slice;
  wire [{lanes*512-1}:0] sr_rsp_data;
  wire [31:0] sr_fills,sr_requests,sr_responses;
"""
        tb = tb.replace("  reg command_valid;", decl + "  reg command_valid;", 1)
        wiring = f"""
  always @* begin
    sr_req_valid='0; sr_req_addr='0; sr_req_slice='0; sr_rsp_ready='0;
    sr_req_valid[{lane}+:2]=value_read_req_valid;
    sr_req_addr[{lane*14}+:28]=value_read_req_address;
    sr_req_slice[{lane*4}+:8]=value_read_req_slice;
    sr_rsp_ready[{lane}+:2]=value_response_ready;
  end
  assign value_read_req_ready=sr_req_ready[{lane}+:2];
  assign value_response_valid=sr_rsp_valid[{lane}+:2];
  assign value_response_address=sr_rsp_addr[{lane*14}+:28];
  assign value_response_slice=sr_rsp_slice[{lane*4}+:8];
  assign value_response_matrix=sr_rsp_data[{lane*512}+:1024];
  canonical_sram_service sram_dut (
    .clk(clk),.rst_n(rst_n),.fill_target_valid(sram_target_valid),.fill_target_ready(sram_target_ready),
    .fill_target_buffer_sel(1'b0),.fill_target_command_id(cmd_id_mem[sg]),
    .fill_target_head_base(cmd_head_base_mem[sg]),.fill_target_wave_index(3'd0),
    .fill_valid(vi_out_valid && cycle%5!=2),.fill_ready(sram_fill_ready),
    .fill_buffer_sel(1'b0),.fill_stream(vi_out_stream),.fill_block_slot(vi_out_slot),
    .fill_slice(vi_out_slice),.fill_data(vi_out_data),
    .command_valid(command_valid && command_ready),.command_ready(sram_command_ready),
    .command_buffer_sel(1'b0),.command_id(cmd_id_mem[issued_commands]),
    .command_head_base(cmd_head_base_mem[issued_commands]),.command_wave_index(3'd0),
    .command_release_valid(sram_release),.command_release_buffer_sel(1'b0),
    .value_read_req_valid(sr_req_valid),.value_read_req_ready(sr_req_ready),
    .value_read_req_address(sr_req_addr),.value_read_req_slice(sr_req_slice),
    .value_response_valid(sr_rsp_valid),.value_response_ready(sr_rsp_ready),
    .value_response_address(sr_rsp_addr),.value_response_slice(sr_rsp_slice),
    .value_response_matrix(sr_rsp_data),.fill_row_accept_count(sr_fills),
    .request_accept_count(sr_requests),.response_accept_count(sr_responses),.protocol_error(sram_error));
  always @(posedge clk) if(rst_n) begin
    if(sram_error) $fatal(1,"generated SRAM service protocol error");
    if(finish_pending && (sr_fills!=8192 || sr_requests==0 || sr_requests!=sr_responses))
      $fatal(1,"generated SRAM service coverage mismatch");
  end
"""
        tb = tb.replace("  always #5 clk = ~clk;", wiring + "\n  always #5 clk = ~clk;")
        return tb + "\n" + _top(top_name="canonical_sram_service", producers=self.producers)
