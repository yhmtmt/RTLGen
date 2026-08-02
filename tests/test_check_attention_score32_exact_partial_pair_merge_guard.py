import json
from pathlib import Path

import pytest

from npu.eval.check_attention_score32_exact_partial_pair_merge_guard import main as guard_main
from npu.rtlgen.gen_attention_score32_exact_partial_pair_merge_folded import (
    FACTORED_H33_L64_MUL_EXACT,
    GENERIC_SCALE_DIVIDER_EXACT,
    MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT,
    generate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKED_IN_DESIGN_DIR = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_partial_pair_merge_sharedscale_factored_l1"
)
CHECKED_IN_SWEEP = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_exact_partial_pair_merge_sharedscale_v1"
    / "sweeps"
    / "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_l1.json"
)
CHECKED_IN_MERSENNE_DESIGN_DIR = (
    REPO_ROOT
    / "runs"
    / "designs"
    / "npu_blocks"
    / "attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1"
)
CHECKED_IN_MERSENNE_SWEEP = (
    REPO_ROOT
    / "runs"
    / "campaigns"
    / "npu"
    / "attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1"
    / "sweeps"
    / "nangate45_attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1.json"
)


def _config(
    *,
    top_name: str = "attention_score32_exact_partial_pair_merge_sharedscale_factored_l1",
    scale_divider_impl: str = GENERIC_SCALE_DIVIDER_EXACT,
) -> dict:
    return {
        "top_name": top_name,
        "attention_score32_exact_partial_pair_merge_folded": {
            "value_slices": 16,
            "head_id_bits": 5,
            "exp_scale_impl": FACTORED_H33_L64_MUL_EXACT,
            "scale_divider_impl": scale_divider_impl,
            "lane_parallelism": 1,
        },
    }


def _sweep(*, tag_prefix: str = "attention_score32_exact_partial_pair_merge_sharedscale_v1") -> dict:
    return {
        "tag_prefix": tag_prefix,
        "flow_params": {
            "CLOCK_PERIOD": [8.0],
            "DIE_AREA": ["0 0 1500 1500"],
            "CORE_AREA": ["50 50 1450 1450"],
            "IO_PLACER_H": ["metal3 metal5"],
            "IO_PLACER_V": ["metal4 metal6"],
            "PLACE_DENSITY": [0.3],
            "PLACE_PINS_ARGS": ["-min_distance 1"],
            "SYNTH_HIERARCHICAL": [1],
        },
    }


def test_pair_merge_guard_accepts_generated_sharedscale_design(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    rtl_dir = design_dir / "verilog"
    rtl_dir.mkdir(parents=True)
    generate(_config(), rtl_dir)
    (design_dir / "config.json").write_text(json.dumps(_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sweep_path = tmp_path / "sweep.json"
    sweep_path.write_text(json.dumps(_sweep(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    assert guard_main(["--design-dir", str(design_dir), "--sweep", str(sweep_path)]) == 0


def test_pair_merge_guard_accepts_checked_in_config_and_sweep_packaging(tmp_path: Path) -> None:
    checked_in_config = CHECKED_IN_DESIGN_DIR / "config.json"
    config = json.loads(checked_in_config.read_text(encoding="utf-8"))
    design_dir = tmp_path / CHECKED_IN_DESIGN_DIR.name
    generate(config, design_dir / "verilog")

    assert (
        guard_main(
            [
                "--design-dir",
                str(design_dir),
                "--config",
                str(checked_in_config),
                "--sweep",
                str(CHECKED_IN_SWEEP),
            ]
        )
        == 0
    )


def test_pair_merge_guard_accepts_checked_in_mersenne_config_and_sweep_packaging(tmp_path: Path) -> None:
    checked_in_config = CHECKED_IN_MERSENNE_DESIGN_DIR / "config.json"
    config = json.loads(checked_in_config.read_text(encoding="utf-8"))
    design_dir = tmp_path / CHECKED_IN_MERSENNE_DESIGN_DIR.name
    generate(config, design_dir / "verilog")

    assert (
        guard_main(
            [
                "--design-dir",
                str(design_dir),
                "--config",
                str(checked_in_config),
                "--sweep",
                str(CHECKED_IN_MERSENNE_SWEEP),
            ]
        )
        == 0
    )


def test_pair_merge_guard_rejects_nonshared_parallelism(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    rtl_dir = design_dir / "verilog"
    rtl_dir.mkdir(parents=True)
    generate(_config(), rtl_dir)
    bad_config = _config()
    bad_config["attention_score32_exact_partial_pair_merge_folded"]["lane_parallelism"] = 2
    (design_dir / "config.json").write_text(json.dumps(bad_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (rtl_dir / "config.json").write_text(json.dumps(bad_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="lane_parallelism must be 1"):
        guard_main(["--design-dir", str(design_dir)])


def test_pair_merge_guard_rejects_second_signed_scale_invocation(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    rtl_dir = design_dir / "verilog"
    rtl_dir.mkdir(parents=True)
    generate(_config(), rtl_dir)
    (design_dir / "config.json").write_text(json.dumps(_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    top_path = rtl_dir / "top.v"
    rtl = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        rtl.replace(
            "lane_merged_r = sat_add_signed41(active_scaled_left_lane_q, shared_signed_scaled_w);",
            "lane_merged_r = sat_add_signed41(active_scaled_left_lane_q, shared_signed_scaled_w);\n"
            "    lane_merged_r = scale_signed41(shared_signed_value_r, shared_signed_scale_r);",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="exactly one scale_signed41 invocation; found 2"):
        guard_main(["--design-dir", str(design_dir)])


def test_pair_merge_guard_rejects_generic_division_inside_mersenne_variant(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    rtl_dir = design_dir / "verilog"
    rtl_dir.mkdir(parents=True)
    config = _config(
        top_name="attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1",
        scale_divider_impl=MERSENNE24_CORRECTION2_SCALE_DIVIDER_EXACT,
    )
    generate(config, rtl_dir)
    (design_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    top_path = rtl_dir / "top.v"
    rtl = top_path.read_text(encoding="utf-8")
    top_path.write_text(
        rtl.replace(
            "quotient = divide_mersenne24_u57(product);",
            "quotient = product / 57'd16777215;",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="must not contain generic division token"):
        guard_main(["--design-dir", str(design_dir)])
