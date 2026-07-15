import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_dense_gemm_tile_stream import generate


def _config(array_m: int = 2, array_n: int = 3, result_mode: str = "scalar_stream") -> dict:
    suffix = "" if result_mode == "scalar_stream" else f"_{result_mode}"
    return {
        "top_name": f"dense_gemm_tile_stream_m{array_m}_n{array_n}{suffix}",
        "dense_gemm_tile_stream": {
            "array_m": array_m,
            "array_n": array_n,
            "precision": "int8",
            "accum_bits": 32,
            "result_mode": result_mode,
        },
    }


def _pack_signed8(values: list[int]) -> str:
    packed = 0
    for index, value in enumerate(values):
        packed |= (value & 0xFF) << (index * 8)
    width = len(values) * 8
    return f"{width}'sh{packed:0{width // 4}x}"


def _reference_outer_product(beats: list[tuple[list[int], list[int]]], array_m: int, array_n: int) -> list[int]:
    accum = [0] * (array_m * array_n)
    for a_vec, b_vec in beats:
        for row, a_lane in enumerate(a_vec):
            for col, b_lane in enumerate(b_vec):
                accum[row * array_n + col] += a_lane * b_lane
    return accum


def _pack_signed32(values: list[int]) -> str:
    packed = 0
    for index, value in enumerate(values):
        packed |= (value & 0xFFFF_FFFF) << (index * 32)
    width = len(values) * 32
    return f"{width}'sh{packed:0{width // 4}x}"


