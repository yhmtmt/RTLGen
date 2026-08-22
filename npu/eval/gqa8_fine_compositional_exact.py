#!/usr/bin/env python3
"""Fine-grained concrete-RTL compositional proof for the full GQA8 hierarchy."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import re
import shutil
from typing import Any

from npu.eval import probe_attention_score32_exact_local_temporal_reducer_gqa8 as reducer_probe
from npu.eval.check_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_guard import (
    main as strict_guard_main,
)
from npu.eval.gqa8_compositional_exact import (
    _run_process,
    _write_global_sidecar,
    extract_module_family,
    global_testbench,
)

JsonDict = dict[str, Any]

BACKEND = "fine_compositional_icarus"
_PRODUCER_RESULT_RE = re.compile(
    r"PRODUCER_RESULT cluster=(\d+) producer=(\d+) cmd=(\d+) head=(\d+) slice=(\d+) "
    r"last=(\d+) max=(-?\d+) sum=(\d+) value=([0-9a-fA-F]+)"
)
_PRODUCER_REQUEST_RE = re.compile(
    r"PRODUCER_REQUEST command=(\d+) stream=(\d+) address=(\d+) slice=(\d+)"
)
_PRODUCER_SUMMARY_RE = re.compile(
    r"PRODUCER_SUMMARY outputs=(\d+) commands=(\d+) completed=(\d+) merge=(\d+) "
    r"stream0_accept=(\d+) stream1_accept=(\d+) stream0_complete=(\d+) "
    r"stream1_complete=(\d+) protocol_error=(\d+)"
)
_SRAM_RESPONSE_RE = re.compile(
    r"SRAM_RESPONSE command=(\d+) lane=(\d+) address=(\d+) slice=(\d+) "
    r"data=([0-9a-fA-F]+) tag=([0-9a-fA-F]+)"
)
_SRAM_SUMMARY_RE = re.compile(
    r"SRAM_SUMMARY fill_targets=(\d+) fill_rows=(\d+) requests=(\d+) responses=(\d+) "
    r"commands=(\d+) releases=(\d+) protocol_error=(\d+)"
)
_GLOBAL_SUMMARY_RE = re.compile(
    r"GLOBAL_SUMMARY root_rows=(\d+) root_completed=(\d+) finalizer_accepted=(\d+) "
    r"tree_completed=(\d+) protocol_error=(\d+) first_root=(-?\d+) last_root=(-?\d+) drain=(\d+)"
)


def component_module_names(top_name: str) -> dict[str, str]:
    return {
        "p54_producer": f"{top_name}__cluster_p54__compute_cluster__producer",
        "p53_producer": f"{top_name}__cluster_p53__compute_cluster__producer",
        "p54_reducer": f"{top_name}__cluster_p54__compute_cluster__reducer",
        "p53_reducer": f"{top_name}__cluster_p53__compute_cluster__reducer",
        "p54_sram": f"{top_name}__cluster_p54__sram_endpoint",
        "p53_sram": f"{top_name}__cluster_p53__sram_endpoint",
        "global_tree": f"{top_name}__global_tree",
    }


def _producer_case(*, cluster: int, producer: int, logical_head_groups: int) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    producers = probe.CLUSTER_PRODUCERS[cluster]
    commands = probe._wave_commands(logical_head_groups=logical_head_groups)
    query_words: list[int] = []
    key_words: list[int] = []
    last_words: list[int] = []
    value_words = [[], []]
    beat_limits: list[int] = []
    block_offsets: list[int] = []
    block_counts: list[int] = []
    expected_rows: list[JsonDict] = []
    block_cursor = 0
    for command in commands:
        block_count = probe.exact_local_cluster_gqa8_command_block_counts(
            producers=producers,
            group_index=int(command["group_index"]),
        )[producer]
        block_offsets.append(block_cursor)
        block_counts.append(block_count)
        stream_blocks = [
            probe.full_probe._stream_block_beats(
                cluster=cluster,
                producer=producer,
                group_index=int(command["group_index"]),
                wave_index=int(command["wave_index"]),
                stream=stream,
                block_count=block_count,
                seed=probe.SEED,
            )
            for stream in range(probe.STREAMS)
        ]
        for block in range(block_count):
            for dimension in range(probe.HEAD_DIM):
                queries0, keys0 = stream_blocks[0][block][dimension]
                queries1, keys1 = stream_blocks[1][block][dimension]
                query_words.append(
                    probe.full_probe._pack(list(queries0), 8)
                    | (probe.full_probe._pack(list(queries1), 8) << 64)
                )
                key_words.append(
                    probe.full_probe._pack(list(keys0), 8)
                    | (probe.full_probe._pack(list(keys1), 8) << 64)
                )
                last_words.append(int(dimension + 1 == probe.HEAD_DIM))
        beat_limits.append(len(query_words))
        for stream in range(probe.STREAMS):
            blocks = probe.full_probe._value_blocks(
                cluster=cluster,
                producer=producer,
                group_index=int(command["group_index"]),
                wave_index=int(command["wave_index"]),
                stream=stream,
                block_count=block_count,
                seed=probe.SEED,
            )
            for block in range(block_count):
                for value_slice in range(probe.VALUE_SLICES):
                    value_words[stream].append(
                        probe.full_probe._pack(
                            [lane for row in blocks[block][value_slice] for lane in row],
                            8,
                        )
                    )
        expected_rows.extend(
            {
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
                "global_max": beat.max_score,
                "exp_sum": beat.exp_sum,
                "value": list(beat.numerators),
            }
            for beat in probe.full_probe._producer_wave_stream(
                cluster=cluster,
                producer=producer,
                logical_command=command,
                wave_index=int(command["wave_index"]),
                block_count=block_count,
                seed=probe.SEED,
            )
        )
        block_cursor += block_count
    return {
        "commands": commands,
        "query_words": query_words,
        "key_words": key_words,
        "last_words": last_words,
        "value_words": value_words[0] + value_words[1],
        "total_blocks": block_cursor,
        "beat_limits": beat_limits,
        "block_offsets": block_offsets,
        "block_counts": block_counts,
        "expected_rows": expected_rows,
    }


def _write_producer_sidecars(
    directory: Path,
    case: JsonDict,
    *,
    value_block_capacity: int,
) -> None:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    probe._write_memh(directory / "query.memh", case["query_words"], width_bits=128)
    probe._write_memh(directory / "key.memh", case["key_words"], width_bits=128)
    probe._write_memh(directory / "last.memh", case["last_words"], width_bits=1)
    total_blocks = int(case["total_blocks"])
    values = list(case["value_words"])
    stream_words = total_blocks * 16
    padded_values = (
        values[:stream_words]
        + [0] * ((value_block_capacity - total_blocks) * 16)
        + values[stream_words:]
    )
    probe._write_memh(directory / "value.memh", padded_values, width_bits=512)
    command_words = []
    for index, command in enumerate(case["commands"]):
        word = int(command["command_id"])
        word |= int(command["head_base"]) << 16
        word |= int(command["wave_index"]) << 21
        word |= int(command["multiplier"]) << 24
        word |= int(command["shift"]) << 56
        word |= int(case["block_counts"][index]) << 62
        word |= int(case["block_offsets"][index]) << 77
        word |= int(case["beat_limits"][index]) << 109
        command_words.append(word)
    probe._write_memh(directory / "producer_commands.memh", command_words, width_bits=141)


def producer_testbench(*, top_name: str, case: JsonDict, cluster: int, producer: int) -> str:
    commands = list(case["commands"])
    total_results = len(case["expected_rows"])
    total_blocks = int(case["total_blocks"])
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer COMMANDS={len(commands)}, TOTAL_BEATS={len(case["query_words"])};
  localparam integer TOTAL_BLOCKS={total_blocks}, TOTAL_RESULTS={total_results};
  reg clk=0, rst_n=0; integer cycle=0, issued=0, input_index=0, seen=0;
  integer active_command=0, pending0=0, pending1=0, command_drive=0, input_drive=0;
  reg finish_pending=0;
  reg [140:0] command_mem [0:COMMANDS-1];
  reg [127:0] query_mem [0:TOTAL_BEATS-1], key_mem [0:TOTAL_BEATS-1];
  reg last_mem [0:TOTAL_BEATS-1];
  reg [511:0] value_mem [0:(2*TOTAL_BLOCKS*16)-1];
  wire command_valid=(issued<COMMANDS); wire command_ready;
  wire input_valid=(input_index < ((issued==0)?0:command_mem[issued-1][140:109])); wire input_ready;
  wire [1:0] req_valid; reg [1:0] req_ready; wire [27:0] req_address; wire [7:0] req_slice;
  reg [1:0] resp_valid; wire [1:0] resp_ready; reg [27:0] resp_address;
  reg [7:0] resp_slice; reg [1023:0] resp_matrix;
  reg [13:0] pending_addr0, pending_addr1; reg [3:0] pending_slice0, pending_slice1;
  wire result_valid; wire [15:0] result_command_id; wire [4:0] result_head_id;
  wire signed [31:0] result_global_max; wire [32:0] result_exp_sum;
  wire [3:0] result_slice; wire result_last; wire [327:0] result_value;
  wire [31:0] command_accept_count, command_completed_count, merge_completed_count;
  wire [63:0] stream_command_accept_count, stream_completed_count;
  wire [1:0] stream_protocol_error; wire merge_protocol_error, protocol_error;
  integer value_index0, value_index1;
  {top_name} dut (
    .clk(clk),.rst_n(rst_n),.command_valid(command_valid),.command_ready(command_ready),
    .command_id(command_mem[command_drive][15:0]),
    .command_head_base(command_mem[command_drive][20:16]),
    .command_block_count(command_mem[command_drive][76:62]),
    .command_score_multiplier(command_mem[command_drive][55:24]),
    .command_score_shift(command_mem[command_drive][61:56]),
    .input_valid(input_valid),.input_ready(input_ready),.input_last(last_mem[input_drive]),
    .input_query(query_mem[input_drive]),.input_key(key_mem[input_drive]),
    .value_read_req_valid(req_valid),.value_read_req_ready(req_ready),
    .value_read_req_address(req_address),.value_read_req_slice(req_slice),
    .value_response_valid(resp_valid),.value_response_ready(resp_ready),
    .value_response_address(resp_address),.value_response_slice(resp_slice),
    .value_response_matrix(resp_matrix),.result_valid(result_valid),.result_ready(1'b1),
    .result_command_id(result_command_id),.result_head_id(result_head_id),
    .result_global_max(result_global_max),.result_exp_sum(result_exp_sum),
    .result_slice(result_slice),.result_last(result_last),.result_value(result_value),
    .command_accept_count(command_accept_count),.command_completed_count(command_completed_count),
    .stream_command_accept_count(stream_command_accept_count),
    .stream_completed_count(stream_completed_count),.merge_completed_count(merge_completed_count),
    .stream_protocol_error(stream_protocol_error),.merge_protocol_error(merge_protocol_error),
    .protocol_error(protocol_error)
  );
  always #5 clk=~clk;
  always @* begin
    command_drive=(issued<COMMANDS)?issued:COMMANDS-1;
    input_drive=(input_index<TOTAL_BEATS)?input_index:TOTAL_BEATS-1;
    req_ready[0]=!pending0 && !resp_valid[0]; req_ready[1]=!pending1 && !resp_valid[1];
    value_index0=((command_mem[active_command][108:77]+pending_addr0)*16)+pending_slice0;
    value_index1=((TOTAL_BLOCKS+command_mem[active_command][108:77]+pending_addr1)*16)+pending_slice1;
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      cycle<=0; issued<=0; input_index<=0; seen<=0; active_command<=0;
      pending0<=0; pending1<=0; resp_valid<=0; finish_pending<=0;
    end else begin
      cycle<=cycle+1;
      if(command_valid&&command_ready) begin active_command<=issued; issued<=issued+1; end
      if(input_valid&&input_ready) input_index<=input_index+1;
      if(req_valid[0]&&req_ready[0]) begin
        $display("PRODUCER_REQUEST command=%0d stream=0 address=%0d slice=%0d",
                 active_command,req_address[13:0],req_slice[3:0]);
        pending0<=1; pending_addr0<=req_address[13:0]; pending_slice0<=req_slice[3:0];
      end
      if(req_valid[1]&&req_ready[1]) begin
        $display("PRODUCER_REQUEST command=%0d stream=1 address=%0d slice=%0d",
                 active_command,req_address[27:14],req_slice[7:4]);
        pending1<=1; pending_addr1<=req_address[27:14]; pending_slice1<=req_slice[7:4];
      end
      if(pending0) begin
        pending0<=0; resp_valid[0]<=1; resp_address[13:0]<=pending_addr0;
        resp_slice[3:0]<=pending_slice0; resp_matrix[511:0]<=value_mem[value_index0];
      end
      if(pending1) begin
        pending1<=0; resp_valid[1]<=1; resp_address[27:14]<=pending_addr1;
        resp_slice[7:4]<=pending_slice1; resp_matrix[1023:512]<=value_mem[value_index1];
      end
      if(resp_valid[0]&&resp_ready[0]) resp_valid[0]<=0;
      if(resp_valid[1]&&resp_ready[1]) resp_valid[1]<=0;
      if(result_valid) begin
        $display("PRODUCER_RESULT cluster={cluster} producer={producer} cmd=%0d head=%0d slice=%0d last=%0d max=%0d sum=%0d value=%082x",
                 result_command_id,result_head_id,result_slice,result_last,$signed(result_global_max),
                 result_exp_sum,result_value);
        seen<=seen+1; if(seen+1==TOTAL_RESULTS) finish_pending<=1;
      end
      if(finish_pending) begin
        $display("PRODUCER_SUMMARY outputs=%0d commands=%0d completed=%0d merge=%0d stream0_accept=%0d stream1_accept=%0d stream0_complete=%0d stream1_complete=%0d protocol_error=%0d",
                 seen,command_accept_count,command_completed_count,merge_completed_count,
                 stream_command_accept_count[31:0],stream_command_accept_count[63:32],
                 stream_completed_count[31:0],stream_completed_count[63:32],
                 protocol_error|(|stream_protocol_error)|merge_protocol_error);
        #1 $finish;
      end
      if(cycle>500000) begin $display("TB_TIMEOUT cycle=%0d",cycle); #1 $finish; end
    end
  end
  initial begin
    $readmemh("query.memh",query_mem); $readmemh("key.memh",key_mem);
    $readmemh("last.memh",last_mem);
    $readmemh("value.memh",value_mem);
    $readmemh("producer_commands.memh",command_mem);
    resp_valid=0; resp_address=0; resp_slice=0; resp_matrix=0;
    repeat(3) @(posedge clk); @(negedge clk); rst_n=1;
  end
endmodule
"""


