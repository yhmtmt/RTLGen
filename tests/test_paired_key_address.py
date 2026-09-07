"""Exhaustive paired K source mapping; not a transport/completion test."""
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_paired_gather import addressed_key_spans

ROOT = Path(__file__).resolve().parents[1]


def test_all_model_key_span_addresses_match_rtl(tmp_path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    vectors = tmp_path / "vectors.hex"
    count = 0
    with vectors.open("w") as out:
        for layer in range(32):
            for tile in range(128):
                for head in range(4):
                    for span in addressed_key_spans(layer=layer, tile=tile, head=head):
                        offset = span.canonical_address & 0x1ffff
                        inputs = (layer << 26) | (tile << 19) | (head << 17) | offset
                        expected = (span.canonical_address << 43) | (span.source_byte_address << 9)
                        expected |= (int(span.source_hbm) << 8) | (span.source_endpoint << 4)
                        expected |= span.destination_cluster
                        out.write(f"{(inputs << 63) | expected:024x}\n")
                        count += 1
    assert count == 2097152
    tb = tmp_path / "tb.sv"
    tb.write_text('''module tb;
reg [4:0] layer; reg [6:0] tile; reg [1:0] head; reg [16:0] offset;
wire [19:0] canonical; wire [33:0] source; wire hbm,error;
wire [3:0] endpoint,destination;
reg [93:0] vector; integer fd,rc,count=0;
attention_kv_paired_key_address dut(.layer(layer),.tile(tile),.kv_head(head),
 .head_byte_offset(offset),.canonical_address(canonical),.source_byte_address(source),
 .source_hbm(hbm),.source_endpoint(endpoint),.destination_cluster(destination),
 .protocol_error(error));
initial begin
 fd=$fopen("vectors.hex","r"); if(!fd) $fatal(1,"missing vectors");
 while(!$feof(fd)) begin
  rc=$fscanf(fd,"%h\\n",vector);
  if(rc==1) begin
   {layer,tile,head,offset}=vector[93:63]; #1;
   if(error || {canonical,source,hbm,endpoint,destination} !== vector[62:0])
    $fatal(1,"address mismatch at %0d layer=%0d tile=%0d head=%0d offset=%0d",count,layer,tile,head,offset);
   count=count+1;
  end else if(!$feof(fd)) $fatal(1,"malformed vector");
 end
 $fclose(fd);
 if(count!=2097152) $fatal(1,"incomplete coverage");
 offset=17'd1; #1; if(!error) $fatal(1,"unaligned accepted");
 offset=17'd131071; #1; if(!error) $fatal(1,"unaligned end accepted");
 offset=17'd130048; #1; if(error) $fatal(1,"final aligned rejected");
 $display("PASS addresses=%0d",count); $finish;
end
endmodule
''')
    binary = tmp_path / "simv"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
                    str(ROOT / "npu/sim/rtl/attention_kv_paired_key_address.sv")],
                   check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS addresses=2097152" in result.stdout
