from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import pytest

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/attention_score32_exact_dual_producer_shared_mesh4x4_full_tb.sv"
TOP = "attention_score32_exact_dual_producer_shared_mesh4x4_full_tb"

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
PASS_RE = re.compile(
    r"PASS exact_dual_producer_shared_mesh_full "
    r"vc0_contexts=(?P<vc0_contexts>\d+) "
    r"vc0_packets=(?P<vc0_packets>\d+) "
    r"vc0_flits=(?P<vc0_flits>\d+) "
    r"vc1_groups=(?P<vc1_groups>\d+) "
    r"vc1_rows=(?P<vc1_rows>\d+) "
    r"vc1_packets=(?P<vc1_packets>\d+) "
    r"vc1_flits=(?P<vc1_flits>\d+) "
    r"overlap_valid=(?P<overlap_valid>\d+) "
    r"overlap_arb=(?P<overlap_arb>\d+) "
    r"contention=(?P<contention>\d+)"
)


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


RUN_ENV = "RTLGEN_RUN_SLOW_SHARED_MESH_FULL_REPLAY"


@pytest.mark.skipif(
    os.environ.get(RUN_ENV) != "1",
    reason=f"set {RUN_ENV}=1 to run the promotion-scale shared-mesh RTL replay",
)
@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_exact_dual_producer_shared_mesh_full_replay(tmp_path: Path) -> None:
    tree_dir = _generate_tree(tmp_path)
    simv = tmp_path / "attention_score32_exact_dual_producer_shared_mesh4x4_full.vvp"

    compile_start = time.monotonic()
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
        timeout=600,
    )
    compile_elapsed = time.monotonic() - compile_start

    run_start = time.monotonic()
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1200,
    )
    run_elapsed = time.monotonic() - run_start

    match = PASS_RE.search(run.stdout)
    assert match is not None, run.stdout
    observed = {name: int(value) for name, value in match.groupdict().items()}

    assert observed["vc0_contexts"] == 112
    assert observed["vc0_packets"] == 7616
    assert observed["vc0_flits"] == 60928
    assert observed["vc1_groups"] == 4
    assert observed["vc1_rows"] == 512
    assert observed["vc1_packets"] == 1260
    assert observed["vc1_flits"] == 10020
    assert observed["overlap_valid"] > 0
    assert observed["overlap_arb"] > 0
    assert observed["contention"] > 0

    print(
        "PASS promotion-scale shared-mesh replay "
        f"compile_s={compile_elapsed:.2f} run_s={run_elapsed:.2f}"
    )
