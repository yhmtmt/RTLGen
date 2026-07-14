from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_audit_rtl_component_equivalence_records_passing_target(tmp_path: Path) -> None:
    out = tmp_path / "evidence.json"
    out_md = tmp_path / "evidence.md"
    run = subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_rtl_component_equivalence.py",
            "--component",
            "attention_score_bank_proxy",
            "--semantic-profile",
            "sync_16kx256_1rw",
            "--test-target",
            "tests/test_attention_score_bank_proxy.py",
            "--reference",
            "behavioral_synchronous_1rw_memory",
            "--out",
            str(out),
            "--out-md",
            str(out_md),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["model"] == "rtl_component_reference_equivalence_v1"
    assert payload["decision"] == "attention_score_bank_proxy_equivalence_pass"
    assert payload["equivalence_pass"] is True
    assert payload["passed_test_count"] == 2
    assert payload["reference"] == "behavioral_synchronous_1rw_memory"
    assert "attention_score_bank_proxy_equivalence_pass" in out_md.read_text(encoding="utf-8")
    assert '"ok": true' in run.stdout
