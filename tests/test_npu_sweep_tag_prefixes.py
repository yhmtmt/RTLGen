from __future__ import annotations

import json
from pathlib import Path


def test_npu_sweep_tag_prefixes_match_declared_tags() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sweep_paths = sorted((repo_root / "runs" / "campaigns" / "npu").glob("**/sweeps/*.json"))
    assert sweep_paths

    mismatches: list[str] = []
    for sweep_path in sweep_paths:
        sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
        tag_prefix = str(sweep.get("tag_prefix", "")).strip()
        tags = sweep.get("flow_params", {}).get("TAG", [])
        if not tag_prefix or not isinstance(tags, list) or not tags:
            continue
        if not any(str(tag).startswith(tag_prefix) for tag in tags):
            mismatches.append(f"{sweep_path.relative_to(repo_root)}: {tag_prefix!r} not in {tags!r}")

    assert mismatches == []
