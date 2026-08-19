from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_design import (  # noqa: E402
    generate_config_mk,
    generate_l1_memory_noc_design,
    generate_wrapper,
    identify_design,
)


CONFIGS = {
    "aligned": REPO_ROOT
    / "runs/designs/noc/l1_attention_score32_exact_matched_aligned_codec_w419_f256_wrapper"
    / "config_l1_attention_score32_exact_matched_aligned_codec_w419_f256.json",
    "stats_once": REPO_ROOT
    / "runs/designs/noc/l1_attention_score32_exact_matched_stats_once_codec_w419_f256_wrapper"
    / "config_l1_attention_score32_exact_matched_stats_once_codec_w419_f256.json",
}


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


@pytest.mark.parametrize(("mode", "mode_value"), [("aligned", 0), ("stats_once", 1)])
def test_exact_matched_codec_generated_hierarchy(
    mode: str, mode_value: int, tmp_path: Path
) -> None:
    config = json.loads(CONFIGS[mode].read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "exact_matched_codec"
    assert design["codec_mode"] == mode

    source_dir = tmp_path / "src"
    source_dir.mkdir()
    generate_l1_memory_noc_design(str(source_dir), design)
    generate_wrapper(config, str(source_dir), design)
    expected_sources = {
        "local_reducer_aggregate_aligned_exact_codec.v",
        "local_reducer_aggregate_stats_once_exact_codec.v",
        "local_reducer_aggregate_exact_codec_matched_ppa_harness.v",
        f"{design['module_name']}.v",
        f"{design['wrapper_name']}.v",
    }
    assert expected_sources == {path.name for path in source_dir.glob("*.v")}
    generated_top = (source_dir / f"{design['module_name']}.v").read_text(
        encoding="utf-8"
    )
    assert f".MODE_STATS_ONCE({mode_value})" in generated_top

    platform_dir = tmp_path / "platform"
    platform_dir.mkdir()
    generate_config_mk(str(platform_dir), "nangate45", design)
    config_mk = (platform_dir / "config.mk").read_text(encoding="utf-8")
    for filename in expected_sources:
        assert f"/{filename}" in config_mk

    sources = [str(path) for path in sorted(source_dir.glob("*.v"))]
    if (iverilog := _tool("iverilog")) is not None:
        subprocess.run(
            [iverilog, "-g2012", "-s", design["wrapper_name"], "-t", "null", *sources],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    if (yosys := _tool("yosys")) is not None:
        subprocess.run(
            [
                yosys,
                "-q",
                "-p",
                "read_verilog -DSYNTHESIS -sv "
                + " ".join(sources)
                + f"; hierarchy -check -top {design['wrapper_name']}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("codec_mode", "lossy", "codec_mode must be aligned or stats_once"),
        ("counter_bits", 7, "requires counter_bits >= 8"),
        ("flit_bits", 128, "requires 256-bit flits"),
    ],
)
def test_exact_matched_codec_rejects_invalid_options(
    field: str, value: object, message: str
) -> None:
    config = json.loads(CONFIGS["aligned"].read_text(encoding="utf-8"))
    config["operations"][0]["options"][field] = value
    with pytest.raises(ValueError, match=message):
        identify_design(config)
