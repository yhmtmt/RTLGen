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

RTL = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_aligned_exact_codec.sv"
TB = REPO_ROOT / "tests/local_reducer_aggregate_aligned_exact_codec_tb.sv"
PPA_CONFIG = (
    REPO_ROOT
    / "runs/designs/noc/l1_attention_score32_exact_aligned_codec_w419_f256_wrapper"
    / "config_l1_attention_score32_exact_aligned_codec_w419_f256.json"
)


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    return None


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_local_reducer_aggregate_aligned_exact_codec_roundtrip_and_cadence(tmp_path: Path) -> None:
    simv = tmp_path / "local_reducer_aggregate_aligned_exact_codec.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_aligned_exact_codec_tb",
            "-o",
            str(simv),
            str(RTL),
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert (
        "PASS local_reducer_aggregate_aligned_exact_codec"
        in run.stdout
    )
    assert "encoder_flits=24" in run.stdout
    assert "loopback_beats=10" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_local_reducer_aggregate_aligned_exact_codec_yosys_import_process_check() -> None:
    for top in (
        "local_reducer_aggregate_aligned_exact_encoder",
        "local_reducer_aggregate_aligned_exact_decoder",
    ):
        subprocess.run(
            [
                str(_tool("yosys")),
                "-q",
                "-p",
                f"read_verilog -DSYNTHESIS -sv {RTL}; hierarchy -check -top {top}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )


def test_local_reducer_aggregate_aligned_exact_codec_ppa_hierarchy(tmp_path: Path) -> None:
    config = json.loads(PPA_CONFIG.read_text(encoding="utf-8"))
    design = identify_design(config)
    assert design["primitive"] == "exact_aligned_codec"

    source_dir = tmp_path / "src"
    source_dir.mkdir()
    generate_l1_memory_noc_design(str(source_dir), design)
    generate_wrapper(config, str(source_dir), design)
    expected_sources = {
        "local_reducer_aggregate_aligned_exact_codec.v",
        "local_reducer_aggregate_aligned_exact_codec_ppa_harness.v",
        f"{design['module_name']}.v",
        f"{design['wrapper_name']}.v",
    }
    assert expected_sources == {path.name for path in source_dir.glob("*.v")}

    platform_dir = tmp_path / "platform"
    platform_dir.mkdir()
    generate_config_mk(str(platform_dir), "nangate45", design)
    config_mk = (platform_dir / "config.mk").read_text(encoding="utf-8")
    for filename in expected_sources:
        assert f"/{filename}" in config_mk

    iverilog = _tool("iverilog")
    if iverilog is not None:
        subprocess.run(
            [
                iverilog,
                "-g2012",
                "-s",
                design["wrapper_name"],
                "-t",
                "null",
                *[str(path) for path in sorted(source_dir.glob("*.v"))],
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

    yosys = _tool("yosys")
    if yosys is not None:
        subprocess.run(
            [
                yosys,
                "-q",
                "-p",
                "read_verilog -DSYNTHESIS -sv "
                + " ".join(str(path) for path in sorted(source_dir.glob("*.v")))
                + f"; hierarchy -check -top {design['wrapper_name']}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
