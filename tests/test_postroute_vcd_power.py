#!/usr/bin/env python3
"""Unit tests for activity-backed post-route power accounting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
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
    def _write_tcl_runtime_stub(
        self, root: Path, result: Path, *, macro_transfer: bool = False
    ) -> str:
        if macro_transfer:
            all_pins = "{pin_other_0 pin_input_u_group_0 pin_nonfinite_u_group}"
            get_pins_body = (
                "  if {[lindex $args 0] eq \"-hierarchical\"} {\n"
                "    set pattern [lindex $args end]\n"
                "    if {$pattern eq \"*u_group_*\"} {\n"
                "      return {}\n"
                "    }\n"
                "  }\n"
                f"  return {all_pins}\n"
            )
            pin_property_body = (
                "  if {$obj eq {pin_input_u_group_0}} {\n"
                "    if {$property eq \"is_hierarchical\"} { return 0 }\n"
                "    if {$property eq \"direction\"} { return \"input\" }\n"
                "    if {$property eq \"activity\"} { return {0.0 0.0 constant} }\n"
                "    if {$property eq \"full_name\"} { return $obj }\n"
                "  }\n"
                "  if {$obj eq {driver_pin_u_group_0}} {\n"
                "    if {$property eq \"activity\"} { return {0.4 0.9 vcd} }\n"
                "  }\n"
            )
            net_driver_body = (
                "  proc net_driver_pins {net} {\n"
                "    if {$net eq {net_u_group_0}} { return {driver_pin_u_group_0} }\n"
                "    return {}\n"
                "  }\n"
            )
            net_and_activity_body = (
                "proc get_nets {args} {\n"
                "  if {[lindex $args 0] eq \"-of_objects\" && [lindex $args 1] eq {pin_input_u_group_0}} {\n"
                "    return {net_u_group_0}\n"
                "  }\n"
                "  return {}\n"
                "}\n"
            )
        else:
            get_pins_body = "  return {pin_nonfinite_u_group}\n"
            pin_property_body = ""
            net_driver_body = ""
            net_and_activity_body = ""
        script = (
            "\n"
            "proc load_design {args} {}\n"
            "proc read_spef {args} {}\n"
            "proc log_cmd {args} {}\n"
            "proc report_activity_annotation {} {}\n"
            "proc report_power {} {}\n"
            "proc get_clocks {args} {\n"
            "  return {clk}\n"
            "}\n"
            "proc get_full_name {leaf} {\n"
            "  return $leaf\n"
            "}\n"
            "proc get_pins {args} {\n"
            + get_pins_body
            + "}\n"
            "proc get_property {obj property} {\n"
            + pin_property_body
            + "  if {[string match \"pin_*\" $obj]} {\n"
            "    if {$property eq \"is_hierarchical\"} {\n"
            "      return 0\n"
            "    }\n"
            "    if {$property eq \"direction\"} {\n"
            "      return \"output\"\n"
            "    }\n"
            "    if {$property eq \"activity\"} {\n"
            "      return {0.25 0.5 vcd}\n"
            "    }\n"
            "    if {$property eq \"full_name\"} {\n"
            "      return $obj\n"
            "    }\n"
            "    return {}\n"
            "  }\n"
            "  if {$property eq \"is_leaf\"} {\n"
            "    return 1\n"
            "  }\n"
            "  if {$property eq \"name\"} {\n"
            "    return $obj\n"
            "  }\n"
            "  return {}\n"
            "}\n"
            + net_and_activity_body
            + "proc get_cells {args} {\n"
            "  return {leaf_group[7]/instance_a leaf_group_b/leaf_b}\n"
            "}\n"
            "proc instance_power {args} {\n"
            "  error \"use sta::instance_power <leaf> <corner>\"\n"
            "}\n"
            "proc set_power_pin_activity {args} {\n"
            "  error \"use sta::set_power_pin_activity <pin> <density> <duty>\"\n"
            "}\n"
            "proc design_power {args} {\n"
            "  error \"use sta::design_power <corner>\"\n"
            "}\n"
            "proc corners {} {\n"
            "  error \"do not call sta::corners\"\n"
            "}\n"
            "namespace eval sta {\n"
            "  proc cmd_corner {} {\n"
            "    return corner0\n"
            "  }\n"
            "  proc design_power {corner} {\n"
            "    if {$corner ne \"corner0\"} {\n"
            "      error \"design_power corner mismatch: $corner\"\n"
            "    }\n"
            "    # First quartet has non-finite total, triggering sample capture.\n"
            "    return {1.0 2.0 3.0 nan 4.0 5.0 6.0 7.0}\n"
            "  }\n"
            "  proc instance_power {leaf corner} {\n"
            "    if {$corner ne \"corner0\"} {\n"
            "      error \"instance_power corner mismatch: $corner\"\n"
            "    }\n"
            "    if {$leaf eq {leaf_group[7]/instance_a}} {\n"
            "      return {0.0 nan inf nan}\n"
            "    }\n"
            "    return {1.0 2.0 3.0 4.0}\n"
            "  }\n"
            "  proc set_power_pin_activity {pin density duty} {\n"
            "    lappend ::sta::power_pin_activity_calls [list $pin $density $duty]\n"
            "  }\n"
            "  proc corners {} {\n"
            "    return {corner0}\n"
            "  }\n"
            "  variable power_pin_activity_calls {}\n"
            + net_driver_body
            + "}\n"
            f"set ::env(SCRIPTS_DIR) \"{root / 'scripts'}\"\n"
            f"set ::env(RESULTS_DIR) \"{root}\"\n"
            f"set ::env(RTLGEN_ACTIVITY_VCD) \"{root / 'trace.vcd'}\"\n"
            f"set ::env(RTLGEN_ACTIVITY_SCOPE) \"tb/dut\"\n"
            f"set ::env(RTLGEN_ACTIVITY_RESULT) \"{result}\"\n"
            "\n"
            + MODULE._tcl_script()
        )
        return script

    def test_tcl_script_non_finite_samples_have_escaped_json_array_literals(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            tcl_script_path = root / "activity_power.tcl"
            tcl_script = self._write_tcl_runtime_stub(root=root, result=result)
            tcl_script_path.write_text(tcl_script, encoding="utf-8")
            tcl = shutil.which("tclsh")
            assert tcl is not None
            completed = MODULE.subprocess.run(
                [tcl, str(tcl_script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"tcl failed: stdout={completed.stdout} stderr={completed.stderr}",
            )
            self.assertFalse(completed.stderr.strip())

            payload = json.loads(result.read_text(encoding="utf-8"))
            diagnostics = payload["non_finite_leaf_instance_power"]
            self.assertEqual(diagnostics["instance_count"], 1)
            self.assertEqual(len(diagnostics["samples"]), 1)
            sample = diagnostics["samples"][0]
            self.assertEqual(sample["full_name"], "leaf_group[7]/instance_a")
            self.assertIsNone(sample["switching_w"])
            self.assertEqual(diagnostics.get("non_leaf_skip_count"), 0)
            self.assertEqual(diagnostics["candidate_cell_count"], 2)
            self.assertEqual(diagnostics["checked_instance_power_count"], 2)
            self.assertGreater(diagnostics["checked_instance_power_count"], 0)
            self.assertEqual(diagnostics["finite_row_count"], 1)
            self.assertEqual(diagnostics["bad_shape_row_count"], 0)
            self.assertEqual(diagnostics["query_error_count"], 0)
            self.assertLess(
                diagnostics["query_error_count"],
                diagnostics["candidate_cell_count"],
            )
            self.assertEqual(
                diagnostics["checked_instance_power_count"],
                diagnostics["finite_row_count"] + diagnostics["instance_count"],
            )
            finite_sums = diagnostics["finite_component_sums"]
            self.assertEqual(finite_sums["internal_w"], 1.0)
            self.assertEqual(finite_sums["switching_w"], 2.0)
            self.assertEqual(finite_sums["leakage_w"], 3.0)
            self.assertEqual(finite_sums["total_w"], 4.0)

    def test_tcl_script_transfers_macro_input_activity(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            tcl_script_path = root / "activity_power.tcl"
            tcl_script = self._write_tcl_runtime_stub(
                root=root, result=result, macro_transfer=True
            )
            tcl_script_path.write_text(tcl_script, encoding="utf-8")
            tcl = shutil.which("tclsh")
            assert tcl is not None
            completed = MODULE.subprocess.run(
                [tcl, str(tcl_script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"tcl failed: stdout={completed.stdout} stderr={completed.stderr}",
            )
            self.assertFalse(completed.stderr.strip())

            payload = json.loads(result.read_text(encoding="utf-8"))
            transfer = payload["macro_pin_transfer"]
            self.assertEqual(transfer["candidate_count"], 1)
            self.assertEqual(transfer["applied_count"], 1)
            self.assertEqual(transfer["query_error_count"], 0)
            self.assertEqual(transfer["apply_error_count"], 0)
            self.assertEqual(transfer["source_vcd_count"], 1)
            self.assertEqual(transfer["source_propagated_count"], 0)
            self.assertEqual(transfer["active_count"], 1)
            self.assertEqual(transfer["zero_count"], 0)
            self.assertEqual(transfer["scanned_pin_count"], 3)
            self.assertEqual(transfer["name_match_pin_count"], 1)
            self.assertEqual(transfer["input_pin_count"], 1)
            self.assertEqual(transfer["connected_pin_count"], 1)
            self.assertEqual(transfer["no_net_pin_count"], 0)
            self.assertEqual(transfer["driver_pin_count"], 1)
            self.assertEqual(transfer["no_driver_pin_count"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["vcd"], 1)
            self.assertEqual(transfer["driver_origin_counts"]["propagated"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["clock"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["constant"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["other"], 0)
            self.assertEqual(len(transfer["transferred"]), 1)
            self.assertEqual(
                transfer["transferred"][0]["full_name"], "pin_input_u_group_0"
            )
            self.assertEqual(transfer["transferred"][0]["source"], "vcd")
            self.assertEqual(len(transfer["scan_samples"]), 1)
            self.assertEqual(
                transfer["scan_samples"][0]["full_name"],
                "pin_input_u_group_0",
            )
            self.assertEqual(transfer["scan_samples"][0]["driver_origin"], "vcd")
            self.assertEqual(payload["macro_activity_origin_counts"]["transferred"], 1)
            self.assertEqual(payload["macro_trace_backed_pin_count"], 1)
            self.assertEqual(payload["macro_trace_active_pin_count"], 1)

    def test_tcl_counts_after_design_power(self) -> None:
        script = MODULE._tcl_script()
        totals_index = script.find("set totals [sta::design_power")
        loop_index = script.find("foreach pin")
        self.assertGreater(totals_index, -1)
        self.assertGreater(loop_index, -1)
        self.assertLess(totals_index, loop_index)
        self.assertIn(
            "set design_power_category_names {total sequential combinational clock macro pad}",
            script,
        )
        self.assertIn("design_power_quartets", script)
        self.assertIn("set power_corner [sta::cmd_corner]", script)
        self.assertIn("set totals [sta::design_power $power_corner]", script)
        self.assertIn("macro_trace_backed_zero_toggle_count", script)
        self.assertIn("leaf_activity_origin_counts", script)
        self.assertIn("macro_activity_origin_counts", script)
        self.assertIn("set all_design_pins_unsorted {}", script)
        self.assertIn("sta::instance_power", script)
        self.assertIn("sta::set_power_pin_activity", script)
        self.assertIn("sta::cmd_corner", script)
        self.assertIn("foreach pin $all_design_pins", script)
        self.assertIn("if {![string match \"*u_group_*\" $macro_pin_full_name]}", script)
        self.assertIn("sta::instance_power \"$leaf\" $power_corner", script)
        self.assertIn("non_finite_leaf_instance_power", script)
        self.assertIn("scan_samples", script)
        self.assertIn(
            "if {$origin_bucket == \"vcd\" || $origin_bucket == \"propagated\"}",
            script,
        )

    def test_tcl_has_initialised_leaf_cells_for_nonfinite_diagnostics(self) -> None:
        script = MODULE._tcl_script()
        init_idx = script.find("set leaf_cells {}")
        primary_catch_idx = script.find(
            'if {[catch {set leaf_cells [get_cells -hierarchical -filter "is_leaf"]}]}'
        )
        empty_check_idx = script.find("if {[llength $leaf_cells] == 0}")
        fallback_catch_idx = script.find(
            'if {[catch {set leaf_cells [get_cells -hierarchical *]}]}'
        )
        self.assertGreater(init_idx, -1)
        self.assertGreater(primary_catch_idx, -1)
        self.assertGreater(empty_check_idx, primary_catch_idx)
        self.assertGreater(fallback_catch_idx, empty_check_idx)
        self.assertLess(init_idx, primary_catch_idx)
        self.assertNotIn(
            "if {[catch {set leaf_cells [get_cells -hierarchical -filter \"is_leaf\"]}] ||",
            script,
        )

    def test_tcl_nonfinite_leaf_instance_fallback_keeps_diagnostics_nonfatal(self) -> None:
        script = MODULE._tcl_script()
        self.assertIn('set leaf_cells {}', script)
        self.assertIn('if {[catch {set leaf_cells [get_cells -hierarchical *]}]} {', script)
        self.assertIn("set leaf_cells {}", script, msg="Fallback catch should recover to empty diagnostics")
        self.assertIn(
            "set leaf_cells_unsorted $leaf_cells",
            script,
            "Sort fallback should preserve original list order",
        )
        self.assertIn(
            "if {[catch {set leaf_cells [lsort -dictionary $leaf_cells_unsorted]}]",
            script,
            "Dictionary sort is now guarded in diagnostics path",
        )
        self.assertIn(
            "if {[catch {set leaf_cells [lsort $leaf_cells_unsorted]}]",
            script,
            "Fallback sort is now guarded to avoid diagnostics abort",
        )
        self.assertIn("set leaf_cells $leaf_cells_unsorted", script)
        self.assertNotIn(
            "set leaf_cells [lsort $leaf_cells]",
            script,
            "Ungarded fallback sort would still be fatal",
        )

    def test_activity_annotation_provenance_is_preserved(self) -> None:
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
                        "annotatable_pin_count": 1000,
                        "leaf_annotatable_pin_count": 1000,
                        "leaf_trace_backed_pin_count": 12,
                        "vcd_annotated_pin_count": 12,
                    }
                ),
                encoding="utf-8",
            )
            completed = SimpleNamespace(
                returncode=0,
                stdout=(
                    "vcd 4\n"
                    "saif 1\n"
                    "input 2\n"
                    "unannotated 993\n"
                ),
                stderr="",
            )
            with mock.patch.object(MODULE, "ORFS_FLOW", orfs), mock.patch.object(
                MODULE.subprocess, "run", return_value=completed
            ) as run:
                payload = MODULE._run_openroad_phase(
                    design_config=config,
                    flow_variant="test",
                    vcd=vcd,
                    scope="tb/dut",
                    tcl=tcl,
                    result=result,
                    timeout_seconds=10,
            )
            self.assertEqual(run.call_args.args[0][0], "make")
            self.assertEqual(payload.get("vcd_annotated_pin_count"), 12)
            self.assertEqual(payload.get("direct_vcd_pin_count"), 4)
            self.assertEqual(payload.get("direct_annotatable_pin_count"), 1000)
            self.assertEqual(payload.get("leaf_direct_vcd_pin_count"), 4)
            self.assertEqual(payload.get("leaf_direct_annotatable_pin_count"), 1000)
            self.assertEqual(payload["direct_vcd_pin_count"], 4)
            self.assertEqual(payload["activity_annotation_counts"]["vcd"], 4)

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
                        "leaf_annotatable_pin_count": 1000,
                        "leaf_trace_backed_pin_count": 500,
                        "vcd_annotated_pin_count": 500,
                        "macro_trace_active_pin_count": 10,
                        "macro_annotatable_pin_count": 100,
                        "direct_annotatable_pin_count": 1000,
                        "direct_vcd_pin_count": 200,
                    },
                    {
                        "total_w": 3.0,
                        "internal_w": 1.5,
                        "switching_w": 1.2,
                        "leakage_w": 0.3,
                        "sdc_clock_period_ns": 8.0,
                        "annotatable_pin_count": 1000,
                        "leaf_annotatable_pin_count": 1000,
                        "leaf_trace_backed_pin_count": 400,
                        "vcd_annotated_pin_count": 400,
                        "macro_trace_active_pin_count": 8,
                        "macro_annotatable_pin_count": 100,
                        "direct_annotatable_pin_count": 1000,
                        "direct_vcd_pin_count": 160,
                    },
                    {
                        "total_w": 1.0,
                        "internal_w": 0.5,
                        "switching_w": 0.4,
                        "leakage_w": 0.1,
                        "sdc_clock_period_ns": 8.0,
                        "annotatable_pin_count": 1000,
                        "leaf_annotatable_pin_count": 1000,
                        "leaf_trace_backed_pin_count": 300,
                        "vcd_annotated_pin_count": 300,
                        "macro_trace_active_pin_count": 0,
                        "macro_annotatable_pin_count": 100,
                        "direct_annotatable_pin_count": 1000,
                        "direct_vcd_pin_count": 80,
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
            self.assertEqual(report["phases"][0]["vcd_annotation_coverage"], 0.5)
            self.assertAlmostEqual(
                report["phases"][0]["direct_vcd_annotation_coverage"],
                0.2,
            )
            self.assertTrue(report["phases"][0]["direct_vcd_annotation_pin_gate_pass"])
            self.assertTrue(report["phases"][0]["trace_coverage_gate_pass"])

    def test_build_report_gates_on_trace_backed_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": "0",
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                        "requires_macro_activity": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            vcd = root / "trace.vcd"
            vcd.write_text("$comment test $end\n", encoding="utf-8")
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = {
                "total_w": 1.0,
                "internal_w": 0.5,
                "switching_w": 0.4,
                "leakage_w": 0.1,
                "sdc_clock_period_ns": 8.0,
                "annotatable_pin_count": 1000,
                "leaf_annotatable_pin_count": 1000,
                "leaf_trace_backed_pin_count": 300,
                "vcd_annotated_pin_count": 300,
                "direct_annotatable_pin_count": 1000,
                "direct_vcd_pin_count": 300,
                "macro_trace_active_pin_count": 10,
                "macro_annotatable_pin_count": 1000,
            }
            with mock.patch.object(MODULE, "_phase_rows", return_value=[{
                "phase": "score_fill",
                "vcd": "trace.vcd",
                "vcd_sha256": "0000",
                "measured_cycles": 20,
                "full_context_cycles": 20,
                "requires_macro_activity": False,
                "_resolved_vcd": str(vcd),
            }]):
                with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                    report = MODULE.build_report(
                        manifest=manifest,
                        manifest_path=manifest_path,
                        design_config=design_config,
                        flow_variant="activity_test",
                        scope="tb/dut",
                        min_vcd_coverage=0.20,
                        min_vcd_pins=250,
                        min_macro_active_coverage=0.01,
                        min_macro_active_pins=2,
                        timeout_seconds=10,
            )
            self.assertTrue(report["promotion_gate_pass"])
            self.assertAlmostEqual(report["phases"][0]["vcd_annotation_coverage"], 0.3)
            self.assertEqual(report["phases"][0]["direct_vcd_annotation_coverage"], 0.3)

    def test_build_report_requires_direct_vcd_pin_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": "0",
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                        "requires_macro_activity": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            vcd = root / "trace.vcd"
            vcd.write_text("$comment test $end\n", encoding="utf-8")
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = {
                "total_w": 1.0,
                "internal_w": 0.5,
                "switching_w": 0.4,
                "leakage_w": 0.1,
                "sdc_clock_period_ns": 8.0,
                "annotatable_pin_count": 1000,
                "leaf_annotatable_pin_count": 1000,
                "leaf_trace_backed_pin_count": 900,
                "vcd_annotated_pin_count": 900,
                "direct_annotatable_pin_count": 1000,
                "direct_vcd_pin_count": 2,
                "macro_trace_active_pin_count": 10,
                "macro_annotatable_pin_count": 1000,
            }
            with mock.patch.object(
                MODULE,
                "_phase_rows",
                return_value=[
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": "0000",
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                        "requires_macro_activity": False,
                        "_resolved_vcd": str(vcd),
                    }
                ],
            ):
                with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                    report = MODULE.build_report(
                        manifest=manifest,
                        manifest_path=manifest_path,
                        design_config=design_config,
                        flow_variant="activity_test",
                        scope="tb/dut",
                        min_vcd_coverage=0.05,
                        min_vcd_pins=3,
                        min_macro_active_coverage=0.01,
                        min_macro_active_pins=2,
                        timeout_seconds=10,
                    )
            self.assertFalse(report["promotion_gate_pass"])
            phase = report["phases"][0]
            self.assertTrue(phase["trace_coverage_gate_pass"])
            self.assertFalse(phase["direct_vcd_annotation_pin_gate_pass"])
            self.assertFalse(phase["annotation_gate_pass"])

    def test_build_report_preserves_non_finite_power_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = {
                "total_w": 1.0,
                "internal_w": 0.5,
                "switching_w": 0.4,
                "leakage_w": 0.1,
                "sdc_clock_period_ns": 8.0,
                "annotatable_pin_count": 1000,
                "leaf_annotatable_pin_count": 1000,
                "leaf_trace_backed_pin_count": 500,
                "vcd_annotated_pin_count": 500,
                "macro_trace_active_pin_count": 10,
                "macro_annotatable_pin_count": 100,
                "design_power_quartets": {
                    "total": {
                        "internal_w": 0.5,
                        "switching_w": 0.4,
                        "leakage_w": 0.1,
                        "total_w": 1.0,
                    },
                },
                "non_finite_leaf_instance_power": {
                    "instance_count": 1,
                    "samples": [
                        {
                            "full_name": "u_group_a/u1",
                            "internal_w": "null",
                            "switching_w": "null",
                            "leakage_w": "null",
                            "total_w": "null",
                        },
                    ],
                },
            }
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
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
            phase_power = report["phases"][0]["power"]
            self.assertIn("non_finite_leaf_instance_power", phase_power)
            self.assertEqual(
                phase_power["non_finite_leaf_instance_power"]["instance_count"], 1
            )
            self.assertEqual(
                phase_power["design_power_quartets"]["total"]["total_w"], 1.0
            )
            self.assertIn("design_power_quartets", report["phases"][1]["power"])

    def test_write_markdown_includes_power_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            payload = {
                "status": "rejected_annotation_gate",
                "promotion_gate_pass": False,
                "clock_period_ns": 8.0,
                "full_context_cycles": 10,
                "full_context_latency_s": 0.001,
                "full_context_energy_j": 0.0,
                "phases": [
                    {
                        "phase": "finalize_result",
                        "measured_cycles": 10,
                        "full_context_cycles": 10,
                        "full_context_energy_j": 0.0,
                        "phase_gate_pass": False,
                        "trace_backed_vcd_annotation_coverage": 0.0,
                        "direct_vcd_annotation_coverage": 0.0,
                        "macro_trace_active_pin_count": 10,
                        "power": {
                            "total_w": 1.0,
                            "macro_trace_active_pin_count": 10,
                            "non_finite_leaf_instance_power": {
                                "instance_count": 2,
                                "samples": [
                                    {
                                        "full_name": "u_group_a/u1",
                                        "internal_w": 1.0,
                                        "switching_w": 1.0,
                                        "leakage_w": 1.0,
                                        "total_w": 1.0,
                                    }
                                ],
                            },
                        },
                    }
                ],
                "remaining_abstractions": [],
            }
            out_md = Path(temp_text) / "report.md"
            MODULE.write_markdown(payload, out_md)
            text = out_md.read_text(encoding="utf-8")
            self.assertIn("## Power Diagnostics", text)
            self.assertIn("`finalize_result` non-finite leaf-instance power samples", text)
            self.assertIn("u_group_a/u1", text)

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
                "direct_annotatable_pin_count": 100,
                "direct_vcd_pin_count": 80,
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
                "direct_annotatable_pin_count": 100,
                "direct_vcd_pin_count": 80,
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
