from pathlib import Path
import os
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("producers", [53, 54])
@pytest.mark.parametrize("head", range(4))
@pytest.mark.parametrize("with_stage", [False, True])
def test_complete_paired_head_through_transposer(tmp_path, producers, head, with_stage):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    extra = 64 - producers
    assignments = [(producer << 1) | block for producer in range(producers)
                   for block in range(2 if head * extra <= producer < (head + 1) * extra else 1)]
    assert len(assignments) == 64
    stage_init = "\n".join(
        f"base[{p}]={assignments.index(p << 1)}; blocks[{p}]={assignments.count(p << 1) + assignments.count((p << 1) | 1)}; accepted[{p}]=0;"
        for p in range(producers))
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
wire stage_ready,fill_complete,command_ready,command_done,stage_error;
wire kr=WITH_STAGE ? stage_ready : (cycle%7!=2 && cycle%7!=3);
reg fv=0,qv=0,cv=0; reg [6:0] qdim=0; reg [63:0] qdata=0;
wire fr,qr;
wire [PRODUCER_COUNT-1:0] pv,pl;
reg [PRODUCER_COUNT-1:0] pr=0;
wire [PRODUCER_COUNT*128-1:0] pq,pk;
integer base[0:PRODUCER_COUNT-1],blocks[0:PRODUCER_COUNT-1],accepted[0:PRODUCER_COUNT-1];
integer p,t,q,qi,ready_p; reg [127:0] expected_k,expected_q;
function automatic [7:0] query_byte;
 input integer dimension,lane;
 begin query_byte=(dimension*5+lane*7)&255; end
endfunction
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
attention_score32_exact_kv_key_stage_wide #(.PRODUCERS(PRODUCER_COUNT)) stage (
 .clk(clk),.rst_n(rst),.fill_target_valid(fv),.fill_target_ready(fr),.fill_target_kv_head(2'dHEAD_INDEX),
 .query_write_valid(qv),.query_write_ready(qr),.query_write_kv_head(2'dHEAD_INDEX),
 .query_write_dimension(qdim),.query_write_data(qdata),.query_write_last(qdim==127),
 .key_write_valid(WITH_STAGE && kv),.key_write_ready(stage_ready),.key_write_kv_head(kh),
 .key_write_producer(kp),.key_write_producer_block(kb),.key_write_dimension_pair(kpair),
 .key_write_data(kd),.key_write_last(kl),.fill_complete(fill_complete),
 .command_valid(cv),.command_ready(command_ready),.command_kv_head(2'dHEAD_INDEX),
 .producer_valid(pv),.producer_ready(pr),.producer_last(pl),.producer_query(pq),.producer_key(pk),
 .command_done(command_done),.protocol_error(stage_error));
always @(negedge clk) for(ready_p=0;ready_p<PRODUCER_COUNT;ready_p=ready_p+1)
 pr[ready_p]=(cycle+ready_p)%11!=2 && (cycle+ready_p)%11!=3;
reg [255:0] expected_data;
integer half_index,token_index;
always @(posedge clk) if(rst) begin
 cycle<=cycle+1;
 if(se||ke||stage_error) $fatal(1,"protocol error");
 for(p=0;p<PRODUCER_COUNT;p=p+1) if(pv[p]&&pr[p]) begin
  if(accepted[p]>=blocks[p]*128) $fatal(1,"extra producer beat");
  for(t=0;t<16;t=t+1) begin
   expected_k[t*8+:8]=tensor_byte(base[p]+accepted[p]/128,t/8,t%8,accepted[p]%128);
   expected_q[t*8+:8]=query_byte(accepted[p]%128,t%8);
  end
  if(pk[p*128+:128]!==expected_k || pq[p*128+:128]!==expected_q || pl[p]!=(accepted[p]%128==127))
   $fatal(1,"producer K/Q mismatch producer=%0d beat=%0d",p,accepted[p]);
  accepted[p]=accepted[p]+1;
 end
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
 if(outputs==4096 && (!WITH_STAGE || command_done)) begin
  if(inputs!=4096) $fatal(1,"input count");
  if(WITH_STAGE) for(p=0;p<PRODUCER_COUNT;p=p+1)
   if(accepted[p]!=blocks[p]*128) $fatal(1,"missing producer beats");
  $display("PASS full paired head"); $finish;
 end
end
initial begin
 STAGE_INIT
 $readmemh("mapping.hex",mapping); repeat(3) @(negedge clk); rst=1;
 if(WITH_STAGE) begin
  fv=1; @(negedge clk);fv=0;
  for(q=0;q<128;q=q+1) begin
   qdim=q;qv=1;for(qi=0;qi<8;qi=qi+1) qdata[qi*8+:8]=query_byte(q,qi);
   if(!qr) $fatal(1,"query not ready");
   @(negedge clk);
  end
  qv=0;
 end
 hv=1; @(negedge clk); hv=0;
 if(WITH_STAGE) begin
  wait(fill_complete);@(negedge clk);cv=1;
  if(!command_ready) $fatal(1,"command not ready");
  @(negedge clk);cv=0;
 end
end
initial begin #200000; $fatal(1,"timeout"); end
endmodule
'''.replace("PRODUCER_COUNT", str(producers)).replace("HEAD_INDEX", str(head))
       .replace("WITH_STAGE", "1" if with_stage else "0").replace("STAGE_INIT", stage_init))
    binary = tmp_path / "simv"
    rtl = ROOT / "npu/sim/rtl"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
        str(rtl / "attention_kv_paired_head_schedule.sv"),
        str(rtl / "attention_score32_exact_kv_key_stage_wide.sv"),
        str(rtl / "attention_score32_exact_kv_key_pingpong_transpose.sv")],
        check=True, capture_output=True, text=True, timeout=30)
    # Shared CI runners exceed 30 seconds for the wide-stage cases. Preserve
    # the RTL cycle watchdog and numerical checks; only budget host runtime.
    result = subprocess.run(["vvp", str(binary)], cwd=tmp_path, capture_output=True, text=True,
                            timeout=int(os.environ.get("RTLGEN_PAIRED_STAGE_TIMEOUT", "180")))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS full paired head" in result.stdout
