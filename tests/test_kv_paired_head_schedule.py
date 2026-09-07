from pathlib import Path
import shutil
import subprocess

import pytest
from npu.sim.perf.attention_kv_paired_gather import key_head_spans

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("prefix", [0, 16384, 131072, 512, 132096])
def test_paired_head_rtl_matches_model_under_stalls(tmp_path, prefix):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    tb.write_text('''module tb;
reg clk=0; always #5 clk=~clk;
reg rst=0,hv=0,ready=0;
wire hr,v,last,done,error,resident;
wire [19:0] address; wire [16:0] offset;
integer cycle=0,count=0; reg held=0; reg [38:0] previous;
attention_kv_paired_head_schedule dut(.clk(clk),.rst_n(rst),
 .head_valid(hv),.head_ready(hr),.head_kv_head(2'd3),
 .head_resident_prefix_bytes(18'dPREFIX),.span_valid(v),.span_ready(ready),
 .span_canonical_address(address),.span_head_byte_offset(offset),
 .span_resident(resident),.span_last(last),.head_done(done),.protocol_error(error));
always @(negedge clk) begin cycle=cycle+1; ready=(cycle%5!=0 && cycle%5!=1); end
always @(posedge clk) if(rst) begin
 if(error) begin
   if(EXPECT_ERROR && !v && !hr && !done && count==0) begin
     $display("PASS invalid prefix rejected"); $finish;
   end
   $fatal(1,"protocol error");
 end
 if(held && (!v || previous !== {address,offset,resident,last})) $fatal(1,"stall instability");
 held=v&&!ready; previous={address,offset,resident,last};
 if(v&&ready) begin
  $display("SPAN %0d %0d %0d %0d",address,offset,resident,last);
  count=count+1;
 end
 if(done) begin if(count!=128) $fatal(1,"count"); $finish; end
end
initial begin repeat(3) @(negedge clk); rst=1; hv=1;
 @(negedge clk); hv=0; end
initial begin #20000; $fatal(1,"timeout"); end
endmodule
'''.replace("PREFIX", str(prefix)).replace("EXPECT_ERROR", "1" if prefix in (512, 132096) else "0"))
    binary = tmp_path / "simv"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
        str(ROOT / "npu/sim/rtl/attention_kv_paired_head_schedule.sv")],
        check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    if prefix in (512, 132096):
        assert "PASS invalid prefix rejected" in result.stdout
        return
    observed = [tuple(map(int, line.split()[1:])) for line in result.stdout.splitlines() if line.startswith("SPAN ")]
    expected = [(3*131072+s.canonical_offset, s.canonical_offset, int(s.resident), int(i==127))
                for i,s in enumerate(key_head_spans(resident_prefix_bytes=prefix))]
    assert observed == expected
