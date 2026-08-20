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
    "global_tree_composition_tb.sv"
)
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition_tb"
COMPOSITION = "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_composition"


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
@pytest.mark.parametrize(
    ("physical_banks", "use_fakeram", "expected_root_span", "expected_final_cycle"),
    [
        (15, 0, 2505, 2600),
        (4, 0, 2505, 2613),
        (2, 1, 3901, 4120),
        (4, 1, 2939, 3077),
        (8, 1, 2733, 2855),
        (15, 1, 2505, 2620),
    ],
)
def test_full_chain_exact_finite_sram_mesh_and_tree(
    tmp_path: Path,
    physical_banks: int,
    use_fakeram: int,
    expected_root_span: int,
    expected_final_cycle: int,
) -> None:
    tree_dir = _generate_tree(tmp_path)
    simv = tmp_path / "full_chain.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            f"-DSHARED_ROOT_PHYSICAL_BANKS={physical_banks}",
            f"-DSHARED_ROOT_USE_FAKERAM={use_fakeram}",
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
    assert "PASS full_chain" in run.stdout
    assert "rows=128" in run.stdout
    assert "remote_beats=1920" in run.stdout
    assert "flits=2505" in run.stdout
    assert "packets=315" in run.stdout
    assert "descriptors=315" in run.stdout
    assert "completions=315" in run.stdout
    assert "replays=315" in run.stdout
    assert "source_mask=7fff" in run.stdout
    assert f"banks={physical_banks}" in run.stdout
    assert f"use_fakeram={use_fakeram}" in run.stdout
    assert f"root_delivery_span={expected_root_span}" in run.stdout
    assert f"final_cycle={expected_final_cycle}" in run.stdout
    assert "max_aggregate_slots=30" in run.stdout
    assert "slots_per_source=2" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_full_chain_structural_composition_has_one_root_and_fifteen_leaves(
    tmp_path: Path,
) -> None:
    tree_dir = _generate_tree(tmp_path)
    netlist = tmp_path / "full_chain.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + " "
            + str(tree_dir / "top.v")
            + f"; hierarchy -check -top {COMPOSITION}; proc; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    design = json.loads(netlist.read_text())
    cells = design["modules"][COMPOSITION]["cells"].values()
    assert sum("shared_root_rx_adapter" in cell["type"] for cell in cells) == 1
    assert sum("shared_root_leaf_adapter" in cell["type"] for cell in cells) == 1
    assert sum("factored_c16_r2_l8_b59" in cell["type"] for cell in cells) == 1