def _parse_producer(stdout: str) -> tuple[list[JsonDict], list[list[JsonDict]], JsonDict | None]:
    from npu.sim.perf.attention_exact_partial import unpack_numerators

    rows: list[JsonDict] = []
    requests: list[list[JsonDict]] = [[], []]
    for match in _PRODUCER_RESULT_RE.finditer(stdout):
        rows.append(
            {
                "command_id": int(match.group(3)),
                "head_id": int(match.group(4)),
                "slice": int(match.group(5)),
                "last": bool(int(match.group(6))),
                "global_max": int(match.group(7)),
                "exp_sum": int(match.group(8)),
                "value": list(unpack_numerators(int(match.group(9), 16))),
            }
        )
    for match in _PRODUCER_REQUEST_RE.finditer(stdout):
        stream = int(match.group(2))
        requests[stream].append(
            {
                "command": int(match.group(1)),
                "address": int(match.group(3)),
                "slice": int(match.group(4)),
            }
        )
    summary_match = _PRODUCER_SUMMARY_RE.search(stdout)
    summary = (
        {
            "outputs": int(summary_match.group(1)),
            "commands": int(summary_match.group(2)),
            "completed": int(summary_match.group(3)),
            "merge": int(summary_match.group(4)),
            "stream0_accept": int(summary_match.group(5)),
            "stream1_accept": int(summary_match.group(6)),
            "stream0_complete": int(summary_match.group(7)),
            "stream1_complete": int(summary_match.group(8)),
            "protocol_error": int(summary_match.group(9)),
        }
        if summary_match
        else None
    )
    return rows, requests, summary


