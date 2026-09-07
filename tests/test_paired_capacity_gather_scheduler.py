"""Full-model paired descriptor schedule, including stalls and legacy V/refill."""
from dataclasses import replace
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_capacity_gather_scheduler import CONSUME, HBM, RESIDENT, llama7b_descriptors
from npu.sim.perf.attention_kv_paired_gather import addressed_key_spans

ROOT = Path(__file__).resolve().parents[1]


def paired_descriptors():
    for row in llama7b_descriptors():
        if row.operation != CONSUME or row.plane >= 4:
            yield row
        elif row.canonical_base_address == row.plane * 131072:
            for span in addressed_key_spans(layer=row.layer, tile=row.tile, head=row.plane):
                yield replace(row, segment=2 * row.plane + int(row.tile == 2 and span.source_hbm),
                              source=HBM if span.source_hbm else RESIDENT,
                              source_endpoint=span.source_endpoint,
                              canonical_base_address=span.canonical_address,
                              source_byte_address=span.source_byte_address,
                              destination_byte_address=span.canonical_address,
                              payload_bytes=1024)


def test_full_paired_scheduler_matches_oracle_under_stalls(tmp_path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    count = 0
    with (tmp_path / "expected.hex").open("w") as out:
        for row in paired_descriptors():
            fields = ((row.layer, 5), (row.tile, 7), (row.segment, 4),
                      (row.operation == CONSUME, 1), (row.source == HBM, 1),
                      (row.source_endpoint, 4), (row.destination_cluster, 4),
                      (row.plane, 4), (row.canonical_base_address, 20),
                      (row.source_byte_address, 34), (row.operation != CONSUME, 1),
                      (row.destination_byte_address, 34), (row.payload_bytes, 21), (row.last, 1))
            packed = 0
            for value, width in fields:
                assert 0 <= value < 1 << width
                packed = (packed << width) | int(value)
            out.write(f"{packed:036x}\n")
            count += 1
    assert count == 2113984
    tb = tmp_path / "tb.sv"
    tb.write_text('''module tb;
reg clk=0,rst_n=0,enable=0; always #1 clk=~clk;
integer cycle=0,count=0,fd,rc;
wire desc_valid; wire desc_ready=(cycle%7!=2 && cycle%7!=3);
wire [4:0] desc_layer; wire [6:0] desc_tile;
wire [3:0] desc_segment,desc_source_endpoint,desc_destination_cluster,desc_plane;
wire desc_operation_consume,desc_source_hbm,desc_destination_is_resident_cache,desc_last;
wire [19:0] desc_canonical_base_address;
wire [33:0] desc_source_byte_address,desc_destination_byte_address;
wire [20:0] desc_payload_bytes; wire [21:0] generated_descriptor_count;
wire done,protocol_error;
wire [140:0] bundle={desc_layer,desc_tile,desc_segment,desc_operation_consume,
 desc_source_hbm,desc_source_endpoint,desc_destination_cluster,desc_plane,
 desc_canonical_base_address,desc_source_byte_address,desc_destination_is_resident_cache,
 desc_destination_byte_address,desc_payload_bytes,desc_last};
reg [140:0] expected,held_bundle; reg held=0;
attention_kv_capacity_gather_scheduler #(.PAIRED_K(1)) dut(.*);
always @(posedge clk) if(rst_n) begin
 cycle<=cycle+1;
 if(held && (!desc_valid || bundle !== held_bundle)) $fatal(1,"unstable descriptor");
 held<=desc_valid&&!desc_ready; held_bundle<=bundle;
 if(desc_valid&&desc_ready) begin
  rc=$fscanf(fd,"%h\\n",expected);
  if(rc!=1 || bundle !== expected) $fatal(1,"mismatch descriptor %0d actual=%h expected=%h",count,bundle,expected);
  if(desc_last != (count==2113983)) $fatal(1,"last");
  count=count+1;
 end
 if(protocol_error || cycle>4000000) $fatal(1,"error or timeout");
end
initial begin
 fd=$fopen("expected.hex","r"); if(!fd) $fatal(1,"missing expected");
 repeat(3) @(negedge clk); rst_n=1; enable=1;
 wait(done); @(negedge clk);
 if(protocol_error || desc_valid || count!=2113984 || generated_descriptor_count!=22'd2113984)
  $fatal(1,"terminal state");
 rc=$fscanf(fd,"%h\\n",expected); if(rc==1) $fatal(1,"extra expected");
 $fclose(fd); $display("PASS paired descriptors=%0d",count); $finish;
end
endmodule
''')
    binary = tmp_path / "simv"
    subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
                    str(ROOT / "npu/sim/rtl/attention_kv_capacity_gather_scheduler.sv"),
                    str(ROOT / "npu/sim/rtl/attention_kv_paired_key_address.sv")],
                   check=True, capture_output=True, text=True, timeout=30)
    result = subprocess.run(["vvp", str(binary)], cwd=tmp_path, capture_output=True,
                            text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS paired descriptors=2113984" in result.stdout
