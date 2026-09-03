from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from npu.sim.perf.attention_kv_tile_layout import (
    encode_kv_byte_address,
    key_producer_location,
    kv_transpose_service,
)


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "npu/sim/rtl/attention_score32_exact_kv_ingress_transpose.sv"


@dataclass(frozen=True)
class Transaction:
    address: int
    data: int
    byte_valid: int


def _byte(address: int) -> int:
    return (address * 37 + 11) & 0xFF


def _pack_bytes(values: list[int]) -> int:
    return sum(value << (8 * index) for index, value in enumerate(values))


def _block_transactions(*, tensor: str, kv_head: int, streams: tuple[int, ...], block_slot: int) -> list[Transaction]:
    complete: list[Transaction] = []
    for stream in streams:
        for token_lane in range(8):
            token = stream * 512 + block_slot * 8 + token_lane
            for dimension in range(0, 128, 32):
                address = encode_kv_byte_address(
                    tensor=tensor,
                    kv_head=kv_head,
                    token=token,
                    dimension=dimension,
                )
                complete.append(
                    Transaction(
                        address=address,
                        data=_pack_bytes([_byte(address + offset) for offset in range(32)]),
                        byte_valid=0xFFFFFFFF,
                    )
                )
    transactions: list[Transaction] = []
    for index, transaction in enumerate(reversed(complete)):
        if index % 7 == 0:
            first_mask = 0x00FF00FF
            transactions.append(
                Transaction(transaction.address, transaction.data, first_mask)
            )
            transactions.append(
                Transaction(transaction.address, transaction.data, 0xFFFFFFFF ^ first_mask)
            )
        else:
            transactions.append(transaction)
    return transactions


def _expected_value_rows(*, kv_head: int, stream: int, block_slot: int) -> list[int]:
    rows = []
    for value_slice in range(16):
        values = []
        for token_lane in range(8):
            token = stream * 512 + block_slot * 8 + token_lane
            for dimension_lane in range(8):
                address = encode_kv_byte_address(
                    tensor="v",
                    kv_head=kv_head,
                    token=token,
                    dimension=value_slice * 8 + dimension_lane,
                )
                values.append(_byte(address))
        rows.append(_pack_bytes(values))
    return rows


def _expected_key_beats(*, kv_head: int, block_slot: int) -> list[int]:
    beats = []
    for dimension in range(128):
        values = []
        for stream in range(2):
            for token_lane in range(8):
                token = stream * 512 + block_slot * 8 + token_lane
                address = encode_kv_byte_address(
                    tensor="k",
                    kv_head=kv_head,
                    token=token,
                    dimension=dimension,
                )
                values.append(_byte(address))
        beats.append(_pack_bytes(values))
    return beats


