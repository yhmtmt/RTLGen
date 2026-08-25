from __future__ import annotations

import json
import re
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


CASES = (
    (
        "runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/"
        "config_l1_noc_segmented_xy_router_p5_w256_vc4_d4.json",
        {"noc_ready_valid_fifo.v", "noc_segmented_mesh_router.v"},
    ),
    (
        "runs/designs/noc/l1_noc_segmented_xy_mesh4x4_w256_vc4_d4_wrapper/"
        "config_l1_noc_segmented_xy_mesh4x4_w256_vc4_d4.json",
        {
            "noc_ready_valid_fifo.v",
            "noc_segmented_mesh_router.v",
            "noc_segmented_mesh4x4.v",
        },
    ),
    (
        "runs/designs/noc/l1_noc_sram_packet_endpoint_w256_td4_to8_rx8_wrapper/"
        "config_l1_noc_sram_packet_endpoint_w256_td4_to8_rx8.json",
        set(),
    ),
    (
        "runs/designs/noc/l1_noc_sram_packet_mesh4x4_w256_vc4_d4_td4_to8_rx8_wrapper/"
        "config_l1_noc_sram_packet_mesh4x4_w256_vc4_d4_td4_to8_rx8.json",
        {
            "noc_ready_valid_fifo.v",
            "noc_segmented_mesh_router.v",
            "noc_segmented_mesh4x4.v",
            "noc_sram_packet_endpoint.v",
            "noc_sram_packet_mesh4x4.v",
            "noc_sram_packet_mesh4x4_ppa_harness.v",
        },
    ),
)


def _config_verilog_basenames(config_mk: Path) -> list[str]:
    match = re.search(
        r"^export VERILOG_FILES = (?P<files>.+)$",
        config_mk.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    assert match is not None
    return [Path(value).name for value in match.group("files").split()]


@pytest.mark.parametrize(("config_path", "dependencies"), CASES)
def test_generated_orfs_config_contains_complete_noc_hierarchy(
    tmp_path: Path,
    config_path: str,
    dependencies: set[str],
) -> None:
    config = json.loads((REPO_ROOT / config_path).read_text(encoding="utf-8"))
    design = identify_design(config)
    src_dir = tmp_path / "src" / design["wrapper_name"]
    platform_dir = tmp_path / "designs" / "nangate45" / design["wrapper_name"]
    src_dir.mkdir(parents=True)
    platform_dir.mkdir(parents=True)

    generate_l1_memory_noc_design(str(src_dir), design)
    generate_wrapper(config, str(src_dir), design)
    generate_config_mk(str(platform_dir), "nangate45", design)

    expected = {
        f"{design['module_name']}.v",
        f"{design['wrapper_name']}.v",
        *dependencies,
    }
    configured = _config_verilog_basenames(platform_dir / "config.mk")
    assert set(configured) == expected
    assert set(path.name for path in src_dir.glob("*.v")) == expected

    yosys = shutil.which("yosys") or "/oss-cad-suite/bin/yosys"
    if not Path(yosys).exists():
        pytest.skip("yosys unavailable")
    subprocess.run(
        [
            yosys,
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(src_dir / filename) for filename in configured)
            + f"; hierarchy -check -top {design['wrapper_name']}",
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
