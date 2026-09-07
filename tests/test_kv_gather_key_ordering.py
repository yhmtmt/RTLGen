"""Reproduce the canonical gather/K-transposer ordering boundary in RTL."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("paired", [False, True])
def test_next_gather_block_requires_matching_second_stream(tmp_path, paired):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    # 32 flits fill stream zero of slot zero. The 33rd ascending flit
    # belongs to slot one; paired delivery instead supplies stream one.
    tb = tmp_path / "tb.sv"
    tb.write_text('''module tb;
reg clk=0; always #5 clk=~clk;
reg rst_n=0, valid=0;
reg [19:0] address=0;
wire ready, error;
attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS(53)) dut (
 .clk(clk), .rst_n(rst_n), .ingress_valid(valid), .ingress_ready(ready),
 .ingress_tile_byte_addr(address), .ingress_data(256'd0),
 .ingress_byte_valid(32'hffffffff), .key_ready(1'b1), .protocol_error(error));
integer i;
initial begin
 repeat(3) @(negedge clk); rst_n=1;
 for(i=0;i<33;i=i+1) begin
   @(negedge clk); valid=1;
   address=(i==32) ? NEXT_ADDRESS : i*32;
   if(!ready) $fatal(1,"unexpected backpressure");
   @(posedge clk); #1;
   if(i<32 && error) $fatal(1,"premature error");
 end
 if(error !== EXPECT_ERROR) $fatal(1,"ordering diagnostic mismatch");
 $display("PASS ordering boundary"); $finish;
end
initial begin #10000; $fatal(1,"timeout"); end
endmodule
'''.replace("NEXT_ADDRESS", "20'h10000" if paired else "20'h00400")
        .replace("EXPECT_ERROR", "1'b0" if paired else "1'b1"))
    binary = tmp_path / "simv"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
        str(ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv")],
        check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS ordering boundary" in result.stdout
