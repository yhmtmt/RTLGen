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
    def _macro_activity(
        self,
        *,
        phase_name: str,
        vcd: Path,
        overrides: dict[str, object] | None = None,
    ) -> dict[str, object]:
        sidecar: dict[str, object] = {
            "version": 1,
            "model": MODULE._FAKERAM_ACTIVITY_MODEL,
            "source_vcd_sha256": MODULE._sha256(vcd),
            "source_vcd": vcd.name,
            "scope": "tb/dut",
            "timescale_seconds": 1e-9,
            "active_start_tick": 0,
            "active_end_tick": 1000,
            "pins": [
                {
                    "full_name": f"{phase_name}_macro_u_group/u_pin_1",
                    "density_hz": 1_000_000.0,
                    "duty_cycle": 0.5,
                    "transition_count": 10.0,
                    "source": "vcd",
                }
            ],
        }
        if overrides is not None:
            sidecar.update(overrides)
        return sidecar

    def _write_macro_activity(self, root: Path, *, phase_name: str, vcd: Path) -> Path:
        sidecar = self._macro_activity(
            phase_name=phase_name,
            vcd=vcd,
        )
        path = root / f"{phase_name}.macro_activity.json"
        path.write_text(json.dumps(sidecar), encoding="utf-8")
        return path

    def _write_tcl_runtime_stub(
        self,
        root: Path,
        result: Path,
        *,
        macro_transfer: bool = False,
        macro_activity_tcl: Path | None = None,
        macro_transfer_pin_names: tuple[str, str, str] | None = None,
        all_pin_names: tuple[str, ...] | None = None,
        pin_properties: dict[str, dict[str, object]] | None = None,
        leaf_pin_map: dict[str, tuple[str, ...]] | None = None,
        leaf_specs: tuple[tuple[str, str, str], ...] | None = None,
    ) -> str:
        if leaf_specs is None:
            leaf_specs = (
                ("leaf_group[7]/instance_a", "reducer", "0.0 nan inf nan"),
                ("leaf_group_b/leaf_b", "other", "1.0 2.0 3.0 4.0"),
            )
        leaf_names = " ".join(f"{{{name}}}" for name, _ref, _value in leaf_specs)
        if pin_properties is None:
            pin_properties = {}
        if leaf_pin_map is None:
            leaf_pin_map = {}
        pin_property_overrides: list[str] = []
        for pin_name in sorted(pin_properties):
            config = pin_properties[pin_name]
            is_hierarchical = int(config.get("is_hierarchical", False))
            direction = str(config.get("direction", "output"))
            full_name = str(config.get("full_name", pin_name))
            activity = config.get("activity")
            if activity is None:
                pin_property_overrides.extend(
                    [
                        f"  if {{$obj eq {{{pin_name}}}}} {{",
                        f"    if {{$property eq \"is_hierarchical\"}} {{ return {is_hierarchical} }}",
                        f"    if {{$property eq \"direction\"}} {{ return \"{direction}\" }}",
                        f"    if {{$property eq \"full_name\"}} {{ return {{{full_name}}} }}",
                        "    if {$property eq \"activity\"} {",
                        f"      error \"forced_activity_query_error {pin_name}\"",
                        "    }",
                        "    return {}",
                        "  }",
                    ]
                )
            else:
                pin_property_overrides.extend(
                    [
                        f"  if {{$obj eq {{{pin_name}}}}} {{",
                        f"    if {{$property eq \"is_hierarchical\"}} {{ return {is_hierarchical} }}",
                        f"    if {{$property eq \"direction\"}} {{ return \"{direction}\" }}",
                        f"    if {{$property eq \"full_name\"}} {{ return {{{full_name}}} }}",
                        f"    if {{$property eq \"activity\"}} {{ return {{{activity}}} }}",
                        "    return {}",
                        "  }",
                    ]
                )
        leaf_pin_map_init_lines = ["set leaf_pin_map_dict {}"]
        for leaf, pins in sorted(leaf_pin_map.items()):
            leaf_pin_map_init_lines.append(
                "dict set leaf_pin_map_dict {{{}}} {{{}}}".format(
                    leaf,
                    " ".join("{" + pin + "}" for pin in pins),
                )
            )
        leaf_ref_name_cases = []
        leaf_instance_power_cases = []
        for leaf_name, ref_name, instance_power in leaf_specs:
            leaf_ref_name_cases.extend(
                [
                    f"    if {{$obj eq {{{leaf_name}}}}} {{",
                    f"      assert_non_empty_string {{{ref_name}}}",
                    f"      return {{{ref_name}}}",
                    "    }",
                ]
            )
            leaf_instance_power_cases.extend(
                [
                    f"    if {{$leaf eq {{{leaf_name}}}}} {{",
                    f"      return {{{instance_power}}}",
                    "    }",
                ]
            )
        if macro_transfer:
            if macro_transfer_pin_names is None:
                macro_transfer_pin_names = (
                    "pin_other_0",
                    "pin_input_u_group_0",
                    "pin_nonfinite_u_group",
                )
            input_pin = macro_transfer_pin_names[1]
            driver_pin = f"driver_{input_pin}"
            peer_pin = f"peer_{input_pin}"
            all_pins = list(macro_transfer_pin_names)
            net_pins = [driver_pin, peer_pin, input_pin]
            get_pins_body = [
                "  if {[lindex $args 0] eq \"-hierarchical\"} {",
                "    set pattern [lindex $args end]",
                "    if {$pattern eq \"*u_group_*\"} {",
                "      return {}",
                "    }",
                "  }",
                "  if {[lindex $args 0] eq \"-of_objects\"} {",
                "    set object [lindex $args end]",
                "    if {[dict exists $leaf_pin_map_dict $object]} {",
                "      return [dict get $leaf_pin_map_dict $object]",
                "    }",
                "    set net $object",
                "    if {$net eq {net_u_group_0}} {",
                f"      return {{{' '.join(net_pins)}}}",
                "    }",
                "    return {}",
                "  }",
                f"  return {{{' '.join(all_pins)}}}",
            ]
            pin_property_body = [
                f"  if {{$obj eq {{{input_pin}}}}} {{",
                "    if {$property eq \"is_hierarchical\"} { return 0 }",
                "    if {$property eq \"direction\"} { return \"input\" }",
                "    if {$property eq \"activity\"} { return {0.0 0.0 constant} }",
                "    if {$property eq \"full_name\"} { return $obj }",
                "  }",
                f"  if {{$obj eq {{{driver_pin}}}}} {{",
                "    if {$property eq \"activity\"} { return {0.4 0.9 other} }",
                "  }",
                f"  if {{$obj eq {{{peer_pin}}}}} {{",
                "    if {$property eq \"activity\"} { return {0.9 0.8 propagated} }",
                "  }",
            ]
            net_driver_body = [
                "  proc net_driver_pins {net} {",
                f"    if {{$net eq {{net_u_group_0}}}} {{ return {{{driver_pin}}} }}",
                "    return {}",
                "  }",
            ]
            net_and_activity_body = [
                "proc get_nets {args} {",
                f"  if {{[lindex $args 0] eq \"-of_objects\" && [lindex $args 1] eq {{{input_pin}}}}} {{",
                "    return {net_u_group_0}",
                "  }",
                "  return {}",
                "}",
            ]
        else:
            if all_pin_names is None:
                all_pins = ["pin_nonfinite_u_group"]
            else:
                all_pins = list(all_pin_names)
            get_pins_body = [
                "  if {[lindex $args 0] eq \"-of_objects\"} {",
                "    set object [lindex $args end]",
                "    if {[dict exists $leaf_pin_map_dict $object]} {",
                "      return [dict get $leaf_pin_map_dict $object]",
                "    }",
                "    return {}",
                "  }",
                f"  return {{{' '.join(all_pins)}}}",
            ]
            pin_property_body = []
            net_driver_body = []
            net_and_activity_body = []
        lines = [
            "",
            "proc load_design {args} {}",
            "proc read_spef {args} {}",
            "proc log_cmd {args} {}",
            "proc report_activity_annotation {} {}",
            "proc report_power {} {}",
            "proc get_clocks {args} {",
            "  return {clk}",
            "}",
            "proc get_full_name {leaf} {",
            "  return $leaf",
            "}",
            "proc assert_non_empty_string {value} {",
            "  if {$value eq \"\"} {",
            "    error \"assertion failed: expected non-empty string\"",
            "  }",
            "}",
            "set ::ref_name_query_count 0",
            *leaf_pin_map_init_lines,
            "set ::leaf_pin_map_dict $leaf_pin_map_dict",
            "proc get_pins {args} {",
            "  global leaf_pin_map_dict",
            *get_pins_body,
            "}",
            "proc get_property {obj property} {",
            *pin_property_body,
            *pin_property_overrides,
            "  if {[string match \"pin_*\" $obj]} {",
            "    if {$property eq \"is_hierarchical\"} {",
            "      return 0",
            "    }",
            "    if {$property eq \"direction\"} {",
            "      return \"output\"",
            "    }",
            "    if {$property eq \"activity\"} {",
            "      return {0.25 0.5 vcd}",
            "    }",
            "    if {$property eq \"full_name\"} {",
            "      return $obj",
            "    }",
            "    return {}",
            "  }",
            "  if {$property eq \"ref_name\"} {",
            "    incr ::ref_name_query_count",
            *leaf_ref_name_cases,
            "    return \"\"",
            "  }",
            "  if {$property eq \"is_leaf\"} {",
            "    return 1",
            "  }",
            "  if {$property eq \"name\"} {",
            "    return $obj",
            "  }",
            "  return {}",
            "}",
            *net_and_activity_body,
            "proc get_cells {args} {",
            "  error \"get_cells should not be used for nonfinite leaf scan\"",
            "}",
            "proc instance_power {args} {",
            "  error \"use sta::instance_power <leaf> <corner>\"",
            "}",
            "proc set_power_pin_activity {args} {",
            "  error \"use sta::set_power_pin_activity <pin> <density> <duty>\"",
            "}",
            "proc design_power {args} {",
            "  error \"use sta::design_power <corner>\"",
            "}",
            "proc corners {} {",
            "  error \"do not call sta::corners\"",
            "}",
            "namespace eval sta {",
            "  proc cmd_corner {} {",
            "    return corner0",
            "  }",
            "  proc design_power {corner} {",
            "    if {$corner ne \"corner0\"} {",
            "      error \"design_power corner mismatch: $corner\"",
            "    }",
            "    # First quartet has non-finite total, triggering sample capture.",
            "    return {1.0 2.0 3.0 nan 4.0 5.0 6.0 7.0}",
            "  }",
            "  proc instance_power {leaf corner} {",
            "    if {$corner ne \"corner0\"} {",
            "      error \"instance_power corner mismatch: $corner\"",
            "    }",
            *leaf_instance_power_cases,
            "    return {1.0 2.0 3.0 4.0}",
            "  }",
            "  proc set_power_pin_activity {pin density duty} {",
            "    lappend ::sta::power_pin_activity_calls [list $pin $density $duty]",
            "  }",
            "  proc corners {} {",
            "    return {corner0}",
            "  }",
            "  proc network_leaf_instances {} {",
            f"    return {{{leaf_names}}}",
            "  }",
            "  variable power_pin_activity_calls {}",
            *net_driver_body,
            "}",
            f"set ::env(SCRIPTS_DIR) \"{root / 'scripts'}\"",
            f"set ::env(RESULTS_DIR) \"{root}\"",
            f"set ::env(RTLGEN_ACTIVITY_VCD) \"{root / 'trace.vcd'}\"",
            f"set ::env(RTLGEN_ACTIVITY_SCOPE) \"tb/dut\"",
            f"set ::env(RTLGEN_ACTIVITY_RESULT) \"{result}\"",
            (
                f"set ::env(RTLGEN_MACRO_ACTIVITY_TCL) \"{macro_activity_tcl}\""
                if macro_activity_tcl is not None
                else "set ::env(RTLGEN_MACRO_ACTIVITY_TCL) \"\""
            ),
            MODULE._tcl_script(),
            "if {$::ref_name_query_count == 0} {",
            "  error \"assertion failed: expected at least one instance ref_name query\"",
            "}",
        ]
        return "\n".join(lines)

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
            self.assertEqual(sample["ref_name"], "reducer")
            self.assertIsNone(sample["switching_w"])
            self.assertEqual(diagnostics.get("non_leaf_skip_count"), 0)
            self.assertEqual(diagnostics["candidate_cell_count"], 2)
            self.assertEqual(diagnostics["checked_instance_power_count"], 2)
            self.assertGreater(diagnostics["checked_instance_power_count"], 0)
            self.assertEqual(diagnostics["finite_row_count"], 1)
            self.assertEqual(diagnostics["bad_shape_row_count"], 0)
            self.assertEqual(diagnostics["query_error_count"], 0)
            self.assertEqual(diagnostics["ref_name_query_error_count"], 0)
            self.assertEqual(len(diagnostics["ref_name_buckets"]), 1)
            self.assertEqual(diagnostics["ref_name_buckets"][0]["ref_name"], "reducer")
            self.assertEqual(diagnostics["ref_name_buckets"][0]["count"], 1)
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

    def test_tcl_script_activity_value_diagnostics_invalid_classification(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            pin_names = (
                "pin_query_error",
                "pin_malformed",
                "pin_nonfinite_toggle",
                "pin_negative_toggle",
                "pin_nonfinite_duty",
                "pin_duty_lt_zero",
                "pin_duty_gt_one",
                "pin_valid",
            )
            tcl_script = self._write_tcl_runtime_stub(
                root=root,
                result=result,
                all_pin_names=pin_names,
                pin_properties={
                    "pin_query_error": {"activity": None, "direction": "internal"},
                    "pin_malformed": {"activity": "0.5"},
                    "pin_nonfinite_toggle": {"activity": "nan 0.5 vcd"},
                    "pin_negative_toggle": {"activity": "-0.2 0.5 vcd"},
                    "pin_nonfinite_duty": {"activity": "0.2 nan vcd"},
                    "pin_duty_lt_zero": {"activity": "0.2 -0.1 vcd"},
                    "pin_duty_gt_one": {"activity": "0.2 1.2 vcd"},
                    "pin_valid": {"activity": "0.8 0.4 vcd"},
                },
            )
            tcl_script_path = root / "activity_power.tcl"
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
            diag = payload["activity_value_diagnostics"]
            self.assertEqual(diag["queried_pin_count"], 8)
            self.assertEqual(diag["malformed_activity_tuple_count"], 1)
            self.assertEqual(diag["query_error_count"], 1)
            self.assertEqual(diag["non_finite_toggle_count"], 1)
            self.assertEqual(diag["negative_toggle_count"], 1)
            self.assertEqual(diag["non_finite_duty_count"], 1)
            self.assertEqual(diag["duty_less_than_zero_count"], 1)
            self.assertEqual(diag["duty_greater_than_one_count"], 1)
            self.assertEqual(diag["valid_pin_count"], 1)
            self.assertEqual(diag["finite_extrema"]["min_toggle"], 0.8)
            self.assertEqual(diag["finite_extrema"]["max_toggle"], 0.8)
            self.assertEqual(diag["finite_extrema"]["min_duty"], 0.4)
            self.assertEqual(diag["finite_extrema"]["max_duty"], 0.4)
            self.assertEqual(len(diag["samples"]), 7)
            reasons = {sample["reason"] for sample in diag["samples"]}
            self.assertEqual(
                reasons,
                {
                    "query_error",
                    "malformed_activity_tuple",
                    "non_finite_toggle",
                    "negative_toggle",
                    "non_finite_duty",
                    "duty_lt_zero",
                    "duty_gt_one",
                },
            )
            self.assertEqual(len(diag["valid_samples"]), 1)
            sample_fields = diag["samples"][0]
            self.assertEqual(
                set(sample_fields),
                {"full_name", "toggle", "duty", "origin", "reason"},
            )
            valid_sample = diag["valid_samples"][0]
            self.assertEqual(
                set(valid_sample),
                {"full_name", "toggle", "duty", "origin", "reason"},
            )

    def test_tcl_script_activity_value_diagnostics_samples_are_bounded_and_deterministic(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            valid_pin_names = tuple(f"pin[{i:03d}]" for i in range(20))
            invalid_pin_name = "pin[999]"
            pin_names = valid_pin_names + (invalid_pin_name,)
            pin_properties = {
                pin_name: {"activity": f"{i / 100:.3f} 0.2 vcd"}
                for i, pin_name in enumerate(valid_pin_names)
            }
            pin_properties[invalid_pin_name] = {"activity": "nan 0.2 vcd"}
            tcl_script = self._write_tcl_runtime_stub(
                root=root,
                result=result,
                all_pin_names=pin_names,
                pin_properties=pin_properties,
            )
            tcl_script_path = root / "activity_power.tcl"
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
            diag = payload["activity_value_diagnostics"]
            self.assertEqual(diag["queried_pin_count"], 21)
            self.assertEqual(diag["valid_pin_count"], 20)
            self.assertEqual(len(diag["samples"]), 1)
            self.assertEqual(diag["samples"][0]["reason"], "non_finite_toggle")
            self.assertEqual(diag["samples"][0]["full_name"], invalid_pin_name)
            self.assertEqual(len(diag["valid_samples"]), 4)
            self.assertEqual(diag["valid_samples"][0]["full_name"], "pin[000]")
            self.assertEqual(diag["valid_samples"][3]["full_name"], "pin[003]")
            self.assertEqual(diag["finite_extrema"]["min_toggle"], 0.0)
            self.assertEqual(diag["finite_extrema"]["max_toggle"], 0.19)

    def test_tcl_script_pin_activity_nested_diagnostics_for_nonfinite_leaf(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            leaf_specs = (
                ("leaf_group_7/instance_a", "reducer", "nan nan nan nan"),
                ("leaf_group_b/leaf_b", "other", "1.0 2.0 3.0 4.0"),
                ("leaf_group_c/leaf_c", "other", "1.0 2.0 3.0 4.0"),
            )
            tcl_script = self._write_tcl_runtime_stub(
                root=root,
                result=result,
                leaf_specs=leaf_specs,
                leaf_pin_map={
                    "leaf_group_7/instance_a": (
                        "pin_query_error",
                        "pin_malformed",
                        "pin_nonfinite_toggle",
                        "pin_negative_toggle",
                        "pin_nonfinite_duty",
                        "pin_duty_lt_zero",
                        "pin_duty_gt_one",
                        "pin_valid",
                    )
                },
                pin_properties={
                    "pin_query_error": {"activity": None, "direction": "internal"},
                    "pin_malformed": {"activity": "0.5", "direction": "output"},
                    "pin_nonfinite_toggle": {
                        "activity": "nan 0.4 vcd",
                        "direction": "output",
                    },
                    "pin_negative_toggle": {
                        "activity": "-0.2 0.5 vcd",
                        "direction": "output",
                    },
                    "pin_nonfinite_duty": {
                        "activity": "0.2 nan vcd",
                        "direction": "output",
                    },
                    "pin_duty_lt_zero": {
                        "activity": "0.2 -0.1 vcd",
                        "direction": "output",
                    },
                    "pin_duty_gt_one": {
                        "activity": "0.2 1.2 vcd",
                        "direction": "output",
                    },
                    "pin_valid": {
                        "activity": "0.2 0.5 vcd",
                        "direction": "output",
                    },
                },
            )
            tcl_script_path = root / "activity_power.tcl"
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
            diag = payload["non_finite_leaf_instance_power"]
            self.assertEqual(diag["instance_count"], 1)
            pin_diag = diag["pin_activity"]
            self.assertEqual(pin_diag["inspected_pin_count"], 8)
            self.assertEqual(pin_diag["malformed_activity_tuple_count"], 1)
            self.assertEqual(pin_diag["query_error_count"], 1)
            self.assertEqual(pin_diag["non_finite_toggle_count"], 1)
            self.assertEqual(pin_diag["negative_toggle_count"], 1)
            self.assertEqual(pin_diag["non_finite_duty_count"], 1)
            self.assertEqual(pin_diag["duty_less_than_zero_count"], 1)
            self.assertEqual(pin_diag["duty_greater_than_one_count"], 1)
            self.assertEqual(pin_diag["valid_pin_count"], 1)
            self.assertEqual(pin_diag["finite_extrema"]["min_toggle"], 0.2)
            self.assertEqual(pin_diag["finite_extrema"]["max_toggle"], 0.2)
            self.assertEqual(pin_diag["finite_extrema"]["min_duty"], 0.5)
            self.assertEqual(pin_diag["finite_extrema"]["max_duty"], 0.5)
            self.assertEqual(len(pin_diag["samples"]), 7)
            self.assertEqual(len(pin_diag["valid_samples"]), 1)
            sample_reasons = {sample["reason"] for sample in pin_diag["samples"]}
            self.assertEqual(
                sample_reasons,
                {
                    "query_error",
                    "malformed_activity_tuple",
                    "non_finite_toggle",
                    "negative_toggle",
                    "non_finite_duty",
                    "duty_lt_zero",
                    "duty_gt_one",
                },
            )
            sample = pin_diag["samples"][0]
            self.assertIn("instance", sample)
            self.assertIn("ref", sample)
            self.assertIn("pin", sample)
            self.assertIn("direction", sample)
            self.assertIn("activity", sample)
            valid_sample = pin_diag["valid_samples"][0]
            self.assertEqual(
                set(valid_sample),
                {"instance", "ref", "pin", "direction", "activity", "reason"},
            )

    def test_tcl_script_ref_name_buckets_are_sorted_and_bounded(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            ref_names = [
                "10",
                "2",
                "1",
                "11",
                "20",
                "3",
                "30",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "001",
                "002",
                "003",
                "004",
                "005",
                "006",
                "007",
                "008",
                "009",
                "010",
                "011",
                "012",
                "013",
                "014",
                "015",
                "016",
                "017",
                "018",
                "019",
                "020",
                "021",
                "022",
            ]
            leaf_specs = tuple(
                (
                    f"leaf_group[7]/instance_{index:03d}",
                    ref_name,
                    "nan nan nan nan",
                )
                for index, ref_name in enumerate(ref_names)
            )
            tcl_script_path = root / "activity_power.tcl"
            tcl_script = self._write_tcl_runtime_stub(
                root=root, result=result, leaf_specs=leaf_specs
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
            diagnostics = payload["non_finite_leaf_instance_power"]
            self.assertEqual(diagnostics["instance_count"], 35)
            self.assertEqual(diagnostics["checked_instance_power_count"], 35)
            self.assertEqual(diagnostics["ref_name_query_error_count"], 0)
            buckets = diagnostics["ref_name_buckets"]
            self.assertEqual(len(buckets), 32)
            bucket_names = [bucket["ref_name"] for bucket in buckets]
            self.assertEqual(bucket_names[-1], "other")
            self.assertEqual(buckets[-1]["count"], 4)
            sorted_ref_names = sorted(ref_names)
            self.assertEqual(sorted_ref_names[30], "5")
            self.assertEqual([bucket["ref_name"] for bucket in buckets[:-1]], sorted_ref_names[:31])
            self.assertEqual(len(diagnostics["samples"]), 16)
            self.assertEqual(diagnostics["samples"][0]["ref_name"], ref_names[0])

    def test_tcl_script_transfers_macro_input_activity(self) -> None:
        if shutil.which("tclsh") is None:
            self.skipTest("tclsh is required for Tcl runtime regression")

        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "load.tcl").write_text("", encoding="utf-8")

            result = root / "activity_power.json"
            macro_activity_tcl = root / "macro_activity.tcl"
            macro_activity_tcl.write_text(
                "set rtlgen_macro_activity_assignments {\n"
                "  {pin_input_u_group[7]/dq[3] 1.234 0.5 8.9}\n"
                "}\n",
                encoding="utf-8",
            )
            tcl_script_path = root / "activity_power.tcl"
            tcl_script = self._write_tcl_runtime_stub(
                root=root,
                result=result,
                macro_transfer=True,
                macro_activity_tcl=macro_activity_tcl,
                macro_transfer_pin_names=(
                    "pin_other_0",
                    "pin_input_u_group[7]/dq[3]",
                    "pin_nonfinite_u_group",
                ),
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
            self.assertEqual(transfer["candidate_count"], 0)
            self.assertEqual(transfer["applied_count"], 1)
            self.assertEqual(transfer["query_error_count"], 0)
            self.assertEqual(transfer["apply_error_count"], 0)
            self.assertEqual(transfer["structural_assignment_count"], 1)
            self.assertEqual(transfer["structural_matched_count"], 1)
            self.assertEqual(transfer["structural_applied_count"], 1)
            self.assertEqual(transfer["structural_unmatched_count"], 0)
            self.assertEqual(transfer["structural_query_error_count"], 0)
            self.assertEqual(transfer["structural_apply_error_count"], 0)
            self.assertEqual(transfer["source_vcd_count"], 1)
            self.assertEqual(transfer["source_propagated_count"], 0)
            self.assertEqual(transfer["active_count"], 1)
            self.assertEqual(transfer["zero_count"], 0)
            self.assertEqual(transfer["scanned_pin_count"], 3)
            self.assertEqual(transfer["name_match_pin_count"], 0)
            self.assertEqual(transfer["input_pin_count"], 0)
            self.assertEqual(transfer["connected_pin_count"], 0)
            self.assertEqual(transfer["no_net_pin_count"], 0)
            self.assertEqual(transfer["driver_pin_count"], 0)
            self.assertEqual(transfer["no_driver_pin_count"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["vcd"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["propagated"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["clock"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["constant"], 0)
            self.assertEqual(transfer["driver_origin_counts"]["other"], 0)
            self.assertEqual(transfer["peer_origin_counts"]["vcd"], 0)
            self.assertEqual(transfer["peer_origin_counts"]["propagated"], 0)
            self.assertEqual(transfer["peer_origin_counts"]["clock"], 0)
            self.assertEqual(transfer["peer_origin_counts"]["constant"], 0)
            self.assertEqual(transfer["peer_origin_counts"]["other"], 0)
            self.assertEqual(transfer["peer_pin_examined_count"], 0)
            self.assertEqual(transfer["peer_eligible_count"], 0)
            self.assertEqual(len(transfer["transferred"]), 1)
            self.assertEqual(
                transfer["transferred"][0]["full_name"], "pin_input_u_group[7]/dq[3]"
            )
            self.assertEqual(transfer["transferred"][0]["source"], "vcd")
            self.assertEqual(
                transfer["transferred"][0]["source_kind"], "structural_vcd_sidecar"
            )
            self.assertEqual(len(transfer["scan_samples"]), 1)
            self.assertEqual(
                transfer["scan_samples"][0]["full_name"],
                "pin_input_u_group[7]/dq[3]",
            )
            self.assertEqual(
                transfer["scan_samples"][0]["driver_origin"], "structural_vcd_sidecar"
            )
            self.assertEqual(
                transfer["scan_samples"][0]["source_kind"], "structural_vcd_sidecar"
            )
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
        self.assertIn("sta::network_leaf_instances", script)
        self.assertIn("scan_samples", script)
        self.assertIn(
            "if {$origin_bucket == \"vcd\" || $origin_bucket == \"propagated\"}",
            script,
        )

    def test_tcl_has_initialised_leaf_cells_for_nonfinite_diagnostics(self) -> None:
        script = MODULE._tcl_script()
        init_idx = script.find("set leaf_cells {}")
        primary_catch_idx = script.find(
            'if {[catch {set leaf_cells [sta::network_leaf_instances]}]}'
        )
        self.assertGreater(init_idx, -1)
        self.assertGreater(primary_catch_idx, -1)
        self.assertLess(init_idx, primary_catch_idx)
        self.assertNotIn(
            "if {[catch {set leaf_cells [get_cells -hierarchical -filter \"is_leaf\"]}] ||",
            script,
        )
        self.assertNotIn("get_cells -hierarchical -filter \"is_leaf\"", script)
        self.assertNotIn("get_cells -hierarchical *", script)

    def test_tcl_nonfinite_leaf_instance_fallback_keeps_diagnostics_nonfatal(self) -> None:
        script = MODULE._tcl_script()
        self.assertIn('set leaf_cells {}', script)
        self.assertIn(
            'if {[catch {set leaf_cells [sta::network_leaf_instances]}]} {',
            script,
        )
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
        self.assertNotIn("get_cells -hierarchical -filter \"is_leaf\"", script)
        self.assertNotIn("get_cells -hierarchical *", script)

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
            macro_activity = self._write_macro_activity(
                root=root,
                phase_name=name,
                vcd=vcd,
            )
            phases.append(
                {
                    "phase": name,
                    "vcd": vcd.name,
                    "vcd_sha256": MODULE._sha256(vcd),
                    "macro_activity": macro_activity.name,
                    "macro_activity_sha256": MODULE._sha256(macro_activity),
                    "measured_cycles": measured,
                    "full_context_cycles": full,
                }
            )
        manifest = {"clock_period_ns": 8.0, "phases": phases}
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest, path

    def _with_structural_macro_transfer(
        self,
        power: dict[str, object],
        assignment_count: int,
    ) -> dict[str, object]:
        payload = dict(power)
        payload["macro_pin_transfer"] = {
            "structural_assignment_count": assignment_count,
            "structural_matched_count": assignment_count,
            "structural_applied_count": assignment_count,
            "structural_unmatched_count": 0,
            "structural_query_error_count": 0,
            "structural_apply_error_count": 0,
        }
        return payload

    def _assert_no_full_pin_arrays_in_phase_payload(self, phase: dict[str, object]) -> None:
        self.assertNotIn("macro_activity_rows", phase)
        for key, value in phase.items():
            if not isinstance(value, list):
                continue
            if any(isinstance(item, dict) and "full_name" in item for item in value):
                self.fail(f"phase payload leaked full pin array '{key}'")

    def test_phase_manifest_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, path = self._fixture(root)
            manifest["phases"][0]["vcd_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                MODULE._phase_rows(manifest, path)

    def test_phase_manifest_rejects_macro_activity_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, path = self._fixture(root)
            manifest["phases"][0]["macro_activity_sha256"] = "f" * 64
            with self.assertRaisesRegex(ValueError, "macro activity hash mismatch"):
                MODULE._phase_rows(manifest, path)

    def test_phase_manifest_rejects_missing_macro_activity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, path = self._fixture(root)
            manifest["phases"][0].pop("macro_activity")
            with self.assertRaisesRegex(ValueError, "macro_activity"):
                MODULE._phase_rows(manifest, path)

    def test_phase_rows_rejects_invalid_macro_activity_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={
                            "pins": [
                                {
                                    "full_name": "",
                                    "density_hz": -1.0,
                                    "duty_cycle": 1.2,
                                    "transition_count": float("nan"),
                                    "source": "vcd",
                                }
                            ],
                        },
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "full_name"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"version": 2},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "version"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_source_vcd_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"source_vcd": "other_trace.vcd"},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_vcd"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_scope_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"scope": ""},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "scope"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_timescale_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"timescale_seconds": -1.0},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "timescale_seconds"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_active_tick_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"active_end_tick": 10, "active_start_tick": 10},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "active range"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_rejects_macro_activity_active_ticks_non_integer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$enddefinitions $end\n", encoding="utf-8")
            invalid_sidecar = root / "bad_macro_activity.json"
            invalid_sidecar.write_text(
                json.dumps(
                    self._macro_activity(
                        phase_name="score_fill",
                        vcd=vcd,
                        overrides={"active_end_tick": 10.5},
                    )
                ),
                encoding="utf-8",
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": "trace.vcd",
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": str(invalid_sidecar),
                        "macro_activity_sha256": MODULE._sha256(invalid_sidecar),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "active_start_tick|active_end_tick|integer"):
                MODULE._phase_rows(manifest, manifest_path)

    def test_phase_rows_stores_macro_activity_rows_privately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, path = self._fixture(root)
            rows = MODULE._phase_rows(manifest, path)
            self.assertEqual(len(rows), 3)
            phase = rows[0]
            self.assertIn("_macro_activity_rows", phase)
            self.assertNotIn("macro_activity_rows", phase)
            self.assertEqual(
                phase["macro_activity_assignment_count"], len(phase["_macro_activity_rows"])
            )

    def test_build_report_fails_if_structural_macro_activity_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            vcd = root / "trace.vcd"
            vcd.write_text("$comment score_fill $end\n", encoding="utf-8")
            macro_activity = self._write_macro_activity(
                root=root,
                phase_name="score_fill",
                vcd=vcd,
            )
            manifest = {
                "clock_period_ns": 8.0,
                "phases": [
                    {
                        "phase": "score_fill",
                        "vcd": vcd.name,
                        "vcd_sha256": MODULE._sha256(vcd),
                        "macro_activity": macro_activity.name,
                        "macro_activity_sha256": MODULE._sha256(macro_activity),
                        "measured_cycles": 20,
                        "full_context_cycles": 20,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = self._with_structural_macro_transfer(
                {
                    "total_w": 1.0,
                    "internal_w": 0.5,
                    "switching_w": 0.5,
                    "leakage_w": 0.0,
                    "sdc_clock_period_ns": 8.0,
                    "annotatable_pin_count": 1000,
                    "leaf_annotatable_pin_count": 1000,
                    "leaf_trace_backed_pin_count": 1000,
                    "vcd_annotated_pin_count": 1000,
                    "macro_trace_active_pin_count": 100,
                    "macro_annotatable_pin_count": 100,
                    "direct_annotatable_pin_count": 1000,
                    "direct_vcd_pin_count": 1000,
                },
                assignment_count=1,
            )
            assert isinstance(power.get("macro_pin_transfer"), dict)
            power["macro_pin_transfer"]["structural_applied_count"] = 0
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                report = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.5,
                    min_vcd_pins=1,
                    min_macro_active_coverage=0.5,
                    min_macro_active_pins=1,
                    timeout_seconds=10,
                )
            phase = report["phases"][0]
            self.assertFalse(phase["structural_macro_activity_gate_pass"])
            self.assertFalse(phase["phase_gate_pass"])
            self.assertFalse(report["promotion_gate_pass"])

    def test_build_report_omits_pin_arrays_from_phase_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=self._with_structural_macro_transfer(
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
                assignment_count=1,
            )):
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
            for phase in report["phases"]:
                self._assert_no_full_pin_arrays_in_phase_payload(phase)
                self.assertTrue(phase["structural_macro_activity_gate_pass"])

    def test_build_report_accounts_phase_energy_and_gates_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power_rows = iter(
                [
                    self._with_structural_macro_transfer(
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
                        assignment_count=1,
                    ),
                    self._with_structural_macro_transfer(
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
                        assignment_count=1,
                    ),
                    self._with_structural_macro_transfer(
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
                        assignment_count=1,
                    ),
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

    def test_build_report_gates_unchanged_when_activity_value_diagnostics_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = self._with_structural_macro_transfer(
                {
                    "total_w": 1.5,
                    "internal_w": 0.7,
                    "switching_w": 0.5,
                    "leakage_w": 0.3,
                    "sdc_clock_period_ns": 8.0,
                    "annotatable_pin_count": 1000,
                    "leaf_annotatable_pin_count": 1000,
                    "leaf_trace_backed_pin_count": 400,
                    "vcd_annotated_pin_count": 400,
                    "direct_annotatable_pin_count": 1000,
                    "direct_vcd_pin_count": 400,
                    "macro_trace_active_pin_count": 64,
                    "macro_annotatable_pin_count": 1000,
                    "activity_value_diagnostics": {
                        "queried_pin_count": 2,
                        "malformed_activity_tuple_count": 1,
                        "query_error_count": 1,
                        "samples": [
                            {
                                "full_name": "pin_a",
                                "toggle": 0.1,
                                "duty": 0.2,
                                "origin": "vcd",
                                "reason": "query_error",
                            }
                        ],
                    },
                },
                assignment_count=1,
            )
            power_with_diag = dict(power)
            power_with_diag["activity_value_diagnostics"] = dict(power_with_diag["activity_value_diagnostics"])
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power):
                report_without_diag = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.25,
                    min_vcd_pins=400,
                    min_macro_active_coverage=0.05,
                    min_macro_active_pins=8,
                    timeout_seconds=10,
                )
            with mock.patch.object(MODULE, "_run_openroad_phase", return_value=power_with_diag):
                report_with_diag = MODULE.build_report(
                    manifest=manifest,
                    manifest_path=manifest_path,
                    design_config=design_config,
                    flow_variant="activity_test",
                    scope="tb/dut",
                    min_vcd_coverage=0.25,
                    min_vcd_pins=400,
                    min_macro_active_coverage=0.05,
                    min_macro_active_pins=8,
                    timeout_seconds=10,
                )
            self.assertEqual(report_without_diag["promotion_gate_pass"], report_with_diag["promotion_gate_pass"])
            self.assertTrue(report_with_diag["promotion_gate_pass"])
            for index, phase_without_diag in enumerate(report_without_diag["phases"]):
                phase_with_diag = report_with_diag["phases"][index]
                self.assertEqual(
                    phase_without_diag["phase_gate_pass"],
                    phase_with_diag["phase_gate_pass"],
                )
                self.assertEqual(
                    phase_without_diag["structural_macro_activity_gate_pass"],
                    phase_with_diag["structural_macro_activity_gate_pass"],
                )

    def test_build_report_preserves_non_finite_power_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_text:
            root = Path(temp_text)
            manifest, manifest_path = self._fixture(root)
            design_config = root / "config.mk"
            design_config.write_text("", encoding="utf-8")
            power = self._with_structural_macro_transfer(
                {
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
                },
                assignment_count=1,
            )
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
            power = self._with_structural_macro_transfer(
                {
                    "total_w": 1.0,
                    "sdc_clock_period_ns": 8.0,
                    "annotatable_pin_count": 100,
                    "vcd_annotated_pin_count": 80,
                    "macro_trace_active_pin_count": 1,
                    "macro_annotatable_pin_count": 100,
                    "direct_annotatable_pin_count": 100,
                    "direct_vcd_pin_count": 80,
                },
                assignment_count=1,
            )
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
            power = self._with_structural_macro_transfer(
                {
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
                },
                assignment_count=1,
            )
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
