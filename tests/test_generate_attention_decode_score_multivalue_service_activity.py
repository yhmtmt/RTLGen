import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.probe_attention_decode_score_multivalue_integrated_service as probe_module
from npu.eval.generate_attention_decode_score_multivalue_service_activity import (
    _OUTPUT_MANIFEST_NAME,
    _OUTPUT_TOP_NAME,
    _OUTPUT_VCD_NAME,
    _REQUIRED_SERVICE_FIELDS,
    _load,
    _normalize_config,
    _sequential_memory_dumpvars,
    generate_activity,
)
from npu.eval.extract_sequential_register_vcd_activity import (
    extract_sequential_register_vcd_activity,
)
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import _workload_contract


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def _config() -> dict[str, object]:
    return {
        "top_name": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_macro_activity",
        "attention_decode_score_multivalue_service": dict(_REQUIRED_SERVICE_FIELDS),
    }


def _c2_repo_config() -> dict[str, object]:
    return _load(
        REPO_ROOT
        / "runs/designs/npu_blocks/attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr/config.json"
    )


def test_normalize_config_requires_macro_backed_c1() -> None:
    normalized = _normalize_config(_config())
    assert normalized["top_name"] == "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_macro_activity"
    assert normalized["attention_decode_score_multivalue_service"] == _REQUIRED_SERVICE_FIELDS
    assert normalized["attention_decode_score_multivalue_service"]["max_blocks"] == _workload_contract()["max_blocks"]


def test_integrated_testbench_default_clock_text_and_8ns_override() -> None:
    values = probe_module._shared_value_matrices()
    default_tb = probe_module._integrated_testbench(
        top_name="demo",
        cluster_count=1,
        values=values,
    )
    fast_tb = probe_module._integrated_testbench(
        top_name="demo",
        cluster_count=1,
        values=values,
        clock_period_ns=8.0,
    )
    assert "  always #5 clk = ~clk;" in default_tb
    assert "always #4 clk = ~clk;" in fast_tb
    assert "always #4 clk = ~clk;" not in default_tb
    assert "cluster_command_block_count[(15*idx) +: 15] = 15'd3;" in default_tb


def test_activity_generator_source_has_no_artificial_macro_touch() -> None:
    source = (REPO_ROOT / "npu/eval/generate_attention_decode_score_multivalue_service_activity.py").read_text(
        encoding="utf-8"
    )
    assert "_inject_bank3_trace_touch" not in source
    assert "force dut" not in source
    assert "release dut" not in source
    assert "post-completion trace touch" not in source


def test_sequential_memory_dumpvars_cover_c1_routed_state_arrays() -> None:
    targets = _sequential_memory_dumpvars(
        {
            "cluster_count": 1,
            "banks": 4,
            "req_queue_depth": 4,
            "resp_queue_depth": 4,
            "bank_queue_depth": 4,
        }
    )

    assert len(targets) == len(set(targets))
    assert "dut.gen_cluster[0].u_cluster.reducer.numerator_accum[127]" in targets
    assert "dut.gen_cluster[0].u_cluster.reducer.block_weight[7]" in targets
    assert "dut.gen_cluster[0].u_cluster.score_tile.accum[7]" in targets
    assert "dut.u_router.gen_resp_fifo[0].u_resp_fifo.mem[3]" in targets
    assert "dut.u_service.active_matrix[3]" in targets
    assert "dut.u_service.gen_bank_fifo[3].u_bank_fifo.mem[3]" in targets
    assert "dut.expected_addr_q[0]" in targets


