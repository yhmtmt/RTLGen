#!/usr/bin/env python3
"""Unit tests for activity-backed post-route power accounting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_postroute_vcd_power", ROOT / "npu/synth/run_postroute_vcd_power.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PostrouteVcdPowerTests(unittest.TestCase):
    def test_activity_annotation_counts_parse_openroad_report(self) -> None:
        counts = MODULE._activity_annotation_counts(
            "vcd            35\nsaif 2\ninput 3\nunannotated 664519\n"
        )
        self.assertEqual(
            counts,
            {"vcd": 35, "saif": 2, "input": 3, "unannotated": 664519},
        )

    def test_openroad_phase_accepts_absolute_out_of_tree_design_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            orfs = root / "orfs"
            orfs.mkdir()
            config = root / "external" / "config.mk"
            config.parent.mkdir()
            config.write_text("", encoding="utf-8")
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            tcl = root / "power.tcl"
            tcl.write_text("", encoding="utf-8")
            result = root / "result.json"
            result.write_text(
                json.dumps(
                    {
                        "total_w": 1.0,
                        "internal_w": 0.5,
                        "switching_w": 0.4,
                        "leakage_w": 0.1,
                    }
                ),
                encoding="utf-8",
            )
            completed = SimpleNamespace(
                returncode=0,
                stdout="vcd 2\nunannotated 8\n",
                stderr="",
            )
            with mock.patch.object(MODULE, "ORFS_FLOW", orfs), mock.patch.object(
                MODULE.subprocess, "run", return_value=completed
            ) as run:
                MODULE._run_openroad_phase(
                    design_config=config,
                    flow_variant="test",
                    vcd=vcd,
                    scope="tb/dut",
                    tcl=tcl,
                    result=result,
                    timeout_seconds=10,
                )
            command = run.call_args.args[0]
            self.assertIn(f"DESIGN_CONFIG={config.resolve()}", command)
    def _fixture(self, root: Path) -> tuple[dict, Path]:
        phases = []
        for name, measured, full in (
            ("score_fill", 20, 200),
            ("replay_value", 30, 300),
            ("finalize_result", 40, 40),
        ):
            vcd = root / f"{name}.vcd"
            vcd.write_text(f"$comment {name} $end\n", encoding="utf-8")
            phases.append(
                {
                    "phase": name,
                    "vcd": vcd.name,
                    "vcd_sha256": MODULE._sha256(vcd),
                    "measured_cycles": measured,
                    "full_context_cycles": full,
                }
            )
        manifest = {"clock_period_ns": 8.0, "phases": phases}
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest, path

    def test_phase_manifest_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, path = self._fixture(root)
            manifest["phases"][0]["vcd_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                MODULE._phase_rows(manifest, path)

    def test_build_report_accounts_phase_energy_and_gates_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power_rows = iter(
                [
                    {
                        "total_w": 2.0,
                        "internal_w": 1.0,
                        "switching_w": 0.8,
                        "leakage_w": 0.2,
                        "sdc_clock_period_ns": 8.0,
                        "annotatable_pin_count": 1000,
                        "vcd_annotated_pin_count": 500,
                        "macro_trace_active_pin_count": 10,
                        "macro_annotatable_pin_count": 100,
                    },
                    {
                        "total_w": 3.0,
                        "internal_w": 1.5,
                        "switching_w": 1.2,
                        "leakage_w": 0.3,
                        "sdc_clock_period_ns": 8.0,
                        "annotatable_pin_count": 1000,
                        "vcd_annotated_pin_count": 400,
                        "macro_trace_active_pin_count": 8,
                        "macro_annotatable_pin_count": 100,
                    },
                    {
                        "total_w": 1.0,
                        "internal_w": 0.5,
                        "switching_w": 0.4,
                        "leakage_w": 0.1,
                        "sdc_clock_period_ns": 8.0,
                        "annotatable_pin_count": 1000,
                        "vcd_annotated_pin_count": 300,
                        "macro_trace_active_pin_count": 0,
                        "macro_annotatable_pin_count": 100,
                    },
                ]
            )
            with mock.patch.object(MODULE, "_run_openroad_phase", side_effect=lambda **_: next(power_rows)):
                report = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.25,
                    min_vcd_pins=32,
                    min_macro_active_coverage=0.05,
                    min_macro_active_pins=8,
                    timeout_seconds=10,
                )
            self.assertTrue(report["promotion_gate_pass"])
            self.assertEqual(report["full_context_cycles"], 540)
            expected = (2.0 * 200 + 3.0 * 300 + 1.0 * 40) * 8.0e-9
            self.assertAlmostEqual(report["full_context_energy_j"], expected)

    def test_required_macro_phase_cannot_promote_without_macro_activity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = {
                "total_w": 1.0,
                "sdc_clock_period_ns": 8.0,
                "annotatable_pin_count": 100,
                "vcd_annotated_pin_count": 80,
                "macro_trace_active_pin_count": 1,
                "macro_annotatable_pin_count": 100,
            }
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                report = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.05,
                    min_vcd_pins=2,
                    min_macro_active_coverage=0.05,
                    min_macro_active_pins=8,
                    timeout_seconds=10,
                )
            self.assertFalse(report["promotion_gate_pass"])
            self.assertIsNone(report["full_context_energy_j"])
            self.assertLess(report["phases"][0]["macro_trace_active_coverage"], 0.05)

    def test_nan_or_missing_power_component_cannot_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = {
                "total_w": 1.0,
                "internal_w": None,
                "switching_w": 0.8,
                "leakage_w": 0.2,
                "sdc_clock_period_ns": 8.0,
                "annotatable_pin_count": 100,
                "vcd_annotated_pin_count": 80,
                "macro_trace_active_pin_count": 10,
                "macro_annotatable_pin_count": 100,
            }
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                report = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.05,
                    min_vcd_pins=2,
                    min_macro_active_coverage=0.05,
                    min_macro_active_pins=8,
                    timeout_seconds=10,
                )
            self.assertFalse(report["promotion_gate_pass"])
            self.assertFalse(report["phases"][0]["power_numeric_gate_pass"])


if __name__ == "__main__":
    unittest.main()
