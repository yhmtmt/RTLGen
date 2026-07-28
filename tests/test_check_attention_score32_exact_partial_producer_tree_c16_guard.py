import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree_c16 import generate


def _config_path() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_producer_tree_c16_r2_l8_b59"
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
            "npu/eval/check_attention_score32_exact_partial_producer_tree_c16_guard.py",
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


def test_exact_partial_producer_tree_c16_guard_accepts_checked_in_config(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    result = _run_guard(design_dir)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["producers"] == 16
    assert payload["clusters"] == 16
    assert payload["divider_lanes"] == 8
    assert payload["finalizer_banks"] == 59
    assert payload["status"] == "ok"


def test_exact_partial_producer_tree_c16_guard_rejects_stale_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_exact_partial_producer_tree_c16_guard_rejects_missing_direct_leaf_wiring(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            "assign tree_leaf_value_w[4920 +: PARTIAL_PAYLOAD_BITS] = producer_result_value_w[4920 +: PARTIAL_PAYLOAD_BITS];",
            "assign tree_leaf_value_w[4920 +: PARTIAL_PAYLOAD_BITS] = 328'd0;",
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert (
        "generated RTL missing semantic token: assign tree_leaf_value_w[4920 +: PARTIAL_PAYLOAD_BITS] = producer_result_value_w[4920 +: PARTIAL_PAYLOAD_BITS];"
        in result.stderr
    )


def test_exact_partial_producer_tree_c16_guard_rejects_banked_tree_cluster_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_producer_tree_c16_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["banked_tree"]["clusters"] = 8
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "banked-tree submodule manifest clusters must be 16" in result.stderr


def test_exact_partial_producer_tree_c16_guard_rejects_equivalence_hash_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path)
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\nwire equivalence_hash = 1'b0;\n", encoding="utf-8")

    result = _run_guard(design_dir)
    assert result.returncode != 0
    assert "functional datapath must not contain equivalence_hash tokens" in result.stderr
