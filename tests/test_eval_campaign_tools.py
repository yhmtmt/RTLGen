#!/usr/bin/env python3
"""Regression tests for NPU evaluation campaign tooling."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_JSON = REPO_ROOT / "runs/campaigns/npu/e2e_eval_v0/campaign.json"
PROFILES_JSON = REPO_ROOT / "runs/campaigns/npu/e2e_eval_v0/objective_profiles.json"


class EvalCampaignToolsRegressionTest(unittest.TestCase):
    def _write_layer1_guard_case(self, root: Path, *, allow_wrapped_io: bool):
        model_path = root / "models" / "m.onnx"
        arch_path = root / "arch" / "minimal.yml"
        perf_path = root / "perf" / "cfg.json"
        design_dir = root / "designs" / "npu_demo"
        sweep_file = root / "sweeps" / "demo_sweep.json"
        candidates_path = root / "candidates" / "module_candidates.json"

        model_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        perf_path.parent.mkdir(parents=True, exist_ok=True)
        design_dir.mkdir(parents=True, exist_ok=True)
        sweep_file.parent.mkdir(parents=True, exist_ok=True)
        candidates_path.parent.mkdir(parents=True, exist_ok=True)

        model_path.write_text("", encoding="utf-8")
        arch_path.write_text("schema_version: 0.2-draft\n", encoding="utf-8")
        perf_path.write_text("{\"latency_scale\":1.0}\n", encoding="utf-8")
        sweep_file.write_text("{\"points\":[]}\n", encoding="utf-8")

        candidates_doc = {
            "version": 0.1,
            "pdk": "nangate45",
            "candidates": [
                {
                    "variant_id": "demo_wrapped",
                    "module": "demo_mul_wrapper",
                    "evaluation_scope": "wrapped_io",
                    "config_hash": "cfg123",
                    "metrics_ref": {
                        "metrics_csv": "runs/designs/multipliers/mult16u_normal_koggestone_wrapper/metrics.csv",
                        "platform": "nangate45",
                        "param_hash": "231d5c19",
                    },
                }
            ],
        }
        candidates_path.write_text(json.dumps(candidates_doc, indent=2) + "\n", encoding="utf-8")

        layer1_modules = {
            "manifest": str(candidates_path),
            "variant_ids": ["demo_wrapped"],
        }
        if allow_wrapped_io:
            layer1_modules["allow_wrapped_io"] = True

        campaign_doc = {
            "version": 0.1,
            "campaign_id": "guard_case",
            "platform": "nangate45",
            "make_target": "3_3_place_gp",
            "repeats": 1,
            "models": [
                {
                    "model_id": "m0",
                    "onnx_path": str(model_path),
                    "mapper_arch": str(arch_path),
                    "perf_config": str(perf_path),
                }
            ],
            "architecture_points": [
                {
                    "arch_id": "a0",
                    "synth_design_dir": str(design_dir),
                    "sweep_file": str(sweep_file),
                    "layer1_modules": layer1_modules,
                }
            ],
            "outputs": {
                "campaign_dir": str(root / "out"),
                "results_csv": str(root / "out" / "results.csv"),
            },
        }
        campaign_path = root / "campaign.json"
        campaign_path.write_text(json.dumps(campaign_doc, indent=2) + "\n", encoding="utf-8")
        return campaign_path

    def test_validate_campaign_check_paths(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/eval/validate.py"),
            "--campaign",
            str(CAMPAIGN_JSON),
            "--check_paths",
        ]
        subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)

    def test_report_campaign_generates_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            out_md = tmp / "report.md"
            out_csv = tmp / "summary.csv"
            best_json = tmp / "best_point.json"
            pareto_csv = tmp / "pareto.csv"

            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/report_campaign.py"),
                "--campaign",
                str(CAMPAIGN_JSON),
                "--out_md",
                str(out_md),
                "--out_csv",
                str(out_csv),
                "--best_json",
                str(best_json),
                "--pareto_csv",
                str(pareto_csv),
            ]
            subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)

            self.assertTrue(out_md.exists())
            self.assertTrue(out_csv.exists())
            self.assertTrue(best_json.exists())
            self.assertTrue(pareto_csv.exists())

            best = json.loads(best_json.read_text(encoding="utf-8"))
            self.assertEqual("npu_e2e_eval_v0", best.get("campaign_id"))
            self.assertIn("best", best)
            self.assertIn("arch_id", best["best"])
            self.assertIn("macro_mode", best["best"])

            with out_csv.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertGreater(len(rows), 0)
            scopes = {str(r.get("scope", "")).strip() for r in rows}
            self.assertIn("model", scopes)
            self.assertIn("aggregate", scopes)

    def test_run_campaign_dry_run_smoke(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/eval/run_campaign.py"),
            "--campaign",
            str(CAMPAIGN_JSON),
            "--max_models",
            "1",
            "--max_arch",
            "1",
            "--modes",
            "flat_nomacro",
            "--skip_existing",
            "--dry_run",
        ]
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
        self.assertIn("done: campaign_id=", proc.stdout)

    def test_run_campaign_dry_run_parallel_model_jobs(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/eval/run_campaign.py"),
            "--campaign",
            str(CAMPAIGN_JSON),
            "--max_models",
            "2",
            "--max_arch",
            "1",
            "--modes",
            "flat_nomacro",
            "--skip_existing",
            "--jobs",
            "2",
            "--dry_run",
        ]
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
        self.assertIn("parallel model artifact build: jobs=2 models=2", proc.stdout)
        self.assertIn("done: campaign_id=", proc.stdout)

    def test_validate_campaign_rejects_wrapped_layer1_without_override(self):
        with tempfile.TemporaryDirectory() as td:
            campaign_path = self._write_layer1_guard_case(Path(td), allow_wrapped_io=False)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/validate.py"),
                "--campaign",
                str(campaign_path),
                "--check_paths",
            ]
            proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("wrapped_io candidates", proc.stderr)

    def test_validate_campaign_allows_wrapped_layer1_with_override(self):
        with tempfile.TemporaryDirectory() as td:
            campaign_path = self._write_layer1_guard_case(Path(td), allow_wrapped_io=True)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/validate.py"),
                "--campaign",
                str(campaign_path),
                "--check_paths",
            ]
            proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, msg=proc.stderr)
            self.assertIn("OK: campaign", proc.stdout)

    def test_optimize_campaign_generates_profile_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            out_csv = tmp / "objective_sweep.csv"
            out_md = tmp / "objective_sweep.md"
            out_dir = tmp / "objective_profiles"

            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/optimize_campaign.py"),
                "--campaign",
                str(CAMPAIGN_JSON),
                "--profiles_json",
                str(PROFILES_JSON),
                "--out_csv",
                str(out_csv),
                "--out_md",
                str(out_md),
                "--out_dir",
                str(out_dir),
            ]
            subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)

            self.assertTrue(out_csv.exists())
            self.assertTrue(out_md.exists())
            self.assertTrue(out_dir.exists())

            with out_csv.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertGreaterEqual(len(rows), 1)
            required = {"profile", "best_arch_id", "best_macro_mode", "objective_score"}
            for row in rows:
                self.assertTrue(required.issubset(set(row.keys())))
                profile = str(row.get("profile", "")).strip()
                self.assertTrue(profile)
                self.assertTrue((out_dir / profile / "best_point.json").exists())
                self.assertTrue((out_dir / profile / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
