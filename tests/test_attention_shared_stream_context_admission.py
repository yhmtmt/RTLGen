from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl/attention_shared_stream_context_admission.sv"
TB = REPO_ROOT / "tests/attention_shared_stream_context_admission_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_admission_round_robin_and_metadata(tmp_path: Path) -> None:
    sim = tmp_path / "admission.vvp"
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "attention_shared_stream_context_admission_tb",
         "-o", str(sim), str(RTL), str(TB)],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    run = subprocess.run([_tool("vvp"), str(sim)], cwd=REPO_ROOT, check=True,
                         capture_output=True, text=True, timeout=30)
    assert "PASS admission contexts=112" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_admission_rejects_local_and_duplicate_events(tmp_path: Path) -> None:
    sim = tmp_path / "admission-errors.vvp"
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "attention_shared_stream_context_admission_tb",
         "-o", str(sim), str(RTL), str(TB)],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    run = subprocess.run([_tool("vvp"), str(sim), "+ERROR_CASE"], cwd=REPO_ROOT,
                         check=True, capture_output=True, text=True, timeout=30)
    assert "PASS admission invalid_event_fail_closed" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_admission_duplicate_event_fails_closed(tmp_path: Path) -> None:
    sim = tmp_path / "admission-duplicate.vvp"
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "attention_shared_stream_context_admission_tb",
         "-o", str(sim), str(RTL), str(TB)],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    run = subprocess.run([_tool("vvp"), str(sim), "+DUPLICATE_CASE"], cwd=REPO_ROOT,
                         check=True, capture_output=True, text=True, timeout=30)
    assert "PASS admission duplicate_event_fail_closed" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_admission_zero_expected_contexts_completes_without_transport(tmp_path: Path) -> None:
    sim = tmp_path / "admission-empty.vvp"
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "attention_shared_stream_context_admission_tb",
         "-o", str(sim), str(RTL), str(TB)],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    run = subprocess.run([_tool("vvp"), str(sim), "+EMPTY_CASE"], cwd=REPO_ROOT,
                         check=True, capture_output=True, text=True, timeout=30)
    assert "PASS admission empty_layer" in run.stdout