def _testbench(
    *,
    producers: int,
    value_transactions: list[Transaction],
    key_transactions: list[Transaction],
    key_head: int,
    key_block_slot: int,
) -> str:
    transactions = value_transactions + key_transactions
    init = "\n".join(
        f"    addr_mem[{index}] = 20'h{transaction.address:05x}; "
        f"data_mem[{index}] = 256'h{transaction.data:064x}; "
        f"mask_mem[{index}] = 32'h{transaction.byte_valid:08x};"
        for index, transaction in enumerate(transactions)
    )
    value_count = len(value_transactions)
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer PRODUCERS = {producers};
  localparam integer TRANSACTIONS = {len(transactions)};
  reg clk = 0;
  reg rst_n = 0;
  integer cycle = 0;
  integer value_seen = 0;
  integer key_seen = 0;
  integer index;
  reg target_valid = 0;
  wire target_ready;
  reg target_is_key = 0;
  reg [1:0] target_kv_head = 0;
  reg target_stream = 0;
  reg [5:0] target_block_slot = 0;
  reg ingress_valid = 0;
  wire ingress_ready;
  reg [19:0] ingress_tile_byte_addr = 0;
  reg [255:0] ingress_data = 0;
  reg [31:0] ingress_byte_valid = 0;
  wire value_valid;
  wire value_ready = (cycle % 4) != 1;
  wire value_stream;
  wire [1:0] value_kv_head;
  wire [5:0] value_block_slot;
  wire [3:0] value_slice;
  wire [511:0] value_data;
  wire value_last;
  wire key_valid;
  wire key_ready = (cycle % 5) != 2;
  wire [5:0] key_producer;
  wire [1:0] key_kv_head;
  wire key_producer_block;
  wire [6:0] key_dimension;
  wire [127:0] key_data;
  wire key_last;
  wire protocol_error;
  reg [19:0] addr_mem [0:TRANSACTIONS-1];
  reg [255:0] data_mem [0:TRANSACTIONS-1];
  reg [31:0] mask_mem [0:TRANSACTIONS-1];

  attention_score32_exact_kv_ingress_transpose #(.PRODUCERS(PRODUCERS)) dut (.*);
  always #5 clk = ~clk;
  always @(posedge clk) begin
    cycle <= cycle + 1;
    if (ingress_valid && ingress_ready)
      $display("INGRESS %0d %0d", cycle, target_is_key);
    if (value_valid && value_ready) begin
      $display("VALUE %0d %0d %0d %0d %0d %0128h", cycle, value_kv_head,
               value_stream, value_block_slot, value_slice, value_data);
      value_seen <= value_seen + 1;
    end
    if (key_valid && key_ready) begin
      $display("KEY %0d %0d %0d %0d %0d %032h", cycle, key_kv_head,
               key_producer, key_producer_block, key_dimension, key_data);
      key_seen <= key_seen + 1;
    end
    if (cycle > 1000) begin
      $display("TIMEOUT");
      $finish(1);
    end
  end

  task automatic send_target(
    input is_key,
    input [1:0] head,
    input stream,
    input [5:0] block_slot
  );
    begin
      @(negedge clk);
      target_is_key = is_key;
      target_kv_head = head;
      target_stream = stream;
      target_block_slot = block_slot;
      target_valid = 1;
      @(posedge clk);
      while (!target_ready) @(posedge clk);
      @(negedge clk);
      target_valid = 0;
    end
  endtask

  task automatic send_range(input integer first, input integer count);
    integer transaction_index;
    begin
      for (transaction_index = first;
           transaction_index < first + count;
           transaction_index = transaction_index + 1) begin
        ingress_tile_byte_addr = addr_mem[transaction_index];
        ingress_data = data_mem[transaction_index];
        ingress_byte_valid = mask_mem[transaction_index];
        ingress_valid = 1;
        @(posedge clk);
        while (!ingress_ready) @(posedge clk);
        @(negedge clk);
      end
      ingress_valid = 0;
      ingress_byte_valid = 0;
    end
  endtask

  initial begin
{init}
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1;

    send_target(0, 2, 1, 7);
    send_range(0, {value_count});
    while (value_seen < 16) @(posedge clk);

    send_target(1, {key_head}, 0, {key_block_slot});
    send_range({value_count}, {len(key_transactions)});
    while (key_seen < 128) @(posedge clk);
    repeat (2) @(posedge clk);
    if (protocol_error) begin
      $display("PROTOCOL_ERROR");
      $finish(1);
    end
    $display("PASS value=%0d key=%0d", value_seen, key_seen);
    $finish(0);
  end
