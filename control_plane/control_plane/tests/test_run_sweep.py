"""Coverage for the standalone OpenROAD sweep runner."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


def _load_run_sweep_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "run_sweep.py"
    spec = importlib.util.spec_from_file_location("rtlgen_run_sweep", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_failed_run_does_not_parse_stale_base_reports(tmp_path: Path, monkeypatch) -> None:
    run_sweep = _load_run_sweep_module()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": "1.1",
                "operands": [{"name": "logits", "dimensions": 1, "bit_width": 16, "signed": True, "kind": "int"}],
                "operations": [
                    {
                        "type": "logit_rank",
                        "module_name": "logit_rank_r64_l16_k1",
                        "operand": "logits",
                        "options": {"row_elems": 64, "logit_bits": 16, "top_k": 1, "logit_signed": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    wrapper = "logit_rank_r64_l16_k1_wrapper"
    report_base = tmp_path / "orfs" / "reports"
    result_base = tmp_path / "orfs" / "results"
    stale_report = report_base / "nangate45" / wrapper / "base" / "6_finish.rpt"
    stale_def = result_base / "nangate45" / wrapper / "base" / "6_final.def"
    stale_report.parent.mkdir(parents=True)
    stale_def.parent.mkdir(parents=True)
    stale_report.write_text("stale report that must not be parsed\n", encoding="utf-8")
    stale_def.write_text("UNITS DISTANCE MICRONS 1000 ;\nDIEAREA ( 0 0 ) ( 1000 1000 ) ;\n", encoding="utf-8")

    monkeypatch.setattr(run_sweep, "REPORT_BASE", report_base)
    monkeypatch.setattr(run_sweep, "RESULT_BASE", result_base)
    monkeypatch.setattr(run_sweep, "ensure_design_assets", lambda *_args, **_kwargs: tmp_path / "config.mk")
    monkeypatch.setattr(run_sweep, "snapshot_artifacts", lambda *_args, **_kwargs: None)

    def fail_make(*_args, **_kwargs):
        raise subprocess.CalledProcessError(2, "make")

    monkeypatch.setattr(run_sweep.subprocess, "run", fail_make)

    run_sweep.run_single(
        config_path=config_path,
        platform="nangate45",
        flow_params={"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 60, "TAG": "macro_pin_failed"},
        out_root=tmp_path / "runs",
        skip_existing=False,
        dry_run=False,
    )

    result_path = tmp_path / "runs" / wrapper / "work" / run_sweep.make_run_id({"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 60, "TAG": "macro_pin_failed"}) / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["metrics"] == {}
    assert result["reports"]["finish"].endswith("macro_pin_failed/6_finish.rpt")
