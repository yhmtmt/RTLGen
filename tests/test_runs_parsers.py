#!/usr/bin/env python3
"""Regression tests for runs metrics parsing in validation/index scripts."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HEADER = (
    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,"
    "die_area,total_power_mw,params_json,result_path"
)


def load_script_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunsParserRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validate_runs = load_script_module(
            "validate_runs", "scripts/validate_runs.py"
        )
        cls.build_runs_index = load_script_module(
            "build_runs_index", "scripts/build_runs_index.py"
        )
        cls.run_sweep = load_script_module(
            "run_sweep", "scripts/run_sweep.py"
        )

    def _write_metrics_csv(self, rows):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "metrics.csv"
        body = "\n".join([HEADER, *rows]) + "\n"
        path.write_text(body, encoding="utf-8")
        return path

    def _assert_parseable_params(self, row):
        params = json.loads(row["params_json"])
        self.assertIsInstance(params, dict)
        self.assertIn("CLOCK_PERIOD", params)
        self.assertTrue(str(row["result_path"]).strip())

    def _set_validate_runs_paths(self, root: Path):
        old = (
            self.validate_runs.REPO_ROOT,
            self.validate_runs.DESIGNS_ROOT,
            self.validate_runs.INDEX_PATH,
            self.validate_runs.CANDIDATES_ROOT,
            self.validate_runs.EVAL_QUEUE_ROOT,
        )
        self.validate_runs.REPO_ROOT = root
        self.validate_runs.DESIGNS_ROOT = root / "runs" / "designs"
        self.validate_runs.INDEX_PATH = root / "runs" / "index.csv"
        self.validate_runs.CANDIDATES_ROOT = root / "runs" / "candidates"
        self.validate_runs.EVAL_QUEUE_ROOT = root / "runs" / "eval_queue"
        return old

    def _restore_validate_runs_paths(self, old):
        (
            self.validate_runs.REPO_ROOT,
            self.validate_runs.DESIGNS_ROOT,
            self.validate_runs.INDEX_PATH,
            self.validate_runs.CANDIDATES_ROOT,
            self.validate_runs.EVAL_QUEUE_ROOT,
        ) = old

    def test_validate_runs_parses_unquoted_and_csv_quoted_params_json(self):
        legacy_row = (
            "adder_koggestone_64u_wrapper,nangate45,7a7b72571aac,ef9c722d,"
            "prefix_adders_nangate45_40523b9d,ok,0.2507,17669.055625,0.00112,"
            '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, '
            '"TAG": "prefix_adders_nangate45_40523b9d"},'
            "/workspaces/RTLGen/runs/designs/prefix_adders/adder_koggestone_64u_wrapper/"
            "work/ef9c722d/result.json"
        )
        quoted_row = (
            "npu_fp16_cpp_hiercmp,nangate45,e94cab253974,77d647dd,"
            "npu_fp16_hiercmp_cmp_33_flat_nomacro,ok,5.701286780426342,2250000.0,0.210414,"
            '"{""CLOCK_PERIOD"": 10.0, ""CORE_AREA"": ""50 50 1450 1450"", '
            '""CORE_UTILIZATION"": """", ""DIE_AREA"": ""0 0 1500 1500"", '
            '""FLOW_VARIANT"": ""cmp33_flat_nomacro"", ""PLACE_DENSITY"": 0.4, '
            '""SYNTH_HIERARCHICAL"": 0, ""SYNTH_KEEP_MODULES"": """", '
            '""TAG"": ""npu_fp16_hiercmp_cmp_33_flat_nomacro"", '
            '""tag_prefix"": ""npu_fp16_hiercmp""}",'
            "/orfs/flow/logs/nangate45/npu_fp16_cpp_hiercmp/cmp33_flat_nomacro/3_3_place_gp.json"
        )
        metrics_path = self._write_metrics_csv([legacy_row, quoted_row])

        fields, rows = self.validate_runs.read_metrics_csv(metrics_path)
        self.assertEqual(2, len(rows))
        self.assertIn("params_json", fields)
        self.assertIn("result_path", fields)
        for row in rows:
            self._assert_parseable_params(row)

    def test_build_runs_index_parses_unquoted_and_csv_quoted_params_json(self):
        legacy_row = (
            "adder_brentkung_16u_wrapper,asap7,727a973b283c,67898f3f,"
            "prefix_adders_asap7_relaxed_a96d1e8e,ok,0.4418263,344.510721,0.000133,"
            '{"CLOCK_PERIOD": 1.0, "CORE_UTILIZATION": 8, "PLACE_DENSITY": 0.5, '
            '"TAG": "prefix_adders_asap7_relaxed_a96d1e8e"},'
            "runs/designs/prefix_adders/adder_brentkung_16u_wrapper/work/67898f3f/result.json"
        )
        quoted_row = (
            "npu_fp16_cpp_l1,nangate45,8e017cf47c46,5d34f219,npu_fp16_5d34f219,ok,"
            "5.6462,2250000.0,0.229,"
            '"{""CLOCK_PERIOD"": 10.0, ""CORE_AREA"": ""50 50 1450 1450"", '
            '""CORE_UTILIZATION"": """", ""DIE_AREA"": ""0 0 1500 1500"", '
            '""PLACE_DENSITY"": 0.4, ""tag_prefix"": ""npu_fp16""}",'
            "/orfs/flow/reports/nangate45/npu_fp16_cpp_l1/base/6_finish.rpt"
        )
        metrics_path = self._write_metrics_csv([legacy_row, quoted_row])

        rows = self.build_runs_index.load_metrics(metrics_path)
        self.assertEqual(2, len(rows))
        for row in rows:
            self._assert_parseable_params(row)

    def test_run_sweep_normalizes_repo_relative_paths(self):
        repo_root = self.run_sweep.REPO_ROOT
        abs_result = str(repo_root / "runs" / "designs" / "activations" / "demo" / "work" / "abcd1234" / "result.json")
        abs_config = str(repo_root / "examples" / "config_demo.json")

        self.assertEqual(
            "runs/designs/activations/demo/work/abcd1234/result.json",
            self.run_sweep.normalize_repo_path(abs_result),
        )
        self.assertEqual(
            "examples/config_demo.json",
            self.run_sweep.normalize_repo_path(abs_config),
        )

    def test_run_sweep_append_index_rewrites_absolute_result_path(self):
        with tempfile.TemporaryDirectory() as td:
            circuit_root = Path(td) / "runs" / "designs" / "activations" / "demo_wrapper"
            circuit_root.mkdir(parents=True, exist_ok=True)
            result_path = self.run_sweep.REPO_ROOT / "runs" / "designs" / "activations" / "demo_wrapper" / "work" / "abcd1234" / "result.json"
            record = {
                "design": "demo_wrapper",
                "platform": "nangate45",
                "config_hash": "cfg123",
                "param_hash": "abcd1234",
                "tag": "demo_tag",
                "status": "ok",
                "metrics": {
                    "critical_path_ns": 1.25,
                    "die_area": 1000.0,
                    "total_power_mw": 0.01,
                },
                "flow_params": {"CLOCK_PERIOD": 6.0, "TAG": "demo_tag"},
                "result_path": str(result_path),
            }

            self.run_sweep.append_index(circuit_root, record)
            lines = (circuit_root / "metrics.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            self.assertTrue(lines[1].endswith("runs/designs/activations/demo_wrapper/work/abcd1234/result.json"))

    def test_validate_runs_module_candidates_manifest_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metrics_path = root / "runs/designs/multipliers/demo_mul/metrics.csv"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                "\n".join(
                    [
                        HEADER,
                        "demo_mul,nangate45,cfg123,ph123,tag123,ok,1.25,1000.0,0.01,"
                        '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, "TAG": "tag123"},'
                        "runs/designs/multipliers/demo_mul/work/ph123/result.json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            cand_path = root / "runs/candidates/nangate45/module_candidates.json"
            cand_path.parent.mkdir(parents=True, exist_ok=True)
            cand_doc = {
                "version": 0.1,
                "pdk": "nangate45",
                "candidates": [
                    {
                        "variant_id": "demo_mul_nangate45_base",
                        "module": "demo_mul",
                        "evaluation_scope": "wrapped_io",
                        "circuit_type": "multipliers",
                        "config_hash": "cfg123",
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/multipliers/demo_mul/metrics.csv",
                            "platform": "nangate45",
                            "param_hash": "ph123",
                            "tag": "tag123",
                            "status": "ok",
                        },
                    }
                ],
            }
            cand_path.write_text(json.dumps(cand_doc, indent=2) + "\n", encoding="utf-8")

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_module_candidates()
            finally:
                self._restore_validate_runs_paths(old)
            self.assertEqual([], errors)

    def test_validate_runs_module_candidates_manifest_bad_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metrics_path = root / "runs/designs/multipliers/demo_mul/metrics.csv"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                "\n".join(
                    [
                        HEADER,
                        "demo_mul,nangate45,cfg123,ph123,tag123,ok,1.25,1000.0,0.01,"
                        '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, "TAG": "tag123"},'
                        "runs/designs/multipliers/demo_mul/work/ph123/result.json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            cand_path = root / "runs/candidates/nangate45/module_candidates.json"
            cand_path.parent.mkdir(parents=True, exist_ok=True)
            cand_doc = {
                "version": 0.1,
                "pdk": "nangate45",
                "candidates": [
                    {
                        "variant_id": "demo_mul_nangate45_bad",
                        "module": "demo_mul",
                        "evaluation_scope": "wrapped_io",
                        "circuit_type": "multipliers",
                        "config_hash": "cfg123",
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/multipliers/demo_mul/metrics.csv",
                            "platform": "nangate45",
                            "param_hash": "ph999",
                            "status": "ok",
                        },
                    }
                ],
            }
            cand_path.write_text(json.dumps(cand_doc, indent=2) + "\n", encoding="utf-8")

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_module_candidates()
            finally:
                self._restore_validate_runs_paths(old)

            self.assertTrue(any("no matching metrics row found" in e for e in errors))

    def test_validate_runs_module_candidates_macro_hardened_requires_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            metrics_path = root / "runs/designs/multipliers/demo_mul/metrics.csv"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                "\n".join(
                    [
                        HEADER,
                        "demo_mul,nangate45,cfg123,ph123,tag123,ok,1.25,1000.0,0.01,"
                        '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, "TAG": "tag123"},'
                        "runs/designs/multipliers/demo_mul/work/ph123/result.json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            cand_path = root / "runs/candidates/nangate45/module_candidates.json"
            cand_path.parent.mkdir(parents=True, exist_ok=True)
            cand_doc = {
                "version": 0.1,
                "pdk": "nangate45",
                "candidates": [
                    {
                        "variant_id": "demo_mul_nangate45_macro",
                        "module": "demo_mul",
                        "evaluation_scope": "macro_hardened",
                        "circuit_type": "multipliers",
                        "config_hash": "cfg123",
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/multipliers/demo_mul/metrics.csv",
                            "platform": "nangate45",
                            "param_hash": "ph123",
                            "tag": "tag123",
                            "status": "ok",
                        },
                    }
                ],
            }
            cand_path.write_text(json.dumps(cand_doc, indent=2) + "\n", encoding="utf-8")

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_module_candidates()
            finally:
                self._restore_validate_runs_paths(old)

            self.assertTrue(any("macro_hardened candidate requires non-empty macro_manifest" in e for e in errors))

    def test_validate_runs_eval_queue_queued_item_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "runs/designs/multipliers/demo_mul/config_demo.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text("{\"version\": 0.1}\n", encoding="utf-8")

            queue_dir = root / "runs/eval_queue/openroad/queued"
            queue_dir.mkdir(parents=True, exist_ok=True)
            (root / "runs/eval_queue/openroad/item.schema.json").write_text("{}", encoding="utf-8")
            item = {
                "version": 0.1,
                "item_id": "demo_queue_item_v1",
                "title": "Demo queue item",
                "layer": "layer1",
                "flow": "openroad",
                "state": "queued",
                "priority": 1,
                "created_utc": "2026-03-04T00:00:00Z",
                "requested_by": "@tester",
                "platform": "nangate45",
                "task": {
                    "objective": "Run one demo command",
                    "source_mode": "config",
                    "inputs": {
                        "configs": ["runs/designs/multipliers/demo_mul/config_demo.json"],
                        "design_dirs": [],
                        "sweeps": [],
                        "macro_manifests": [],
                        "candidate_manifests": [],
                    },
                    "commands": [
                        {
                            "name": "run_demo",
                            "run": "python3 scripts/run_sweep.py --configs <...>",
                        }
                    ],
                    "expected_outputs": ["runs/designs/multipliers/demo_mul/metrics.csv"],
                    "acceptance": ["metrics row appended"],
                },
                "handoff": {
                    "branch": "eval/demo_queue_item_v1/<session_id>",
                    "pr_title": "eval: demo queue item",
                    "identity_block_format": "[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]",
                    "pr_body_fields": {
                        "evaluator_id": "<evaluator_id>",
                        "session_id": "<session_id>",
                        "host": "<host>",
                        "queue_item_id": "demo_queue_item_v1",
                    },
                    "checklist": ["run python3 scripts/validate_runs.py"],
                },
                "result": None,
            }
            (queue_dir / "demo_queue_item_v1.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_eval_queue()
            finally:
                self._restore_validate_runs_paths(old)
            self.assertEqual([], errors)

    def test_validate_runs_eval_queue_evaluated_item_requires_matching_metrics_row(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "runs/designs/multipliers/demo_mul/config_demo.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text("{\"version\": 0.1}\n", encoding="utf-8")
            metrics_path = root / "runs/designs/multipliers/demo_mul/metrics.csv"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                "\n".join(
                    [
                        HEADER,
                        "demo_mul,nangate45,cfg123,ph123,tag123,ok,1.25,1000.0,0.01,"
                        '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, "TAG": "tag123"},'
                        "runs/designs/multipliers/demo_mul/work/ph123/result.json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            queue_dir = root / "runs/eval_queue/openroad/evaluated"
            queue_dir.mkdir(parents=True, exist_ok=True)
            (root / "runs/eval_queue/openroad/item.schema.json").write_text("{}", encoding="utf-8")
            item = {
                "version": 0.1,
                "item_id": "demo_evaluated_item_v1",
                "title": "Demo evaluated queue item",
                "layer": "layer1",
                "flow": "openroad",
                "state": "evaluated",
                "priority": 1,
                "created_utc": "2026-03-04T00:00:00Z",
                "requested_by": "@tester",
                "platform": "nangate45",
                "task": {
                    "objective": "Verify evaluated payload checks metrics traceability",
                    "source_mode": "config",
                    "inputs": {
                        "configs": ["runs/designs/multipliers/demo_mul/config_demo.json"],
                        "design_dirs": [],
                        "sweeps": [],
                        "macro_manifests": [],
                        "candidate_manifests": [],
                    },
                    "commands": [{"name": "noop", "run": "true"}],
                    "expected_outputs": ["runs/designs/multipliers/demo_mul/metrics.csv"],
                },
                "handoff": {
                    "branch": "eval/demo_evaluated_item_v1/<session_id>",
                    "pr_title": "eval: demo evaluated item",
                    "identity_block_format": "[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]",
                    "pr_body_fields": {
                        "evaluator_id": "tester",
                        "session_id": "s20260305t000000z",
                        "host": "test-host",
                        "queue_item_id": "demo_evaluated_item_v1",
                    },
                    "checklist": ["run python3 scripts/validate_runs.py"],
                },
                "result": {
                    "completed_utc": "2026-03-04T01:00:00Z",
                    "executor": "@evaluator",
                    "branch": "eval/demo_evaluated_item_v1/s20260305t000000z",
                    "evaluator_id": "tester",
                    "session_id": "s20260305t000000z",
                    "host": "test-host",
                    "queue_item_id": "demo_evaluated_item_v1",
                    "identity_block": "[role:evaluator][account:tester][session:s20260305t000000z][host:test-host][item:demo_evaluated_item_v1]",
                    "status": "ok",
                    "summary": "done",
                    "metrics_rows": [
                        {
                            "metrics_csv": "runs/designs/multipliers/demo_mul/metrics.csv",
                            "platform": "nangate45",
                            "param_hash": "ph999",
                            "status": "ok",
                        }
                    ],
                },
            }
            (queue_dir / "demo_evaluated_item_v1.json").write_text(
                json.dumps(item, indent=2) + "\n", encoding="utf-8"
            )

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_eval_queue()
            finally:
                self._restore_validate_runs_paths(old)
            self.assertTrue(any("no matching metrics row found" in e for e in errors))

    def test_validate_runs_eval_queue_rejects_wrapper_module_in_config_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "runs/designs/multipliers/demo_mul/config_demo.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text("{\"version\": 0.1}\n", encoding="utf-8")

            queue_dir = root / "runs/eval_queue/openroad/queued"
            queue_dir.mkdir(parents=True, exist_ok=True)
            (root / "runs/eval_queue/openroad/item.schema.json").write_text("{}", encoding="utf-8")
            item = {
                "version": 0.1,
                "item_id": "demo_queue_bad_wrapper_mode_v1",
                "title": "Demo bad queue item",
                "layer": "layer1",
                "flow": "openroad",
                "state": "queued",
                "priority": 1,
                "created_utc": "2026-03-04T00:00:00Z",
                "requested_by": "@tester",
                "platform": "nangate45",
                "task": {
                    "objective": "Detect wrapper mismatch with source_mode=config",
                    "source_mode": "config",
                    "inputs": {
                        "configs": ["runs/designs/multipliers/demo_mul/config_demo.json"],
                        "design_dirs": [],
                        "sweeps": [],
                        "macro_manifests": [],
                        "candidate_manifests": [],
                    },
                    "commands": [
                        {
                            "name": "bad_harden",
                            "run": (
                                "python3 npu/synth/pre_synth_compute.py "
                                "--platform nangate45 "
                                "--config runs/designs/multipliers/demo_mul/config_demo.json "
                                "--module demo_mul_wrapper"
                            ),
                        }
                    ],
                    "expected_outputs": ["runs/designs/npu_macros/demo_mul_wrapper/macro_manifest.json"],
                },
                "handoff": {
                    "branch": "eval/demo_queue_bad_wrapper_mode_v1/<session_id>",
                    "pr_title": "eval: demo bad queue item",
                    "identity_block_format": "[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]",
                    "pr_body_fields": {
                        "evaluator_id": "<evaluator_id>",
                        "session_id": "<session_id>",
                        "host": "<host>",
                        "queue_item_id": "demo_queue_bad_wrapper_mode_v1",
                    },
                    "checklist": ["run python3 scripts/validate_runs.py"],
                },
                "result": None,
            }
            (queue_dir / "demo_queue_bad_wrapper_mode_v1.json").write_text(
                json.dumps(item, indent=2) + "\n", encoding="utf-8"
            )

            old = self._set_validate_runs_paths(root)
            try:
                errors = self.validate_runs.validate_eval_queue()
            finally:
                self._restore_validate_runs_paths(old)
            self.assertTrue(any("use source_mode=src_verilog with --src_verilog_dir" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
