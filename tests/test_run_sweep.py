import importlib.util
import csv
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
    monkeypatch.setattr(run_sweep, "current_repo_head", lambda: "source123")
    monkeypatch.setattr(run_sweep, "current_repo_is_clean", lambda: True)
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


def test_cached_result_requires_complete_identity_and_retained_reports(tmp_path, monkeypatch):
    run_sweep = _load_run_sweep()
    monkeypatch.setattr(run_sweep, "REPORT_BASE", tmp_path / "reports")
    monkeypatch.setattr(run_sweep, "RESULT_BASE", tmp_path / "results")
    params = {"CLOCK_PERIOD": 2.0, "FLOW_VARIANT": "mesh_r2"}
    run_id = run_sweep.make_run_id(params)
    variant = run_sweep.isolated_flow_variant(params, run_id)
    finish, final_def = run_sweep.resolve_flow_output_paths(
        platform="nangate45",
        wrapper="mesh_wrapper",
        flow_variant=variant,
    )
    result_path = tmp_path / "result.json"
    record = {
        "design": "mesh_wrapper",
        "platform": "nangate45",
        "config_hash": "config123",
        "param_hash": run_id,
        "flow_params": params,
        "effective_flow_variant": variant,
        "repo_head_sha": "source123",
        "repo_clean": True,
        "status": "dry_run",
        "metrics": {},
        "reports": {"finish": str(finish), "def": str(final_def)},
    }
    result_path.write_text(json.dumps(record), encoding="utf-8")

    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="source123",
        repo_clean=True,
    )
    assert not reusable
    assert "dry_run" in reason

    record["status"] = "ok"
    record["metrics"] = {
        "critical_path_ns": 1.5,
        "die_area": 100.0,
        "total_power_mw": 2.0,
    }
    result_path.write_text(json.dumps(record), encoding="utf-8")
    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="source123",
        repo_clean=True,
    )
    assert not reusable
    assert "not retained" in reason

    finish.parent.mkdir(parents=True)
    final_def.parent.mkdir(parents=True)
    finish.write_text("finish", encoding="utf-8")
    final_def.write_text("def", encoding="utf-8")
    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="source123",
        repo_clean=True,
    )
    assert reusable
    assert "identity-matched" in reason

    record["repo_head_sha"] = "older-source"
    result_path.write_text(json.dumps(record), encoding="utf-8")
    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="source123",
        repo_clean=True,
    )
    assert not reusable
    assert "repo_head_sha" in reason

    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="",
        repo_clean=True,
    )
    assert not reusable
    assert "source identity" in reason

    reusable, reason = run_sweep.reusable_result(
        result_path,
        design="mesh_wrapper",
        platform="nangate45",
        config_hash="config123",
        param_hash=run_id,
        flow_params=params,
        effective_flow_variant=variant,
        repo_head_sha="source123",
        repo_clean=False,
    )
    assert not reusable
    assert "tracked source modifications" in reason