def _write_tb(
    path: Path,
    *,
    top_name: str,
    first_beats: list[tuple[list[int], list[int]]],
    second_beats: list[tuple[list[int], list[int]]],
) -> None:
    array_m = len(first_beats[0][0])
    array_n = len(first_beats[0][1])
    row_bits = max(1, (array_m - 1).bit_length())
    col_bits = max(1, (array_n - 1).bit_length())
    index_bits = max(1, ((array_m * array_n) - 1).bit_length())
    first_beat_lines = []
    for idx, (a_vec, b_vec) in enumerate(first_beats):
        first_beat_lines.append(
            f"    send_input({_pack_signed8(a_vec)}, {_pack_signed8(b_vec)}, "
            f"1'b{1 if idx + 1 == len(first_beats) else 0});"
        )
        if idx == 0:
            first_beat_lines.append("    wait_cycles(2);")
        elif idx + 1 < len(first_beats):
            first_beat_lines.append("    wait_cycles(1);")
    second_beat_lines = []
    for idx, (a_vec, b_vec) in enumerate(second_beats):
        second_beat_lines.append(
            f"    send_input({_pack_signed8(a_vec)}, {_pack_signed8(b_vec)}, "
            f"1'b{1 if idx + 1 == len(second_beats) else 0});"
        )
        if idx + 1 < len(second_beats):
            second_beat_lines.append("    wait_cycles(1);")

    tb = f"""`timescale 1ns/1ps
module tb;
  localparam integer ARRAY_M = {array_m};
  localparam integer ARRAY_N = {array_n};
  localparam integer RESULT_COUNT = ARRAY_M * ARRAY_N;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid = 1'b0;
  wire command_ready;
  reg input_valid = 1'b0;
  wire input_ready;
  reg input_last = 1'b0;
  reg signed [ARRAY_M*8-1:0] input_a = '0;
  reg signed [ARRAY_N*8-1:0] input_b = '0;
  wire result_valid;
  reg result_ready = 1'b0;
  wire [{row_bits - 1}:0] result_row;
  wire [{col_bits - 1}:0] result_col;
  wire [{index_bits - 1}:0] result_index;
  wire signed [31:0] result_value;

  integer cycle_count = 0;
  integer seen_first = 0;
  integer seen_second = 0;
  integer hold_cycle = 0;
  reg hold_active = 1'b0;
  reg [{row_bits - 1}:0] hold_row = '0;
  reg [{col_bits - 1}:0] hold_col = '0;
  reg [{index_bits - 1}:0] hold_index = '0;
  reg signed [31:0] hold_value = 32'sd0;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_a(input_a),
      .input_b(input_b),
      .result_valid(result_valid),
      .result_ready(result_ready),
      .result_row(result_row),
      .result_col(result_col),
      .result_index(result_index),
      .result_value(result_value)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle_count <= 0;
      hold_active <= 1'b0;
    end else begin
      cycle_count <= cycle_count + 1;
      if (result_valid) begin
        $display(
            "OBSERVE cycle=%0d ready=%0d row=%0d col=%0d index=%0d value=%0d",
            cycle_count,
            result_ready,
            result_row,
            result_col,
            result_index,
            result_value
        );
        if (hold_active) begin
          if (
              result_row !== hold_row
              || result_col !== hold_col
              || result_index !== hold_index
              || result_value !== hold_value
          ) begin
            $fatal(1, "result changed under backpressure at cycle %0d", cycle_count);
          end
        end
        if (!result_ready) begin
          hold_active <= 1'b1;
          hold_row <= result_row;
          hold_col <= result_col;
          hold_index <= result_index;
          hold_value <= result_value;
          hold_cycle <= cycle_count;
        end else if (hold_active) begin
          $display("HOLD_RELEASE cycle=%0d start=%0d index=%0d", cycle_count, hold_cycle, result_index);
          hold_active <= 1'b0;
        end
      end else begin
        hold_active <= 1'b0;
      end

      if (command_valid && command_ready) begin
        $display("COMMAND_ACCEPT cycle=%0d", cycle_count);
      end
      if (input_valid && input_ready) begin
        $display("INPUT_ACCEPT cycle=%0d last=%0d", cycle_count, input_last);
      end
      if (result_valid && result_ready) begin
        if (seen_first < RESULT_COUNT) begin
          $display(
              "RESULT cmd=1 cycle=%0d row=%0d col=%0d index=%0d value=%0d",
              cycle_count,
              result_row,
              result_col,
              result_index,
              result_value
          );
          seen_first <= seen_first + 1;
        end else begin
          $display(
              "RESULT cmd=2 cycle=%0d row=%0d col=%0d index=%0d value=%0d",
              cycle_count,
              result_row,
              result_col,
              result_index,
              result_value
          );
          seen_second <= seen_second + 1;
        end
      end
      if (cycle_count > 250) begin
        $fatal(1, "timeout");
      end
    end
  end

  task automatic wait_cycles(input integer count);
    integer idx;
    begin
      for (idx = 0; idx < count; idx = idx + 1) begin
        @(posedge clk);
      end
    end
  endtask

  task automatic send_command;
    begin
      @(negedge clk);
      command_valid <= 1'b1;
      while (!command_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      command_valid <= 1'b0;
    end
  endtask

  task automatic send_input(
      input signed [ARRAY_M*8-1:0] a_vec,
      input signed [ARRAY_N*8-1:0] b_vec,
      input bit last_vec
  );
    begin
      @(negedge clk);
      input_a <= a_vec;
      input_b <= b_vec;
      input_last <= last_vec;
      input_valid <= 1'b1;
      while (!input_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      input_valid <= 1'b0;
      input_last <= 1'b0;
      input_a <= '0;
      input_b <= '0;
    end
  endtask

  task automatic set_result_ready(input bit ready_value);
    begin
      @(negedge clk);
      result_ready <= ready_value;
    end
  endtask

  initial begin
    wait_cycles(2);
    @(negedge clk);
    rst_n = 1'b1;
    result_ready = 1'b0;

    send_command();
{chr(10).join(first_beat_lines)}

    wait_cycles(1);
    set_result_ready(1'b1);
    wait_cycles(1);
    set_result_ready(1'b0);

    @(negedge clk);
    command_valid <= 1'b1;
    wait_cycles(1);
    if (command_ready !== 1'b0) begin
      $fatal(1, "command_ready must stay low while draining results");
    end
    @(negedge clk);
    command_valid <= 1'b0;

    wait_cycles(1);
    set_result_ready(1'b1);
    wait_cycles(1);
    set_result_ready(1'b0);
    wait_cycles(1);
    set_result_ready(1'b1);
    wait_cycles(4);

    while (seen_first < RESULT_COUNT) begin
      wait_cycles(1);
    end

    wait_cycles(1);
    send_command();
{chr(10).join(second_beat_lines)}

    wait_cycles(1);
    set_result_ready(1'b1);
    while (seen_second < RESULT_COUNT) begin
      wait_cycles(1);
    end
    wait_cycles(2);
    $finish;
  end
endmodule
"""
    path.write_text(tb, encoding="utf-8")


