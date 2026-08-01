import json
from pathlib import Path

import pytest

from npu.eval.check_attention_score32_exact_partial_pair_merge_guard import main as guard_main
from npu.rtlgen.gen_attention_score32_online_state_merge import FACTORED_H33_L64_MUL_EXACT, generate


def _config() -> dict:
    return {
        "top_name": "attention_score32_exact_partial_pair_merge_sharedscale_factored_l1",
        "attention_score32_online_state_merge": {
            "value_slices": 16,
            "head_id_bits": 5,
            "exp_scale_impl": FACTORED_H33_L64_MUL_EXACT,
            "lane_parallelism": 1,
        },
    }


def _sweep() -> dict:
    return {
        "tag_prefix": "attention_score32_exact_partial_pair_merge_sharedscale_v1",
        "flow_params": {
            "CLOCK_PERIOD": [8.0],
            "DIE_AREA": ["0 0 1500 1500"],
            "CORE_AREA": ["50 50 1450 1450"],
            "PLACE_DENSITY": [0.3],
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


def test_pair_merge_guard_rejects_nonshared_parallelism(tmp_path: Path) -> None:
    design_dir = tmp_path / "design"
    rtl_dir = design_dir / "verilog"
    rtl_dir.mkdir(parents=True)
    generate(_config(), rtl_dir)
    bad_config = _config()
    bad_config["attention_score32_online_state_merge"]["lane_parallelism"] = 2
    (design_dir / "config.json").write_text(json.dumps(bad_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (rtl_dir / "config.json").write_text(json.dumps(bad_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="lane_parallelism must be 1"):
        guard_main(["--design-dir", str(design_dir)])
