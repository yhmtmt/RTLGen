import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.check_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_guard import main as guard_main


def _design_dir() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_p54x8_p53x8_c16_r2_l8_b59"
    )


def test_checked_in_guard_accepts_generated_full_cluster_sram_hierarchy() -> None:
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


def test_checked_in_guard_reports_expected_manifest_shape() -> None:
    manifest = json.loads(
        (
            _design_dir()
            / "verilog"
            / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["internal_value_memory_lanes"] == 1712
    assert manifest["external_fill_interfaces"] == 16
    assert manifest["service_model"]["per_cluster_internal_value_memory_lanes"] == [108] * 8 + [106] * 8
