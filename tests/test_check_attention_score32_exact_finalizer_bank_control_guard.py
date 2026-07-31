import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_finalizer_bank_control import generate


def _config_path(banks: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_finalizer_bank_control_l8_b{banks}"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path, *, banks: int) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / f"attention_score32_exact_finalizer_bank_control_l8_b{banks}"
    design_dir.mkdir()
    config = json.loads(_config_path(banks).read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path, sweep: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "npu/eval/check_attention_score32_exact_finalizer_bank_control_guard.py",
        "--design-dir",
        str(design_dir),
        "--config",
        str(design_dir / "config.json"),
    ]
    if sweep is not None:
        command.extend(["--sweep", str(sweep)])
    return subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)


def test_finalizer_bank_control_guard_accepts_all_checked_in_configs(tmp_path: Path) -> None:
    for banks in (1, 4, 8, 16, 32, 59):
        design_dir = _prepare_design_dir(tmp_path / f"case_{banks}", banks=banks)
        result = _run_guard(design_dir)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["finalizer_banks"] == banks
        assert payload["status"] == "ok"


def test_finalizer_bank_control_guard_rejects_stale_generated_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=59)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale artifact drift\n", encoding="utf-8")
    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_finalizer_bank_control_guard_rejects_arithmetic_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, banks=32)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    marker = "assign protocol_error = order_protocol_error_q;\n"
    top_path.write_text(
        text.replace(marker, marker + "  localparam integer DIVIDE_ITERATIONS = 57;\n", 1),
        encoding="utf-8",
    )
    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated bank-control RTL must not embed finalizer arithmetic or exp-scale logic" in result.stderr


def test_finalizer_bank_control_guard_accepts_control_sweep_membership(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_finalizer_bank_control_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
    )
    for banks in (1, 4, 8, 16, 32, 59):
        design_dir = _prepare_design_dir(tmp_path / f"ppa_{banks}", banks=banks)
        result = _run_guard(design_dir, sweep=sweep_path)
        assert result.returncode == 0, result.stderr


def test_finalizer_bank_control_guard_rejects_sweep_bank_mismatch(tmp_path: Path) -> None:
    sweep_path = (
        REPO_ROOT
        / "runs"
        / "campaigns"
        / "npu"
        / "attention_score32_exact_finalizer_bank_control_v1"
        / "sweeps"
        / "nangate45_attention_score32_exact_finalizer_bank_control_lane8_firstpass.json"
    )
    design_dir = _prepare_design_dir(tmp_path, banks=32)
    config = json.loads((design_dir / "config.json").read_text(encoding="utf-8"))
    config["attention_score32_exact_finalizer_bank_control"]["finalizer_banks"] = 64
    config["top_name"] = "attention_score32_exact_finalizer_bank_control_l8_b64"
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    result = _run_guard(design_dir, sweep=sweep_path)
    assert result.returncode != 0
    assert "finalizer bank-control sweep membership requires divider_lanes == 8 and finalizer_banks in [1, 4, 8, 16, 32, 59]" in result.stderr
