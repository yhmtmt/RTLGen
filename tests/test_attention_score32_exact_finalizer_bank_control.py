import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_finalizer_bank_control import build_report
from npu.rtlgen.gen_attention_score32_exact_finalizer_bank_control import generate


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


def _config(finalizer_banks: int, *, divider_lanes: int = 8) -> dict[str, object]:
    return {
        "top_name": f"attention_score32_exact_finalizer_bank_control_l{divider_lanes}_b{finalizer_banks}",
        "attention_score32_exact_finalizer_bank_control": {
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": divider_lanes,
            "finalizer_banks": finalizer_banks,
        },
    }


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalizer_bank_control_manifest_and_verilator_lint(tmp_path: Path) -> None:
    cfg = _config(59)
    generate(cfg, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_finalizer_bank_control_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["finalizer_banks"] == 59
    assert manifest["divider_lanes"] == 8
    assert manifest["order_fifo_depth"] == 59
    assert manifest["control_only_embodied"] is True
    assert manifest["bank_arithmetic_embodied"] is False
    assert manifest["service_model"]["per_bank_accept_interval_cycles"] == 59

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "--top-module",
            str(cfg["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert lint.returncode == 0, lint.stderr


def test_finalizer_bank_control_rejects_invalid_bank_counts(tmp_path: Path) -> None:
    for banks in (0, 65):
        with pytest.raises(SystemExit, match="finalizer_banks must be in \\[1, 64\\]"):
            generate(_config(banks), tmp_path / f"rtl_{banks}")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("finalizer_banks", [1, 4, 8, 16, 32, 59])
def test_finalizer_bank_control_probe_matches_service_model(finalizer_banks: int) -> None:
    report = build_report(clusters=2, heads=2, divider_lanes=8, finalizer_banks=finalizer_banks)
    assert report["passed"] is True
    assert report["outputs"] == 32
    assert report["service_contract"]["finalizer_banks"] == finalizer_banks
    assert report["service_contract"]["per_bank_accept_interval_cycles"] == 59


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_finalizer_bank_control_full_wave_b59_matches_exact_hash() -> None:
    report = build_report(clusters=16, heads=32, divider_lanes=8, finalizer_banks=59)
    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["dispatch_stall_cycles"] == 0
    assert report["expected_root_hash"] == "027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd"

