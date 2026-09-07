from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("producers", [53, 54])
def test_complete_paired_head_through_transposer(tmp_path, producers):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    tb.write_text('''module tb;
reg clk=0; always #5 clk=~clk;
reg rst=0,hv=0; wire hr,sv,sr,sl,sd,se;
wire [19:0] address; wire [16:0] offset; wire resident;
reg [4:0] flit=0; integer inputs=0,outputs=0,cycle=0;
wire ir,kv,ke; wire [255:0] kd;
wire kr=(cycle%7!=2 && cycle%7!=3);
wire iv=sv;
wire [7:0] byte_value={2'd0,offset[15:10]};
wire [19:0] byte_address=address+{10'd0,flit,5'd0};
assign sr=iv && ir && flit==31;
attention_kv_paired_head_schedule schedule(.clk(clk),.rst_n(rst),
 .head_valid(hv),.head_ready(hr),.head_kv_head(2'd2),
 .head_resident_prefix_bytes(18'd16384),.span_valid(sv),.span_ready(sr),
 .span_canonical_address(address),.span_head_byte_offset(offset),
 .span_resident(resident),.span_last(sl),.head_done(sd),.protocol_error(se));
attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS(PRODUCER_COUNT)) transpose(
 .clk(clk),.rst_n(rst),.ingress_valid(iv),.ingress_ready(ir),
 .ingress_tile_byte_addr(byte_address),.ingress_data({32{byte_value}}),
 .ingress_byte_valid(32'hffffffff),.key_valid(kv),.key_ready(kr),
 .key_data(kd),.protocol_error(ke));
reg [7:0] expected_byte;
always @(posedge clk) if(rst) begin
 cycle<=cycle+1;
 if(se||ke) $fatal(1,"protocol error");
 if(iv&&ir) begin inputs<=inputs+1; flit<=flit+1'b1; end
 if(kv&&kr) begin
  expected_byte=outputs/64;
  if(kd !== {32{expected_byte}}) $fatal(1,"numerical transpose mismatch %0d",outputs);
  outputs<=outputs+1;
 end
 if(outputs==4096) begin
  if(inputs!=4096) $fatal(1,"input count");
  $display("PASS full paired head"); $finish;
 end
end
initial begin repeat(3) @(negedge clk); rst=1; hv=1;
 @(negedge clk); hv=0; end
initial begin #200000; $fatal(1,"timeout"); end
endmodule
'''.replace("PRODUCER_COUNT", str(producers)))
    binary = tmp_path / "simv"
    rtl = ROOT / "npu/sim/rtl"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
        str(rtl / "attention_kv_paired_head_schedule.sv"),
        str(rtl / "attention_score32_exact_kv_key_pingpong_transpose.sv")],
        check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS full paired head" in result.stdout