def _check_request_metadata(requests: list[list[JsonDict]], block_counts: list[int]) -> JsonDict:
    for stream in range(2):
        for command, block_count in enumerate(block_counts):
            observed = sorted(
                (int(row["address"]), int(row["slice"]))
                for row in requests[stream]
                if int(row["command"]) == command
            )
            expected = sorted((block, value_slice) for block in range(block_count) for value_slice in range(16))
            if observed != expected:
                return {
                    "passed": False,
                    "stream": stream,
                    "command": command,
                    "expected_count": len(expected),
                    "observed_count": len(observed),
                }
    return {"passed": True}


def _write_sram_sidecars(
    directory: Path,
    *,
    cluster: int,
    logical_head_groups: int,
    producer_requests: list[list[list[JsonDict]]],
) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    commands = probe._wave_commands(logical_head_groups=logical_head_groups)
    lanes = probe.CLUSTER_PRODUCERS[cluster] * 2
    per_command_lane: list[list[list[JsonDict]]] = [
        [[] for _ in range(lanes)] for _ in commands
    ]
    max_requests = 1
    for producer, streams in enumerate(producer_requests):
        for stream, requests in enumerate(streams):
            lane = producer * 2 + stream
            for command in range(len(commands)):
                rows = [row for row in requests if int(row["command"]) == command]
                per_command_lane[command][lane] = rows
                max_requests = max(max_requests, len(rows))
    request_words = [0] * (len(commands) * lanes * max_requests)
    counts = [[0 for _ in range(lanes)] for _ in commands]
    for command in range(len(commands)):
        for lane in range(lanes):
            counts[command][lane] = len(per_command_lane[command][lane])
            for index, row in enumerate(per_command_lane[command][lane]):
                request_words[(command * lanes + lane) * max_requests + index] = (
                    int(row["address"]) | (int(row["slice"]) << 14)
                )
    fill_words = [
        value
        for command in commands
        for value in probe._fill_rows_for_wave(
            cluster=cluster,
            head_base=int(command["head_base"]),
            wave=int(command["wave_index"]),
        )
    ]
    probe._write_memh(directory / "sram_requests.memh", request_words, width_bits=18)
    probe._write_memh(directory / "sram_fill.memh", fill_words, width_bits=512)
    return {
        "commands": commands,
        "counts": counts,
        "max_requests": max_requests,
        "fill_words": fill_words,
        "request_count": sum(sum(row) for row in counts),
        "expected_responses": [
            {
                "command": command,
                "lane": lane,
                "address": int(row["address"]),
                "slice": int(row["slice"]),
            }
            for command in range(len(commands))
            for lane in range(lanes)
            for row in per_command_lane[command][lane]
        ],
    }


