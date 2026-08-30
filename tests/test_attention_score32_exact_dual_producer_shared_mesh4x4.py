from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/attention_score32_exact_dual_producer_shared_mesh4x4_tb.sv"
TOP = "attention_score32_exact_dual_producer_shared_mesh4x4_tb"
COMPOSED_TOP = "attention_score32_exact_dual_producer_shared_mesh4x4"

RTL_SOURCES = [
    RTL / "noc_ready_valid_fifo.sv",
    RTL / "noc_segmented_mesh_router.sv",
    RTL / "noc_segmented_mesh4x4.sv",
    RTL / "noc_endpoint_vc_injection_arbiter.sv",
    RTL / "noc_shared_vc_dual_producer_transport4x4.sv",
    RTL / "noc_sram_packet_endpoint.sv",
    RTL / "noc_sram_packet_endpoint_array16.sv",
    RTL / "attention_shared_stream_context_admission.sv",
    RTL / "attention_shared_stream_context_engine.sv",
    RTL / "attention_shared_stream_context_service.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_packet_bridge.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_group_admission.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper.sv",
    RTL / "attention_score32_exact_dual_producer_shared_mesh4x4.sv",
]
FAKERAM_MODEL = RTL / "fakeram45_64x32_model.sv"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


def _generate_tree(tmp_path: Path) -> Path:
    config = {
        "top_name": "attention_score32_exact_banked_finalized_tree_factored_c16_r2_l8_b59",
        "attention_score32_exact_banked_finalized_tree": {
            "clusters": 16,
            "radix": 2,
            "value_slices": 16,
            "head_id_bits": 5,
            "divider_lanes": 8,
            "finalizer_banks": 59,
            "exp_scale_impl": "factored_h33_l64_mul_exact",
        },
    }
    tree_dir = tmp_path / "generated_tree"
    generate(config, tree_dir)
    return tree_dir


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_exact_dual_producer_shared_mesh_simultaneous_integration(tmp_path: Path) -> None:
    tree_dir = _generate_tree(tmp_path)
    simv = tmp_path / "attention_score32_exact_dual_producer_shared_mesh4x4.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TOP,
            "-o",
            str(simv),
            str(tree_dir / "top.v"),
            *[str(path) for path in RTL_SOURCES],
            str(FAKERAM_MODEL),
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=240,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=360,
    )
    assert "PASS exact_dual_producer_shared_mesh" in run.stdout
    assert "vc0_words=64" in run.stdout
    assert "vc0_contexts=4" in run.stdout
    assert "vc1_rows=128" in run.stdout
    assert "vc1_packets=315" in run.stdout
    assert "vc1_flits=2505" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_exact_dual_producer_shared_mesh_structure(tmp_path: Path) -> None:
    tree_dir = _generate_tree(tmp_path)
    netlist = tmp_path / "attention_score32_exact_dual_producer_shared_mesh4x4.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + " "
            + str(tree_dir / "top.v")
            + " "
            + str(FAKERAM_MODEL)
            + f"; hierarchy -check -top {COMPOSED_TOP}; proc; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=360,
    )
    design = json.loads(netlist.read_text(encoding="utf-8"))
    top_cells = list(design["modules"][COMPOSED_TOP]["cells"].values())
    all_cells = [
        cell
        for module in design["modules"].values()
        for cell in module.get("cells", {}).values()
    ]

    assert sum("attention_shared_stream_context_service" in cell["type"] for cell in top_cells) == 1
    assert (
        sum(
            "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper"
            in cell["type"]
            for cell in top_cells
        )
        == 1
    )
    assert sum("noc_shared_vc_dual_producer_transport4x4" in cell["type"] for cell in top_cells) == 1
    assert sum("noc_segmented_mesh4x4" in cell["type"] for cell in all_cells) == 1
    assert sum("noc_endpoint_vc_injection_arbiter" in cell["type"] for cell in all_cells) == 16
