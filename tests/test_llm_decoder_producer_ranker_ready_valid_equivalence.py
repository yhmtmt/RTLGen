from pathlib import Path

from npu.eval.probe_llm_decoder_producer_ranker_ready_valid_equivalence import (
    _resolve_executable,
    _run,
    build_report,
)


def test_ready_valid_equivalence_report_requires_r64_k1_and_rtl_match() -> None:
    producer_config = {
        "compute": {"gemm": {"mac_type": "fp16", "num_modules": 16, "lanes_per_module": 1}}
    }
    logit_rank_config = {
        "operations": [
            {
                "type": "logit_rank",
                "module_name": "logit_rank_r64_l16_k1",
                "options": {"row_elems": 64, "logit_bits": 16, "top_k": 1},
            }
        ]
    }
    merge_config = {
        "operations": [
            {
                "type": "candidate_stream_merge_fifo",
                "module_name": "candidate_stream_merge_fifo_k1_l16_t16_d16",
                "options": {
                    "top_k": 1,
                    "logit_bits": 16,
                    "token_id_bits": 16,
                    "fifo_depth_groups": 16,
                },
            }
        ]
    }
    rtl_sim = {
        "status": "ok",
        "expected": {"token": 5, "logit": 500},
        "observed": {"token": 5, "logit": 500, "accepted": 3},
    }

    report = build_report(
        producer_config=producer_config,
        logit_rank_config=logit_rank_config,
        merge_config=merge_config,
        integration_plan={"recommendation": {"next_target": {"name": "r64_k1_nm16_ready_valid_equivalence"}}},
        rtl_sim=rtl_sim,
    )

    assert report["target"]["producer_lanes"] == 64
    assert report["target"]["top_k"] == 1
    assert report["producer_config_summary"]["mac_lanes_per_cycle"] == 16
    assert report["decision"]["decision"] == "ready_valid_equivalence_passed"


def test_missing_tool_execution_is_reportable(tmp_path: Path) -> None:
    result = _run([str(tmp_path / "missing-rtlgen")], cwd=tmp_path)

    assert result.returncode == 127
    assert "No such file or directory" in result.stdout


def test_resolve_executable_handles_repo_relative_build_path(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "build" / "rtlgen"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.chdir(tmp_path)

    assert _resolve_executable("build/rtlgen") == str(binary.resolve())
