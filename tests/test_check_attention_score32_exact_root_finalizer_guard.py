import json
from pathlib import Path
import subprocess
import sys

from npu.rtlgen.gen_attention_score32_exact_root_finalizer import generate

REPO_ROOT = Path(__file__).resolve().parents[1]


def _config_path(lanes: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_root_finalizer_l{lanes}"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path, *, lanes: int) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / f"attention_score32_exact_root_finalizer_l{lanes}"
    design_dir.mkdir()
    config = json.loads(_config_path(lanes).read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def test_exact_root_finalizer_guard_accepts_all_checked_in_lane_configs(tmp_path: Path) -> None:
    for lanes in (1, 2, 4, 8):
        design_dir = _prepare_design_dir(tmp_path / f"case_{lanes}", lanes=lanes)
        result = subprocess.run(
            [
                sys.executable,
                "npu/eval/check_attention_score32_exact_root_finalizer_guard.py",
                "--design-dir",
                str(design_dir),
                "--config",
                str(design_dir / "config.json"),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["divider_lanes"] == lanes
        assert payload["divider_iterations_per_group"] == 57
        assert payload["status"] == "ok"


def test_exact_root_finalizer_guard_rejects_stale_generated_config(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, lanes=4)
    config = json.loads((design_dir / "config.json").read_text(encoding="utf-8"))
    config["attention_score32_exact_root_finalizer"]["divider_lanes"] = 2
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_root_finalizer_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / "config.json"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "generated config does not match source config" in result.stderr


def test_exact_root_finalizer_guard_rejects_combinational_divide(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, lanes=8)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace("endmodule\n", "  wire [31:0] bad_div = 32'd8 / 32'd2;\nendmodule\n"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_root_finalizer_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / "config.json"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "must not contain combinational division operators" in result.stderr
