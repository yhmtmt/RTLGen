import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.check_attention_score32_exact_local16_global_tree_gqa8_guard import _module, main as guard_main


def _design_dir() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59"
    )


def _rtl_dir() -> Path:
    return _design_dir() / "verilog"


def test_checked_in_guard_accepts_generated_full_hierarchy() -> None:
    assert (
        guard_main(
            [
                "--design-dir",
                str(_design_dir()),
                "--config",
                str(_design_dir() / "config.json"),
            ]
        )
        == 0
    )


def test_checked_in_full_hierarchy_dimensions_are_concrete() -> None:
    rtl_dir = _rtl_dir()
    manifest = json.loads(
        (rtl_dir / "attention_score32_exact_local16_global_tree_gqa8_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    top_name = str(manifest["top_name"])
    top = _module(rtl, top_name)

    assert manifest["semantic_profile"] == "score32_exact_local16_global_tree_gqa8_full_compute_v1"
    assert manifest["total_local_producers"] == 856
    assert manifest["total_value_memory_lanes"] == 1712
    assert manifest["submodule_manifests"]["cluster_instance_counts"] == {"p53": 8, "p54": 8}
    assert "input  wire [855:0] input_valid" in top
    assert "output wire [1711:0] value_read_req_valid" in top
    assert "input  wire [876543:0] value_response_matrix" in top
    assert "input  wire [12839:0] command_block_count" not in top
    assert "(* blackbox *)" not in rtl


def test_checked_in_hierarchy_has_unique_shared_modules() -> None:
    rtl_dir = _rtl_dir()
    manifest = json.loads(
        (rtl_dir / "attention_score32_exact_local16_global_tree_gqa8_manifest.json").read_text(encoding="utf-8")
    )
    rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
    top_name = str(manifest["top_name"])
    for suffix in ("__producer", "__cluster_p54", "__cluster_p53", "__global_tree"):
        _module(rtl, f"{top_name}{suffix}")
