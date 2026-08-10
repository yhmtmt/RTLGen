import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.llama7b_rmsnorm_phase2 import (
    CANONICAL_PROTOCOL_ERROR_BF16,
    HIDDEN_SIZE,
    rmsnorm_bf16_phase2,
)
from npu.rtlgen.gen_llama7b_rmsnorm import generate


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config(top_name: str = "llama7b_rmsnorm_bf16_l16") -> dict[str, object]:
    return {
        "top_name": top_name,
        "llama7b_rmsnorm": {
            "lanes": 16,
        },
    }


def _write_memh(path: Path, words: list[int] | tuple[int, ...]) -> None:
    path.write_text("".join(f"{word:04x}\n" for word in words), encoding="ascii")


def _finite_random_case() -> tuple[list[int], list[int], tuple[int, ...], bool, bool]:
    rng = random.Random(0x524D5333)
    row = []
    gamma = []
    for _ in range(HIDDEN_SIZE):
        exponent = rng.randrange(0, 255)
        fraction = rng.randrange(0, 128)
        sign = rng.randrange(0, 2) << 15
        row.append(sign | (exponent << 7) | fraction)

        gamma_exponent = rng.randrange(0, 255)
        gamma_fraction = rng.randrange(0, 128)
        gamma_sign = rng.randrange(0, 2) << 15
        gamma.append(gamma_sign | (gamma_exponent << 7) | gamma_fraction)

    oracle = rmsnorm_bf16_phase2(row, gamma, lanes=16)
    return row, gamma, oracle.output, False, False