def _write_packed_tb(
    path: Path,
    *,
    top_name: str,
    first_beats: list[tuple[list[int], list[int]]],
    second_beats: list[tuple[list[int], list[int]]],
) -> None:
    array_n = len(first_beats[0][1])
    first_rows = _reference_outer_product(first_beats, array_m=1, array_n=array_n)
    second_rows = _reference_outer_product(second_beats, array_m=1, array_n=array_n)
    first_beat_lines = []
    for idx, (a_vec, b_vec) in enumerate(first_beats):
        first_beat_lines.append(
            f"    send_input({_pack_signed8(a_vec)}, {_pack_signed8(b_vec)}, "
            f"1'b{1 if idx + 1 == len(first_beats) else 0});"
        )
        if idx == 0:
            first_beat_lines.append("    wait_cycles(2);")
        elif idx + 1 < len(first_beats):
            first_beat_lines.append("    wait_cycles(1);")
    second_beat_lines = []
    for idx, (a_vec, b_vec) in enumerate(second_beats):
        second_beat_lines.append(
            f"    send_input({_pack_signed8(a_vec)}, {_pack_signed8(b_vec)}, "
            f"1'b{1 if idx + 1 == len(second_beats) else 0});"
        )
        if idx + 1 < len(second_beats):
            second_beat_lines.append("    wait_cycles(1);")

    tb = f"""`timescale 1ns/1ps
module tb;
  localparam integer ARRAY_N = {array_n};
  localparam integer SCORE_WIDTH = ARRAY_N * 32;
  localparam [SCORE_WIDTH-1:0] EXPECTED_FIRST = {_pack_signed32(first_rows)};
  localparam [SCORE_WIDTH-1:0] EXPECTED_SECOND = {_pack_signed32(second_rows)};

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  reg command_valid = 1'b0;
  wire command_ready;
  reg input_valid = 1'b0;
  wire input_ready;
  reg input_last = 1'b0;
  reg signed [7:0] input_a = '0;
  reg signed [ARRAY_N*8-1:0] input_b = '0;
  wire result_valid;
  reg result_ready = 1'b0;
  wire [0:0] result_row;
  wire [{max(1, (array_n - 1).bit_length()) - 1}:0] result_col;
  wire [{max(1, (array_n - 1).bit_length()) - 1}:0] result_index;
  wire signed [31:0] result_value;
  wire signed [SCORE_WIDTH-1:0] result_score_row;

  integer cycle_count = 0;
  integer seen_results = 0;
  reg hold_active = 1'b0;
  reg signed [SCORE_WIDTH-1:0] hold_score_row = '0;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .command_valid(command_valid),
      .command_ready(command_ready),
      .input_valid(input_valid),
      .input_ready(input_ready),
      .input_last(input_last),
      .input_a(input_a),
      .input_b(input_b),
      .result_valid(result_valid),
      .result_ready(result_ready),
      .result_row(result_row),
      .result_col(result_col),
      .result_index(result_index),
      .result_value(result_value),
      .result_score_row(result_score_row)
  );

  always #5 clk = ~clk;

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle_count <= 0;
      seen_results <= 0;
      hold_active <= 1'b0;
      hold_score_row <= '0;
    end else begin
      cycle_count <= cycle_count + 1;
      if (result_valid) begin
        $display("OBSERVE cycle=%0d ready=%0d row=%064x", cycle_count, result_ready, result_score_row);
        if (hold_active && result_score_row !== hold_score_row) begin
          $fatal(1, "packed row changed under backpressure at cycle %0d", cycle_count);
        end
        if (!result_ready) begin
          hold_active <= 1'b1;
          hold_score_row <= result_score_row;
        end else begin
          hold_active <= 1'b0;
        end
      end else begin
        hold_active <= 1'b0;
      end

      if (command_valid && command_ready) begin
        $display("COMMAND_ACCEPT cycle=%0d", cycle_count);
      end
      if (input_valid && input_ready) begin
        $display("INPUT_ACCEPT cycle=%0d last=%0d", cycle_count, input_last);
      end
      if (result_valid && result_ready) begin
        seen_results <= seen_results + 1;
        if (seen_results == 0) begin
          $display("PACKED_RESULT cmd=1 cycle=%0d row=%064x", cycle_count, result_score_row);
          if (result_score_row !== EXPECTED_FIRST) begin
            $fatal(1, "first packed row mismatch got=%064x expected=%064x", result_score_row, EXPECTED_FIRST);
          end
        end else if (seen_results == 1) begin
          $display("PACKED_RESULT cmd=2 cycle=%0d row=%064x", cycle_count, result_score_row);
          if (result_score_row !== EXPECTED_SECOND) begin
            $fatal(1, "second packed row mismatch got=%064x expected=%064x", result_score_row, EXPECTED_SECOND);
          end
        end else begin
          $fatal(1, "unexpected extra packed result");
        end
      end
      if (cycle_count > 200) begin
        $fatal(1, "timeout");
      end
    end
  end

  task automatic wait_cycles(input integer count);
    integer idx;
    begin
      for (idx = 0; idx < count; idx = idx + 1) begin
        @(posedge clk);
      end
    end
  endtask

  task automatic send_command;
    begin
      @(negedge clk);
      command_valid <= 1'b1;
      while (!command_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      command_valid <= 1'b0;
    end
  endtask

  task automatic send_input(
      input signed [7:0] a_vec,
      input signed [ARRAY_N*8-1:0] b_vec,
      input bit last_vec
  );
    begin
      @(negedge clk);
      input_a <= a_vec;
      input_b <= b_vec;
      input_last <= last_vec;
      input_valid <= 1'b1;
      while (!input_ready) begin
        @(negedge clk);
      end
      @(negedge clk);
      input_valid <= 1'b0;
      input_last <= 1'b0;
      input_a <= '0;
      input_b <= '0;
    end
  endtask

  task automatic set_result_ready(input bit ready_value);
    begin
      @(negedge clk);
      result_ready <= ready_value;
    end
  endtask

  initial begin
    wait_cycles(2);
    @(negedge clk);
    rst_n = 1'b1;
    result_ready = 1'b0;

    send_command();
{chr(10).join(first_beat_lines)}

    wait_cycles(1);
    @(negedge clk);
    command_valid <= 1'b1;
    wait_cycles(1);
    if (command_ready !== 1'b0) begin
      $fatal(1, "command_ready must stay low while packed result is pending");
    end
    @(negedge clk);
    command_valid <= 1'b0;
    set_result_ready(1'b1);
    while (seen_results < 1) begin
      wait_cycles(1);
    end
    set_result_ready(1'b0);
    wait_cycles(1);

    send_command();
{chr(10).join(second_beat_lines)}

    wait_cycles(1);
    set_result_ready(1'b1);
    while (seen_results < 2) begin
      wait_cycles(1);
    end
    wait_cycles(2);
    $finish;
  end
endmodule
"""
    path.write_text(tb, encoding="utf-8")


