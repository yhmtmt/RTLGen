from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from control_plane.services.l1_task_generator import _read_config_target
from npu.eval.check_attention_score32_exact_shared_root_storage_physical_guard import (
    main as guard_main,
)
from npu.rtlgen.gen_attention_score32_exact_shared_root_storage_physical_harness import (
    generate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FAKERAM_MODEL = REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"
FAKERAM_BLACKBOX = REPO_ROOT / "npu/rtl/fakeram45_64x32_blackbox.v"
EXPECTED_MACROS = {2: 32, 4: 32, 8: 64, 15: 120}
PROPOSAL_ID = "prop_l1_attention_score32_exact_shared_root_storage_macro_ppa_v1"


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    pytest.skip(f"{name} unavailable")


def _config(top: str, banks: int) -> dict:
    return {
        "top_name": top,
        "attention_score32_exact_shared_root_storage_physical_harness": {
            "physical_banks": banks,
        },
    }


@pytest.mark.parametrize("banks", [2, 4, 8, 15])
def test_generator_retains_expected_macro_inventory(tmp_path: Path, banks: int) -> None:
    top = f"shared_root_storage_macro_b{banks}"
    generate(_config(top, banks), tmp_path)
    manifest = json.loads(
        (
            tmp_path
            / "attention_score32_exact_shared_root_storage_physical_harness_manifest.json"
        ).read_text(encoding="utf-8")
    )
    macro_manifest = json.loads(
        (tmp_path / "macro_manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["physical_banks"] == banks
    assert manifest["macro_count"] == EXPECTED_MACROS[banks]
    assert manifest["macro_area_um2"] == pytest.approx(
        EXPECTED_MACROS[banks] * 20.14 * 61.6
    )
    assert manifest["top_pin_bits"] == 228
    assert manifest["traffic"]["writes"] == 240
    assert macro_manifest["blackboxes"] == ["fakeram45_64x32"]
    assert macro_manifest["manifest_params"]["macro_count"] == EXPECTED_MACROS[banks]

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "-Wno-UNUSEDSIGNAL",
            "-Wno-UNDRIVEN",
            "-Wno-TIMESCALEMOD",
            "-Wno-SIDEEFFECT",
            "-Wno-LATCH",
            "-Wno-UNOPTFLAT",
            "-Wno-MULTIDRIVEN",
            "--top-module",
            top,
            str(tmp_path / "top.v"),
            str(FAKERAM_BLACKBOX),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert lint.returncode == 0, lint.stderr


@pytest.mark.parametrize("banks", [2, 4, 8, 15])
def test_harness_completes_all_macro_reads_and_writes(
    tmp_path: Path,
    banks: int,
) -> None:
    top = f"shared_root_storage_macro_b{banks}"
    generate(_config(top, banks), tmp_path)
    tb = tmp_path / "tb.sv"
    tb.write_text(
        f"""`timescale 1ns/1ps
module tb;
  reg clk = 0; always #5 clk = ~clk;
  reg rst_n = 0;
  reg start = 0;
  reg [31:0] seed = 32'h12345678;
  wire done;
  wire [31:0] folded_result;
  wire [31:0] cycle_count;
  wire [31:0] write_count;
  wire [31:0] read_request_count;
  wire [31:0] read_response_count;
  wire [31:0] protocol_error_count;
  {top} dut (.*);
  initial begin
    repeat (4) @(posedge clk); rst_n <= 1;
    repeat (2) @(posedge clk); start <= 1;
    @(posedge clk); start <= 0;
    wait (done); @(posedge clk);
    if (write_count != 240 || read_request_count != 240 ||
        read_response_count != 240 || protocol_error_count != 0)
      $fatal(1, "invalid harness counts w=%0d rq=%0d rs=%0d err=%0d",
        write_count, read_request_count, read_response_count,
        protocol_error_count);
    $display("PASS harness banks={banks} cycles=%0d fold=%h", cycle_count,
      folded_result);
    $finish;
  end
  initial begin #1000000; $fatal(1, "timeout"); end
endmodule
""",
        encoding="utf-8",
    )
    simv = tmp_path / "simv"
    compile_result = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "tb",
            "-o",
            str(simv),
            str(tmp_path / "top.v"),
            str(FAKERAM_MODEL),
            str(tb),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    run_result = subprocess.run(
        [_tool("vvp"), str(simv)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr
    assert f"PASS harness banks={banks}" in run_result.stdout


@pytest.mark.parametrize("banks", [2, 4, 8, 15])
def test_checked_configs_guards_sweeps_and_task_commands(
    tmp_path: Path,
    banks: int,
) -> None:
    design_name = f"attention_score32_exact_shared_root_storage_macro_b{banks}"
    source_dir = REPO_ROOT / "runs/designs/npu_blocks" / design_name
    config = json.loads((source_dir / "config.json").read_text(encoding="utf-8"))
    assert config["report_links"]["proposal_id"] == PROPOSAL_ID

    copied = tmp_path / "runs/designs/npu_blocks" / design_name
    copied.mkdir(parents=True)
    (copied / "config.json").write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )
    generate(config, copied / "verilog")
    assert guard_main(["--design-dir", str(copied)]) == 0

    target = _read_config_target(
        source_dir / "config.json",
        repo_root=REPO_ROOT,
        config_rel=str((source_dir / "config.json").relative_to(REPO_ROOT)),
        out_root="runs/designs/npu_blocks",
        make_target=None,
    )
    assert [command["name"] for command in target.commands] == [
        "generate_attention_score32_exact_shared_root_storage_physical_harness_rtl",
        "check_attention_score32_exact_shared_root_storage_physical_guard",
        "run_block_sweep",
        "extract_attention_score32_exact_shared_root_storage_physical_harness_timing_paths",
    ]
    assert "--macro_manifest" in target.commands[2]["run"]
    assert "/verilog/macro_manifest.json" in target.commands[2]["run"]

    sweep = json.loads(
        (
            REPO_ROOT
            / "runs/campaigns/npu/attention_score32_exact_shared_root_storage_macro_ppa_v1"
            / f"sweeps/nangate45_b{banks}.json"
        ).read_text(encoding="utf-8")
    )["flow_params"]
    assert sweep["CLOCK_PERIOD"] == [4.0, 6.0, 8.0, 10.0, 12.0]
    assert sweep["PLACE_DENSITY"] == [0.4]
    assert sweep["SYNTH_HIERARCHICAL"] == [1]


def test_proposal_requests_all_four_bank_points() -> None:
    request = json.loads(
        (
            REPO_ROOT / f"docs/proposals/{PROPOSAL_ID}/evaluation_requests.json"
        ).read_text(encoding="utf-8")
    )
    assert request["source_commit"] == "TBD"
    assert "source_requirement.required_sha" in request["source_commit_note"]
    assert [
        item["item_id"] for item in request["requested_items"]
    ] == [
        "l1_attention_score32_exact_shared_root_storage_macro_b2_ppa_v1",
        "l1_attention_score32_exact_shared_root_storage_macro_b4_ppa_v1",
        "l1_attention_score32_exact_shared_root_storage_macro_b8_ppa_v1",
        "l1_attention_score32_exact_shared_root_storage_macro_b15_ppa_v1",
    ]
