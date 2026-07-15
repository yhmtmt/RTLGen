import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_decode_score_multivalue_cluster_equivalence import build_report
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate


def _config(*, scale_lanes: int = 1) -> dict:
    return {
        "top_name": f"attention_decode_score_multivalue_cluster_s{scale_lanes}",
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": scale_lanes,
        },
    }


def test_multivalue_cluster_manifest_closes_full_head_boundary(tmp_path: Path) -> None:
    generate(_config(), tmp_path)
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_cluster_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["semantic_profile"] == "decode_m1x8_shared_score_16x8d_value_iterdiv_v1"
    assert manifest["value_dimensions"] == 128
    assert manifest["score_passes_per_command"] == 1
    assert manifest["score_writes_per_block"] == 1
    assert manifest["score_reads_per_block"] == 1
    assert manifest["value_reads_per_block"] == 16
    assert manifest["result_beats_per_command"] == 16
    assert manifest["divider_cycles_per_command"] == 7680


def test_multivalue_cluster_guard_accepts_generated_design(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    design_dir.mkdir()
    config = _config()
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    generate(config, design_dir / "verilog")
    subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_decode_score_multivalue_cluster_guard.py",
            "--design-dir",
            str(design_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("scale_lanes", [1, 8])
def test_multivalue_cluster_perf_rtl_equivalence(scale_lanes: int) -> None:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog/vvp unavailable")
    report = build_report(_config(scale_lanes=scale_lanes))
    assert report["decision"] == "decode_score_multivalue_cluster_equivalence_pass", json.dumps(
        report, indent=2
    )
    assert report["equivalence_pass"] is True
    assert report["scenario_count"] == 5
    assert any(row["head_dim"] == 128 for row in report["scenarios"])
    for scenario in report["scenarios"]:
        assert scenario["score_read_addresses"] == [0, 1, 2]
        assert scenario["value_read_requests"] == [
            [block, value_slice] for block in range(3) for value_slice in range(16)
        ]
