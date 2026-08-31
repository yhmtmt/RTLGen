from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness import (
    generate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TB = REPO_ROOT / (
    "tests/attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_tb.sv"
)
TOP = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_tb"
DUT_TOP = "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_l1"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


def _generate(tmp_path: Path) -> Path:
    out_dir = tmp_path / "verilog"
    generate(
        {
            "top_name": DUT_TOP,
            "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness": {
                "physical_banks": 15,
                "use_fakeram": 1,
                "hierarchy_area_prefixes": [
                    "composition/vc0_activity/service/",
                    "composition/vc1_activity/exact_transport_wrapper/",
                    "composition/shared_transport/",
                ],
            },
            "report_links": {
                "proposal_id": (
                    "prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"
                ),
                "proposal_path": (
                    "docs/proposals/"
                    "prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1/"
                    "proposal.json"
                ),
            },
        },
        out_dir,
    )
    return out_dir


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_composed_activity_harness_drives_both_vcs(tmp_path: Path) -> None:
    out_dir = _generate(tmp_path)
    simv = tmp_path / "composed_activity.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TOP,
            "-o",
            str(simv),
            str(out_dir / "top.v"),
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert "PASS dual-producer PPA activity" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_composed_activity_harness_has_one_shared_mesh(tmp_path: Path) -> None:
    out_dir = _generate(tmp_path)
    netlist = tmp_path / "composed_activity.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -sv npu/rtl/fakeram45_64x32_blackbox.v; "
            f"read_verilog -DSYNTHESIS -sv {out_dir / 'top.v'}; "
            f"hierarchy -check -top {DUT_TOP}; proc; check; write_json {netlist}",
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    design = json.loads(netlist.read_text(encoding="utf-8"))
    all_cells = [
        cell
        for module in design["modules"].values()
        for cell in module.get("cells", {}).values()
    ]
    assert sum("noc_segmented_mesh4x4" in cell["type"] for cell in all_cells) == 1
    assert sum("noc_endpoint_vc_injection_arbiter" in cell["type"] for cell in all_cells) == 16

    manifest = json.loads(
        (
            out_dir
            / "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["top_pin_bits"] == 163
    assert manifest["blackbox_instance_counts"] == {"fakeram45_64x32": 120}
    assert manifest["shared_transport"]["mesh_count"] == 1
    assert manifest["shared_transport"]["injection_arbiter_count"] == 16
