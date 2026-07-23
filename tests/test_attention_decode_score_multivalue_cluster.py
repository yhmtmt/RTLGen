import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from npu.eval.probe_attention_decode_score_multivalue_cluster_equivalence import build_report
from npu.rtlgen.gen_attention_decode_score_multivalue_cluster import generate
from npu.rtlgen.gen_attention_two_pass_multivalue_stream import (
    generate as generate_multivalue_reducer,
)


def _config(*, scale_lanes: int = 1, fsm_encoding: str | None = None) -> dict:
    config = {
        "top_name": f"attention_decode_score_multivalue_cluster_s{scale_lanes}",
        "attention_decode_score_multivalue_cluster": {
            "max_blocks": 16,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": scale_lanes,
        },
    }
    if fsm_encoding is not None:
        config["attention_decode_score_multivalue_cluster"]["fsm_encoding"] = fsm_encoding
    return config


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
    assert manifest["fsm_encoding"] == "default"
    assert manifest["controller_state_width"] == 3
    assert manifest["submodule_manifests"]["multivalue_reducer"]["fsm_encoding"] == "default"
    assert manifest["submodule_manifests"]["multivalue_reducer"]["state_width"] == 4


def test_multivalue_cluster_default_fsm_encoding_preserves_rtl_and_has_no_attribute(
    tmp_path: Path,
) -> None:
    implicit_dir = tmp_path / "implicit"
    explicit_dir = tmp_path / "explicit"
    generate(_config(), implicit_dir)
    generate(_config(fsm_encoding="default"), explicit_dir)

    implicit_rtl = (implicit_dir / "top.v").read_bytes()
    explicit_rtl = (explicit_dir / "top.v").read_bytes()
    assert implicit_rtl == explicit_rtl
    assert b"fsm_encoding" not in implicit_rtl


def test_multivalue_cluster_targeted_binary_attributes_and_manifests(tmp_path: Path) -> None:
    generate(_config(fsm_encoding="binary"), tmp_path)

    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_cluster_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert '(* fsm_encoding = "binary" *) reg [2:0] state_q;' in rtl
    assert '(* fsm_encoding = "binary" *) reg [3:0] state;' in rtl
    assert rtl.count('(* fsm_encoding = "binary" *)') == 2
    assert manifest["fsm_encoding"] == "binary"
    assert manifest["submodule_manifests"]["multivalue_reducer"]["fsm_encoding"] == "binary"


def test_multivalue_cluster_explicit_onehot_attributes_and_manifests(tmp_path: Path) -> None:
    generate(_config(fsm_encoding="explicit_onehot"), tmp_path)

    rtl = (tmp_path / "top.v").read_text(encoding="utf-8")
    manifest = json.loads(
        (tmp_path / "attention_decode_score_multivalue_cluster_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert '(* fsm_encoding = "none", fsm_extract = "no" *) reg [6:0] state_q;' in rtl
    assert '(* fsm_encoding = "none", fsm_extract = "no" *) reg [10:0] state;' in rtl
    assert manifest["fsm_encoding"] == "explicit_onehot"
    assert manifest["controller_state_width"] == 7
    assert manifest["submodule_manifests"]["multivalue_reducer"]["fsm_encoding"] == "explicit_onehot"
    assert manifest["submodule_manifests"]["multivalue_reducer"]["state_width"] == 11


@pytest.mark.parametrize(
    ("generator", "config"),
    [
        ("cluster", _config(fsm_encoding="onehot")),
        (
            "reducer",
            {
                "top_name": "reducer",
                "attention_two_pass_multivalue_stream": {
                    "max_blocks": 16,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "fsm_encoding": "onehot",
                },
            },
        ),
    ],
)
def test_multivalue_generators_reject_invalid_fsm_encoding(
    tmp_path: Path, generator: str, config: dict
) -> None:
    generate_fn = generate if generator == "cluster" else generate_multivalue_reducer
    with pytest.raises(
        SystemExit, match="fsm_encoding must be default, binary, or explicit_onehot"
    ):
        generate_fn(config, tmp_path)


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


def test_multivalue_cluster_targeted_binary_matches_default_functional_hashes() -> None:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog/vvp unavailable")

    default_report = build_report(_config())
    targeted_report = build_report(_config(fsm_encoding="binary"))

    assert default_report["equivalence_pass"] is True
    assert targeted_report["equivalence_pass"] is True
    assert targeted_report["score_tensor_hash"] == default_report["score_tensor_hash"]
    assert targeted_report["final_tensor_hash"] == default_report["final_tensor_hash"]


def test_multivalue_cluster_explicit_onehot_matches_default_functional_hashes() -> None:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog/vvp unavailable")

    default_report = build_report(_config())
    onehot_report = build_report(_config(fsm_encoding="explicit_onehot"))

    assert default_report["equivalence_pass"] is True
    assert onehot_report["equivalence_pass"] is True
    assert onehot_report["score_tensor_hash"] == default_report["score_tensor_hash"]
    assert onehot_report["final_tensor_hash"] == default_report["final_tensor_hash"]
