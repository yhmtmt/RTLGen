import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import npu.eval.probe_attention_decode_score_multivalue_integrated_service as probe_module
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import (
    build_report,
    validate_report,
)


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def _exact_partial_case(*, case_id: str, cluster_count: int) -> dict:
    return {
        "case_id": case_id,
        "cluster_count": cluster_count,
        "packet_w": 128,
        "banks": 2,
        "req_queue_depth": 2,
        "resp_queue_depth": 2,
        "bank_queue_depth": 2,
        "read_latency": 1,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
        "result_mode": "exact_partial",
        "head_id_bits": 5,
    }


def test_exact_partial_probe_testbenches_emit_literal_head_slices() -> None:
    case = _exact_partial_case(case_id="literal_head_slices", cluster_count=2)
    values = probe_module._shared_value_matrices()

    baseline_tb = probe_module._baseline_testbench(
        top_name="baseline_cluster_exact_partial",
        cluster_count=2,
        values=values,
        case=case,
    )
    integrated_tb = probe_module._integrated_testbench(
        top_name="integrated_service_exact_partial",
        cluster_count=2,
        values=values,
        case=case,
    )

    for tb_text in (baseline_tb, integrated_tb):
        assert "cluster_command_head_id[(5*0) +: 5]" in tb_text
        assert "cluster_command_head_id[(5*1) +: 5]" in tb_text
        assert "cluster_command_head_id[(5*idx) +: 5]" not in tb_text


def test_exact_partial_integrated_service_probe_build_report_passes() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report({"cases": [_exact_partial_case(case_id="c2_p128_b2_exact_partial", cluster_count=2)]})

    assert report["decision"] == "pass"
    validate_report(report)

    case = report["cases"][0]
    assert case["config"]["result_mode"] == "exact_partial"
    assert case["config"]["head_id_bits"] == 5
    assert case["decision"] == "pass"
    assert case["integrated_service"]["exact_match"] is True
    assert case["integrated_service"]["result_count"] == 32
    assert case["integrated_service"]["counters"]["shared_result"]["egress_block_cycles"] > 0
    assert case["integrated_service"]["shared_result_egress"]["back_to_back_fire_seen"] is True
    assert any(
        row["path"] == "npu/sim/perf/attention_exact_partial.py"
        for row in report["source_identities"]["files"]
    )


def test_main_applies_exact_partial_mode_to_default_cases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict = {}

    def fake_build_report(config: dict, **kwargs: object) -> dict:
        captured["config"] = config
        captured["kwargs"] = kwargs
        return {"decision": "pass"}

    out = tmp_path / "report.json"
    monkeypatch.setattr(probe_module, "build_report", fake_build_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "probe_attention_decode_score_multivalue_integrated_service.py",
            "--result-mode",
            "exact_partial",
            "--out",
            str(out),
        ],
    )

    assert probe_module.main() == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["decision"] == "pass"
    assert len(captured["config"]["cases"]) == len(probe_module.DEFAULT_CASES)
    assert all(case["result_mode"] == "exact_partial" for case in captured["config"]["cases"])
    assert all(case["head_id_bits"] == 5 for case in captured["config"]["cases"])
