from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.check_attention_shared_sram_read_group_adapter_ppa_guard import check
from npu.rtlgen.gen_attention_shared_sram_read_group_adapter_ppa_harness import generate


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_guard_accepts_all_four_checked_geometries(tmp_path: Path) -> None:
    for width in (256, 512):
        for slots in (1, 2):
            name = f"attention_shared_sram_read_group_adapter_w{width}_s{slots}"
            design_dir = tmp_path / name
            config = json.loads(
                (REPO_ROOT / "runs/designs/npu_blocks" / name / "config.json").read_text(encoding="utf-8")
            )
            generate(config, design_dir / "verilog")
            (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
            check(design_dir)


def test_guard_rejects_missing_proposal_link(tmp_path: Path) -> None:
    name = "attention_shared_sram_read_group_adapter_w256_s2"
    config = json.loads(
        (REPO_ROOT / "runs/designs/npu_blocks" / name / "config.json").read_text(encoding="utf-8")
    )
    config["report_links"]["proposal_id"] = "wrong"
    design_dir = tmp_path / name
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SystemExit, match="proposal linkage"):
        check(design_dir)
