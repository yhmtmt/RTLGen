import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_partial_producer_tree import generate


def _config_path(name: str = "config.json") -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_partial_producer_tree_c2_r2_l8_b59"
        / name
    )


def _prepare_design_dir(tmp_path: Path, *, config_name: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    design_dir = tmp_path / config_name.replace(".json", "")
    design_dir.mkdir()
    config = json.loads(_config_path(config_name).read_text(encoding="utf-8"))
    (design_dir / config_name).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path, *, config_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_partial_producer_tree_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / config_name),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_exact_partial_producer_tree_guard_accepts_checked_in_configs(tmp_path: Path) -> None:
    for config_name, expected_heads in (("config.json", 4), ("config_heads32_native.json", 32)):
        design_dir = _prepare_design_dir(tmp_path / config_name.replace(".json", ""), config_name=config_name)
        result = _run_guard(design_dir, config_name=config_name)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["producers"] == 2
        assert payload["clusters"] == 2
        assert payload["divider_lanes"] == 8
        assert payload["finalizer_banks"] == 59
        assert payload["status"] == "ok"


def test_exact_partial_producer_tree_guard_rejects_stale_top(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "generated RTL artifacts do not match current generator output: top.v" in result.stderr


def test_exact_partial_producer_tree_guard_rejects_manifest_result_mode_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_producer_tree_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["producer"]["result_mode"] = "normalized"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "producer submodule manifest result_mode must be exact_partial" in result.stderr


def test_exact_partial_producer_tree_guard_rejects_missing_direct_leaf_wiring(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    text = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        text.replace(
            "assign tree_leaf_value_w[PARTIAL_PAYLOAD_BITS +: PARTIAL_PAYLOAD_BITS] = producer1_result_value_w;",
            "assign tree_leaf_value_w[PARTIAL_PAYLOAD_BITS +: PARTIAL_PAYLOAD_BITS] = 328'd0;",
        ),
        encoding="utf-8",
    )

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert (
        "generated RTL missing semantic token: assign tree_leaf_value_w[PARTIAL_PAYLOAD_BITS +: PARTIAL_PAYLOAD_BITS] = producer1_result_value_w;"
        in result.stderr
    )


def test_exact_partial_producer_tree_guard_rejects_b59_timing_drift(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    manifest_path = design_dir / "verilog" / "attention_score32_exact_partial_producer_tree_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["submodule_manifests"]["banked_tree"]["actual_finalizer_accept_interval_cycles"] = 58
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "banked-tree submodule manifest actual_finalizer_accept_interval_cycles must be 59" in result.stderr


def test_exact_partial_producer_tree_guard_rejects_equivalence_hash_token(tmp_path: Path) -> None:
    design_dir = _prepare_design_dir(tmp_path, config_name="config.json")
    top_path = design_dir / "verilog" / "top.v"
    top_path.write_text(top_path.read_text(encoding="utf-8") + "\nwire equivalence_hash = 1'b0;\n", encoding="utf-8")

    result = _run_guard(design_dir, config_name="config.json")
    assert result.returncode != 0
    assert "functional datapath must not contain equivalence_hash tokens" in result.stderr
