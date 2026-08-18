from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_design import (  # noqa: E402
    generate_config_mk,
    generate_l1_memory_noc_design,
    generate_wrapper,
    identify_design,
)

PPA_CONFIG = (
    REPO_ROOT
    / "runs/designs/noc/l1_noc_descriptor_pair_scheduler_n16_wrapper"
    / "config_l1_noc_descriptor_pair_scheduler_n16.json"
)


def test_noc_descriptor_pair_scheduler_protocol() -> None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    assert iverilog is not None
    assert vvp is not None

    with tempfile.TemporaryDirectory() as temporary:
        simulator = Path(temporary) / "scheduler.vvp"
        compile_result = subprocess.run(
            [
                iverilog,
                "-g2012",
                "-s",
                "noc_descriptor_pair_scheduler_tb",
                "-o",
                str(simulator),
                str(REPO_ROOT / "npu/sim/rtl/noc_descriptor_pair_scheduler.sv"),
                str(REPO_ROOT / "tests/noc_descriptor_pair_scheduler_tb.sv"),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr
        simulation = subprocess.run(
            [vvp, str(simulator)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert simulation.returncode == 0, simulation.stderr
        assert "PASS accepted=3 rx=2 tx=2" in simulation.stdout


def test_noc_descriptor_pair_scheduler_generator_emits_exact_hierarchy(
    tmp_path: Path,
) -> None:
    config = json.loads(PPA_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "descriptor_pair_scheduler"

    source_dir = tmp_path / "src"
    source_dir.mkdir()
    generate_l1_memory_noc_design(str(source_dir), design)
    generate_wrapper(config, str(source_dir), design)

    expected_sources = {
        "noc_descriptor_command_prefetch.v",
        "noc_descriptor_pair_scheduler.v",
        "noc_descriptor_pair_scheduler_ppa_harness.v",
        f"{design['module_name']}.v",
        f"{design['wrapper_name']}.v",
    }
    assert expected_sources == {path.name for path in source_dir.glob("*.v")}

    platform_dir = tmp_path / "platform"
    platform_dir.mkdir()
    generate_config_mk(str(platform_dir), "nangate45", design)
    config_mk = (platform_dir / "config.mk").read_text(encoding="utf-8")
    for filename in expected_sources:
        assert f"/{filename}" in config_mk

    iverilog = shutil.which("iverilog")
    if iverilog is None:
        return
    compile_result = subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            design["wrapper_name"],
            "-t",
            "null",
            *[str(path) for path in sorted(source_dir.glob("*.v"))],
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert compile_result.returncode == 0, compile_result.stderr


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("ports", 8, "requires 16 endpoints"),
        ("flit_bits", 32, "requires at least 42 observation bits"),
    ],
)
def test_noc_descriptor_pair_scheduler_rejects_unsupported_physical_shape(
    option: str,
    value: int,
    message: str,
) -> None:
    config = json.loads(PPA_CONFIG.read_text(encoding="utf-8"))
    config["operations"][0]["options"][option] = value
    with pytest.raises(ValueError, match=message):
        identify_design(config)


def test_noc_descriptor_scheduler_prefetch_harness_makes_progress(
    tmp_path: Path,
) -> None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        pytest.skip("iverilog/vvp unavailable")
    testbench = tmp_path / "harness_tb.sv"
    testbench.write_text(
        """
module harness_tb;
  reg clk = 1'b0;
  reg rst_n = 1'b0;
  wire [31:0] accepted;
  wire [31:0] installed;
  wire [31:0] submitted;
  wire [31:0] stalls;
  wire protocol_error;
  wire [255:0] observed;
  always #1 clk = ~clk;
  noc_descriptor_pair_scheduler_ppa_harness dut (
    .clk(clk), .rst_n(rst_n),
    .accepted_command_count(accepted),
    .installed_receive_count(installed),
    .submitted_transmit_count(submitted),
    .endpoint_stall_cycles(stalls),
    .protocol_error(protocol_error),
    .observed_state(observed)
  );
  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1'b1;
    repeat (200) @(negedge clk);
    if (accepted < 16 || installed < 16 || submitted < 16 || protocol_error)
      $fatal(1, "harness did not progress accepted=%0d rx=%0d tx=%0d error=%0d",
        accepted, installed, submitted, protocol_error);
    if (observed == 0)
      $fatal(1, "harness observation state did not change");
    $display("PASS harness accepted=%0d rx=%0d tx=%0d", accepted, installed, submitted);
    $finish;
  end
endmodule
""",
        encoding="ascii",
    )
    simulator = tmp_path / "harness.vvp"
    sources = [
        REPO_ROOT / "npu/sim/rtl/noc_descriptor_command_prefetch.sv",
        REPO_ROOT / "npu/sim/rtl/noc_descriptor_pair_scheduler.sv",
        REPO_ROOT / "npu/sim/rtl/noc_descriptor_pair_scheduler_ppa_harness.sv",
        testbench,
    ]
    compile_result = subprocess.run(
        [
            iverilog,
            "-g2012",
            "-s",
            "harness_tb",
            "-o",
            str(simulator),
            *[str(path) for path in sources],
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    simulation = subprocess.run(
        [vvp, str(simulator)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert simulation.returncode == 0, simulation.stderr
    assert "PASS harness" in simulation.stdout
