from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (
    DEFAULT_MEASURED_L1_COSTS,
    DEFAULT_SOURCE_JSON,
    build_report,
)
from npu.eval.verify_llm_decoder_attention_score32_noc_phase2_endpoint_rtl import (
    _schedule_args,
    command_words_from_packets,
    descriptors_from_packet_specs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tool(name: str) -> str:
    candidate = shutil.which(name)
    if candidate:
        return candidate
    bundled = Path("/oss-cad-suite/bin") / name
    if bundled.exists():
        return str(bundled)
    raise RuntimeError(f"{name} unavailable")


@pytest.mark.skipif(
    not (shutil.which("iverilog") or Path("/oss-cad-suite/bin/iverilog").exists())
    or not (shutil.which("vvp") or Path("/oss-cad-suite/bin/vvp").exists()),
    reason="iverilog/vvp unavailable",
)
def test_generator_matches_all_authoritative_commands_under_backpressure(
    tmp_path: Path,
) -> None:
    args = argparse.Namespace(
        repo_root=REPO_ROOT,
        source_json=DEFAULT_SOURCE_JSON,
        measured_l1_costs=DEFAULT_MEASURED_L1_COSTS,
        wave_limit=None,
        noc_clock_ns=1.0,
        schedule_max_cycles=1_000_000,
    )
    packet_specs = []
    build_report(_schedule_args(args), packet_spec_output=packet_specs)
    packets = descriptors_from_packet_specs(packet_specs)
    words = command_words_from_packets(packets)
    assert len(words) == 11576

    expected_mem = tmp_path / "expected_commands.mem"
    expected_mem.write_text(
        "".join(f"{word:026x}\n" for word in words), encoding="ascii"
    )
    simulator = tmp_path / "command_generator.vvp"
    compile_result = subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "noc_llama7b_phase2_command_generator_tb",
            "-o",
            str(simulator),
            str(
                REPO_ROOT
                / "npu/sim/rtl/noc_llama7b_phase2_command_generator.sv"
            ),
            str(REPO_ROOT / "tests/noc_llama7b_phase2_command_generator_tb.sv"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    run_result = subprocess.run(
        [
            _tool("vvp"),
            str(simulator),
            f"+EXPECTED_COMMAND_MEM={expected_mem}",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr
    assert "PASS commands=11576" in run_result.stdout