def _framing_error_case() -> tuple[list[int], list[int], tuple[int, ...], bool, bool]:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    expected = (CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE
    return row, gamma, expected, True, True


def _exponent_255_case() -> tuple[list[int], list[int], tuple[int, ...], bool, bool]:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    row[-1] = 0x7F80
    expected = (CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE
    return row, gamma, expected, True, False


def _render_tb(
    *,
    top_name: str,
    row_path: Path,
    gamma_path: Path,
    expected_path: Path,
    expect_protocol_error: bool,
    wrong_last: bool,
    stall_output: bool,
) -> str:
    wrong_last_expr = "(beat == BEATS-2)" if wrong_last else "(beat == BEATS-1)"
    out_ready_expr = "((beat + cycles) % 4 != 1)" if stall_output else "1'b1"
    expect_error_bit = "1'b1" if expect_protocol_error else "1'b0"
    return f"""module tb;
  localparam integer LANES = 16;
  localparam integer HIDDEN_SIZE = 4096;
  localparam integer BEATS = 256;

  reg clk = 0;
  always #5 clk = ~clk;

  reg rst_n = 0;
  reg in_valid = 0;
  wire in_ready;
  reg [255:0] in_row = 0;
  reg [255:0] in_gamma = 0;
  reg in_last = 0;

  wire out_valid;
  reg out_ready = 1;
  wire [255:0] out_row;
  wire out_last;
  wire out_protocol_error;
  wire [31:0] accepted_row_count;
  wire [31:0] completed_row_count;

  reg [15:0] row_mem [0:HIDDEN_SIZE-1];
  reg [15:0] gamma_mem [0:HIDDEN_SIZE-1];
  reg [15:0] expected_mem [0:HIDDEN_SIZE-1];

  integer beat;
  integer lane;
  integer index;
  integer cycles;
  reg stalled;
  reg [255:0] held_row;
  reg held_last;
  reg held_error;

  {top_name} dut (
      .clk(clk),
      .rst_n(rst_n),
      .in_valid(in_valid),
      .in_ready(in_ready),
      .in_row(in_row),
      .in_gamma(in_gamma),
      .in_last(in_last),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_row(out_row),
      .out_last(out_last),
      .out_protocol_error(out_protocol_error),
      .accepted_row_count(accepted_row_count),
      .completed_row_count(completed_row_count)
  );

  initial begin
    $readmemh("{row_path}", row_mem);
    $readmemh("{gamma_path}", gamma_mem);
    $readmemh("{expected_path}", expected_mem);

    repeat (3) @(posedge clk);
    rst_n = 1'b1;

    beat = 0;
    while (beat < BEATS) begin
      @(posedge clk);
      if (in_ready) begin
        in_valid <= 1'b1;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
          index = beat * LANES + lane;
          in_row[(lane * 16) +: 16] <= row_mem[index];
          in_gamma[(lane * 16) +: 16] <= gamma_mem[index];
        end
        in_last <= {wrong_last_expr};
        beat = beat + 1;
      end
    end

    @(posedge clk);
    in_valid <= 1'b0;
    in_last <= 1'b0;

    beat = 0;
    cycles = 0;
    stalled = 1'b0;
    while (beat < BEATS && cycles < 5000) begin
      @(negedge clk);
      out_ready = {out_ready_expr};
      @(posedge clk);
      cycles = cycles + 1;
      if (out_valid && !out_ready) begin
        if (!stalled) begin
          held_row = out_row;
          held_last = out_last;
          held_error = out_protocol_error;
          stalled = 1'b1;
        end else if (out_row !== held_row || out_last !== held_last || out_protocol_error !== held_error) begin
          $display("output changed while stalled beat=%0d", beat);
          $fatal;
        end
      end else begin
        stalled = 1'b0;
      end

      if (out_valid && out_ready) begin
        for (lane = 0; lane < LANES; lane = lane + 1) begin
          index = beat * LANES + lane;
          if (out_row[(lane * 16) +: 16] !== expected_mem[index]) begin
            $display(
                "mismatch beat=%0d lane=%0d got=%h exp=%h",
                beat,
                lane,
                out_row[(lane * 16) +: 16],
                expected_mem[index]
            );
            $fatal;
          end
        end
        if ((beat == BEATS - 1) !== out_last) begin
          $display("out_last mismatch beat=%0d", beat);
          $fatal;
        end
        if (out_protocol_error !== {expect_error_bit}) begin
          $display(
              "protocol_error mismatch beat=%0d got=%b exp=%b",
              beat,
              out_protocol_error,
              {expect_error_bit}
          );
          $fatal;
        end
        beat = beat + 1;
      end
    end

    if (beat != BEATS) begin
      $display("timeout beat=%0d cycles=%0d", beat, cycles);
      $fatal;
    end

    @(posedge clk);
    if (accepted_row_count !== 32'd1 || completed_row_count !== 32'd1) begin
      $display(
          "counter mismatch accepted=%0d completed=%0d",
          accepted_row_count,
          completed_row_count
      );
      $fatal;
    end

    $display("PASS");
    $finish;
  end
endmodule
"""


def _run_case(
    tmp_path: Path,
    *,
    row: list[int],
    gamma: list[int],
    expected: tuple[int, ...],
    expect_protocol_error: bool,
    wrong_last: bool,
    stall_output: bool,
) -> None:
    top_name = "llama7b_rmsnorm_bf16_l16"
    rtl_dir = tmp_path / "rtl"
    generate(_config(top_name), rtl_dir)

    row_path = tmp_path / "row.mem"
    gamma_path = tmp_path / "gamma.mem"
    expected_path = tmp_path / "expected.mem"
    tb_path = tmp_path / "tb.v"
    sim_path = tmp_path / "sim"

    _write_memh(row_path, row)
    _write_memh(gamma_path, gamma)
    _write_memh(expected_path, expected)
    tb_path.write_text(
        _render_tb(
            top_name=top_name,
            row_path=row_path,
            gamma_path=gamma_path,
            expected_path=expected_path,
            expect_protocol_error=expect_protocol_error,
            wrong_last=wrong_last,
            stall_output=stall_output,
        ),
        encoding="ascii",
    )

    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(sim_path),
            str(rtl_dir / "top.v"),
            str(tb_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    run = subprocess.run(
        [_tool("vvp"), str(sim_path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert "PASS" in run.stdout


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_llama7b_rmsnorm_phase3_generator_bootstraps_and_lints(tmp_path: Path) -> None:
    config = _config("llama7b_rmsnorm_bf16_l16")
    config_path = tmp_path / "config.json"
    out_dir = tmp_path / "rtl"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "npu" / "rtlgen" / "gen_llama7b_rmsnorm.py"),
            "--config",
            str(config_path),
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    manifest = json.loads((out_dir / "llama7b_rmsnorm_manifest.json").read_text(encoding="utf-8"))
    assert manifest["top_name"] == "llama7b_rmsnorm_bf16_l16"
    assert manifest["lanes"] == 16
    assert manifest["beats_per_row"] == 256
    assert manifest["no_stall_cycles"] == 776
    assert manifest["newton_iterations"] == 1
    assert manifest["newton_bias_q20"] == 4
    assert manifest["protocol_error"] == "canonical_qnan_row_on_exponent255_or_framing_error"
    assert manifest["semantic_profile"] == "llama7b_bf16_rmsnorm_phase3_bounded_ready_valid_v1"

    verilator = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-DECLFILENAME",
            "-Wno-UNUSEDSIGNAL",
            "-Wno-BLKSEQ",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            "llama7b_rmsnorm_bf16_l16",
            str(out_dir / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert verilator.returncode == 0, verilator.stderr


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_llama7b_rmsnorm_phase3_matches_phase2_with_backpressure(tmp_path: Path) -> None:
    row, gamma, expected, expect_protocol_error, wrong_last = _finite_random_case()
    _run_case(
        tmp_path,
        row=row,
        gamma=gamma,
        expected=expected,
        expect_protocol_error=expect_protocol_error,
        wrong_last=wrong_last,
        stall_output=True,
    )


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize(
    "case_fn",
    [_framing_error_case, _exponent_255_case],
    ids=["framing_error", "exponent_255"],
)
def test_llama7b_rmsnorm_phase3_protocol_error_cases(tmp_path: Path, case_fn) -> None:
    row, gamma, expected, expect_protocol_error, wrong_last = case_fn()
    _run_case(
        tmp_path,
        row=row,
        gamma=gamma,
        expected=expected,
        expect_protocol_error=expect_protocol_error,
        wrong_last=wrong_last,
        stall_output=False,
    )
