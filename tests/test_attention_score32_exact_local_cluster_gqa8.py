import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local_cluster_gqa8 import build_report
from npu.rtlgen.gen_attention_score32_exact_local_cluster_gqa8 import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_CLUSTER_GQA8_HEAD_BASES,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_service_manifest,
)

_FAKERAM_MODEL = """
module fakeram45_2048x39 (
    output wire [38:0] rd_out, input wire [10:0] addr_in,
    input wire we_in, input wire [38:0] wd_in, input wire [38:0] w_mask_in,
    input wire clk, input wire ce_in
);
  reg [38:0] mem [0:2047];
  reg [10:0] addr_q;
  reg [38:0] rd_out_q;
  integer idx;
  initial begin
    addr_q = 0;
    rd_out_q = 0;
    for (idx = 0; idx < 2048; idx = idx + 1) mem[idx] = 0;
  end
  always @(posedge clk) begin
    rd_out_q <= mem[addr_q];
    if (ce_in) begin
      if (we_in) begin
        for (idx = 0; idx < 39; idx = idx + 1) begin
          if (w_mask_in[idx]) mem[addr_in][idx] <= wd_in[idx];
        end
      end
      addr_q <= addr_in;
    end
  end
  assign rd_out = rd_out_q;
endmodule
"""


def _tool_available(name: str) -> bool:
    return bool(shutil.which(name) or (Path("/oss-cad-suite/bin") / name).exists())


def _rtl_tools_available() -> bool:
    return all(_tool_available(name) for name in ("iverilog", "vvp", "verilator"))


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    if fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required tool unavailable: {name}")


def _config_path(producers: int) -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / f"attention_score32_exact_local_cluster_gqa8_p{producers}_w8"
        / "config.json"
    )


def _load_config(producers: int) -> dict[str, object]:
    return json.loads(_config_path(producers).read_text(encoding="utf-8"))


def test_local_cluster_gqa8_schedule_rotation_and_counts() -> None:
    schedule53 = [
        list(exact_local_cluster_gqa8_command_block_counts(producers=53, group_index=group_index))
        for group_index in range(4)
    ]
    schedule54 = [
        list(exact_local_cluster_gqa8_command_block_counts(producers=54, group_index=group_index))
        for group_index in range(4)
    ]

    assert schedule53[0][:11] == [2] * 11
    assert schedule53[0][11:] == [1] * 42
    assert schedule53[1][11:22] == [2] * 11
    assert schedule53[2][22:33] == [2] * 11
    assert schedule53[3][33:44] == [2] * 11
    assert all(sum(group) == 64 for group in schedule53)

    assert schedule54[0][:10] == [2] * 10
    assert schedule54[0][10:] == [1] * 44
    assert schedule54[1][10:20] == [2] * 10
    assert schedule54[2][20:30] == [2] * 10
    assert schedule54[3][30:40] == [2] * 10
    assert all(sum(group) == 64 for group in schedule54)

    manifest53 = exact_local_cluster_gqa8_service_manifest(producers=53)
    manifest54 = exact_local_cluster_gqa8_service_manifest(producers=54)
    assert manifest53["head_bases"] == list(LOCAL_CLUSTER_GQA8_HEAD_BASES)
    assert manifest54["head_bases"] == list(LOCAL_CLUSTER_GQA8_HEAD_BASES)
    assert manifest53["aggregate_output_beats_per_full_run"] == 512
    assert manifest54["aggregate_output_beats_per_full_run"] == 512


def test_local_cluster_gqa8_rejects_wrong_max_blocks(tmp_path: Path) -> None:
    config = _load_config(53)
    config["attention_score32_exact_local_cluster_gqa8"]["max_blocks"] = 16
    with pytest.raises(SystemExit, match="max_blocks must remain fixed at 8"):
        generate(config, tmp_path / "rtl")


