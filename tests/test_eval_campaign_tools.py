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
