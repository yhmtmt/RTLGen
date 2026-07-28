import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8 import build_report
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import generate


def _rtl_tools_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp") and shutil.which("verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config_path() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59"
        / "config.json"
    )


def _load_config() -> dict[str, object]:
    return json.loads(_config_path().read_text(encoding="utf-8"))


def _extract_module(text: str, module_name: str) -> str:
    match = re.search(rf"module\s+{re.escape(module_name)}\b.*?endmodule\s*", text, flags=re.DOTALL)
    assert match is not None
    return match.group(0)


def _local_reducer_stub(module_name: str, producers: int) -> str:
    return f"""/* verilator lint_off UNUSEDSIGNAL */
/* verilator lint_off UNDRIVEN */
module {module_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [{producers - 1}:0] leaf_valid,
    output wire [{producers - 1}:0] leaf_ready,
    input  wire [{producers * 16 - 1}:0] leaf_command_id,
    input  wire [{producers * 5 - 1}:0] leaf_head_id,
    input  wire [{producers * 32 - 1}:0] leaf_global_max,
    input  wire [{producers * 33 - 1}:0] leaf_exp_sum,
    input  wire [{producers * 4 - 1}:0] leaf_slice,
    input  wire [{producers - 1}:0] leaf_last,
    input  wire [{producers * 328 - 1}:0] leaf_value,
    output wire         out_valid,
    input  wire         out_ready,
    output wire [15:0]  out_command_id,
    output wire [4:0]   out_head_id,
    output wire [31:0]  out_global_max,
    output wire [32:0]  out_exp_sum,
    output wire [3:0]   out_slice,
    output wire         out_last,
    output wire [327:0] out_value,
    output wire [2:0]   active_wave_index,
    output wire         emitting,
    output wire [4:0]   active_head_base,
    output wire [6:0]   collect_beat_index,
    output wire [6:0]   emit_beat_index,
    output wire [31:0]  cycle_count,
    output wire [31:0]  local_root_completed_count,
    output wire [31:0]  temporal_merge_completed_count,
    output wire [31:0]  emitted_beat_count,
    output wire [31:0]  completed_command_count,
    output wire [31:0]  local_stall_cycles,
    output wire [31:0]  output_stall_cycles,
    output wire         group_contract_error,
    output wire         local_tree_protocol_error,
    output wire         temporal_merge_protocol_error,
    output wire         protocol_error
);
endmodule
/* verilator lint_on UNDRIVEN */
/* verilator lint_on UNUSEDSIGNAL */
"""


def _global_tree_stub(module_name: str) -> str:
    return f"""/* verilator lint_off UNUSEDSIGNAL */
/* verilator lint_off UNDRIVEN */
module {module_name} (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [15:0]  leaf_valid,
    output wire [15:0]  leaf_ready,
    input  wire [255:0] leaf_command_id,
    input  wire [79:0]  leaf_head_id,
    input  wire [511:0] leaf_global_max,
    input  wire [527:0] leaf_exp_sum,
    input  wire [63:0]  leaf_slice,
    input  wire [15:0]  leaf_last,
    input  wire [5247:0] leaf_value,
    output wire         root_valid,
    input  wire         root_ready,
    output wire [15:0]  root_command_id,
    output wire [4:0]   root_head_id,
    output wire [3:0]   root_slice,
    output wire         root_last,
    output wire [319:0] root_value,
    output wire [31:0]  cycle_count,
    output wire [31:0]  root_completed_count,
    output wire [31:0]  finalizer_accepted_count,
    output wire [31:0]  tree_root_completed_count,
    output wire [31:0]  order_fifo_occupancy,
    output wire [31:0]  order_fifo_high_watermark,
    output wire [31:0]  order_enqueued_count,
    output wire [31:0]  order_dequeued_count,
    output wire [31:0]  dispatch_stall_cycles,
    output wire [31:0]  dispatch_bank_id,
    output wire [31:0]  head_bank_id,
    output wire [479:0] node_completed_count,
    output wire [127:0] stage_completed_count,
    output wire [14:0]  node_protocol_error,
    output wire [3:0]   stage_protocol_error,
    output wire [58:0]  bank_protocol_error,
    output wire [58:0]  bank_outstanding,
    output wire         tree_protocol_error,
    output wire         order_protocol_error,
    output wire         finalizer_protocol_error,
    output wire         protocol_error
);
endmodule
/* verilator lint_on UNDRIVEN */
/* verilator lint_on UNUSEDSIGNAL */
"""


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local16_global_tree_manifest_and_verilator_lint(tmp_path: Path) -> None:
    config = _load_config()
    generate(config, tmp_path / "rtl")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_local16_global_tree_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    top_text = (tmp_path / "rtl" / "top.v").read_text(encoding="utf-8")

    assert manifest["clusters"] == 16
    assert manifest["cluster_producers"] == [54] * 8 + [53] * 8
    assert manifest["clusters_with_54_producers"] == 8
    assert manifest["clusters_with_53_producers"] == 8
    assert manifest["total_local_producers"] == 856
    assert manifest["divider_lanes"] == 8
    assert manifest["finalizer_banks"] == 59
    assert manifest["result_interface"] == (
        "packed_856_leaf_exact_partial_inputs_to_c16_ordered_banked_exact_finalized_root_stream"
    )
    assert manifest["interface_adaptation"] == {
        "top_leaf_partitioning": "direct_flat_packed_leaf_buses_partitioned_by_cluster_leaf_base_indices",
        "local_to_global_leaf_mapping": (
            "direct_ready_valid_command_id_head_id_global_max_exp_sum_slice_last_value_mapping_without_field_remap"
        ),
        "finalized_output_semantics": (
            "existing_c16_banked_tree_root_contract_consumes_global_max_and_exp_sum_and_emits_finalized_values_only"
        ),
    }
    assert manifest["remaining_abstractions"] == [
        "producer_leaf_source_open",
        "noc_sram_transport_open",
        "physical_ppa_open",
    ]
    assert manifest["service_model"]["query_head_groups"] == 1
    assert manifest["linked_proposal_id"] == "prop_l1_decoder_attention_score32_exact_local16_global_tree_gqa8_v1"
    assert manifest["linked_proposal_path"].endswith("/proposal.json")
    assert manifest["submodule_manifests"]["cluster_instance_counts"] == {"p54": 8, "p53": 8}
    assert manifest["submodule_manifests"]["local_temporal_reducer_p54"]["producers"] == 54
    assert manifest["submodule_manifests"]["local_temporal_reducer_p53"]["producers"] == 53
    assert manifest["submodule_manifests"]["banked_tree"]["clusters"] == 16
    assert manifest["submodule_manifests"]["banked_tree"]["divider_lanes"] == 8
    assert manifest["submodule_manifests"]["banked_tree"]["finalizer_banks"] == 59

    for token in (
        "input  wire [855:0] leaf_valid,",
        "output wire [855:0] leaf_ready,",
        "input  wire [13695:0] leaf_command_id,",
        "input  wire [4279:0] leaf_head_id,",
        "input  wire [27391:0] leaf_global_max,",
        "input  wire [28247:0] leaf_exp_sum,",
        "input  wire [3423:0] leaf_slice,",
        "input  wire [280767:0] leaf_value,",
        ".leaf_valid(leaf_valid[0 +: 54])",
        ".leaf_valid(leaf_valid[803 +: 53])",
        ".leaf_command_id(cluster_out_command_id_w)",
        "assign protocol_error = (|cluster_protocol_error) || global_protocol_error;",
    ):
        assert token in top_text

    wrapper_only = tmp_path / "wrapper_only.v"
    wrapper_only.write_text(
        _extract_module(top_text, str(config["top_name"]))
        + "\n\n"
        + _local_reducer_stub(f"{config['top_name']}__local_temporal_p54", 54)
        + "\n\n"
        + _local_reducer_stub(f"{config['top_name']}__local_temporal_p53", 53)
        + "\n\n"
        + _global_tree_stub(f"{config['top_name']}__global_tree"),
        encoding="utf-8",
    )

    lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(wrapper_only),
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert lint.returncode == 0, lint.stderr