endmodule
"""


@pytest.mark.parametrize(
    ("producers", "key_head", "key_block_slot"),
    [(53, 3, 34), (54, 2, 21)],
)
def test_rtl_transposes_canonical_kv_under_partial_writes_and_backpressure(
    tmp_path: Path,
    producers: int,
    key_head: int,
    key_block_slot: int,
) -> None:
    if shutil.which("iverilog") is None or shutil.which("vvp") is None:
        pytest.skip("iverilog and vvp are required")
    value_transactions = _block_transactions(
        tensor="v", kv_head=2, streams=(1,), block_slot=7
    )
    key_transactions = _block_transactions(
        tensor="k", kv_head=key_head, streams=(0, 1), block_slot=key_block_slot
    )
    tb = tmp_path / "tb.sv"
    tb.write_text(
        _testbench(
            producers=producers,
            value_transactions=value_transactions,
            key_transactions=key_transactions,
            key_head=key_head,
            key_block_slot=key_block_slot,
        ),
        encoding="utf-8",
    )
    binary = tmp_path / "sim.vvp"
    compile_result = subprocess.run(
        ["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(RTL), str(tb)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    run_result = subprocess.run(
        ["vvp", str(binary)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr
    assert "PASS value=16 key=128" in run_result.stdout
    assert "PROTOCOL_ERROR" not in run_result.stdout

    value_rows = [
        (int(cycle), int(head), int(stream), int(block), int(value_slice), int(data, 16))
        for cycle, head, stream, block, value_slice, data in re.findall(
            r"^VALUE (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]+)$",
            run_result.stdout,
            flags=re.MULTILINE,
        )
    ]
    ingress_cycles = [
        (int(cycle), int(is_key))
        for cycle, is_key in re.findall(
            r"^INGRESS (\d+) (\d+)$", run_result.stdout, flags=re.MULTILINE
        )
    ]
    value_last_ingress = [cycle for cycle, is_key in ingress_cycles if not is_key][-1]
    expected_value_cycles = []
    candidate_cycle = value_last_ingress + 1
    while len(expected_value_cycles) < 16:
        if candidate_cycle % 4 != 1:
            expected_value_cycles.append(candidate_cycle)
        candidate_cycle += 1
    assert [row[0] for row in value_rows] == expected_value_cycles

    assert [(row[1], row[2], row[3], row[4], row[5]) for row in value_rows] == [
        (2, 1, 7, value_slice, data)
        for value_slice, data in enumerate(
            _expected_value_rows(kv_head=2, stream=1, block_slot=7)
        )
    ]

    mapping = key_producer_location(
        producers=producers,
        kv_head=key_head,
        token=key_block_slot * 8,
        dimension=0,
    )
    key_beats = [
        (int(cycle), int(head), int(producer), int(producer_block), int(dimension), int(data, 16))
        for cycle, head, producer, producer_block, dimension, data in re.findall(
            r"^KEY (\d+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]+)$",
            run_result.stdout,
            flags=re.MULTILINE,
        )
    ]
    assert [(row[1], row[2], row[3], row[4], row[5]) for row in key_beats] == [
        (key_head, mapping.producer, mapping.producer_block, dimension, data)
        for dimension, data in enumerate(
            _expected_key_beats(kv_head=key_head, block_slot=key_block_slot)
        )
    ]
    key_last_ingress = [cycle for cycle, is_key in ingress_cycles if is_key][-1]
    expected_key_cycles = []
    candidate_cycle = key_last_ingress + 1
    while len(expected_key_cycles) < 128:
        if candidate_cycle % 5 != 2:
            expected_key_cycles.append(candidate_cycle)
        candidate_cycle += 1
    assert [row[0] for row in key_beats] == expected_key_cycles


def test_one_buffer_service_model_discloses_no_overlap() -> None:
    value = kv_transpose_service(tensor="v")
    assert (
        value.input_flits,
        value.output_beats,
        value.transfer_cycles_without_stall,
        value.minimum_target_ii_cycles,
    ) == (
        32,
        16,
        48,
        49,
    )
    key = kv_transpose_service(tensor="k")
    assert (
        key.input_flits,
        key.output_beats,
        key.transfer_cycles_without_stall,
        key.minimum_target_ii_cycles,
    ) == (
        64,
        128,
        192,
        193,
    )