def sram_testbench(*, top_name: str, producers: int, sidecar: JsonDict) -> str:
    commands = list(sidecar["commands"])
    lanes = producers * 2
    count_init = "\n".join(
        f"    req_count_mem[{command}][{lane}]=32'd{int(sidecar['counts'][command][lane])};"
        for command in range(len(commands))
        for lane in range(lanes)
    )
    command_init = "\n".join(
        f"    cmd_id_mem[{index}]=16'h{int(command['command_id']):04x}; "
        f"head_mem[{index}]=5'd{int(command['head_base'])}; "
        f"wave_mem[{index}]=3'd{int(command['wave_index'])};"
        for index, command in enumerate(commands)
    )
    total_requests = int(sidecar["request_count"])
    return f"""`timescale 1ns/1ps
module tb;
  localparam integer LANES={lanes}, COMMANDS={len(commands)}, MAX_REQ={int(sidecar["max_requests"])};
  localparam integer ROWS=2048, TOTAL_REQUESTS={total_requests};
  reg clk=0,rst_n=0; integer cycle=0,phase=0,command_index=0,fill_row=0,lane=0;
  integer requests_seen=0,responses_seen=0; reg finish_pending=0;
  reg [15:0] cmd_id_mem [0:COMMANDS-1]; reg [4:0] head_mem [0:COMMANDS-1];
  reg [2:0] wave_mem [0:COMMANDS-1]; reg [31:0] req_count_mem [0:COMMANDS-1][0:LANES-1];
  reg [31:0] req_issue [0:LANES-1]; reg [17:0] req_mem [0:(COMMANDS*LANES*MAX_REQ)-1];
  reg [511:0] fill_mem [0:(COMMANDS*ROWS)-1];
  reg fill_target_valid,fill_valid,command_valid,release_valid;
  wire fill_target_ready,fill_ready,command_ready;
  reg [LANES-1:0] req_valid; wire [LANES-1:0] req_ready,resp_valid;
  reg [(LANES*14)-1:0] req_address; reg [(LANES*4)-1:0] req_slice;
  wire [(LANES*14)-1:0] resp_address; wire [(LANES*4)-1:0] resp_slice;
  wire [(LANES*512)-1:0] resp_matrix; wire [(LANES*16)-1:0] resp_tag;
  wire [31:0] fill_targets,fill_rows,request_count,response_count,command_count,release_count;
  wire [7:0] outstanding; wire invalid_metadata,invalid_address,residency,overwrite,command_error,protocol_error;
  reg [17:0] req_word; reg all_issued;
  {top_name} dut (
    .clk(clk),.rst_n(rst_n),.fill_target_valid(fill_target_valid),
    .fill_target_ready(fill_target_ready),.fill_target_buffer_sel(wave_mem[command_index][0]),
    .fill_target_command_id(cmd_id_mem[command_index]),.fill_target_head_base(head_mem[command_index]),
    .fill_target_wave_index(wave_mem[command_index]),.fill_valid(fill_valid),.fill_ready(fill_ready),
    .fill_buffer_sel(wave_mem[command_index][0]),.fill_stream(fill_row>=1024),
    .fill_block_slot((fill_row>>4)&6'h3f),.fill_slice(fill_row&4'hf),
    .fill_data(fill_mem[command_index*ROWS+fill_row]),.command_valid(command_valid),
    .command_ready(command_ready),.command_buffer_sel(wave_mem[command_index][0]),
    .command_id(cmd_id_mem[command_index]),.command_head_base(head_mem[command_index]),
    .command_wave_index(wave_mem[command_index]),.command_release_valid(release_valid),
    .command_release_buffer_sel(wave_mem[command_index][0]),.value_read_req_valid(req_valid),
    .value_read_req_ready(req_ready),.value_read_req_address(req_address),
    .value_read_req_slice(req_slice),.value_response_valid(resp_valid),
    .value_response_ready({{LANES{{1'b1}}}}),.value_response_address(resp_address),
    .value_response_slice(resp_slice),.value_response_matrix(resp_matrix),.value_response_tag(resp_tag),
    .fill_target_accept_count(fill_targets),.fill_row_accept_count(fill_rows),
    .request_accept_count(request_count),.response_accept_count(response_count),
    .command_accept_count(command_count),.command_release_count(release_count),
    .outstanding_response_occupancy(outstanding),
    .protocol_error_invalid_metadata(invalid_metadata),
    .protocol_error_invalid_address(invalid_address),.protocol_error_residency(residency),
    .protocol_error_overwrite(overwrite),.protocol_error_command(command_error),
    .protocol_error(protocol_error)
  );
  always #5 clk=~clk;
  always @* begin
    fill_target_valid=(phase==0); fill_valid=(phase==1); command_valid=(phase==2);
    release_valid=(phase==4); req_valid='0; req_address='0; req_slice='0; req_word=0;
    all_issued=1'b1;
    if(phase==3) for(lane=0;lane<LANES;lane=lane+1)
      if(req_issue[lane]<req_count_mem[command_index][lane]) begin
        all_issued=1'b0;
        req_word=req_mem[(command_index*LANES+lane)*MAX_REQ+req_issue[lane]];
        req_valid[lane]=1; req_address[lane*14 +: 14]=req_word[13:0];
        req_slice[lane*4 +: 4]=req_word[17:14];
      end
  end
  always @(posedge clk) begin
    if(!rst_n) begin
      cycle<=0;phase<=0;command_index<=0;fill_row<=0;requests_seen<=0;responses_seen<=0;
      finish_pending<=0; for(lane=0;lane<LANES;lane=lane+1) req_issue[lane]<=0;
    end else begin
      cycle<=cycle+1;
      if(phase==0&&fill_target_ready) begin phase<=1;fill_row<=0;end
      if(phase==1&&fill_ready) begin
        if(fill_row==ROWS-1) phase<=2; else fill_row<=fill_row+1;
      end
      if(phase==2&&command_ready) phase<=3;
      for(lane=0;lane<LANES;lane=lane+1) begin
        if(req_valid[lane]&&req_ready[lane]) begin
          req_issue[lane]<=req_issue[lane]+1;requests_seen<=requests_seen+1;
        end
        if(resp_valid[lane]) begin
          $display("SRAM_RESPONSE command=%0d lane=%0d address=%0d slice=%0d data=%0128x tag=%04x",
                   command_index,lane,resp_address[lane*14 +: 14],resp_slice[lane*4 +: 4],
                   resp_matrix[lane*512 +: 512],resp_tag[lane*16 +: 16]);
          responses_seen<=responses_seen+1;
        end
      end
      if(phase==3&&all_issued&&outstanding==0) phase<=4;
      if(phase==4) begin
        if(command_index==COMMANDS-1) begin finish_pending<=1;phase<=5;end
        else begin
          command_index<=command_index+1;fill_row<=0;phase<=0;
          for(lane=0;lane<LANES;lane=lane+1) req_issue[lane]<=0;
        end
      end
      if(finish_pending) begin
        $display("SRAM_SUMMARY fill_targets=%0d fill_rows=%0d requests=%0d responses=%0d commands=%0d releases=%0d protocol_error=%0d",
                 fill_targets,fill_rows,request_count,response_count,command_count,release_count,
                 protocol_error|invalid_metadata|invalid_address|residency|overwrite|command_error);
        #1 $finish;
      end
      if(cycle>1000000) begin $display("TB_TIMEOUT cycle=%0d",cycle);#1 $finish;end
    end
  end
  initial begin
    $readmemh("sram_requests.memh",req_mem);$readmemh("sram_fill.memh",fill_mem);
{command_init}
{count_init}
    repeat(3) @(posedge clk);@(negedge clk);rst_n=1;
  end
endmodule
"""


