from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
RTL_FILES = [
    "npu/sim/rtl/attention_kv_capacity_gather_scheduler.sv",
    "npu/sim/rtl/attention_kv_gather_span_packetizer.sv",
    "npu/sim/rtl/attention_kv_gather_span_dispatch16.sv",
    "npu/sim/rtl/attention_kv_gather_layer_barrier.sv",
    "npu/sim/rtl/attention_kv_destination_descriptor_guard16.sv",
    "npu/sim/rtl/attention_kv_gather_packet_mesh4x4.sv",
    "npu/sim/rtl/attention_kv_capacity_gather_mesh_ingress.sv",
    "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint_array16.sv",
    "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    "npu/sim/rtl/noc_segmented_mesh_router.sv",
    "npu/sim/rtl/noc_ready_valid_fifo.sv",
]


def test_complete_capacity_gather_mesh_ingress_elaborates(tmp_path: Path) -> None:
    if shutil.which("iverilog") is None:
        pytest.skip("iverilog is required")
    result = subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "attention_kv_capacity_gather_mesh_ingress",
            "-o",
            str(tmp_path / "top.vvp"),
            *(str(ROOT / path) for path in RTL_FILES),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
