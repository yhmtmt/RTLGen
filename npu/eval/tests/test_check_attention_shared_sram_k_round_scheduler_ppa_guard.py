from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.check_attention_shared_sram_k_round_scheduler_ppa_guard import check
from npu.rtlgen.gen_attention_shared_sram_k_round_scheduler_ppa_harness import generate


REPO_ROOT = Path(__file__).resolve().parents[3]
TOP_NAME = "attention_shared_sram_k_round_scheduler_b17_w17"


def _config() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "runs/designs/npu_blocks" / TOP_NAME / "config.json").read_text(encoding="utf-8")
    )


def test_guard_accepts_checked_round_geometry(tmp_path: Path) -> None:
    config = _config()
    design_dir = tmp_path / TOP_NAME
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    check(design_dir)


def test_guard_rejects_missing_proposal_link(tmp_path: Path) -> None:
    config = _config()
    config["report_links"]["proposal_id"] = "wrong"  # type: ignore[index]
    design_dir = tmp_path / TOP_NAME
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(SystemExit, match="proposal linkage"):
        check(design_dir)


def test_guard_rejects_manifest_that_claims_checksum_equivalence(tmp_path: Path) -> None:
    config = _config()
    design_dir = tmp_path / TOP_NAME
    generate(config, design_dir / "verilog")
    (design_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    manifest_path = (
        design_dir / "verilog" / "attention_shared_sram_k_round_scheduler_ppa_harness_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["activity_checksum_is_equivalence_proof"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SystemExit, match="manifest mismatch"):
        check(design_dir)