def test_append_index_replaces_same_parameter_row(tmp_path):
    run_sweep = _load_run_sweep()
    circuit_root = tmp_path / "mesh"
    circuit_root.mkdir()
    base = {
        "design": "mesh",
        "platform": "nangate45",
        "config_hash": "config123",
        "param_hash": "point123",
        "tag": "mesh_point",
        "flow_params": {"CLOCK_PERIOD": 2.0},
        "result_path": "runs/mesh/work/point123/result.json",
    }
    run_sweep.append_index(circuit_root, {**base, "status": "dry_run", "metrics": {}})
    run_sweep.append_index(
        circuit_root,
        {
            **base,
            "status": "ok",
            "metrics": {
                "critical_path_ns": 1.5,
                "die_area": 100.0,
                "total_power_mw": 2.0,
            },
        },
    )

    with (circuit_root / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["param_hash"] == "point123"
    assert rows[0]["status"] == "ok"


def test_append_index_preserves_same_param_hash_for_other_identity(tmp_path):
    run_sweep = _load_run_sweep()
    circuit_root = tmp_path / "mesh"
    circuit_root.mkdir()
    for platform, config_hash in (
        ("nangate45", "config123"),
        ("asap7", "config123"),
        ("nangate45", "config456"),
    ):
        run_sweep.append_index(
            circuit_root,
            {
                "design": "mesh",
                "platform": platform,
                "config_hash": config_hash,
                "param_hash": "point123",
                "tag": f"{platform}_{config_hash}",
                "status": "ok",
                "metrics": {
                    "critical_path_ns": 1.5,
                    "die_area": 100.0,
                    "total_power_mw": 2.0,
                },
                "flow_params": {"CLOCK_PERIOD": 2.0},
                "result_path": f"runs/{platform}/{config_hash}/result.json",
            },
        )

    with (circuit_root / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert {(row["platform"], row["config_hash"]) for row in rows} == {
        ("nangate45", "config123"),
        ("asap7", "config123"),
        ("nangate45", "config456"),
    }


def test_append_index_repairs_unquoted_legacy_params_json(tmp_path):
    run_sweep = _load_run_sweep()
    circuit_root = tmp_path / "mesh"
    circuit_root.mkdir()
    metrics_path = circuit_root / "metrics.csv"
    metrics_path.write_text(
        "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,"
        "total_power_mw,params_json,result_path\n"
        "other,nangate45,oldconfig,oldpoint,old,ok,1.0,10.0,1.0,"
        "{\"CLOCK_PERIOD\": 1.0, \"PLACE_DENSITY\": 0.5},runs/old/result.json\n",
        encoding="utf-8",
    )
    run_sweep.append_index(
        circuit_root,
        {
            "design": "mesh",
            "platform": "nangate45",
            "config_hash": "newconfig",
            "param_hash": "newpoint",
            "tag": "new",
            "status": "ok",
            "metrics": {
                "critical_path_ns": 1.5,
                "die_area": 100.0,
                "total_power_mw": 2.0,
            },
            "flow_params": {"CLOCK_PERIOD": 2.0},
            "result_path": "runs/new/result.json",
        },
    )

    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert json.loads(rows[0]["params_json"]) == {
        "CLOCK_PERIOD": 1.0,
        "PLACE_DENSITY": 0.5,
    }
    assert rows[0]["result_path"] == "runs/old/result.json"


def test_reusable_cache_rebuilds_missing_metrics_index(tmp_path, monkeypatch):
    run_sweep = _load_run_sweep()
    config = tmp_path / "mesh.json"
    config.write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "type": "l1_memory_noc_primitive",
                        "module_name": "mesh",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(run_sweep, "REPORT_BASE", tmp_path / "reports")
    monkeypatch.setattr(run_sweep, "RESULT_BASE", tmp_path / "results")
    monkeypatch.setattr(run_sweep, "current_repo_head", lambda: "source123")
    monkeypatch.setattr(run_sweep, "current_repo_is_clean", lambda: True)
    monkeypatch.setattr(
        run_sweep.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("OpenROAD must be skipped")),
    )

    params = {"CLOCK_PERIOD": 2.0, "FLOW_VARIANT": "mesh_r2"}
    run_id = run_sweep.make_run_id(params)
    variant = run_sweep.isolated_flow_variant(params, run_id)
    finish, final_def = run_sweep.resolve_flow_output_paths(
        platform="nangate45",
        wrapper="mesh_wrapper",
        flow_variant=variant,
    )
    finish.parent.mkdir(parents=True)
    final_def.parent.mkdir(parents=True)
    finish.write_text("finish", encoding="utf-8")
    final_def.write_text("def", encoding="utf-8")

    circuit_root = tmp_path / "runs/mesh_wrapper"
    result_path = circuit_root / f"work/{run_id}/result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "design": "mesh_wrapper",
                "platform": "nangate45",
                "config_hash": run_sweep.sha1_file(config)[:12],
                "param_hash": run_id,
                "tag": "mesh_point",
                "flow_params": params,
                "effective_flow_variant": variant,
                "repo_head_sha": "source123",
                "repo_clean": True,
                "status": "ok",
                "metrics": {
                    "critical_path_ns": 1.5,
                    "die_area": 100.0,
                    "total_power_mw": 2.0,
                },
                "reports": {"finish": str(finish), "def": str(final_def)},
                "result_path": str(result_path),
            }
        ),
        encoding="utf-8",
    )

    run_sweep.run_single(config, "nangate45", params, tmp_path / "runs", True, False)

    with (circuit_root / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["status"] == "ok"
    assert rows[0]["param_hash"] == run_id


def test_ineligible_cache_forces_design_asset_refresh(tmp_path, monkeypatch):
    run_sweep = _load_run_sweep()
    config = tmp_path / "mesh.json"
    config.write_text(
        json.dumps(
            {
                "operations": [
                    {
                        "type": "l1_memory_noc_primitive",
                        "module_name": "mesh",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "config.mk").write_text("DESIGN_NAME = mesh_wrapper\n", encoding="utf-8")
    monkeypatch.setattr(run_sweep, "current_repo_head", lambda: "source123")
    monkeypatch.setattr(run_sweep, "current_repo_is_clean", lambda: True)
    force_values = []

    def ensure_assets(*args, **kwargs):
        force_values.append(kwargs["force"])
        return generated

    monkeypatch.setattr(run_sweep, "ensure_design_assets", ensure_assets)
    monkeypatch.setattr(run_sweep, "snapshot_artifacts", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_sweep.subprocess, "run", lambda *args, **kwargs: None)
    params = {"CLOCK_PERIOD": 2.0, "FLOW_VARIANT": "mesh_r2"}
    run_id = run_sweep.make_run_id(params)
    result_path = tmp_path / f"runs/mesh_wrapper/work/{run_id}/result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"status": "dry_run"}', encoding="utf-8")

    run_sweep.run_single(config, "nangate45", params, tmp_path / "runs", True, False)

    assert force_values == [True]