def test_local16_global_tree_rejects_invalid_cluster_distribution(tmp_path: Path) -> None:
    config = _load_config()
    body = config["attention_score32_exact_local16_global_tree_gqa8"]
    assert isinstance(body, dict)
    body["cluster_producers"] = [54] * 9 + [53] * 7
    with pytest.raises(SystemExit, match="cluster_producers must contain exactly eight 54s and eight 53s"):
        generate(config, tmp_path / "rtl")


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local16_global_tree_bounded_probe_matches_reference() -> None:
    report = build_report(config=_load_config(), timeout_sec=240)

    assert report["passed"] is True
    assert report["simulation_status"] == "ok"
    assert report["outputs"] == 128
    assert report["expected_outputs"] == 128
    assert report["cluster_aggregate_outputs"] == 2048
    assert report["expected_cluster_aggregate_outputs"] == 2048
    assert report["observed_root_hash"] == "a8e78a3e4c551fec6aeb050b92fc08d2ece9a32a06d21b2789bc1b19c5416821"
    assert report["expected_root_hash"] == "a8e78a3e4c551fec6aeb050b92fc08d2ece9a32a06d21b2789bc1b19c5416821"
    assert report["observed_cluster_hashes"][0] == "e69137999fe4c2b05e5cbccc4f77fba8eb40c2c03b756bef9292f2c03ba503c3"
    assert report["summary"]["drain_cycles"] == 3268
    assert report["summary"]["first_root_cycle"] == 3139
    assert report["summary"]["last_root_cycle"] == 3266
    assert report["summary"]["global_dispatch_stall_cycles"] == 0
    assert report["summary"]["protocol_error"] == 0
    assert report["source_links"]["proposal_id"] == "prop_l1_decoder_attention_score32_exact_local16_global_tree_gqa8_v1"


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local16_global_tree_root_backpressure_probe_matches_reference() -> None:
    report = build_report(
        config=_load_config(),
        output_ready_pattern=(True, False, True, True, False, True, False, True),
        timeout_sec=240,
    )

    assert report["passed"] is True
    assert report["simulation_status"] == "ok"
    assert report["outputs"] == 128
    assert report["observed_root_hash"] == "a8e78a3e4c551fec6aeb050b92fc08d2ece9a32a06d21b2789bc1b19c5416821"
    assert max(summary["output_stall_cycles"] for summary in report["cluster_summaries"]) > 0
    assert report["summary"]["last_root_cycle"] > report["summary"]["first_root_cycle"]
    assert report["summary"]["global_order_protocol_error"] == 0
    assert report["summary"]["global_finalizer_protocol_error"] == 0
