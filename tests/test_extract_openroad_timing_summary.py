from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


def test_extract_openroad_timing_summary_reports_startpoint_endpoint(tmp_path: Path) -> None:
    design_dir = tmp_path / "runs" / "designs" / "npu_blocks" / "attention_dual_stream_composed_smoke"
    report_dir = tmp_path / "orfs" / "flow" / "reports" / "nangate45" / "attention_dual_stream_composed_smoke" / "base"
    design_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    timing_report = report_dir / "5_route_check.rpt"
    timing_report.write_text(
        """Startpoint: stream_buf_reg[0] (rising edge-triggered flip-flop clocked by clk)
Endpoint: softmax_unit/sum_reg[7] (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  data arrival time              23.8349
  data required time             20.0000
  slack (VIOLATED)               -3.8349

==========================================================================
route report_power
--------------------------------------------------------------------------
This section must not be included in the path excerpt.
""",
        encoding="utf-8",
    )
    floorplan_report = report_dir / "2_floorplan_final.rpt"
    floorplan_report.write_text(
        """Startpoint: seed_state[0] (rising edge-triggered flip-flop clocked by clk)
Endpoint: softmax_unit/weight_hash[8] (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  data arrival time              29.0000
  data required time             10.0000
  slack (VIOLATED)               -19.0000
""",
        encoding="utf-8",
    )
    finish_report = report_dir / "6_finish.rpt"
    finish_report.write_text("finish critical path delay\n-----\n23.8349\n", encoding="utf-8")
    with (design_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "param_hash",
                "tag",
                "status",
                "critical_path_ns",
                "params_json",
                "result_path",
                "work_result_json",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "param_hash": "abcd1234",
                "tag": "base",
                "status": "ok",
                "critical_path_ns": "23.8349",
                "params_json": '{"place_density": 0.3}',
                "result_path": str(finish_report),
                "work_result_json": "",
            }
        )

    out_path = design_dir / "timing_debug_report.md"
    subprocess.run(
        [
            sys.executable,
            "npu/eval/extract_openroad_timing_summary.py",
            "--design-dir",
            str(design_dir),
            "--out",
            str(out_path),
            "--max-paths",
            "4",
        ],
        check=True,
    )

    report = out_path.read_text(encoding="utf-8")
    assert "raw_path_block_count: 2" in report
    assert "unique_path_block_count: 2" in report
    assert "preferred_stage: `route`" in report
    assert "stream_buf_reg[0]" in report
    assert "softmax_unit/sum_reg[7]" in report
    assert "-3.8349" in report
    assert "Worst Timing Paths Across All Stages" in report
    assert report.index("stream_buf_reg[0]") < report.index("seed_state[0]")
    assert "This section must not be included" not in report
