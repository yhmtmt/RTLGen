import json
from pathlib import Path
import shutil
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.generate_attention_dual_stream_schedule_wrapper_activity import (
    _OUTPUT_MANIFEST_NAME,
    generate_activity,
)


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


@pytest.mark.skipif(not _iverilog_available(), reason="iverilog/vvp unavailable")
def test_generate_schedule_wrapper_activity_real_window_contract(tmp_path: Path) -> None:
    config = json.loads(
        (
            REPO_ROOT
            / "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/config.json"
        ).read_text(encoding="utf-8")
    )

    manifest = generate_activity(config, tmp_path / "activity")
    manifest_path = tmp_path / "activity" / _OUTPUT_MANIFEST_NAME

    assert manifest_path.is_file()
    assert manifest["cycle_count"] == 986
    assert manifest["service_window_cycles"] == 986
    assert manifest["cluster_service_cycles"] == 4
    assert manifest["total_sim_cycles"] == 1023
    assert manifest["gates"]["service_window_gate_ok"] is True
    assert manifest["gates"]["window_active_gate_ok"] is True
    assert manifest["gates"]["both_clusters_issue_gate_ok"] is True
    assert manifest["request_result_protocol_counters"]["accepted_count"] == 340
    assert manifest["request_result_protocol_counters"]["issue_count"] == 340
    assert manifest["request_result_protocol_counters"]["completed_count"] == 340
    assert manifest["request_result_protocol_counters"]["window_active_cycles"] == 986
    assert manifest["request_result_protocol_counters"]["window_issue_counts"] == {"0": 165, "1": 164}
    assert manifest["request_result_protocol_counters"]["ready_low_cycles"] > 0
    assert manifest["completion_result_evidence"]["hardware_final_result_fold"] == "0000015b"
    assert manifest["completion_result_evidence"]["reference_final_result_fold"] != "0000015b"
    assert not any(str(value).startswith("/") for value in manifest["artifacts"].values())
