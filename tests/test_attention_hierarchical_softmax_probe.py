from pathlib import Path
import subprocess
import sys

from npu.eval.probe_attention_hierarchical_softmax import build_report


def test_hierarchical_softmax_probe_selects_exact_two_pass() -> None:
    report = build_report(
        lengths=[128],
        distributions=["normal_std1", "normal_std4", "monotonic_ramp16"],
        seed=1,
    )

    assert report["decision"] == "two_pass_exact_selected"
    assert report["online_pass"] is False
    assert report["llama7b_score_buffer"]["mib"] == 16.0
    assert all(
        row["arithmetic_exact_vs_two_pass"]
        for row in report["rows"]
        if row["architecture"] == "two_pass_global_max"
    )


def test_hierarchical_softmax_probe_runs_directly(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "npu/eval/probe_attention_hierarchical_softmax.py",
            "--lengths",
            "128",
            "--out",
            str(tmp_path / "report.json"),
            "--out-md",
            str(tmp_path / "report.md"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "report.json").is_file()
    assert (tmp_path / "report.md").is_file()