def _iverilog() -> str | None:
    iverilog = shutil.which("iverilog")
    if iverilog is not None:
        return iverilog
    fallback = Path("/oss-cad-suite/bin/iverilog")
    return str(fallback) if fallback.exists() else None


def _vvp() -> str | None:
    vvp = shutil.which("vvp")
    if vvp is not None:
        return vvp
    fallback = Path("/oss-cad-suite/bin/vvp")
    return str(fallback) if fallback.exists() else None


def test_dense_gemm_tile_stream_generator_manifest_and_header(tmp_path: Path) -> None:
    config = _config(array_m=16, array_n=16)
    generate(config, tmp_path)

    manifest = json.loads((tmp_path / "dense_gemm_tile_stream_manifest.json").read_text())
    text = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["array_m"] == 16
    assert manifest["array_n"] == 16
    assert manifest["semantic_profile"] == "operational_dense_gemm_outer_product_stream_s8_s8_acc32"
    assert manifest["result_mode"] == "scalar_stream"
    assert manifest["result_interface"] == "ready_valid_scalar_accumulator_stream"
    assert manifest["all_accumulators_observable"] is True
    assert manifest["input_accepts_same_cycle_as_command"] is False
    assert "Operational dense GEMM stream tile." in text
    assert "distinct from the PPA harness generated by gen_dense_gemm_tile.py" in text
    assert "result_value = accum[result_index_q];" in text
    assert "result_score_row" in text