@pytest.mark.skipif(not _iverilog_available(), reason="iverilog/vvp unavailable")
def test_generate_service_activity_is_deterministic(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"
    script = REPO_ROOT / "npu/eval/generate_attention_decode_score_multivalue_service_activity.py"
    for out_dir in (out_a, out_b):
        run = subprocess.run(
            [sys.executable, str(script), "--config", str(config_path), "--out-dir", str(out_dir)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=240,
        )
        assert run.returncode == 0, f"generator failed:\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"

    manifest_a = json.loads((out_a / _OUTPUT_MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest_b = json.loads((out_b / _OUTPUT_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest_a == manifest_b
    assert manifest_a["workload_contract"] == _workload_contract()
    assert manifest_a["workload_contract"]["active_context_tokens"] == 24
    assert manifest_a["workload_contract"]["max_context_capacity_tokens"] == 128
    assert manifest_a["cycle_count"] > 0
    assert manifest_a["clock_period_ns"] == 10.0
    assert manifest_a["request_result_protocol_counters"]["request_count"] == 48
    assert manifest_a["request_result_protocol_counters"]["wide_response_count"] == 48
    assert manifest_a["request_result_protocol_counters"]["result_count"] == 16
    assert manifest_a["request_result_protocol_counters"]["shared"]["protocol_error"] is False
    assert manifest_a["value_bank_coverage"]["addressed_banks_over_trace"] == [0, 1, 2]
    assert manifest_a["value_bank_coverage"]["request_banks"] == [0, 1, 2]
    assert manifest_a["value_bank_coverage"]["inactive_banks"] == [3]
    assert manifest_a["value_bank_coverage"]["inactive_reason"] == "three_block_reference_workload"
    assert manifest_a["compiled_behavioral_models"] == ["fakeram45_2048x39", "fakeram45_64x32"]
    assert manifest_a["artifacts"]["vcd"] == _OUTPUT_VCD_NAME
    assert not manifest_a["artifacts"]["vcd"].startswith("/")
    assert str(REPO_ROOT / "npu/eval") not in json.dumps(manifest_a, sort_keys=True)
    assert "every bank's switching" in " ".join(manifest_a["scope"]["remaining"])
    assert "24 active context tokens" in " ".join(manifest_a["scope"]["exercised"])

    top_text = (out_a / _OUTPUT_TOP_NAME).read_text(encoding="utf-8")
    assert "fakeram45_2048x39" in top_text
    assert "fakeram45_64x32" in top_text

    vcd_a = (out_a / _OUTPUT_VCD_NAME).read_bytes()
    vcd_b = (out_b / _OUTPUT_VCD_NAME).read_bytes()
    assert vcd_a == vcd_b
    assert manifest_a["hashes"]["vcd_sha256"] == manifest_b["hashes"]["vcd_sha256"]
    sequential = extract_sequential_register_vcd_activity(
        out_a / _OUTPUT_VCD_NAME,
        source_vcd_sha256=manifest_a["hashes"]["vcd_sha256"],
    )
    register_names = {row["full_name"] for row in sequential["register_bits"]}
    assert "gen_cluster[0]/u_cluster/reducer/numerator_accum[127][40]" in register_names
    assert "gen_cluster[0]/u_cluster/score_tile/accum[7][31]" in register_names
    assert "u_router/gen_resp_fifo[0]/u_resp_fifo/mem[3][157]" in register_names
    assert "u_service/active_matrix[3][511]" in register_names
    assert "u_service/gen_bank_fifo[3]/u_bank_fifo/mem[3][26]" in register_names


@pytest.mark.skipif(not _iverilog_available(), reason="iverilog/vvp unavailable")
def test_generate_service_activity_c2_uses_aggregate_protocol_counts(tmp_path: Path) -> None:
    activity_dir = tmp_path / "activity_c2"
    manifest = generate_activity(_c2_repo_config(), activity_dir, case_id="c2_p128_b4_rr")

    assert manifest["case_id"] == "c2_p128_b4_rr"
    assert manifest["cycle_count"] == 8863
    assert manifest["request_result_protocol_counters"]["request_count"] == 96
    assert manifest["request_result_protocol_counters"]["wide_response_count"] == 96
    assert manifest["request_result_protocol_counters"]["result_count"] == 32
    assert manifest["request_result_protocol_counters"]["shared"]["protocol_error"] is False
