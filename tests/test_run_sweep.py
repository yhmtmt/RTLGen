import importlib.util
import json
from pathlib import Path


def _load_run_sweep():
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_sweep.py"
    spec = importlib.util.spec_from_file_location("run_sweep_under_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_explicit_flow_variant_selects_orfs_output_directory(tmp_path, monkeypatch):
    run_sweep = _load_run_sweep()
    monkeypatch.setattr(run_sweep, "REPORT_BASE", tmp_path / "reports")
    monkeypatch.setattr(run_sweep, "RESULT_BASE", tmp_path / "results")

    flow_variant = run_sweep.isolated_flow_variant(
        {"FLOW_VARIANT": "router_component_r5"},
        "deadbeef",
    )
    finish, final_def = run_sweep.resolve_flow_output_paths(
        platform="nangate45",
        wrapper="router_wrapper",
        flow_variant=flow_variant,
    )

    assert finish == tmp_path / "reports/nangate45/router_wrapper/router_component_r5__deadbeef/6_finish.rpt"
    assert final_def == tmp_path / "results/nangate45/router_wrapper/router_component_r5__deadbeef/6_final.def"


def test_default_flow_variant_is_also_isolated_per_parameter_hash():
    run_sweep = _load_run_sweep()

    assert run_sweep.isolated_flow_variant({}, "0123abcd") == "sweep__0123abcd"


def test_successful_command_without_ppa_is_not_recorded_as_ok(tmp_path, monkeypatch):
    run_sweep = _load_run_sweep()
    config = tmp_path / "router.json"
    config.write_text(
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
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "config.mk").write_text("DESIGN_NAME = router_wrapper\n", encoding="utf-8")
    monkeypatch.setattr(run_sweep, "REPORT_BASE", tmp_path / "reports")
    monkeypatch.setattr(run_sweep, "RESULT_BASE", tmp_path / "results")
    monkeypatch.setattr(run_sweep, "ensure_design_assets", lambda *args, **kwargs: generated)
    monkeypatch.setattr(run_sweep, "snapshot_artifacts", lambda *args, **kwargs: None)
    commands = []
    monkeypatch.setattr(run_sweep.subprocess, "run", lambda command, **kwargs: commands.append(command))

    params = {"CLOCK_PERIOD": 1.0, "FLOW_VARIANT": "router_component_r5"}
    out_root = tmp_path / "runs"
    run_sweep.run_single(config, "nangate45", params, out_root, False, False)

    run_id = run_sweep.make_run_id(params)
    result = json.loads((out_root / f"router_wrapper/work/{run_id}/result.json").read_text(encoding="utf-8"))
    assert result["status"] == "metrics_missing"
    assert result["missing_metrics"] == ["critical_path_ns", "die_area", "total_power_mw"]
    assert result["effective_flow_variant"] == f"router_component_r5__{run_id}"
    assert result["reports"]["finish"].endswith(f"router_component_r5__{run_id}/6_finish.rpt")
    assert f"FLOW_VARIANT=router_component_r5__{run_id}" in commands[0]