def _parse_sram(stdout: str) -> tuple[list[JsonDict], JsonDict | None]:
    responses = [
        {
            "command": int(match.group(1)),
            "lane": int(match.group(2)),
            "address": int(match.group(3)),
            "slice": int(match.group(4)),
            "data": int(match.group(5), 16),
            "tag": int(match.group(6), 16),
        }
        for match in _SRAM_RESPONSE_RE.finditer(stdout)
    ]
    match = _SRAM_SUMMARY_RE.search(stdout)
    summary = (
        {
            "fill_targets": int(match.group(1)),
            "fill_rows": int(match.group(2)),
            "requests": int(match.group(3)),
            "responses": int(match.group(4)),
            "commands": int(match.group(5)),
            "releases": int(match.group(6)),
            "protocol_error": int(match.group(7)),
        }
        if match
        else None
    )
    return responses, summary


def _check_sram_responses(
    *,
    cluster: int,
    logical_head_groups: int,
    responses: list[JsonDict],
    expected_responses: list[JsonDict],
) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    producers = probe.CLUSTER_PRODUCERS[cluster]
    commands = probe._wave_commands(logical_head_groups=logical_head_groups)
    metadata_fields = ("command", "lane", "address", "slice")
    expected_metadata = sorted(
        tuple(int(row[field]) for field in metadata_fields) for row in expected_responses
    )
    observed_metadata = sorted(
        tuple(int(row[field]) for field in metadata_fields) for row in responses
    )
    if observed_metadata != expected_metadata:
        return {
            "passed": False,
            "reason": "response_metadata_mismatch",
            "expected_count": len(expected_metadata),
            "observed_count": len(observed_metadata),
        }
    fill_rows = [
        probe._fill_rows_for_wave(
            cluster=cluster,
            head_base=int(command["head_base"]),
            wave=int(command["wave_index"]),
        )
        for command in commands
    ]
    for index, row in enumerate(responses):
        command = int(row["command"])
        lane = int(row["lane"])
        producer = lane // 2
        stream = lane % 2
        address = int(row["address"])
        value_slice = int(row["slice"])
        slot_base = probe.exact_local_cluster_gqa8_slot_bases(
            producers=producers,
            group_index=int(commands[command]["group_index"]),
        )[producer]
        flat = stream * probe.ROWS_PER_STREAM + (slot_base + address) * probe.VALUE_SLICES + value_slice
        expected_data = fill_rows[command][flat]
        expected_tag = (lane << 7) | ((address & 7) << 4) | value_slice
        if row["data"] != expected_data or row["tag"] != expected_tag:
            return {
                "passed": False,
                "response": index,
                "expected_data": expected_data,
                "observed_data": row["data"],
                "expected_tag": expected_tag,
                "observed_tag": row["tag"],
            }
    return {"passed": True}


def _parse_reducer(stdout: str, *, cluster: int) -> tuple[list[JsonDict], JsonDict | None]:
    from npu.sim.perf.attention_exact_partial import unpack_numerators

    rows = [
        {
            "cluster": cluster,
            "command_id": int(match.group(2)),
            "head_id": int(match.group(3)),
            "slice": int(match.group(4)),
            "last": bool(int(match.group(5))),
            "global_max": int(match.group(6)),
            "exp_sum": int(match.group(7)),
            "value": list(unpack_numerators(int(match.group(8), 16))),
        }
        for match in reducer_probe._RESULT_RE.finditer(stdout)
    ]
    match = reducer_probe._SUMMARY_RE.search(stdout)
    summary = (
        {
            "outputs": int(match.group(1)),
            "protocol_error": int(match.group(3)),
            "group_error": int(match.group(4)),
            "local_tree_error": int(match.group(5)),
            "temporal_error": int(match.group(6)),
            "local_root_completed": int(match.group(7)),
            "temporal_completed": int(match.group(8)),
            "emitted": int(match.group(9)),
            "commands": int(match.group(10)),
        }
        if match
        else None
    )
    return rows, summary


def _failure(*, failure: JsonDict, phase_records: list[JsonDict]) -> JsonDict:
    diagnostic = [f"phase={failure['phase']} returncode={failure['returncode']}"]
    stdout = str(failure.get("stdout") or "").strip()
    stderr = str(failure.get("stderr") or "").strip()
    if stdout:
        diagnostic.extend(("stdout:", stdout))
    if stderr:
        diagnostic.extend(("stderr:", stderr))
    return {
        "simulation_status": failure["status"],
        "returncode": failure["returncode"],
        "stderr": "\n".join(diagnostic),
        "stdout": stdout,
        "phase_records": phase_records,
    }


