#!/usr/bin/env python3
"""Regression tests for NPU evaluation campaign tooling."""

import csv
import hashlib
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
    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _write_layer1_guard_case(self, root: Path, *, allow_wrapped_io: bool):
        model_path = root / "models" / "m.onnx"
        model_manifest = root / "models" / "manifest.json"
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
        model_sha = self._sha256_file(model_path)
        model_manifest.write_text(
            json.dumps(
                {
                    "version": 0.1,
                    "model_set_id": "guard_models_v0",
                    "models": [
                        {
                            "model_id": "m0",
                            "onnx_path": str(model_path),
                            "onnx_sha256": model_sha,
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

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
            "model_set_id": "guard_models_v0",
            "model_manifest": str(model_manifest),
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

    def _write_external_fetch_case(self, root: Path):
        source_dir = root / "source"
        cache_dir = root / "cache"
        model_manifest = root / "models" / "manifest.json"
        arch_path = root / "arch" / "minimal.yml"
        perf_path = root / "perf" / "cfg.json"
        design_dir = root / "designs" / "npu_demo"
        sweep_file = root / "sweeps" / "demo_sweep.json"

        source_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_manifest.parent.mkdir(parents=True, exist_ok=True)
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        perf_path.parent.mkdir(parents=True, exist_ok=True)
        design_dir.mkdir(parents=True, exist_ok=True)
        sweep_file.parent.mkdir(parents=True, exist_ok=True)

        source_path = source_dir / "remote_m0.onnx"
        source_path.write_bytes(b"external-onnx-payload-v0\n")
        model_sha = self._sha256_file(source_path)
        cached_model_path = cache_dir / "m0.onnx"

        arch_path.write_text("schema_version: 0.2-draft\n", encoding="utf-8")
        perf_path.write_text("{\"latency_scale\":1.0}\n", encoding="utf-8")
        sweep_file.write_text("{\"points\":[]}\n", encoding="utf-8")
        model_manifest.write_text(
            json.dumps(
                {
                    "version": 0.1,
                    "model_set_id": "external_models_v0",
                    "models": [
                        {
                            "model_id": "m0",
                            "onnx_path": str(cached_model_path),
                            "onnx_sha256": model_sha,
                            "fetch": {
                                "url": source_path.as_uri(),
                                "notes": "Local file URI used to emulate evaluator-side external fetch",
                            },
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        campaign_doc = {
            "version": 0.1,
            "campaign_id": "external_fetch_case",
            "model_set_id": "external_models_v0",
            "model_manifest": str(model_manifest),
            "platform": "nangate45",
            "make_target": "3_3_place_gp",
            "repeats": 1,
            "models": [
                {
                    "model_id": "m0",
                    "onnx_path": str(cached_model_path),
                    "mapper_arch": str(arch_path),
                    "perf_config": str(perf_path),
                }
            ],
            "architecture_points": [
                {
                    "arch_id": "a0",
                    "synth_design_dir": str(design_dir),
                    "sweep_file": str(sweep_file),
                }
            ],
            "outputs": {
                "campaign_dir": str(root / "out"),
                "results_csv": str(root / "out" / "results.csv"),
            },
        }
        campaign_path = root / "campaign.json"
        campaign_path.write_text(json.dumps(campaign_doc, indent=2) + "\n", encoding="utf-8")
        return campaign_path, model_manifest, cached_model_path, model_sha

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

    def test_report_campaign_uses_sample_id_for_rerun_statistics(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            results_csv = tmp / "results.csv"
            out_md = tmp / "report.md"
            out_csv = tmp / "summary.csv"
            best_json = tmp / "best_point.json"
            pareto_csv = tmp / "pareto.csv"

            header = [
                "version",
                "campaign_id",
                "run_id",
                "sample_id",
                "batch_id",
                "sample_index",
                "timestamp_utc",
                "status",
                "platform",
                "model_id",
                "arch_id",
                "macro_mode",
                "repeat_index",
                "physical_critical_path_ns",
                "physical_die_area_um2",
                "physical_total_power_mw",
                "physical_flow_elapsed_s",
                "physical_place_gp_elapsed_s",
                "performance_cycles",
                "performance_latency_ms",
                "performance_throughput_infer_per_s",
                "performance_energy_mj",
                "artifact_synth_result_json",
                "artifact_perf_trace_json",
                "artifact_schedule_yml",
                "artifact_descriptors_bin",
                "notes",
            ]

            base = {
                "version": "0.1",
                "campaign_id": "npu_e2e_eval_v0",
                "run_id": "rid0",
                "batch_id": "b0",
                "timestamp_utc": "2026-03-04T00:00:00Z",
                "status": "ok",
                "platform": "nangate45",
                "model_id": "mlp1",
                "arch_id": "fp16_nm1",
                "macro_mode": "flat_nomacro",
                "repeat_index": "1",
                "physical_critical_path_ns": "5.0",
                "physical_die_area_um2": "100.0",
                "physical_total_power_mw": "1.0",
                "physical_flow_elapsed_s": "10.0",
                "physical_place_gp_elapsed_s": "5.0",
                "performance_cycles": "100.0",
                "performance_throughput_infer_per_s": "1000.0",
                "performance_energy_mj": "0.1",
                "artifact_synth_result_json": "",
                "artifact_perf_trace_json": "",
                "artifact_schedule_yml": "",
                "artifact_descriptors_bin": "",
                "notes": "",
            }
            rows = [
                {
                    **base,
                    "sample_id": "rid0__bb0__s1",
                    "sample_index": "1",
                    "performance_latency_ms": "1.0",
                },
                {
                    **base,
                    "sample_id": "rid0__bb0__s2",
                    "sample_index": "2",
                    "performance_latency_ms": "2.0",
                },
                {
                    # Duplicate sample_id: latest row should win (latency 8.0).
                    **base,
                    "sample_id": "rid0__bb0__s2",
                    "sample_index": "2",
                    "performance_latency_ms": "8.0",
                },
            ]
            with results_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/report_campaign.py"),
                "--campaign",
                str(CAMPAIGN_JSON),
                "--results_csv",
                str(results_csv),
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

            with out_csv.open("r", encoding="utf-8", newline="") as f:
                rows_out = list(csv.DictReader(f))
            model_rows = [
                r
                for r in rows_out
                if r.get("scope") == "model"
                and r.get("arch_id") == "fp16_nm1"
                and r.get("macro_mode") == "flat_nomacro"
                and r.get("model_id") == "mlp1"
            ]
            self.assertEqual(1, len(model_rows))
            m = model_rows[0]
            self.assertEqual("2", str(m.get("n", "")).strip())
            self.assertEqual("2", str(m.get("sample_count", "")).strip())
            self.assertAlmostEqual(4.5, float(m["latency_ms_mean"]), places=6)

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

    def test_validate_campaign_rejects_model_manifest_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            campaign_path = self._write_layer1_guard_case(Path(td), allow_wrapped_io=True)
            campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
            manifest_path = Path(campaign["model_manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["models"][0]["onnx_sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/validate.py"),
                "--campaign",
                str(campaign_path),
                "--check_paths",
            ]
            proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("onnx_sha256 mismatch", proc.stderr)

    def test_external_fetch_manifest_flow(self):
        with tempfile.TemporaryDirectory() as td:
            campaign_path, manifest_path, cached_model_path, model_sha = self._write_external_fetch_case(
                Path(td)
            )

            validate_cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/validate.py"),
                "--campaign",
                str(campaign_path),
            ]
            proc = subprocess.run(validate_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, msg=proc.stderr)

            validate_check_cmd = validate_cmd + ["--check_paths"]
            proc = subprocess.run(validate_check_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("path does not exist", proc.stderr)

            fetch_cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/fetch_models.py"),
                "--manifest",
                str(manifest_path),
            ]
            proc = subprocess.run(fetch_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, msg=proc.stderr)
            self.assertTrue(cached_model_path.exists())
            self.assertEqual(model_sha, self._sha256_file(cached_model_path))

            proc = subprocess.run(validate_check_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, msg=proc.stderr)

    def test_run_campaign_missing_external_model_suggests_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            campaign_path, _, _, _ = self._write_external_fetch_case(Path(td))
            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/eval/run_campaign.py"),
                "--campaign",
                str(campaign_path),
                "--dry_run",
            ]
            proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("fetch_models.py", proc.stderr)

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
