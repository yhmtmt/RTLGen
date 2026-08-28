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


def test_load_sweep_param_sets_keeps_floorplan_bounds_paired() -> None:
    run_sweep = _load_run_sweep_module()

    combos = run_sweep.load_sweep_param_sets(
        {
            "flow_param_sets": [
                {
                    "CLOCK_PERIOD": 2.5,
                    "DIE_AREA": "0 0 581 581",
                    "CORE_AREA": "20 20 561 561",
                },
                {
                    "CLOCK_PERIOD": 2.5,
                    "DIE_AREA": "0 0 640 640",
                    "CORE_AREA": "20 20 620 620",
                },
            ]
        }
    )

    assert combos == [
        {
            "CLOCK_PERIOD": 2.5,
            "DIE_AREA": "0 0 581 581",
            "CORE_AREA": "20 20 561 561",
        },
        {
            "CLOCK_PERIOD": 2.5,
            "DIE_AREA": "0 0 640 640",
            "CORE_AREA": "20 20 620 620",
        },
    ]


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
    monkeypatch.setattr(run_sweep, "LOG_BASE", tmp_path / "orfs" / "logs")
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
    assert result["reports"]["finish"].endswith(
        f"sweep__{result['param_hash']}/6_finish.rpt"
    )
    assert result["make_returncode"] == 2
    assert result["failure_evidence"]["log_dir_exists"] is False


def test_failed_run_retains_bounded_orfs_log_tail(tmp_path: Path, monkeypatch) -> None:
    run_sweep = _load_run_sweep_module()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "type": "l1_memory_noc_primitive",
                        "module_name": "router",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    wrapper = "router_wrapper"
    logs = tmp_path / "orfs" / "logs"
    results = tmp_path / "orfs" / "results"
    reports = tmp_path / "orfs" / "reports"
    params = {"CLOCK_PERIOD": 1.8, "FLOW_VARIANT": "router_diag"}
    run_id = run_sweep.make_run_id(params)
    variant = run_sweep.isolated_flow_variant(params, run_id)
    log_dir = logs / "nangate45" / wrapper / variant
    result_dir = results / "nangate45" / wrapper / variant
    log_dir.mkdir(parents=True)
    result_dir.mkdir(parents=True)
    (log_dir / "1_1_yosys.log").write_text(
        "\n".join(f"line {index}" for index in range(130)) + "\nERROR: synthesis failed\n",
        encoding="utf-8",
    )
    (result_dir / "1_synth.v").write_text("partial netlist\n", encoding="utf-8")

    monkeypatch.setattr(run_sweep, "LOG_BASE", logs)
    monkeypatch.setattr(run_sweep, "RESULT_BASE", results)
    monkeypatch.setattr(run_sweep, "REPORT_BASE", reports)
    monkeypatch.setattr(
        run_sweep,
        "ensure_design_assets",
        lambda *_args, **_kwargs: tmp_path / "generated",
    )
    monkeypatch.setattr(run_sweep, "snapshot_artifacts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        run_sweep.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            subprocess.CalledProcessError(2, "make")
        ),
    )

    out_root = tmp_path / "runs"
    run_sweep.run_single(config_path, "nangate45", params, out_root, False, False)
    result = json.loads(
        (out_root / wrapper / "work" / run_id / "result.json").read_text(
            encoding="utf-8"
        )
    )
    evidence = result["failure_evidence"]
    assert evidence["log_dir"] == str(log_dir)
    assert evidence["logs"][0]["path"].endswith("1_1_yosys.log")
    assert evidence["logs"][0]["tail"].startswith("line 31")
    assert evidence["logs"][0]["tail"].endswith("ERROR: synthesis failed")
    assert evidence["result_entries"][0]["path"].endswith("1_synth.v")


def test_failure_evidence_error_does_not_mask_make_failure(tmp_path: Path, monkeypatch) -> None:
    run_sweep = _load_run_sweep_module()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "type": "l1_memory_noc_primitive",
                        "module_name": "router",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        run_sweep,
        "ensure_design_assets",
        lambda *_args, **_kwargs: tmp_path / "generated",
    )
    monkeypatch.setattr(run_sweep, "snapshot_artifacts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        run_sweep,
        "collect_flow_failure_evidence",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("diagnostic read failed")),
    )
    monkeypatch.setattr(
        run_sweep.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            subprocess.CalledProcessError(2, "make")
        ),
    )

    params = {"CLOCK_PERIOD": 1.8}
    out_root = tmp_path / "runs"
    run_sweep.run_single(config_path, "nangate45", params, out_root, False, False)
    run_id = run_sweep.make_run_id(params)
    result = json.loads(
        (out_root / "router_wrapper" / "work" / run_id / "result.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] == "failed"
    assert result["make_returncode"] == 2
    assert result["failure_evidence"] == {
        "collection_error": "OSError: diagnostic read failed"
    }