def run_fine_compositional_exact(
    *,
    config: JsonDict,
    work_dir: Path,
    rtl_dir: Path,
    fakeram_path: Path,
    logical_head_groups: int,
    output_ready_pattern: tuple[bool, ...],
    compile_timeout_sec: int,
    simulation_timeout_sec: int,
) -> JsonDict:
    from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe

    top_name = str(config["top_name"])
    modules = component_module_names(top_name)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            strict_guard_main(["--design-dir", str(work_dir), "--config", str(rtl_dir / "config.json")])
    except SystemExit as exc:
        return {
            "simulation_status": "guard_failed",
            "returncode": 1,
            "stderr": f"phase=strict_generated_top_guard\n{exc}",
            "stdout": "",
            "phase_records": [{"phase": "strict_generated_top_guard", "returncode": 1}],
        }
    phase_records: list[JsonDict] = [{"phase": "strict_generated_top_guard", "returncode": 0}]
    build_dir = work_dir / "fine_components"
    build_dir.mkdir()
    generated_rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    binaries: dict[str, Path] = {}
    testbenches = {
        "p54_producer": producer_testbench(
            top_name=modules["p54_producer"],
            case=_producer_case(cluster=0, producer=0, logical_head_groups=logical_head_groups),
            cluster=0,
            producer=0,
        ),
        "p53_producer": producer_testbench(
            top_name=modules["p53_producer"],
            case=_producer_case(cluster=8, producer=0, logical_head_groups=logical_head_groups),
            cluster=8,
            producer=0,
        ),
    }
    producer_block_capacity = {
        "p54_producer": int(
            _producer_case(cluster=0, producer=0, logical_head_groups=logical_head_groups)["total_blocks"]
        ),
        "p53_producer": int(
            _producer_case(cluster=8, producer=0, logical_head_groups=logical_head_groups)["total_blocks"]
        ),
    }
    component_keys = (
        "p54_producer",
        "p53_producer",
        "p54_reducer",
        "p53_reducer",
        "p54_sram",
        "p53_sram",
        "global_tree",
    )
    for key in component_keys:
        source_dir = build_dir / f"{key}_rtl"
        source_dir.mkdir()
        (source_dir / "top.v").write_text(
            extract_module_family(generated_rtl, prefix=modules[key]),
            encoding="utf-8",
        )
        if key not in testbenches:
            continue
        tb_path = build_dir / f"{key}_tb.v"
        sim_path = build_dir / f"{key}.out"
        tb_path.write_text(testbenches[key], encoding="ascii")
        result, failure = _run_process(
            probe._icarus_compile_command(
                rtl_dir=source_dir,
                fakeram_path=fakeram_path,
                tb_path=tb_path,
                sim_path=sim_path,
            ),
            cwd=build_dir,
            timeout_sec=compile_timeout_sec,
            phase=f"compile_{key}",
        )
        phase_records.append({"phase": f"compile_{key}", "returncode": failure["returncode"] if failure else 0})
        if failure:
            return _failure(failure=failure, phase_records=phase_records)
        binaries[key] = sim_path

    producer_rows: list[list[list[JsonDict]]] = [
        [[] for _ in range(producers)] for producers in probe.CLUSTER_PRODUCERS
    ]
    producer_requests: list[list[list[list[JsonDict]]]] = [
        [[[], []] for _ in range(producers)] for producers in probe.CLUSTER_PRODUCERS
    ]
    producer_handshakes_by_cluster = [0 for _ in range(probe.CLUSTERS)]
    producer_replays = 0
    producer_replays_by_type = {"p54": 0, "p53": 0}
    for cluster, producers in enumerate(probe.CLUSTER_PRODUCERS):
        key = "p54_producer" if producers == 54 else "p53_producer"
        for producer in range(producers):
            case = _producer_case(
                cluster=cluster,
                producer=producer,
                logical_head_groups=logical_head_groups,
            )
            run_dir = work_dir / f"producer_{cluster:02d}_{producer:02d}"
            run_dir.mkdir()
            try:
                _write_producer_sidecars(
                    run_dir,
                    case,
                    value_block_capacity=producer_block_capacity[key],
                )
                result, failure = _run_process(
                    [probe._tool("vvp"), str(binaries[key])],
                    cwd=run_dir,
                    timeout_sec=simulation_timeout_sec,
                    phase=f"run_producer_c{cluster}_p{producer}",
                )
            finally:
                shutil.rmtree(run_dir, ignore_errors=True)
            producer_replays += 1
            producer_replays_by_type["p54" if producers == 54 else "p53"] += 1
            if failure:
                phase_records.append({"phase": failure["phase"], "returncode": failure["returncode"]})
                return _failure(failure=failure, phase_records=phase_records)
            rows, requests, summary = _parse_producer(result.stdout or "")
            row_audit = probe.compare_full_rows(case["expected_rows"], rows)
            request_audit = _check_request_metadata(requests, list(case["block_counts"]))
            commands = len(case["commands"])
            summary_ok = bool(
                summary
                and summary["outputs"] == len(case["expected_rows"])
                and summary["commands"] == commands
                and summary["completed"] == commands
                and summary["merge"] == len(case["expected_rows"])
                and summary["stream0_accept"] == commands
                and summary["stream1_accept"] == commands
                and summary["stream0_complete"] == commands
                and summary["stream1_complete"] == commands
                and summary["protocol_error"] == 0
            )
            if not row_audit["passed"] or not request_audit["passed"] or not summary_ok:
                return {
                    "simulation_status": "component_mismatch",
                    "returncode": 1,
                    "stderr": (
                        f"phase=run_producer_c{cluster}_p{producer}\n"
                        f"row_audit={row_audit} request_audit={request_audit} summary_ok={summary_ok}"
                    ),
                    "stdout": "",
                    "phase_records": phase_records,
                }
            producer_rows[cluster][producer] = rows
            producer_requests[cluster][producer] = requests
            producer_handshakes_by_cluster[cluster] += len(case["query_words"])
    phase_records.extend(
        {
            "phase": f"run_{label}_single_producer_serial",
            "returncode": 0,
            "replays": producer_replays_by_type[label],
        }
        for label in ("p54", "p53")
    )

    sram_summaries: list[JsonDict] = []
    for cluster, producers in enumerate(probe.CLUSTER_PRODUCERS):
        key = "p54_sram" if producers == 54 else "p53_sram"
        run_dir = work_dir / f"sram_{cluster:02d}"
        run_dir.mkdir()
        sidecar = _write_sram_sidecars(
            run_dir,
            cluster=cluster,
            logical_head_groups=logical_head_groups,
            producer_requests=producer_requests[cluster],
        )
        tb_path = build_dir / f"{key}_c{cluster}_tb.v"
        sim_path = build_dir / f"{key}.out"
        tb_path.write_text(sram_testbench(top_name=modules[key], producers=producers, sidecar=sidecar), encoding="ascii")
        if key not in binaries:
            result, failure = _run_process(
                probe._icarus_compile_command(
                    rtl_dir=build_dir / f"{key}_rtl",
                    fakeram_path=fakeram_path,
                    tb_path=tb_path,
                    sim_path=sim_path,
                ),
                cwd=build_dir,
                timeout_sec=compile_timeout_sec,
                phase=f"compile_{key}",
            )
            phase_records.append({"phase": f"compile_{key}", "returncode": failure["returncode"] if failure else 0})
            if failure:
                return _failure(failure=failure, phase_records=phase_records)
            binaries[key] = sim_path
        try:
            result, failure = _run_process(
                [probe._tool("vvp"), str(binaries[key])],
                cwd=run_dir,
                timeout_sec=simulation_timeout_sec,
                phase=f"run_sram_c{cluster}",
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
        if failure:
            phase_records.append({"phase": failure["phase"], "returncode": failure["returncode"]})
            return _failure(failure=failure, phase_records=phase_records)
        responses, summary = _parse_sram(result.stdout or "")
        response_audit = _check_sram_responses(
            cluster=cluster,
            logical_head_groups=logical_head_groups,
            responses=responses,
            expected_responses=list(sidecar["expected_responses"]),
        )
        commands = logical_head_groups * probe.WAVES
        summary_ok = bool(
            summary
            and summary["fill_targets"] == commands
            and summary["fill_rows"] == commands * probe.ROWS_PER_BUFFER
            and summary["requests"] == sidecar["request_count"]
            and summary["responses"] == sidecar["request_count"]
            and summary["commands"] == commands
            and summary["releases"] == commands
            and summary["protocol_error"] == 0
            and len(responses) == sidecar["request_count"]
        )
        if not response_audit["passed"] or not summary_ok:
            return {
                "simulation_status": "component_mismatch",
                "returncode": 1,
                "stderr": f"phase=run_sram_c{cluster}\nresponse_audit={response_audit} summary_ok={summary_ok}",
                "stdout": "",
                "phase_records": phase_records,
            }
        sram_summaries.append(summary)
        phase_records.append(
            {"phase": f"run_{'p54' if producers == 54 else 'p53'}_sram_c{cluster}", "returncode": 0}
        )

    reference = probe._reference(logical_head_groups=logical_head_groups)
    observed_cluster_rows: list[list[JsonDict]] = [[] for _ in range(probe.CLUSTERS)]
    reducer_summaries: list[JsonDict] = []
    for cluster, producers in enumerate(probe.CLUSTER_PRODUCERS):
        key = "p54_reducer" if producers == 54 else "p53_reducer"
        flattened = [row for rows in producer_rows[cluster] for row in rows]
        run_dir = work_dir / f"reducer_{cluster:02d}"
        run_dir.mkdir()
        leaf_mem = run_dir / "leaf.memh"
        reducer_probe._write_leaf_mem(leaf_mem, flattened)
        tb_path = build_dir / f"{key}_c{cluster}_tb.v"
        sim_path = build_dir / f"{key}.out"
        tb_path.write_text(
            reducer_probe._testbench(
                top_name=modules[key],
                producers=producers,
                command_count=logical_head_groups,
                leaf_rows=flattened,
                output_ready_pattern=output_ready_pattern,
                stress_interfaces=True,
                seed=probe.SEED,
                leaf_mem_path=Path("leaf.memh"),
            ),
            encoding="ascii",
        )
        if key not in binaries:
            result, failure = _run_process(
                probe._icarus_compile_command(
                    rtl_dir=build_dir / f"{key}_rtl",
                    fakeram_path=fakeram_path,
                    tb_path=tb_path,
                    sim_path=sim_path,
                ),
                cwd=build_dir,
                timeout_sec=compile_timeout_sec,
                phase=f"compile_{key}",
            )
            phase_records.append({"phase": f"compile_{key}", "returncode": failure["returncode"] if failure else 0})
            if failure:
                return _failure(failure=failure, phase_records=phase_records)
            binaries[key] = sim_path
        try:
            result, failure = _run_process(
                [probe._tool("vvp"), str(binaries[key])],
                cwd=run_dir,
                timeout_sec=simulation_timeout_sec,
                phase=f"run_reducer_c{cluster}",
            )
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)
        if failure:
            phase_records.append({"phase": failure["phase"], "returncode": failure["returncode"]})
            return _failure(failure=failure, phase_records=phase_records)
        rows, summary = _parse_reducer(result.stdout or "", cluster=cluster)
        row_audit = probe.compare_full_rows(reference["cluster_rows"][cluster], rows)
        summary_ok = bool(
            summary
            and summary["outputs"] == logical_head_groups * probe.EXPECTED_PER_CLUSTER["emitted_beat_count"]
            and summary["emitted"] == logical_head_groups * probe.EXPECTED_PER_CLUSTER["emitted_beat_count"]
            and summary["commands"] == logical_head_groups
            and not any(
                summary[key]
                for key in ("protocol_error", "group_error", "local_tree_error", "temporal_error")
            )
        )
        if not row_audit["passed"] or not summary_ok:
            return {
                "simulation_status": "component_mismatch",
                "returncode": 1,
                "stderr": f"phase=run_reducer_c{cluster}\nrow_audit={row_audit} summary_ok={summary_ok}",
                "stdout": "",
                "phase_records": phase_records,
            }
        observed_cluster_rows[cluster] = rows
        reducer_summaries.append(summary)
        phase_records.append(
            {"phase": f"run_{'p54' if producers == 54 else 'p53'}_reducer_c{cluster}", "returncode": 0}
        )

    global_dir = work_dir / "global_fine"
    global_dir.mkdir()
    global_sidecar = _write_global_sidecar(global_dir, observed_cluster_rows)
    global_tb_path = build_dir / "global_tree_tb.v"
    global_sim = build_dir / "global_tree.out"
    global_tb_path.write_text(
        global_testbench(
            top_name=modules["global_tree"],
            rows_per_cluster=int(global_sidecar["rows_per_cluster"]),
            output_ready_pattern=output_ready_pattern,
            timeout_cycles=logical_head_groups * probe.TB_TIMEOUT_CYCLES,
        ),
        encoding="ascii",
    )
    result, failure = _run_process(
        probe._icarus_compile_command(
            rtl_dir=build_dir / "global_tree_rtl",
            fakeram_path=fakeram_path,
            tb_path=global_tb_path,
            sim_path=global_sim,
        ),
        cwd=build_dir,
        timeout_sec=compile_timeout_sec,
        phase="compile_global_tree",
    )
    phase_records.append({"phase": "compile_global_tree", "returncode": failure["returncode"] if failure else 0})
    if failure:
        return _failure(failure=failure, phase_records=phase_records)
    result, failure = _run_process(
        [probe._tool("vvp"), str(global_sim)],
        cwd=global_dir,
        timeout_sec=simulation_timeout_sec,
        phase="run_global_tree",
    )
    if failure:
        phase_records.append({"phase": failure["phase"], "returncode": failure["returncode"]})
        return _failure(failure=failure, phase_records=phase_records)
    global_stdout = result.stdout or ""
    _, _, _, root_rows, timeout_cycle = probe._parse_stdout(global_stdout)
    global_match = _GLOBAL_SUMMARY_RE.search(global_stdout)
    root_audit = probe.compare_full_rows(reference["root_rows"], root_rows)
    global_ok = bool(
        global_match
        and timeout_cycle is None
        and not int(global_match.group(5))
        and all(int(global_match.group(index)) == len(root_rows) for index in (1, 2, 3, 4))
        and root_audit["passed"]
    )
    if not global_ok:
        return {
            "simulation_status": "component_mismatch",
            "returncode": 1,
            "stderr": f"phase=run_global_tree\nroot_audit={root_audit} global_summary={global_match.groups() if global_match else None}",
            "stdout": global_stdout,
            "phase_records": phase_records,
        }
    phase_records.append({"phase": "run_global_tree", "returncode": 0})

    cluster_summaries = []
    for cluster in range(probe.CLUSTERS):
        sram = sram_summaries[cluster]
        reducer = reducer_summaries[cluster]
        cluster_summaries.append(
            {
                "cluster": cluster,
                "wave_command_accept_count": logical_head_groups * probe.WAVES,
                "completed_command_count": int(reducer["commands"]),
                "emitted_beat_count": int(reducer["emitted"]),
                "fill_target_accept_count": int(sram["fill_targets"]),
                "fill_row_accept_count": int(sram["fill_rows"]),
                "request_accept_count": int(sram["requests"]),
                "response_accept_count": int(sram["responses"]),
                "command_accept_count": int(sram["commands"]),
                "command_release_count": int(sram["releases"]),
                "errors": 0,
            }
        )
    first_root, last_root, drain = (int(global_match.group(index)) for index in (6, 7, 8))
    summary = {
        "producer_handshake_count": sum(producer_handshakes_by_cluster),
        "fill_target_accept_count": sum(int(row["fill_targets"]) for row in sram_summaries),
        "fill_row_accept_count": sum(int(row["fill_rows"]) for row in sram_summaries),
        "sram_request_accept_count": sum(int(row["requests"]) for row in sram_summaries),
        "sram_response_accept_count": sum(int(row["responses"]) for row in sram_summaries),
        "cluster_row_count": sum(len(rows) for rows in observed_cluster_rows),
        "root_row_count": len(root_rows),
        "command_accept_count": logical_head_groups * probe.WAVES,
        "cadence_command_accept_count": logical_head_groups * probe.WAVES,
        "protocol_error": 0,
        "first_root_cycle": first_root,
        "last_root_cycle": last_root,
        "drain_cycles": drain,
    }
    synthetic = [
        (
            f"CLUSTER_RESULT cluster={row['cluster']} cmd={row['command_id']} head={row['head_id']} "
            f"slice={row['slice']} last={int(row['last'])} max={row['global_max']} sum={row['exp_sum']} "
            f"value={reducer_probe.pack_numerators(row['value']):082x} cycle=0"
        )
        for rows in observed_cluster_rows
        for row in rows
    ]
    synthetic.extend(
        (
            f"CLUSTER_SUMMARY cluster={row['cluster']} wave_accept={row['wave_command_accept_count']} "
            f"completed={row['completed_command_count']} emitted={row['emitted_beat_count']} "
            f"fill_targets={row['fill_target_accept_count']} fill_rows={row['fill_row_accept_count']} "
            f"requests={row['request_accept_count']} responses={row['response_accept_count']} "
            f"command_accepts={row['command_accept_count']} command_releases={row['command_release_count']} "
            f"errors={row['errors']}"
        )
        for row in cluster_summaries
    )
    synthetic.append(global_stdout)
    synthetic.append(
        "SUMMARY "
        + " ".join(
            [
                f"producer_handshakes={summary['producer_handshake_count']}",
                f"fill_targets={summary['fill_target_accept_count']}",
                f"fill_rows={summary['fill_row_accept_count']}",
                f"sram_requests={summary['sram_request_accept_count']}",
                f"sram_responses={summary['sram_response_accept_count']}",
                f"cluster_rows={summary['cluster_row_count']}",
                f"root_rows={summary['root_row_count']}",
                f"command_accepts={summary['command_accept_count']}",
                f"cadence_accepts={summary['cadence_command_accept_count']}",
                "protocol_error=0",
                f"first_root={first_root}",
                f"last_root={last_root}",
                f"drain={drain}",
            ]
        )
    )
    return {
        "simulation_status": "ok",
        "returncode": 0,
        "stderr": "",
        "stdout": "\n".join(synthetic),
        "phase_records": phase_records,
        "component_metadata": {
            "proof": "fine_grained_concrete_rtl_composition",
            "strict_generated_top_guard": "passed",
            "producer_replays": producer_replays,
            "producer_replay_parallelism": 1,
            "sram_endpoint_replays": probe.CLUSTERS,
            "reducer_replays": probe.CLUSTERS,
            "global_tree_simulations": 1,
            "global_sidecar": global_sidecar,
            "compiled_modules": list(component_keys),
            "avoided_modules": ["p54_cluster_wrapper", "p53_cluster_wrapper"],
            "global_counts": {
                "root_completed_count": int(global_match.group(2)),
                "finalizer_accepted_count": int(global_match.group(3)),
                "tree_root_completed_count": int(global_match.group(4)),
                "counts_passed": True,
            },
        },
    }
