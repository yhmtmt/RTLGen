import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import generate


def _config_path() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59"
        / "config.json"
    )


def _prepare_design_dir(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / "design"
    design_dir.mkdir()
    config = json.loads(_config_path().read_text(encoding="utf-8"))
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_local16_global_tree_gqa8_guard.py",
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


def test_local16_global_tree_guard_accepts_generated_design(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    result = _run_guard(design_dir)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["clusters"] == 16
    assert payload["total_local_producers"] == 856
    assert payload["divider_lanes"] == 8
    assert payload["finalizer_banks"] == 59
    assert payload["status"] == "ok"


def test_local16_global_tree_guard_rejects_stale_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_local16_global_tree_guard_rejects_missing_direct_leaf_mapping(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            ".leaf_value(leaf_value[263384 +: 17384])",
            ".leaf_value(17384'd0)",
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL missing semantic token: .leaf_value(leaf_value[263384 +: 17384])" in result.stderr


def test_local16_global_tree_guard_rejects_banked_tree_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    manifest_path = design_dir / "verilog" / "attention_score32_exact_local16_global_tree_gqa8_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["banked_tree"]["finalizer_banks"] = 58
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "banked-tree manifest finalizer_banks must be 59" in result.stderr


def test_local16_global_tree_guard_rejects_producer_tokens(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            "  assign protocol_error = (|cluster_protocol_error) || global_protocol_error;\nendmodule",
            "  assign protocol_error = (|cluster_protocol_error) || global_protocol_error;\n"
            "  wire producer_value_read_req_valid = 1'b0;\nendmodule",
            1,
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "functional wrapper top must not contain producer-coupled token: producer_value_read_req" in result.stderr
