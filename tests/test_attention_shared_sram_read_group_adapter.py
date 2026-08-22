from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl/attention_shared_sram_read_group_adapter.sv"
TB = REPO_ROOT / "tests/attention_shared_sram_read_group_adapter_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


def _run(
    tmp_path: Path,
    *,
    beat_w: int = 256,
    group_slots: int = 2,
    test_groups: int = 4,
    plusargs: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    sim = tmp_path / f"adapter-{beat_w}-{group_slots}.vvp"
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "attention_shared_sram_read_group_adapter_tb",
            f"-Pattention_shared_sram_read_group_adapter_tb.BEAT_W={beat_w}",
            f"-Pattention_shared_sram_read_group_adapter_tb.GROUP_SLOTS={group_slots}",
            f"-Pattention_shared_sram_read_group_adapter_tb.TEST_GROUPS={test_groups}",
            "-o",
            str(sim),
            str(RTL),
            str(TB),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return subprocess.run(
        [_tool("vvp"), str(sim), *plusargs],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


pytestmark = pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)


def test_default_256b_depth2_streams_one_response_per_cycle(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=256, group_slots=2, test_groups=2, plusargs=("+STEADY",))
    assert "PASS adapter BEAT_W=256 GROUP_SLOTS=2 requests=8 macro_reads=2 responses=8" in run.stdout
    assert "steady_interval=1" in run.stdout
    assert "request_stalls=" in run.stdout


def test_locality_aware_512b_depth2_streams_one_response_per_cycle(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=512, group_slots=2, test_groups=2, plusargs=("+STEADY",))
    assert "PASS adapter BEAT_W=512 GROUP_SLOTS=2 requests=4 macro_reads=2 responses=4" in run.stdout
    assert "steady_interval=1" in run.stdout


def test_depth1_serial_comparison_preserves_exact_access_ratio(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=256, group_slots=1, plusargs=("+STEADY",))
    assert "PASS adapter BEAT_W=256 GROUP_SLOTS=1 requests=16 macro_reads=4 responses=16" in run.stdout


def test_depth1_512b_comparison_preserves_exact_access_ratio(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=512, group_slots=1)
    assert "PASS adapter BEAT_W=512 GROUP_SLOTS=1 requests=8 macro_reads=4 responses=8" in run.stdout


def test_nonsequential_request_fails_closed(tmp_path: Path) -> None:
    run = _run(tmp_path, plusargs=("+MALFORMED",))
    assert "PASS adapter malformed_sequence BEAT_W=256" in run.stdout


def test_macro_response_without_request_fails_closed(tmp_path: Path) -> None:
    run = _run(tmp_path, plusargs=("+ORPHAN",))
    assert "PASS adapter orphan_response BEAT_W=256" in run.stdout


def test_invalid_macro_metadata_fails_closed(tmp_path: Path) -> None:
    run = _run(tmp_path, plusargs=("+INVALID_META",))
    assert "PASS adapter invalid_metadata BEAT_W=256" in run.stdout


def test_depth2_multiple_consecutive_groups_and_backpressure(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=512, group_slots=2, test_groups=4)
    assert "PASS adapter BEAT_W=512 GROUP_SLOTS=2 requests=8 macro_reads=4 responses=8" in run.stdout
    assert "request_stalls=" in run.stdout
    assert "response_stalls=" in run.stdout


def test_256b_multiple_consecutive_groups_and_backpressure(tmp_path: Path) -> None:
    run = _run(tmp_path, beat_w=256, group_slots=2, test_groups=4)
    assert "PASS adapter BEAT_W=256 GROUP_SLOTS=2 requests=16 macro_reads=4 responses=16" in run.stdout
    assert "request_stalls=" in run.stdout
    assert "response_stalls=" in run.stdout
