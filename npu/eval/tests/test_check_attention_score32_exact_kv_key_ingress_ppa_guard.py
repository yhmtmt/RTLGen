from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.check_attention_score32_exact_kv_key_ingress_ppa_guard import check
from npu.rtlgen.gen_attention_score32_exact_kv_key_ingress_ppa_harness import (
    MANIFEST_NAME,
    generate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGNS = (
    "attention_score32_exact_kv_key_ingress_onebuf_p53_g3",
    "attention_score32_exact_kv_key_ingress_pingpong_p54_g2",
)


def _config(design: str) -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "runs/designs/npu_blocks" / design / "config.json").read_text(
            encoding="utf-8"
        )
    )


@pytest.mark.parametrize("design", DESIGNS)
def test_guard_accepts_both_architectures(tmp_path: Path, design: str) -> None:
    config = _config(design)
    design_dir = tmp_path / design
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    check(design_dir)


def test_guard_rejects_missing_proposal_link(tmp_path: Path) -> None:
    design = DESIGNS[0]
    config = _config(design)
    config["report_links"]["proposal_id"] = "wrong"  # type: ignore[index]
    design_dir = tmp_path / design
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SystemExit, match="proposal linkage"):
        check(design_dir)


def test_guard_rejects_false_macro_area_claim(tmp_path: Path) -> None:
    design = DESIGNS[1]
    config = _config(design)
    design_dir = tmp_path / design
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    manifest_path = design_dir / "verilog" / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["full_k_stage_macro_area_included"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SystemExit, match="manifest mismatch"):
        check(design_dir)
