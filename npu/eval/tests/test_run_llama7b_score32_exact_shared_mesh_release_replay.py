from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from npu.eval.prepare_llama7b_score32_exact_shared_mesh_release_replay import build_replay
from npu.eval.run_llama7b_score32_exact_shared_mesh_release_replay import (
    build_result,
    render_markdown,
)

from npu.eval.tests.test_prepare_llama7b_score32_exact_shared_mesh_release_replay import (
    _cadence,
)


PASS_LINE = (
    "PASS promotion-scale shared-mesh replay compile_s=1.25 run_s=2.50 "
    "arb_decisions=70948 envelope_s=2.00 envelope_cycles=15769 "
    "release_coupled_cycles=17000 release_vc0_done_cycle=15769 "
    "release_vc1_done_cycle=17000 release_arb_decisions=70948 "
    "release_source_fires=8192"
)


def test_result_retains_completion_split_and_exact_contract(tmp_path: Path) -> None:
    cadence = _cadence()
    cadence_path = tmp_path / "cadence.json"
    cadence_path.write_text(json.dumps(cadence), encoding="utf-8")
    replay = build_replay(cadence, cadence_path=cadence_path)

    result = build_result(
        replay=replay,
        cadence_path=cadence_path,
        pytest_stdout=f"session output\n{PASS_LINE}\n",
    )

    assert result["passed"] is True
    assert result["rtl_observation"]["service_cycles"] == 17000
    assert result["rtl_observation"]["vc0_done_cycle"] == 15769
    assert result["rtl_observation"]["vc1_done_cycle"] == 17000
    assert result["rtl_observation"]["exact_traffic"]["vc1_flits"] == 10020
    assert result["rtl_observation"]["release_source_handshakes_checked"] == 8192
    assert "VC0 destination SRAM" in result["next_gate"]
    assert "17,000" not in render_markdown(result)
    assert "`17000` cycles" in render_markdown(result)


def test_result_rejects_missing_or_inconsistent_pass_summary(tmp_path: Path) -> None:
    cadence_path = tmp_path / "cadence.json"
    cadence_path.write_text(json.dumps(_cadence()), encoding="utf-8")
    replay = build_replay(_cadence(), cadence_path=cadence_path)

    with pytest.raises(ValueError, match="passing release summary"):
        build_result(replay=replay, cadence_path=cadence_path, pytest_stdout="1 passed")
    inconsistent = PASS_LINE.replace("release_coupled_cycles=17000", "release_coupled_cycles=16999")
    with pytest.raises(ValueError, match="later producer"):
        build_result(replay=replay, cadence_path=cadence_path, pytest_stdout=inconsistent)


@pytest.mark.parametrize(
    "script",
    [
        "npu/eval/probe_llama7b_score32_exact_cluster_release_cadence.py",
        "npu/eval/run_llama7b_score32_exact_shared_mesh_release_replay.py",
        "npu/eval/audit_llama7b_score32_exact_kv_ingress_closure.py",
    ],
)
def test_executable_entrypoint_imports_from_repo_root(script: str) -> None:
    completed = subprocess.run(
        [sys.executable, script, "--help"],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
