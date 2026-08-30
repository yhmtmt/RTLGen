from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / (
    "tests/local_reducer_aggregate_stats_once_exact_shared_root_"
    "transport_wrapper_tb.sv"
)
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper_tb"
WRAPPER = "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


RTL_SOURCES = [
    RTL / "noc_ready_valid_fifo.sv",
    RTL / "noc_segmented_mesh_router.sv",
    RTL / "noc_segmented_mesh4x4.sv",
    RTL / "noc_sram_packet_endpoint.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_packet_bridge.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_group_admission.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_transport_wrapper.sv",
]
FAKERAM_MODEL = RTL / "fakeram45_64x32_model.sv"


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
@pytest.mark.parametrize("external_mesh", [False, True])
def test_exact_transport_wrapper_four_groups(
    tmp_path: Path, external_mesh: bool
) -> None:
    tree_dir = _generate_tree(tmp_path)
    simv = tmp_path / "exact_transport_wrapper.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TOP,
            "-P",
            f"{TOP}.EXTERNAL_MESH={int(external_mesh)}",
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
        timeout=180,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert "PASS exact_transport_wrapper" in run.stdout
    assert "groups=4" in run.stdout
    assert "rows=512" in run.stdout
    assert "packets_per_group=315" in run.stdout
    assert "flits_per_group=2505" in run.stdout
    assert "txdesc=1260" in run.stdout
    assert "root_flits=10020" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
@pytest.mark.parametrize(("internal_mesh", "expected_meshes"), [(1, 1), (0, 0)])
def test_exact_transport_wrapper_structural_composition(
    tmp_path: Path, internal_mesh: int, expected_meshes: int
) -> None:
    tree_dir = _generate_tree(tmp_path)
    netlist = tmp_path / "exact_transport_wrapper.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + " "
            + str(tree_dir / "top.v")
            + f"; chparam -set INTERNAL_MESH {internal_mesh} {WRAPPER}"
            + f"; hierarchy -check -top {WRAPPER}; proc; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    design = json.loads(netlist.read_text())
    cells = list(design["modules"][WRAPPER]["cells"].values())
    assert sum("exact_encoder" in cell["type"] for cell in cells) == 15
    assert sum("exact_sram_packet_adapter" in cell["type"] for cell in cells) == 15
    assert (
        sum("noc_segmented_mesh4x4" in cell["type"] for cell in cells)
        == expected_meshes
    )
    assert sum("shared_root_global_tree_composition" in cell["type"] for cell in cells) == 1
    assert sum("shared_root_group_admission" in cell["type"] for cell in cells) == 1
