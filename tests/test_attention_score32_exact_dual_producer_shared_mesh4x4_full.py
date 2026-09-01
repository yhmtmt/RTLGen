from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import time

import pytest

from npu.rtlgen.gen_attention_score32_exact_banked_finalized_tree import generate
from npu.sim.perf.noc_endpoint_vc_injection_arbiter import (
    EndpointVcInjectionArbiter,
    ModelFlit,
)


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
    r"contention=(?P<contention>\d+) "
    r"service_envelope=(?P<service_envelope>\d+) "
    r"service_cycles=(?P<service_cycles>\d+) "
    r"vc0_done_cycle=(?P<vc0_done_cycle>\d+) "
    r"vc1_done_cycle=(?P<vc1_done_cycle>\d+)"
)
ARB_TRACE_RE = re.compile(
    r"^ARB "
    r"(?P<cycle>\d+) "
    r"(?P<producer0_valid>[0-9a-fA-F]+) "
    r"(?P<producer1_valid>[0-9a-fA-F]+) "
    r"(?P<mesh_ready>[0-9a-fA-F]+) "
    r"(?P<producer0_ready>[0-9a-fA-F]+) "
    r"(?P<producer1_ready>[0-9a-fA-F]+) "
    r"(?P<out_valid>[0-9a-fA-F]+) "
    r"(?P<out_vc_pack>[0-9a-fA-F]+)$"
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
EXPECTED_SERVICE_ENVELOPE = {
    "service_cycles": 15769,
    "vc0_done_cycle": 15769,
    "vc1_done_cycle": 10219,
    "overlap_valid": 20624,
    "overlap_arb": 5764,
    "contention": 100725,
}


def _mask_bit(mask: int, bit: int) -> bool:
    return bool((mask >> bit) & 1)


def _packed_vc(word: int, endpoint: int) -> int:
    return (word >> (endpoint * 2)) & 0x3


def _placeholder_flit(endpoint: int, *, vc: int) -> ModelFlit:
    return ModelFlit(
        source=endpoint,
        destination=endpoint,
        tag=endpoint,
        fragment=0,
        last=True,
        vc=vc,
        data=endpoint | (vc << 8),
        label=f"ep{endpoint}_vc{vc}",
    )


def _load_arb_trace(path: Path) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = ARB_TRACE_RE.match(line)
        assert match is not None, f"unexpected arb trace row: {line}"
        rows.append(
            {
                "cycle": int(match.group("cycle")),
                "producer0_valid": int(match.group("producer0_valid"), 16),
                "producer1_valid": int(match.group("producer1_valid"), 16),
                "mesh_ready": int(match.group("mesh_ready"), 16),
                "producer0_ready": int(match.group("producer0_ready"), 16),
                "producer1_ready": int(match.group("producer1_ready"), 16),
                "out_valid": int(match.group("out_valid"), 16),
                "out_vc_pack": int(match.group("out_vc_pack"), 16),
            }
        )
    return rows


def _assert_arbiter_trace_matches_model(path: Path) -> int:
    rows = _load_arb_trace(path)
    assert rows, "arbiter trace is empty"

    models = [EndpointVcInjectionArbiter() for _ in range(16)]
    decision_count = 0
    for expected_cycle, row in enumerate(rows):
        assert row["cycle"] == expected_cycle, (
            f"arb trace cycle mismatch: expected {expected_cycle}, "
            f"got {row['cycle']}"
        )
        for endpoint, model in enumerate(models):
            vc0_valid = _mask_bit(row["producer0_valid"], endpoint)
            vc1_valid = _mask_bit(row["producer1_valid"], endpoint)
            out_ready = _mask_bit(row["mesh_ready"], endpoint)
            observed_vc0_ready = _mask_bit(row["producer0_ready"], endpoint)
            observed_vc1_ready = _mask_bit(row["producer1_ready"], endpoint)
            observed_out_valid = _mask_bit(row["out_valid"], endpoint)
            observed_out_vc = _packed_vc(row["out_vc_pack"], endpoint)

            result = model.step(
                vc0=_placeholder_flit(endpoint, vc=0) if vc0_valid else None,
                vc1=_placeholder_flit(endpoint, vc=1) if vc1_valid else None,
                out_ready=out_ready,
            )
            assert result.protocol_error is False
            assert result.vc0_ready == observed_vc0_ready, (
                f"endpoint {endpoint} cycle {expected_cycle}: "
                f"vc0_ready expected {int(result.vc0_ready)} "
                f"observed {int(observed_vc0_ready)}"
            )
            assert result.vc1_ready == observed_vc1_ready, (
                f"endpoint {endpoint} cycle {expected_cycle}: "
                f"vc1_ready expected {int(result.vc1_ready)} "
                f"observed {int(observed_vc1_ready)}"
            )
            assert (result.output is not None) == observed_out_valid, (
                f"endpoint {endpoint} cycle {expected_cycle}: "
                f"out_valid expected {int(result.output is not None)} "
                f"observed {int(observed_out_valid)}"
            )
            if result.output is not None:
                decision_count += 1
                assert result.output.vc == observed_out_vc, (
                    f"endpoint {endpoint} cycle {expected_cycle}: "
                    f"out_vc expected {result.output.vc} observed {observed_out_vc}"
                )
            else:
                assert observed_out_vc == 0, (
                    f"endpoint {endpoint} cycle {expected_cycle}: "
                    f"out_vc should be zero when out_valid=0, observed {observed_out_vc}"
                )

    assert decision_count > 0, "arbiter replay did not observe any decisions"
    return decision_count


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
    arb_trace = tmp_path / "attention_score32_exact_dual_producer_shared_mesh4x4_full_arb.trace"

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
    try:
        run = subprocess.run(
            [str(_tool("vvp")), str(simv), f"+ARB_TRACE={arb_trace}"],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            "vvp failed\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
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
    assert observed["service_envelope"] == 0
    assert observed["service_cycles"] == max(
        observed["vc0_done_cycle"], observed["vc1_done_cycle"]
    )
    arb_decisions = _assert_arbiter_trace_matches_model(arb_trace)
    arb_trace.unlink(missing_ok=True)

    envelope_start = time.monotonic()
    try:
        envelope_run = subprocess.run(
            [str(_tool("vvp")), str(simv), "+SERVICE_ENVELOPE"],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            "service-envelope vvp failed\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        )
    envelope_elapsed = time.monotonic() - envelope_start
    envelope_match = PASS_RE.search(envelope_run.stdout)
    assert envelope_match is not None, envelope_run.stdout
    envelope = {name: int(value) for name, value in envelope_match.groupdict().items()}
    for field in (
        "vc0_contexts",
        "vc0_packets",
        "vc0_flits",
        "vc1_groups",
        "vc1_rows",
        "vc1_packets",
        "vc1_flits",
    ):
        assert envelope[field] == observed[field]
    assert envelope["service_envelope"] == 1
    assert envelope["service_cycles"] == max(
        envelope["vc0_done_cycle"], envelope["vc1_done_cycle"]
    )
    assert envelope["service_cycles"] <= observed["service_cycles"]
    assert envelope["overlap_valid"] > 0
    assert envelope["overlap_arb"] > 0
    assert envelope["contention"] > 0
    for field, expected in EXPECTED_SERVICE_ENVELOPE.items():
        assert envelope[field] == expected

    print(
        "PASS promotion-scale shared-mesh replay "
        f"compile_s={compile_elapsed:.2f} run_s={run_elapsed:.2f} "
        f"arb_decisions={arb_decisions} envelope_s={envelope_elapsed:.2f} "
        f"envelope_cycles={envelope['service_cycles']}"
    )