def test_local_cluster_gqa8_generated_top_contains_full_width_wiring_tokens(tmp_path: Path) -> None:
    config = _load_config(54)
    generate(config, tmp_path / "rtl")

    top_text = (tmp_path / "rtl" / "top.v").read_text(encoding="utf-8")
    top_name = str(config["top_name"])
    top_start = top_text.index(f"module {top_name} ")
    top_end = top_text.index("endmodule", top_start)
    top_module = top_text[top_start:top_end]

    assert top_module.count(f"{top_name}__producer u_producer_") == 54
    assert f"{top_name}__reducer u_reducer" in top_module
    assert "wire group_command_fire_w = command_valid && command_ready;" in top_module
    assert "wire [PRODUCERS-1:0] producer_command_accept_w = {PRODUCERS{group_command_fire_w}} & producer_command_ready_w;" in top_module
    assert "assign command_ready = &producer_command_ready_w;" in top_module
    assert ".leaf_valid(producer_result_valid_w)" in top_module
    assert ".leaf_ready(producer_result_ready_w)" in top_module
    assert ".leaf_command_id(producer_result_command_id_w)" in top_module
    assert ".leaf_value(producer_result_value_w)" in top_module
    assert ".command_block_count(command_block_count[14:0])" in top_module
    assert ".command_block_count(command_block_count[809:795])" in top_module
    assert ".value_read_req_valid(value_read_req_valid[1:0])" in top_module
    assert ".value_read_req_valid(value_read_req_valid[107:106])" in top_module
    assert ".value_response_matrix(value_response_matrix[1023:0])" in top_module
    assert ".value_response_matrix(value_response_matrix[55295:54272])" in top_module


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
@pytest.mark.parametrize("producers", (53, 54))
def test_local_cluster_gqa8_manifest_and_verilator_lint(tmp_path: Path, producers: int) -> None:
    config = _load_config(producers)
    generate(config, tmp_path / "rtl")
    fakeram_path = tmp_path / "fakeram45_2048x39.sv"
    fakeram_path.write_text(_FAKERAM_MODEL, encoding="utf-8")

    manifest = json.loads(
        (tmp_path / "rtl" / "attention_score32_exact_local_cluster_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["producers"] == producers
    assert manifest["max_blocks"] == 8
    assert manifest["persistent_waves"] == 8
    assert manifest["query_head_groups"] == 4
    assert manifest["query_heads_per_group"] == 8
    assert manifest["value_memory_lanes"] == producers * 2
    assert manifest["producer_input_lanes"] == producers
    assert manifest["remaining_abstractions"] == [
        "noc_sram_ppa_open",
        "global_c16_exact_reduction_open",
    ]
    assert manifest["checked_in_probe_defaults"] == {
        "head_bases": [0, 8, 16, 24],
        "head_dim": 1,
        "seed": 73,
        "timeout_s": 300,
    }
    assert manifest["rtl_files"] == [
        "top.v",
        "producer.v",
        "reducer.v",
        "verilator_wrapper_blackboxes.v",
    ]
    assert manifest["service_model"]["per_group_total_blocks_per_stream"] == [64, 64, 64, 64]
    assert manifest["service_model"]["full_run_wave_command_count"] == 32
    assert manifest["submodule_manifests"]["producer"]["max_blocks"] == 8
    assert manifest["submodule_manifests"]["gqa8_local_temporal_reducer"]["producers"] == producers

    producer_lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            f"{config['top_name']}__producer",
            str(tmp_path / "rtl" / "producer.v"),
            str(fakeram_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert producer_lint.returncode == 0, producer_lint.stderr

    reducer_lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            f"{config['top_name']}__reducer",
            str(tmp_path / "rtl" / "reducer.v"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert reducer_lint.returncode == 0, reducer_lint.stderr

    wrapper_lint = subprocess.run(
        [
            _tool("verilator"),
            "--lint-only",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "--top-module",
            str(config["top_name"]),
            str(tmp_path / "rtl" / "top.v"),
            str(tmp_path / "rtl" / "verilator_wrapper_blackboxes.v"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert wrapper_lint.returncode == 0, wrapper_lint.stderr


@pytest.mark.skipif(not _rtl_tools_available(), reason="RTL tools unavailable")
def test_local_cluster_gqa8_full_p53_probe_attempt_is_bounded_and_honest() -> None:
    report = build_report(config=_load_config(53))

    assert report["full_probe_attempted"] is True
    assert report["producers"] == 53
    assert report["groups"] == 4
    assert report["waves"] == 8
    assert report["wave_commands"] == 32
    assert report["head_bases"] == [0, 8, 16, 24]
    assert report["head_dim"] == 1
    assert report["expected_outputs"] == 512
    assert report["service_model"]["per_group_total_blocks_per_stream"] == [64, 64, 64, 64]

    if report["timed_out"]:
        assert report["timeout_s"] == 300
        assert report["passed"] is False
        return

    assert report["passed"] is True
    assert report["outputs"] == 512
    assert report["command_schedule_matches"] is True
    assert report["producer_counts_match"] is True
    assert report["wave_command_accept_count"] == 32
    assert report["reducer_completed_command_count"] == 4
    assert report["reducer_local_root_completed_count"] == 4096
    assert report["reducer_temporal_merge_completed_count"] == 3584
    assert report["reducer_emitted_beat_count"] == 512
    assert report["protocol_error"] is False
    assert report["atomic_command_protocol_error"] is False
    assert report["group_contract_error"] is False
    assert report["local_tree_protocol_error"] is False
    assert report["temporal_merge_protocol_error"] is False
    assert report["reducer_protocol_error"] is False
    assert report["observed_rows"] == report["expected_rows"]
