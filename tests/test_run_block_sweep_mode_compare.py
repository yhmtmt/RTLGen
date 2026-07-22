#!/usr/bin/env python3
"""Regression tests for run_block_sweep mode_compare behavior."""

import csv
import importlib.util
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModeCompareRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_block_sweep = load_script_module(
            "run_block_sweep", "npu/synth/run_block_sweep.py"
        )
        cls.synth_fixture_dir = tempfile.TemporaryDirectory()
        cls.synth_fixture_path = Path(cls.synth_fixture_dir.name) / "synth.tcl"
        cls.synth_fixture_path.write_text(
            "hierarchy -check -top $::env(DESIGN_NAME)\n"
            "synth -run :fine\n"
            "synth -flatten -run coarse:fine\n"
            "synth -top $::env(DESIGN_NAME) -run fine:\n"
            "setundef -zero\n",
            encoding="utf-8",
        )
        cls.default_synth_script = cls.run_block_sweep.DEFAULT_SYNTH_SCRIPT
        cls.run_block_sweep.DEFAULT_SYNTH_SCRIPT = cls.synth_fixture_path

    @classmethod
    def tearDownClass(cls):
        cls.run_block_sweep.DEFAULT_SYNTH_SCRIPT = cls.default_synth_script
        cls.synth_fixture_dir.cleanup()

    @staticmethod
    def _collect_encfile_arg(cmd: list) -> str | None:
        for token in cmd:
            if not token.startswith("SYNTH_ARGS="):
                continue
            arg_text = token[len("SYNTH_ARGS=") :]
            args = shlex.split(arg_text)
            for i, arg in enumerate(args):
                if arg == "-encfile" and i + 1 < len(args):
                    return args[i + 1]
            for i, arg in enumerate(args):
                if arg.startswith("-encfile="):
                    return arg.split("=", 1)[1]
        return None

    @staticmethod
    def _collect_fsm_capture_base(env: dict[str, str]) -> str | None:
        return env.get("SYNTH_FSM_ENCFILE_BASE")

    def test_parse_mode_compare_default(self):
        cfg = self.run_block_sweep.parse_mode_compare_config({"mode_compare": True})
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual("comparisons", cfg["report_dir"])
        self.assertEqual(2, len(cfg["modes"]))
        self.assertEqual("flat_nomacro", cfg["modes"][0]["name"])
        self.assertFalse(cfg["modes"][0]["use_macro"])
        self.assertEqual(0, cfg["modes"][0]["param_overrides"]["SYNTH_HIERARCHICAL"])
        self.assertEqual("", cfg["modes"][0]["param_overrides"]["SYNTH_KEEP_MODULES"])
        self.assertEqual("hier_macro", cfg["modes"][1]["name"])
        self.assertTrue(cfg["modes"][1]["use_macro"])

    def test_fixed_floorplan_clears_template_core_utilization(self):
        self.assertEqual(
            ["CORE_UTILIZATION="],
            self.run_block_sweep.fixed_floorplan_make_overrides(
                {"DIE_AREA": "0 0 2500 2500", "CORE_AREA": "50 50 2450 2450"}
            ),
        )
        self.assertEqual(
            [],
            self.run_block_sweep.fixed_floorplan_make_overrides(
                {"CORE_AREA": "0 0 100 100", "CORE_UTILIZATION": 40}
            ),
        )
        self.assertEqual(
            [],
            self.run_block_sweep.fixed_floorplan_make_overrides(
                {"CORE_UTILIZATION": 40}
            ),
        )

    def test_hierarchical_macro_synth_disables_cost_threshold_without_macro_liberty(self):
        self.assertEqual(
            ["SYNTH_MINIMUM_KEEP_SIZE=", "ADDITIONAL_LIBS="],
            self.run_block_sweep.macro_synth_make_overrides(
                {"SYNTH_HIERARCHICAL": 1}
            ),
        )
        self.assertEqual(
            ["ADDITIONAL_LIBS="],
            self.run_block_sweep.macro_synth_make_overrides(
                {"SYNTH_HIERARCHICAL": 0}
            ),
        )

    def test_parse_mode_compare_custom_modes(self):
        raw = {
            "mode_compare": {
                "report_dir": "cmp_reports",
                "modes": [
                    {
                        "name": "Flat",
                        "use_macro": "false",
                        "param_overrides": {"SYNTH_HIERARCHICAL": 0},
                    },
                    {
                        "name": "Flat",
                        "use_macro": True,
                        "param_overrides": {"SYNTH_HIERARCHICAL": 1},
                    },
                ],
            }
        }
        cfg = self.run_block_sweep.parse_mode_compare_config(raw)
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual("cmp_reports", cfg["report_dir"])
        self.assertEqual("flat", cfg["modes"][0]["slug"])
        self.assertEqual("flat_2", cfg["modes"][1]["slug"])
        self.assertFalse(cfg["modes"][0]["use_macro"])
        self.assertTrue(cfg["modes"][1]["use_macro"])

    def test_parse_mode_compare_macro_placement_modes(self):
        raw = {
            "mode_compare": {
                "modes": [
                    {
                        "name": "Flattened_wrapper",
                        "use_macro": True,
                        "param_overrides": {
                            "SYNTH_HIERARCHICAL": 0,
                            "DIE_AREA": "0 0 3550 3550",
                            "CORE_AREA": "50 50 3500 3500",
                        },
                    },
                    {
                        "name": "Hierarchical_macro",
                        "use_macro": "true",
                        "param_overrides": {
                            "SYNTH_HIERARCHICAL": 1,
                            "DIE_AREA": "0 0 3550 3550",
                            "CORE_AREA": "50 50 3500 3500",
                        },
                    },
                ]
            }
        }
        cfg = self.run_block_sweep.parse_mode_compare_config(raw)
        self.assertIsNotNone(cfg)
        assert cfg is not None
        modes = cfg["modes"]
        self.assertEqual("flattened_wrapper", modes[0]["slug"])
        self.assertEqual("hierarchical_macro", modes[1]["slug"])
        self.assertTrue(modes[0]["use_macro"])
        self.assertTrue(modes[1]["use_macro"])
        self.assertEqual(0, modes[0]["param_overrides"]["SYNTH_HIERARCHICAL"])
        self.assertEqual(1, modes[1]["param_overrides"]["SYNTH_HIERARCHICAL"])


    def test_apply_mode_to_params(self):
        base = {
            "TAG": "run_tag",
            "FLOW_VARIANT": "basevar",
            "tag_prefix": "npu_fp16",
            "CLOCK_PERIOD": 10.0,
        }
        mode = {
            "slug": "flat_nomacro",
            "param_overrides": {"SYNTH_HIERARCHICAL": 0},
        }
        out = self.run_block_sweep.apply_mode_to_params(base, mode, "npu_fp16")
        self.assertEqual("run_tag_flat_nomacro", out["TAG"])
        self.assertEqual("basevar_flat_nomacro", out["FLOW_VARIANT"])
        self.assertEqual(0, out["SYNTH_HIERARCHICAL"])

        out2 = self.run_block_sweep.apply_mode_to_params(
            {"tag_prefix": "seed"}, mode, "fallback"
        )
        self.assertEqual("seed_flat_nomacro", out2["tag_prefix"])
        self.assertEqual("flat_nomacro", out2["FLOW_VARIANT"])

    def test_apply_mode_to_params_does_not_duplicate_binary_fsm_proxy_mode(self) -> None:
        sweep_path = (
            REPO_ROOT
            / "runs"
            / "campaigns"
            / "npu"
            / "decode_score_multivalue_cluster_v1"
            / "sweeps"
            / "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v3.json"
        )
        sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
        mode_cfg = self.run_block_sweep.parse_mode_compare_config(sweep)
        assert mode_cfg is not None
        proxy_mode = next(
            mode for mode in mode_cfg["modes"] if str(mode.get("slug", "")).strip() == "proxy_die_2500"
        )
        out = self.run_block_sweep.apply_mode_to_params(
            {
                "TAG": sweep["flow_params"]["TAG"][0],
                "FLOW_VARIANT": sweep["flow_params"]["FLOW_VARIANT"][0],
            },
            proxy_mode,
            str(sweep["tag_prefix"]),
        )
        self.assertEqual(
            "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
            out["FLOW_VARIANT"],
        )

    def test_apply_mode_to_params_distinguishes_v3_and_v4_binary_fsm_sweeps(self) -> None:
        v3_sweep_path = (
            REPO_ROOT
            / "runs"
            / "campaigns"
            / "npu"
            / "decode_score_multivalue_cluster_v1"
            / "sweeps"
            / "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v3.json"
        )
        v4_sweep_path = (
            REPO_ROOT
            / "runs"
            / "campaigns"
            / "npu"
            / "decode_score_multivalue_cluster_v1"
            / "sweeps"
            / "nangate45_decode_score_multivalue_cluster_8ns_binary_fsm_v4.json"
        )
        v3_sweep = json.loads(v3_sweep_path.read_text(encoding="utf-8"))
        v4_sweep = json.loads(v4_sweep_path.read_text(encoding="utf-8"))
        v3_cfg = self.run_block_sweep.parse_mode_compare_config(v3_sweep)
        v4_cfg = self.run_block_sweep.parse_mode_compare_config(v4_sweep)
        assert v3_cfg is not None
        assert v4_cfg is not None
        v3_mode = next(
            m for m in v3_cfg["modes"] if str(m.get("slug", "")).strip() == "proxy_die_2500"
        )
        v4_mode = next(
            m for m in v4_cfg["modes"] if str(m.get("slug", "")).strip() == "proxy_die_2500"
        )
        v3_applied = self.run_block_sweep.apply_mode_to_params(
            {
                "TAG": v3_sweep["flow_params"]["TAG"][0],
                "FLOW_VARIANT": v3_sweep["flow_params"]["FLOW_VARIANT"][0],
            },
            v3_mode,
            str(v3_sweep["tag_prefix"]),
        )
        v4_applied = self.run_block_sweep.apply_mode_to_params(
            {
                "TAG": v4_sweep["flow_params"]["TAG"][0],
                "FLOW_VARIANT": v4_sweep["flow_params"]["FLOW_VARIANT"][0],
            },
            v4_mode,
            str(v4_sweep["tag_prefix"]),
        )

        self.assertEqual(
            "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500",
            v3_applied["FLOW_VARIANT"],
        )
        self.assertEqual(
            "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4_proxy_die_2500",
            v4_applied["FLOW_VARIANT"],
        )
        self.assertEqual(1, v4_applied["FLOW_VARIANT"].count("_proxy_die_2500"))
        self.assertNotEqual(
            self.run_block_sweep.make_run_id(v3_applied),
            self.run_block_sweep.make_run_id(v4_applied),
        )
        self.assertNotEqual(v3_applied["FLOW_VARIANT"], v4_applied["FLOW_VARIANT"])

    def test_apply_repeat_to_params_sets_flow_random_seed(self):
        out = self.run_block_sweep.apply_repeat_to_params(
            {"TAG": "tag_flat", "FLOW_VARIANT": "var_flat"},
            repeat_index=1,
            repeat_count=3,
        )
        self.assertEqual("tag_flat_r2", out["TAG"])
        self.assertEqual("var_flat_r2", out["FLOW_VARIANT"])
        self.assertEqual(2, out["FLOW_RANDOM_SEED"])

        explicit_seed = self.run_block_sweep.apply_repeat_to_params(
            {"TAG": "tag_flat", "FLOW_RANDOM_SEED": 99},
            repeat_index=1,
            repeat_count=3,
        )
        self.assertEqual(99, explicit_seed["FLOW_RANDOM_SEED"])

    def test_write_mode_compare_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "npu_fp16_cpp_hiercmp"
            rows = [
                {
                    "mode_name": "flat_nomacro",
                    "mode_use_macro": False,
                    "status": "ok",
                    "tag": "flat_tag",
                    "critical_path_ns": 5.70,
                    "die_area": 2250000.0,
                    "total_power_mw": 0.2100,
                    "macro_manifest_path": "",
                    "missing_blackboxes": [],
                    "work_result_json": str(root / "work/a/result.json"),
                },
                {
                    "mode_name": "hier_macro",
                    "mode_use_macro": True,
                    "status": "ok",
                    "tag": "hier_tag",
                    "critical_path_ns": 5.80,
                    "die_area": 2300000.0,
                    "total_power_mw": 0.2000,
                    "macro_manifest_path": str(
                        REPO_ROOT
                        / "runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json"
                    ),
                    "missing_blackboxes": ["gemm_compute_array"],
                    "work_result_json": str(root / "work/b/result.json"),
                },
            ]
            report = self.run_block_sweep.write_mode_compare_report(
                circuit_root=root,
                report_dir_name="comparisons",
                design_name="npu_fp16_cpp_hiercmp",
                platform="nangate45",
                compare_group="deadbeef",
                base_params={"TAG": "npu_fp16_cmp"},
                make_target="3_3_place_gp",
                mode_rows=rows,
            )
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("| mode | repeat | use_macro | status |", text)
            self.assertIn("flat_nomacro", text)
            self.assertIn("hier_macro", text)
            self.assertIn("+0.1000", text)

    def test_dry_run_expands_two_modes(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, input rst_n, output done);\n"
                "  assign done = rst_n & clk;\n"
                "endmodule\n",
                encoding="utf-8",
            )

            sweep_path = design_dir / "sweep_compare.json"
            sweep_path.write_text(
                json.dumps(
                    {
                        "flow_params": {
                            "TAG": ["npu_fp16_hiercmp_cmp_33"],
                            "FLOW_VARIANT": ["cmp33"],
                            "CLOCK_PERIOD": [10.0],
                            "DIE_AREA": ["0 0 1500 1500"],
                            "CORE_AREA": ["50 50 1450 1450"],
                            "PLACE_DENSITY": [0.40],
                            "SYNTH_KEEP_MODULES": ["gemm_compute_array"],
                        },
                        "tag_prefix": "npu_fp16_hiercmp",
                        "mode_compare": True,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            cmd = [
                sys.executable,
                str(REPO_ROOT / "npu/synth/run_block_sweep.py"),
                "--design_dir",
                str(design_dir),
                "--platform",
                "nangate45",
                "--top",
                "npu_top",
                "--sweep",
                str(sweep_path),
                "--dry_run",
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            out = proc.stdout
            self.assertIn("mode_compare enabled with modes: flat_nomacro, hier_macro", out)
            self.assertIn("npu_fp16_hiercmp_cmp_33_flat_nomacro", out)
            self.assertIn("npu_fp16_hiercmp_cmp_33_hier_macro", out)
            self.assertIn("'SYNTH_HIERARCHICAL': 0", out)
            self.assertIn("'SYNTH_HIERARCHICAL': 1", out)

    def test_run_single_records_flow_failure_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done);\n"
                "  assign done = clk;\n"
                "endmodule\n",
                encoding="utf-8",
            )

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run

            def fake_run(cmd, *, cwd, check, env):
                raise subprocess.CalledProcessError(returncode=17, cmd=cmd)

            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_fail",
                        "FLOW_VARIANT": "demo_fail",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target=None,
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("flow_failed", row["status"])
            self.assertEqual(17, row["failure_returncode"])
            self.assertEqual("flow", row["failure_stage"])
            self.assertIn("exit_code=17", row["failure_signature"])
            self.assertEqual("", row["failure_log_path"])
            metrics_text = (tmp / "out" / "demo_design" / "metrics.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("flow_failed", metrics_text)
            self.assertIn("failure_signature", metrics_text)
            self.assertTrue((tmp / "out" / "demo_design" / "work").is_dir())
            payload = json.loads(Path(row["work_result_json"]).read_text(encoding="utf-8"))
            self.assertEqual("flow_failed", payload["status"])
            self.assertEqual("flow", payload["failure_stage"])
            self.assertEqual(17, payload["failure_returncode"])

    def test_macro_pre_synth_failure_uses_exception_command(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )
            lib_path = tmp / "dummy.lib"
            lib_path.write_text("library(dummy);\n", encoding="utf-8")
            macro_manifest = {"additional_libs": [lib_path]}

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run

            def fake_run(cmd, *, cwd, check, env):
                raise subprocess.CalledProcessError(returncode=23, cmd=cmd)

            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_pre_synth_fail",
                        "FLOW_VARIANT": "demo_pre_synth_fail",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target=None,
                    macro_manifest=macro_manifest,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("flow_failed", row["status"])
            self.assertEqual("synth", row["failure_stage"])
            self.assertEqual(23, row["failure_returncode"])
            self.assertIn("synth", row["failure_command"])

    def test_run_single_failure_infers_stage_and_signature_from_logs(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done);\\n"
                "  assign done = clk;\\n"
                "endmodule\\n",
                encoding="utf-8",
            )

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run

            def fake_run(cmd, *, cwd, check, env):
                log_dir = (
                    self.run_block_sweep.LOG_BASE
                    / "nangate45"
                    / "demo_design"
                    / "demo_fail"
                )
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "3_3_place_gp.log"
                long_error = "error: " + ("E" * 400)
                log_path.write_text(
                    "\\n".join(
                        [
                            "running place_gp...",
                            long_error,
                        ]
                    ),
                    encoding="utf-8",
                )
                raise subprocess.CalledProcessError(returncode=19, cmd=cmd)

            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_fail",
                        "FLOW_VARIANT": "demo_fail",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target="3_3_place_gp",
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("flow_failed", row["status"])
            self.assertEqual("globalplace", row["failure_stage"])
            expected_log = tmp / "orfs" / "logs" / "nangate45" / "demo_design" / "demo_fail" / "3_3_place_gp.log"
            self.assertEqual(str(expected_log), row["failure_log_path"])
            self.assertLessEqual(len(row["failure_signature"]), 255)
            self.assertIn("failure_signature", row)
            self.assertIn("error:", row["failure_signature"])

    def test_synth_keep_modules_must_exist_in_generated_rtl(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done);\n"
                "  helper u_helper(.clk(clk), .done(done));\n"
                "endmodule\n"
                "module helper(input clk, output done);\n"
                "  assign done = clk;\n"
                "endmodule\n",
                encoding="utf-8",
            )

            self.assertEqual(
                {"helper", "npu_top"},
                self.run_block_sweep.verilog_module_names(verilog_dir),
            )
            with self.assertRaisesRegex(ValueError, "missing_helper"):
                self.run_block_sweep.validate_synth_keep_modules(
                    verilog_dir=verilog_dir,
                    sweep_params={"SYNTH_KEEP_MODULES": "helper missing_helper"},
                    macro_manifest=None,
                )

    def test_run_single_rejects_missing_synth_keep_module_before_openroad(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done);\n"
                "  assign done = clk;\n"
                "endmodule\n",
                encoding="utf-8",
            )

            old_run = self.run_block_sweep.subprocess.run
            calls = []

            def fake_run(cmd, *, cwd, check, env):
                calls.append(cmd)
                raise AssertionError("OpenROAD should not run for invalid keep modules")

            self.run_block_sweep.subprocess.run = fake_run
            try:
                with self.assertRaisesRegex(ValueError, "missing_mod"):
                    self.run_block_sweep.run_single(
                        design_dir=design_dir,
                        design_name="demo_design",
                        platform="nangate45",
                        top="npu_top",
                        verilog_dir=verilog_dir,
                        sdc_template=None,
                        sweep_params={
                            "TAG": "demo_fail",
                            "FLOW_VARIANT": "demo_fail",
                            "CLOCK_PERIOD": 10.0,
                            "CORE_AREA": "0 0 100 100",
                            "SYNTH_KEEP_MODULES": "npu_top missing_mod",
                        },
                        out_root=tmp / "out",
                        skip_existing=False,
                        dry_run=False,
                        force_copy=True,
                        make_target=None,
                        macro_manifest=None,
                    )
            finally:
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual([], calls)

    def test_append_metrics_replaces_same_run_identity(self):
        with tempfile.TemporaryDirectory() as td:
            metrics_path = Path(td) / "metrics.csv"
            old_row = {
                "design": "demo_design",
                "platform": "nangate45",
                "config_hash": "old_cfg",
                "param_hash": "same_params",
                "tag": "same_tag",
                "status": "ok",
                "critical_path_ns": 5.0,
                "die_area": 1000.0,
                "total_power_mw": 0.1,
                "params_json": json.dumps({"TAG": "same_tag"}),
                "result_path": "/orfs/flow/reports/old/6_finish.rpt",
            }
            new_row = dict(old_row)
            new_row.update(
                {
                    "config_hash": "new_cfg",
                    "status": "flow_failed",
                    "critical_path_ns": None,
                    "die_area": None,
                    "total_power_mw": None,
                    "result_path": "/orfs/flow/logs/new",
                }
            )

            self.run_block_sweep.append_metrics(metrics_path, old_row)
            self.run_block_sweep.append_metrics(metrics_path, new_row)

            with metrics_path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(1, len(rows))
            self.assertEqual("new_cfg", rows[0]["config_hash"])
            self.assertEqual("flow_failed", rows[0]["status"])
            self.assertEqual("/orfs/flow/logs/new", rows[0]["result_path"])

    def test_run_single_assigns_distinct_fsm_capture_base_per_synth_invocation(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )
            lib_path = tmp / "dummy.lib"
            lib_path.write_text("library(dummy);\n", encoding="utf-8")
            macro_manifest = {
                "additional_libs": [lib_path],
            }

            calls = []

            def fake_run(cmd, *, cwd, check, env):
                calls.append((list(cmd), dict(env)))
                flow_variant = str(env.get("FLOW_VARIANT", "base")).strip() or "base"
                for variant in (flow_variant, "base"):
                    synth_out = tmp / "orfs" / "results" / "nangate45" / "demo_design" / variant / "1_synth.v"
                    synth_out.parent.mkdir(parents=True, exist_ok=True)
                    synth_out.write_text("// synthesized\n", encoding="utf-8")
                capture_base = self._collect_fsm_capture_base(env)
                if capture_base:
                    Path(f"{capture_base}.01").write_text(
                        ".fsm npu_top top\n.map 0 1\n",
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_invocable",
                        "FLOW_VARIANT": "demo_invocable",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_FSM_ENCFILE": True,
                        "SYNTH_FSM_ENCFILE_PATH": "fsm_encoding.enc",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target=None,
                    macro_manifest=macro_manifest,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            capture_bases = [
                Path(self._collect_fsm_capture_base(call_env))
                for _, call_env in calls
                if self._collect_fsm_capture_base(call_env) is not None
            ]
            self.assertEqual(2, len(capture_bases))
            self.assertEqual(
                {"fsm_encoding_01.enc", "fsm_encoding_02.enc"},
                {p.name for p in capture_bases},
            )
            self.assertNotEqual(capture_bases[0], capture_bases[1])
            self.assertIsNotNone(row["fsm_encfile_path"])
            self.assertTrue(row["fsm_encfile_path"] != "")

    def test_run_single_records_fsm_encoding_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )

            def fake_run(cmd, *, cwd, check, env):
                capture_base = self._collect_fsm_capture_base(env)
                if capture_base:
                    Path(f"{capture_base}.01").write_text(
                        ".fsm npu_top top_state\\n.map 0 1\\n",
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_capture",
                        "FLOW_VARIANT": "demo_capture",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_FSM_ENCFILE": True,
                        "SYNTH_FSM_ENCFILE_PATH": "fsm_encoding.enc",
                        "SYNTH_FSM_ENCFILE_REQUIRED": False,
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target="1_synth.v",
                    macro_manifest=None,
                )
                payload = json.loads(Path(row["work_result_json"]).read_text(encoding="utf-8"))
                metrics_rows = list(
                    csv.DictReader(
                        (tmp / "out" / "demo_design" / "metrics.csv").open(encoding="utf-8")
                    )
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertIn("fsm_encoding_json", row)
            self.assertTrue(row["fsm_encfile_path"])
            self.assertTrue(row["fsm_encfile_sha1"])
            self.assertTrue(row["fsm_encfile_sha256"])
            self.assertTrue(row["fsm_encoding_json"])
            self.assertEqual(payload["fsm_encfile_path"], row["fsm_encfile_path"])
            encoded = json.loads(row["fsm_encoding_json"])
            self.assertEqual(1, encoded["version"])
            self.assertEqual("npu_top", encoded["fsm_encodings"][0]["module"])
            self.assertIn("result_path", row)
            self.assertEqual(row["fsm_encfile_sha1"], payload["fsm_encfile_sha1"])
            self.assertEqual(row["fsm_encoding_json"], metrics_rows[0]["fsm_encoding_json"])

    def test_run_single_fails_clearly_when_fsm_capture_required_but_missing(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )

            def fake_run(cmd, *, cwd, check, env):
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_req_missing",
                        "FLOW_VARIANT": "demo_req_missing",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_FSM_ENCFILE_REQUIRED": True,
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target="1_synth.v",
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("flow_failed", row["status"])
            self.assertEqual("synth", row["failure_stage"])
            self.assertEqual("missing_required_fsm_encoding_capture", row["failure_signature"])

    def test_skip_existing_rejects_missing_required_capture_map(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )

            sweep_params = {
                "TAG": "demo_skip",
                "FLOW_VARIANT": "demo_skip",
                "CLOCK_PERIOD": 10.0,
                "CORE_AREA": "0 0 100 100",
                "SYNTH_FSM_ENCFILE_REQUIRED": True,
            }
            run_id = self.run_block_sweep.make_run_id(sweep_params)
            old_payload = {
                "design": "demo_design",
                "platform": "nangate45",
                "config_hash": "cfg",
                "param_hash": run_id,
                "tag": "demo_skip",
                "status": "ok",
                "work_result_json": str(tmp / "out" / "demo_design" / "work" / run_id / "result.json"),
            }
            result_dir = tmp / "out" / "demo_design" / "work" / run_id
            result_dir.mkdir(parents=True, exist_ok=True)
            (result_dir / "result.json").write_text(
                json.dumps(old_payload),
                encoding="utf-8",
            )

            calls = []

            def fake_run(cmd, *, cwd, check, env):
                calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params=sweep_params,
                    out_root=tmp / "out",
                    skip_existing=True,
                    dry_run=False,
                    force_copy=True,
                    make_target="1_synth.v",
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual(1, len(calls))
            self.assertNotEqual("ok", row["status"])

    def test_run_single_merges_fsm_encodings_from_multiple_synth_invocations(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )
            lib_path = tmp / "dummy.lib"
            lib_path.write_text("library(dummy);\n", encoding="utf-8")
            macro_manifest = {
                "additional_libs": [lib_path],
            }

            calls = []

            def fake_run(cmd, *, cwd, check, env):
                calls.append((list(cmd), dict(env)))
                capture_base = self._collect_fsm_capture_base(env)
                flow_variant = str(env.get("FLOW_VARIANT", "base")).strip() or "base"
                for variant in (flow_variant, "base"):
                    synth_out = tmp / "orfs" / "results" / "nangate45" / "demo_design" / variant / "1_synth.v"
                    synth_out.parent.mkdir(parents=True, exist_ok=True)
                    synth_out.write_text("// synthesized\n", encoding="utf-8")
                if capture_base:
                    if "_01" in str(capture_base):
                        Path(f"{capture_base}.01").write_text(
                            ".fsm npu_top reducer\n.map 1 2\n",
                            encoding="utf-8",
                        )
                    else:
                        Path(f"{capture_base}.01").write_text(
                            ".fsm npu_top score_tile\n.map S T\n",
                            encoding="utf-8",
                        )
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_multi",
                        "FLOW_VARIANT": "demo_multi",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_FSM_ENCFILE": True,
                        "SYNTH_FSM_ENCFILE_PATH": "fsm_encoding.enc",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target=None,
                    macro_manifest=macro_manifest,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            synth_calls = [
                call
                for call in calls
                if self._collect_fsm_capture_base(call[1]) is not None
            ]
            self.assertEqual(2, len(synth_calls))
            encoded = json.loads(row["fsm_encoding_json"])
            module_states = {
                (entry.get("module"), entry.get("state"))
                for entry in encoded.get("fsm_encodings", [])
            }
            self.assertIn(("npu_top", "reducer"), module_states)
            self.assertIn(("npu_top", "score_tile"), module_states)

    def test_merge_fsm_encodings_accepts_identical_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            first = tmp / "first.enc"
            second = tmp / "second.enc"
            content = ".fsm npu_top score_tile\n.map 00 01\n"
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")

            merged = self.run_block_sweep.merge_fsm_encoding_payloads([first, second])

            self.assertEqual(
                [{"module": "npu_top", "state": "score_tile", "maps": [["00", "01"]]}],
                merged,
            )

    def test_merge_fsm_encodings_rejects_conflicting_recodes(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            first = tmp / "first.enc"
            second = tmp / "second.enc"
            first.write_text(
                ".fsm npu_top score_tile\n.map 00 01\n",
                encoding="utf-8",
            )
            second.write_text(
                ".fsm npu_top score_tile\n.map 00 10\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Conflicting FSM encoding"):
                self.run_block_sweep.merge_fsm_encoding_payloads([first, second])

    def test_run_single_records_conflicting_fsm_encodings_as_flow_failure(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )

            def fake_run(cmd, *, cwd, check, env):
                capture_base = self._collect_fsm_capture_base(env)
                if capture_base:
                    Path(f"{capture_base}.01").write_text(
                        ".fsm npu_top score_tile\n.map 00 01\n",
                        encoding="utf-8",
                    )
                    Path(f"{capture_base}.02").write_text(
                        ".fsm npu_top score_tile\n.map 00 10\n",
                        encoding="utf-8",
                    )
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_conflict",
                        "FLOW_VARIANT": "demo_conflict",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_FSM_ENCFILE": True,
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target="1_synth.v",
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("flow_failed", row["status"])
            self.assertEqual("synth", row["failure_stage"])
            self.assertEqual(
                "conflicting_fsm_encoding_capture",
                row["failure_signature"],
            )
            self.assertIn("module='npu_top'", row["failure_command"])
            result_payload = json.loads(
                Path(row["work_result_json"]).read_text(encoding="utf-8")
            )
            self.assertEqual("flow_failed", result_payload["status"])
            metrics_rows = list(
                csv.DictReader(
                    (tmp / "out" / "demo_design" / "metrics.csv").open(
                        encoding="utf-8"
                    )
                )
            )
            self.assertEqual(1, len(metrics_rows))
            self.assertEqual("flow_failed", metrics_rows[0]["status"])
            self.assertEqual(
                "conflicting_fsm_encoding_capture",
                metrics_rows[0]["failure_signature"],
            )

    def test_run_single_applies_synth_args_through_generated_script_without_capture(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            design_dir = tmp / "demo_design"
            verilog_dir = design_dir / "verilog"
            verilog_dir.mkdir(parents=True, exist_ok=True)
            (verilog_dir / "top.v").write_text(
                "module npu_top(input clk, output done); assign done = clk; endmodule\n",
                encoding="utf-8",
            )

            calls = []

            def fake_run(cmd, *, cwd, check, env):
                calls.append((list(cmd), dict(env)))
                flow_variant = str(env.get("FLOW_VARIANT", "base")).strip() or "base"
                out_dir = (
                    tmp / "orfs" / "results" / "nangate45" / "demo_design" / flow_variant
                )
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "1_synth.v").write_text("// synth result\n", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0)

            old_dest = self.run_block_sweep.DEST_BASE
            old_src = self.run_block_sweep.SRC_BASE
            old_report = self.run_block_sweep.REPORT_BASE
            old_result = self.run_block_sweep.RESULT_BASE
            old_log = self.run_block_sweep.LOG_BASE
            old_run = self.run_block_sweep.subprocess.run
            self.run_block_sweep.DEST_BASE = tmp / "orfs" / "designs"
            self.run_block_sweep.SRC_BASE = self.run_block_sweep.DEST_BASE / "src"
            self.run_block_sweep.REPORT_BASE = tmp / "orfs" / "reports"
            self.run_block_sweep.RESULT_BASE = tmp / "orfs" / "results"
            self.run_block_sweep.LOG_BASE = tmp / "orfs" / "logs"
            self.run_block_sweep.subprocess.run = fake_run
            try:
                row = self.run_block_sweep.run_single(
                    design_dir=design_dir,
                    design_name="demo_design",
                    platform="nangate45",
                    top="npu_top",
                    verilog_dir=verilog_dir,
                    sdc_template=None,
                    sweep_params={
                        "TAG": "demo_synth_args",
                        "FLOW_VARIANT": "demo_synth_args",
                        "CLOCK_PERIOD": 10.0,
                        "CORE_AREA": "0 0 100 100",
                        "SYNTH_ARGS": "-nofsm",
                    },
                    out_root=tmp / "out",
                    skip_existing=False,
                    dry_run=False,
                    force_copy=True,
                    make_target="1_synth.v",
                    macro_manifest=None,
                )
            finally:
                self.run_block_sweep.DEST_BASE = old_dest
                self.run_block_sweep.SRC_BASE = old_src
                self.run_block_sweep.REPORT_BASE = old_report
                self.run_block_sweep.RESULT_BASE = old_result
                self.run_block_sweep.LOG_BASE = old_log
                self.run_block_sweep.subprocess.run = old_run

            self.assertEqual("ok", row["status"])
            synth_cmds = [
                cmd
                for cmd, _ in calls
                if any(token.startswith("SYNTH_SCRIPT=") for token in cmd)
            ]
            self.assertEqual(1, len(synth_cmds))
            make_cmd = synth_cmds[0]
            synth_script_token = next(
                token for token in make_cmd if token.startswith("SYNTH_SCRIPT=")
            )
            synth_script_path = Path(synth_script_token.split("=", 1)[1])
            synth_text = synth_script_path.read_text(encoding="utf-8")
            self.assertIn("synth -run :fine {*}$synth_full_args", synth_text)
            self.assertNotIn("proc yosys_synth_with_fsm_capture", synth_text)

    def test_synth_script_instruments_all_internal_synth_calls(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            script_path = tmp / "synth_capture.tcl"
            self.run_block_sweep.write_preserve_blackbox_synth_script(
                script_path=script_path,
                instrument_fsm_capture=True,
            )

            text = script_path.read_text(encoding="utf-8")

            self.assertIn("proc yosys_synth_with_fsm_capture", text)
            self.assertIn(
                "yosys_synth_with_fsm_capture -run :fine {*}$synth_full_args", text,
            )
            self.assertIn(
                "yosys_synth_with_fsm_capture -flatten -run coarse:fine {*}$synth_full_args",
                text,
            )
            self.assertIn(
                "yosys_synth_with_fsm_capture -top $::env(DESIGN_NAME) -run fine: {*}$synth_full_args",
                text,
            )
            self.assertNotIn("synth -run :fine", text)
            self.assertNotIn("synth -flatten -run coarse:fine", text)
            self.assertNotIn("synth -top $::env(DESIGN_NAME) -run fine:", text)
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("synth ") or stripped.startswith(
                    "yosys_synth_with_fsm_capture "
                ):
                    self.assertIn("{*}$synth_full_args", line)

    def test_synth_script_fails_when_generated_call_lacks_synth_full_args(self):
        malformed = (
            "synth -run :fine\n"
            "yosys_synth_with_fsm_capture -run :fine\n"
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "Generated synth/wrapper calls missing",
        ):
            self.run_block_sweep._inject_fsm_capture_into_synth_script(malformed)

class SynthTargetMappingRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_block_sweep = load_script_module(
            "run_block_sweep_map", "npu/synth/run_block_sweep.py"
        )

    def test_is_synth_target_accepts_canonicalize_stage_token(self):
        self.assertTrue(self.run_block_sweep.is_synth_target("1_1_yosys_canonicalize"))

    def test_resolve_make_target_maps_canonicalize_to_valid_rule(self):
        self.assertEqual(
            "do-yosys-canonicalize",
            self.run_block_sweep.resolve_make_target("1_1_yosys_canonicalize"),
        )

    def test_resolve_make_target_maps_synth_variants_to_synth(self):
        self.assertEqual("synth", self.run_block_sweep.resolve_make_target("1_2_yosys"))
        self.assertEqual("synth", self.run_block_sweep.resolve_make_target("1_synth.v"))

    def test_should_generate_openroad_metadata_for_full_flow_and_finish(self):
        self.assertTrue(self.run_block_sweep.should_generate_openroad_metadata(None))
        self.assertTrue(self.run_block_sweep.should_generate_openroad_metadata(""))
        self.assertTrue(self.run_block_sweep.should_generate_openroad_metadata("finish"))
        self.assertFalse(self.run_block_sweep.should_generate_openroad_metadata("3_3_place_gp"))
        self.assertFalse(self.run_block_sweep.should_generate_openroad_metadata("synth"))

    def test_merge_openroad_metrics_json_prefers_later_paths(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            first = base / "6_finish.json"
            second = base / "metadata.json"
            first.write_text(
                json.dumps({"finish__design__instance__area": 1.0, "shared": 1}),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps({"synth__design__instance__count__stdcell": 2, "shared": 2}),
                encoding="utf-8",
            )
            merged = self.run_block_sweep.merge_openroad_metrics_json([first, second])
        self.assertEqual(1.0, merged["finish__design__instance__area"])
        self.assertEqual(2, merged["synth__design__instance__count__stdcell"])
        self.assertEqual(2, merged["shared"])

    def test_add_utilization_metrics_from_finish_json(self):
        metrics = {}
        self.run_block_sweep.add_utilization_metrics(
            metrics,
            metrics_json={
                "finish__design__instance__area": 490000.0,
                "synth__design__instance__area__stdcell": 470000.0,
                "placeopt__design__instance__count__stdcell": 12345,
            },
            sweep_params={"CORE_AREA": "50 50 1450 1450"},
        )
        self.assertEqual(490000.0, metrics["instance_area_um2"])
        self.assertEqual(470000.0, metrics["stdcell_area_um2"])
        self.assertEqual(12345.0, metrics["stdcell_count"])
        self.assertEqual(1960000.0, metrics["core_area_um2"])
        self.assertAlmostEqual(25.0, metrics["utilization_pct"])

    def test_add_utilization_metrics_accepts_final_stage_cell_metrics(self):
        metrics = {}
        self.run_block_sweep.add_utilization_metrics(
            metrics,
            metrics_json={
                "final__design__instance__area": 510000.0,
                "final__design__instance__area__stdcell": 501000.0,
                "final__design__instance__count__stdcell": 23456,
            },
            sweep_params={"CORE_AREA": "50 50 1450 1450"},
        )
        self.assertEqual(510000.0, metrics["instance_area_um2"])
        self.assertEqual(501000.0, metrics["stdcell_area_um2"])
        self.assertEqual(23456.0, metrics["stdcell_count"])
        self.assertAlmostEqual(510000.0 * 100.0 / 1960000.0, metrics["utilization_pct"])

    def test_add_utilization_metrics_accepts_synth_only_cell_metrics(self):
        metrics = {}
        self.run_block_sweep.add_utilization_metrics(
            metrics,
            metrics_json={
                "synth__design__instance__area": 410000.0,
                "synth__design__instance__area__stdcell": 409000.0,
                "synth__design__instance__count__stdcell": 19876,
            },
            sweep_params={"CORE_AREA": "0 0 1000 1000"},
        )
        self.assertEqual(410000.0, metrics["instance_area_um2"])
        self.assertEqual(409000.0, metrics["stdcell_area_um2"])
        self.assertEqual(19876.0, metrics["stdcell_count"])
        self.assertAlmostEqual(41.0, metrics["utilization_pct"])


if __name__ == "__main__":
    unittest.main()
