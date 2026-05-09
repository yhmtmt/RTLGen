"""Coverage for generated OpenROAD design collateral."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_generate_design_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "generate_design.py"
    spec = importlib.util.spec_from_file_location("rtlgen_generate_design", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_nangate45_generated_config_uses_macro_pin_placement_defaults(tmp_path: Path) -> None:
    generate_design = _load_generate_design_module()
    design = {
        "module_name": "logit_rank_r128_l16_k1",
        "wrapper_name": "logit_rank_r128_l16_k1_wrapper",
        "include_mg_cpa": False,
    }

    generate_design.generate_config_mk(tmp_path, "nangate45", design)

    content = (tmp_path / "config.mk").read_text(encoding="utf-8")
    assert "Register-wrapped Layer-1 blocks are evaluated as macro timing boundaries" in content
    assert "export IO_PLACER_H ?= metal3 metal5" in content
    assert "export IO_PLACER_V ?= metal4 metal6" in content
    assert "export PLACE_PINS_ARGS ?= -min_distance 1" in content
