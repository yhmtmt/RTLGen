from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("producers", [53, 54])
@pytest.mark.parametrize("head", range(4))
def test_complete_paired_head_through_transposer(tmp_path, producers, head):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    extra = 64 - producers
    assignments = [(producer << 1) | block for producer in range(producers)
                   for block in range(2 if head * extra <= producer < (head + 1) * extra else 1)]
    assert len(assignments) == 64
    (tmp_path / "mapping.hex").write_text("".join(f"{v:02x}\n" for v in assignments))
    tb.write_text('''module tb;
reg clk=0; always #5 clk=~clk;
reg rst=0,hv=0; wire hr,sv,sr,sl,sd,se;
wire [19:0] address; wire [16:0] offset; wire resident;
reg [4:0] flit=0; integer inputs=0,outputs=0,cycle=0;
wire ir,kv,ke; wire [255:0] kd;
wire [5:0] kp,kpair; wire [1:0] kh; wire kb,kl;
reg [6:0] mapping[0:63];
reg held=0; reg [271:0] previous;
wire [271:0] key_bundle={kd,kp,kpair,kh,kb,kl};
wire kr=(cycle%7!=2 && cycle%7!=3);
wire iv=sv;
wire [19:0] byte_address=address+{10'd0,flit,5'd0};
function automatic [7:0] tensor_byte;
 input integer slot,stream,token,dimension;
 begin tensor_byte=(slot*13+stream*71+token*17+dimension*3)&255; end
endfunction
function automatic [255:0] ingress_payload;
 input [19:0] a;
 integer b;
 begin
  for(b=0;b<32;b=b+1)
   ingress_payload[b*8+:8]=tensor_byte(a[15:10],a[16],a[9:7],a[6:0]+b);
 end
endfunction
assign sr=iv && ir && flit==31;
attention_kv_paired_head_schedule schedule(.clk(clk),.rst_n(rst),
 .head_valid(hv),.head_ready(hr),.head_kv_head(2'dHEAD_INDEX),
 .head_resident_prefix_bytes(18'd16384),.span_valid(sv),.span_ready(sr),
 .span_canonical_address(address),.span_head_byte_offset(offset),
 .span_resident(resident),.span_last(sl),.head_done(sd),.protocol_error(se));
attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS(PRODUCER_COUNT)) transpose(
 .clk(clk),.rst_n(rst),.ingress_valid(iv),.ingress_ready(ir),
 .ingress_tile_byte_addr(byte_address),.ingress_data(ingress_payload(byte_address)),
 .ingress_byte_valid(32'hffffffff),.key_valid(kv),.key_ready(kr),
 .key_data(kd),.key_producer(kp),.key_kv_head(kh),.key_producer_block(kb),
 .key_dimension_pair(kpair),.key_last(kl),.protocol_error(ke));
reg [255:0] expected_data;
integer half_index,token_index;
always @(posedge clk) if(rst) begin
 cycle<=cycle+1;
 if(se||ke) $fatal(1,"protocol error");
 if(held && (!kv || key_bundle !== previous)) $fatal(1,"unstable key output");
 held=kv&&!kr;previous=key_bundle;
 if(iv&&ir) begin inputs<=inputs+1; flit<=flit+1'b1; end
 if(kv&&kr) begin
  if(kh!=HEAD_INDEX || {kp,kb}!==mapping[outputs/64] || kpair!=outputs%64 || kl!=(outputs%64==63))
   $fatal(1,"producer/head/dimension metadata mismatch %0d",outputs);
  for(half_index=0;half_index<2;half_index=half_index+1)
   for(token_index=0;token_index<16;token_index=token_index+1)
    expected_data[(half_index*16+token_index)*8+:8]=tensor_byte(
     outputs/64,token_index/8,token_index%8,(outputs%64)*2+half_index);
  if(kd !== expected_data) $fatal(1,"numerical transpose mismatch %0d",outputs);
  outputs<=outputs+1;
 end
 if(outputs==4096) begin
  if(inputs!=4096) $fatal(1,"input count");
  $display("PASS full paired head"); $finish;
 end
end
initial begin $readmemh("mapping.hex",mapping); repeat(3) @(negedge clk); rst=1; hv=1;
 @(negedge clk); hv=0; end
initial begin #200000; $fatal(1,"timeout"); end
endmodule
'''.replace("PRODUCER_COUNT", str(producers)).replace("HEAD_INDEX", str(head)))
    binary = tmp_path / "simv"
    rtl = ROOT / "npu/sim/rtl"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
        str(rtl / "attention_kv_paired_head_schedule.sv"),
        str(rtl / "attention_score32_exact_kv_key_pingpong_transpose.sv")],
        check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS full paired head" in result.stdout
