from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.eval.model_llama7b_phase2_exact_command_scheduler import (
    ReadinessEvent,
    derive_commands,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = [
    REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint_array16.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/attention_shared_stream_context_admission.sv",
    REPO_ROOT / "npu/sim/rtl/attention_shared_stream_context_engine.sv",
    REPO_ROOT / "npu/sim/rtl/attention_shared_stream_context_service.sv",
]
TB = REPO_ROOT / "tests/attention_shared_stream_context_service_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}"
        if Path(f"/oss-cad-suite/bin/{name}").exists()
        else None
    )


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
@pytest.mark.parametrize("external_mesh", [False, True])
def test_shared_stream_context_service_preserves_contexts_addresses_and_payloads(
    tmp_path: Path, external_mesh: bool,
) -> None:
    sim = tmp_path / "shared-stream-service.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "attention_shared_stream_context_service_tb",
            "-P",
            f"attention_shared_stream_context_service_tb.EXTERNAL_MESH={int(external_mesh)}",
            "-o",
            str(sim),
            *[str(path) for path in RTL_SOURCES],
            str(TB),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(sim)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )

    contexts = [
        tuple(int(value) for value in line.split()[1:])
        for line in run.stdout.splitlines()
        if line.startswith("TRACE_CONTEXT ")
    ]
    completions = [
        tuple(int(value) for value in line.split()[1:])
        for line in run.stdout.splitlines()
        if line.startswith("TRACE_COMPLETION ")
    ]
    model_commands = derive_commands(
        [
            ReadinessEvent.shared(
                wave=0,
                cluster=destination,
                cycle=0,
                source_base_addr=0x0100_0000 + destination * 0x1000,
                destination_base_addr=0x0200_0000 + destination * 0x1000,
                packet_count=3,
            )
            for destination in range(4)
        ]
    )
    rtl_commands = [
        (wave, destination, source, packets, source_base, destination_base)
        for (
            _,
            wave,
            destination,
            source,
            packets,
            source_base,
            destination_base,
        ) in contexts
    ]
    expected_commands = [
        (
            command.wave,
            command.destination,
            command.sources[0],
            command.packet_count,
            command.source_base_addr,
            command.destination_base_addr,
        )
        for command in model_commands
    ]
    assert rtl_commands == expected_commands
    assert sorted((wave, destination) for _, wave, destination in completions) == [
        (0, destination) for destination in range(4)
    ]
    assert "PASS shared_stream_service contexts=4 packets=12 flits=96" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
@pytest.mark.parametrize(("internal_mesh", "expected_meshes"), [(1, 1), (0, 0)])
def test_shared_stream_context_service_yosys_import(
    tmp_path: Path, internal_mesh: int, expected_meshes: int
) -> None:
    netlist = tmp_path / f"service-{internal_mesh}.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + f"; chparam -set INTERNAL_MESH {internal_mesh} "
            + "attention_shared_stream_context_service"
            + "; hierarchy -check -top attention_shared_stream_context_service"
            + f"; proc; check; write_json {netlist}",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    design = json.loads(netlist.read_text(encoding="utf-8"))
    service_cells = list(
        design["modules"]["attention_shared_stream_context_service"]["cells"].values()
    )
    engine_types = [cell["type"] for cell in service_cells if "context_engine" in cell["type"]]
    assert len(engine_types) == 1
    engine_cells = list(design["modules"][engine_types[0]]["cells"].values())
    assert sum("noc_segmented_mesh4x4" in cell["type"] for cell in engine_cells) == expected_meshes