def test_dense_gemm_tile_stream_matches_reference_and_stream_protocol(tmp_path: Path) -> None:
    iverilog = _iverilog()
    vvp = _vvp()
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")

    config = _config(array_m=2, array_n=3)
    generate(config, tmp_path)

    first_beats = [
        ([3, -2], [4, -5, 6]),
        ([-7, 8], [-9, 10, -11]),
        ([12, -13], [-1, 2, -3]),
    ]
    second_beats = [
        ([1, 2], [-3, 4, -5]),
        ([-6, 7], [8, -9, 10]),
    ]
    _write_tb(tmp_path / "tb.v", top_name=config["top_name"], first_beats=first_beats, second_beats=second_beats)

    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(tmp_path / "simv"),
            str(tmp_path / "top.v"),
            str(tmp_path / "tb.v"),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    sim = subprocess.run(
        [vvp, str(tmp_path / "simv")],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    result_pattern = re.compile(
        r"RESULT cmd=(?P<cmd>\d+) cycle=(?P<cycle>\d+) row=(?P<row>\d+) col=(?P<col>\d+) index=(?P<index>\d+) value=(?P<value>-?\d+)"
    )
    observe_pattern = re.compile(
        r"OBSERVE cycle=(?P<cycle>\d+) ready=(?P<ready>\d+) row=(?P<row>\d+) col=(?P<col>\d+) index=(?P<index>\d+) value=(?P<value>-?\d+)"
    )
    command_pattern = re.compile(r"COMMAND_ACCEPT cycle=(?P<cycle>\d+)")
    input_pattern = re.compile(r"INPUT_ACCEPT cycle=(?P<cycle>\d+) last=(?P<last>\d+)")

    results: dict[int, list[tuple[int, int, int, int, int]]] = {1: [], 2: []}
    observes: list[dict[str, int]] = []
    command_cycles: list[int] = []
    input_events: list[tuple[int, int]] = []

    for line in sim.stdout.splitlines():
        if match := result_pattern.fullmatch(line):
            cmd = int(match.group("cmd"))
            results[cmd].append(
                (
                    int(match.group("cycle")),
                    int(match.group("row")),
                    int(match.group("col")),
                    int(match.group("index")),
                    int(match.group("value")),
                )
            )
        elif match := observe_pattern.fullmatch(line):
            observes.append({key: int(value) for key, value in match.groupdict().items()})
        elif match := command_pattern.fullmatch(line):
            command_cycles.append(int(match.group("cycle")))
        elif match := input_pattern.fullmatch(line):
            input_events.append((int(match.group("cycle")), int(match.group("last"))))

    expected_first = _reference_outer_product(first_beats, array_m=2, array_n=3)
    expected_second = _reference_outer_product(second_beats, array_m=2, array_n=3)

    assert [value for _, _, _, _, value in results[1]] == expected_first
    assert [value for _, _, _, _, value in results[2]] == expected_second
    assert [(row, col, index) for _, row, col, index, _ in results[1]] == [
        (0, 0, 0),
        (0, 1, 1),
        (0, 2, 2),
        (1, 0, 3),
        (1, 1, 4),
        (1, 2, 5),
    ]
    assert [(row, col, index) for _, row, col, index, _ in results[2]] == [
        (0, 0, 0),
        (0, 1, 1),
        (0, 2, 2),
        (1, 0, 3),
        (1, 1, 4),
        (1, 2, 5),
    ]
    assert len(command_cycles) == 2
    assert len(input_events) == 5
    assert [last for _, last in input_events] == [0, 0, 1, 0, 1]
    assert command_cycles[1] > results[1][-1][0]

    stalled = [entry for entry in observes if entry["ready"] == 0]
    assert stalled, sim.stdout
    for previous, current in zip(stalled, stalled[1:]):
        if current["cycle"] == previous["cycle"] + 1:
            assert current["row"] == previous["row"]
            assert current["col"] == previous["col"]
            assert current["index"] == previous["index"]
            assert current["value"] == previous["value"]

    assert expected_first[0] != _reference_outer_product(first_beats[:-1], array_m=2, array_n=3)[0]


def test_packed_decode_score_tile_matches_reference_and_protocol(tmp_path: Path) -> None:
    iverilog = _iverilog()
    vvp = _vvp()
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")

    config = _config(array_m=1, array_n=8, result_mode="packed_score_row")
    generate(config, tmp_path)

    manifest = json.loads((tmp_path / "dense_gemm_tile_stream_manifest.json").read_text())
    text = (tmp_path / "top.v").read_text(encoding="utf-8")

    assert manifest["result_mode"] == "packed_score_row"
    assert manifest["result_interface"] == "ready_valid_packed_score_row"
    assert manifest["functional_observability"] == "packed_score_row"
    assert manifest["packed_score_row_semantics"]["fill_score_row_compatible"] is True
    assert manifest["packed_score_row_semantics"]["lane_order"] == "result_score_row[j*32 +: 32] == lane_j"
    assert "result_score_row_q" in text

    first_beats = [
        ([-3], [2, -4, 5, -6, 7, -8, 9, -10]),
        ([11], [-12, 13, -14, 15, -16, 17, -18, 19]),
        ([-20], [21, -22, 23, -24, 25, -26, 27, -28]),
    ]
    second_beats = [
        ([4], [-1, 2, -3, 4, -5, 6, -7, 8]),
        ([-9], [10, -11, 12, -13, 14, -15, 16, -17]),
    ]
    _write_packed_tb(tmp_path / "tb_packed.v", top_name=config["top_name"], first_beats=first_beats, second_beats=second_beats)

    subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(tmp_path / "simv_packed"),
            str(tmp_path / "top.v"),
            str(tmp_path / "tb_packed.v"),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    sim = subprocess.run(
        [vvp, str(tmp_path / "simv_packed")],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    result_pattern = re.compile(r"PACKED_RESULT cmd=(?P<cmd>\d+) cycle=(?P<cycle>\d+) row=(?P<row>[0-9a-f]+)")
    observe_pattern = re.compile(r"OBSERVE cycle=(?P<cycle>\d+) ready=(?P<ready>\d+) row=(?P<row>[0-9a-f]+)")
    command_pattern = re.compile(r"COMMAND_ACCEPT cycle=(?P<cycle>\d+)")
    input_pattern = re.compile(r"INPUT_ACCEPT cycle=(?P<cycle>\d+) last=(?P<last>\d+)")

    packed_results: dict[int, tuple[int, str]] = {}
    observes: list[dict[str, str]] = []
    command_cycles: list[int] = []
    input_events: list[tuple[int, int]] = []

    for line in sim.stdout.splitlines():
        if match := result_pattern.fullmatch(line):
            packed_results[int(match.group("cmd"))] = (int(match.group("cycle")), match.group("row"))
        elif match := observe_pattern.fullmatch(line):
            observes.append(match.groupdict())
        elif match := command_pattern.fullmatch(line):
            command_cycles.append(int(match.group("cycle")))
        elif match := input_pattern.fullmatch(line):
            input_events.append((int(match.group("cycle")), int(match.group("last"))))

    expected_first = _pack_signed32(_reference_outer_product(first_beats, array_m=1, array_n=8)).split("sh", 1)[1]
    expected_second = _pack_signed32(_reference_outer_product(second_beats, array_m=1, array_n=8)).split("sh", 1)[1]

    assert packed_results[1][1] == expected_first
    assert packed_results[2][1] == expected_second
    assert len(command_cycles) == 2
    assert len(input_events) == 5
    assert [last for _, last in input_events] == [0, 0, 1, 0, 1]
    assert command_cycles[1] > packed_results[1][0]
    stalled = [entry for entry in observes if entry["ready"] == "0"]
    assert stalled, sim.stdout
    for previous, current in zip(stalled, stalled[1:]):
        if int(current["cycle"]) == int(previous["cycle"]) + 1:
            assert current["row"] == previous["row"]

    assert packed_results[1][1] != _pack_signed32(_reference_outer_product(first_beats[:-1], array_m=1, array_n=8)).split("sh", 1)[1]
