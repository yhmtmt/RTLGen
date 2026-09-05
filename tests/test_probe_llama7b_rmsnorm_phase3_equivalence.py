import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from npu.eval.probe_llama7b_rmsnorm_phase3_equivalence import build_report


REPO_ROOT = Path(__file__).resolve().parents[1]


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_phase3_equivalence_probe_passes_representative_cases() -> None:
    report = build_report()

    assert report["decision"] == "llama7b_rmsnorm_phase3_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert report["semantic_profile"] == "llama7b_bf16_rmsnorm_phase3_bounded_ready_valid_v1"
    assert report["gates"]["exact_bf16_output_beats"] is True
    assert report["gates"]["exact_protocol_error_row_replay"] is True
    assert report["gates"]["exact_ready_valid_row_schedule"] is True
    assert report["gates"]["exact_row_accounting"] is True
    assert any(row["case_id"] == "gamma_exponent_255" for row in report["rows"])
    assert all(row["equivalence_pass"] for row in report["rows"])
    assert report["remaining_abstractions"] == [
        "row_mem and gamma_mem are internal register arrays, not SRAM-macro evidence",
        "no DRAM or external-memory controller behavior is claimed by this equivalence gate",
        "clock-gating and physical overlap policy remain outside this functional/workload proof",
    ]


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_macro_banked_phase3_equivalence_probe_passes() -> None:
    report = build_report(
        cases=["unity_identity", "framing_error", "row_exponent_255", "gamma_exponent_255"],
        scenarios=["always_ready", "periodic_backpressure"],
        storage_backend="fakeram45_64x32_banked",
    )

    assert report["decision"] == "llama7b_rmsnorm_phase3_equivalence_pass"
    assert report["equivalence_pass"] is True
    assert report["storage_backend"] == "fakeram45_64x32_banked"
    assert report["semantic_profile"] == "llama7b_bf16_rmsnorm_phase3_macro_banked_ready_valid_v1"
    assert all(row["equivalence_pass"] for row in report["rows"])


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_pipelined_macro_banked_phase3_equivalence_probe_passes() -> None:
    report = build_report(storage_backend="fakeram45_64x32_banked_pipelined")

    assert report["decision"] == "llama7b_rmsnorm_phase3_equivalence_pass"
    assert report["semantic_profile"] == (
        "llama7b_bf16_rmsnorm_phase3_macro_banked_pipelined_ready_valid_v1"
    )
    assert report["storage_backend"] == "fakeram45_64x32_banked_pipelined"
    assert all(row["equivalence_pass"] for row in report["rows"])
    always_ready = [row for row in report["rows"] if row["scenario"] == "always_ready"]
    assert {row["last_output_cycle"] for row in always_ready} == {1035}


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_phase3_equivalence_probe_cli_writes_json(tmp_path: Path) -> None:
    out_path = tmp_path / "phase3_equivalence.json"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "npu" / "eval" / "probe_llama7b_rmsnorm_phase3_equivalence.py"),
            "--cases",
            "unity_identity,gamma_exponent_255",
            "--scenarios",
            "always_ready",
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=180,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["equivalence_pass"] is True
    assert [row["case_id"] for row in payload["rows"]] == ["unity_identity", "gamma_exponent_255"]
    assert {row["scenario"] for row in payload["rows"]} == {"always_ready"}
