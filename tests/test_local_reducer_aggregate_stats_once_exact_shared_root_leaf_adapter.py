from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter_tb.sv"
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter_tb"
BRIDGE_TOP = "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter"
GLOBAL_TREE_TB = (
    REPO_ROOT
    / "tests/local_reducer_aggregate_stats_once_exact_shared_root_global_tree_tb.sv"
)


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


RTL_SOURCES = [
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter.sv",
]


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_shared_root_leaf_adapter_mapping_and_independent_backpressure(
    tmp_path: Path,
) -> None:
    simv = tmp_path / "shared_root_leaf_adapter.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TOP,
            "-o",
            str(simv),
            *[str(path) for path in RTL_SOURCES],
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
        timeout=120,
    )
    assert "PASS shared_root_leaf_adapter leaves=16 beats_per_leaf=128" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_shared_root_leaf_adapter_has_exactly_fifteen_decoders(
    tmp_path: Path,
) -> None:
    netlist = tmp_path / "shared_root_leaf_adapter.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + f"; hierarchy -check -top {BRIDGE_TOP}; proc; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    design = json.loads(netlist.read_text())
    top = design["modules"][BRIDGE_TOP]
    decoder_cells = [
        cell
        for cell in top["cells"].values()
        if "local_reducer_aggregate_stats_once_exact_decoder" in cell["type"]
    ]
    assert len(decoder_cells) == 15
    assert len(top["ports"]["leaf_valid"]["bits"]) == 16
    assert len(top["ports"]["leaf_command_id"]["bits"]) == 16 * 16
    assert len(top["ports"]["leaf_head_id"]["bits"]) == 16 * 5
    assert len(top["ports"]["leaf_global_max"]["bits"]) == 16 * 32
    assert len(top["ports"]["leaf_exp_sum"]["bits"]) == 16 * 33
    assert len(top["ports"]["leaf_slice"]["bits"]) == 16 * 4
    assert len(top["ports"]["leaf_last"]["bits"]) == 16
    assert len(top["ports"]["leaf_value"]["bits"]) == 16 * 328


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_shared_root_leaf_adapter_composes_with_exact_global_tree(
    tmp_path: Path,
) -> None:
    config = {
        "top_name": (
            "attention_score32_exact_banked_finalized_tree_"
            "factored_c16_r2_l8_b59"
        ),
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
    tree_dir = tmp_path / "tree"
    generate(config, tree_dir)
    simv = tmp_path / "shared_root_global_tree.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_stats_once_exact_shared_root_global_tree_tb",
            "-o",
            str(simv),
            str(tree_dir / "top.v"),
            *[str(path) for path in RTL_SOURCES],
            str(GLOBAL_TREE_TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert "PASS shared_root_global_tree rows=128 lane_value=65535" in run.stdout
