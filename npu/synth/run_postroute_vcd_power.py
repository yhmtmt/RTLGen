#!/usr/bin/env python3
"""Measure post-route power from explicit phase VCD activity.

This utility intentionally lives outside the normal PPA sweep.  A regular
``run_block_sweep.py`` result remains vectorless; only this command may turn a
functional simulation trace into activity-backed power evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any


JsonDict = dict[str, Any]
ORFS_FLOW = Path(os.environ.get("ORFS_FLOW", "/orfs/flow"))


def _load_json(path: Path) -> JsonDict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return raw


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _activity_annotation_counts(stdout: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in stdout.splitlines():
        match = re.fullmatch(r"\s*(vcd|saif|input|unannotated)\s+(\d+)\s*", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def _phase_rows(manifest: JsonDict, manifest_path: Path) -> list[JsonDict]:
    raw_phases = manifest.get("phases")
    if not isinstance(raw_phases, list) or not raw_phases:
        raise ValueError("activity manifest requires a non-empty phases[]")
    rows: list[JsonDict] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_phases):
        if not isinstance(raw, dict):
            raise ValueError(f"phases[{index}] must be an object")
        phase = str(raw.get("phase", raw.get("name", ""))).strip()
        if not phase or phase in seen:
            raise ValueError(f"invalid or duplicate phase name at phases[{index}]")
        seen.add(phase)
        vcd_value = str(raw.get("vcd", raw.get("vcd_path", ""))).strip()
        if not vcd_value:
            raise ValueError(f"phase {phase} is missing vcd/vcd_path")
        vcd = Path(vcd_value)
        if not vcd.is_absolute():
            vcd = (manifest_path.parent / vcd).resolve()
        if not vcd.is_file():
            raise FileNotFoundError(f"phase VCD does not exist: {vcd}")
        expected_hash = str(raw.get("vcd_sha256", "")).strip().lower()
        actual_hash = _sha256(vcd)
        if expected_hash and expected_hash != actual_hash:
            raise ValueError(
                f"phase {phase} VCD hash mismatch: expected {expected_hash}, got {actual_hash}"
            )
        measured_cycles = int(raw.get("measured_cycles", raw.get("trace_cycles", 0)))
        scaling = raw.get("scaling") if isinstance(raw.get("scaling"), dict) else {}
        full_context_cycles = int(
            raw.get("full_context_cycles", scaling.get("full_context_cycles", 0))
        )
        if measured_cycles <= 0 or full_context_cycles <= 0:
            raise ValueError(
                f"phase {phase} requires positive measured_cycles and full_context_cycles"
            )
        rows.append(
            {
                **raw,
                "phase": phase,
                "vcd": vcd_value,
                "_resolved_vcd": str(vcd),
                "vcd_sha256": actual_hash,
                "measured_cycles": measured_cycles,
                "full_context_cycles": full_context_cycles,
                "requires_macro_activity": bool(
                    raw.get("requires_macro_activity", phase in {"score_fill", "replay_value"})
                ),
            }
        )
    return rows


def _tcl_script() -> str:
    return r'''source $::env(SCRIPTS_DIR)/load.tcl
load_design 6_final.odb 6_final.sdc
read_spef $::env(RESULTS_DIR)/6_final.spef
log_cmd read_vcd -scope $::env(RTLGEN_ACTIVITY_SCOPE) $::env(RTLGEN_ACTIVITY_VCD)

proc rtlgen_json_number {value} {
  if {[string match -nocase "*nan*" "$value"] ||
      [string match -nocase "*inf*" "$value"]} {
    return "null"
  }
  if {[catch {format "%.12g" $value} formatted]} {
    return "null"
  }
  return $formatted
}

proc rtlgen_json_escape {value} {
  return [string map {"\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"} $value]
}

proc rtlgen_json_escape_array_literal_chars {value} {
  return [string map {"[" "\\u005B" "]" "\\u005D"} $value]
}

proc rtlgen_is_finite_power_value {value} {
  if {[catch {set numeric_value [expr {double($value)}]}]} {
    return 0
  }
  if {$numeric_value != $numeric_value} {
    return 0
  }
  if {$numeric_value == Inf || $numeric_value == -Inf} {
    return 0
  }
  return 1
}

proc rtlgen_activity_origin_bucket {origin} {
  if {$origin == "vcd"} {
    return "vcd"
  }
  if {$origin == "propagated"} {
    return "propagated"
  }
  if {$origin == "clock"} {
    return "clock"
  }
  if {$origin == "constant"} {
    return "constant"
  }
  return "other"
}

proc rtlgen_sorted_list {values} {
  if {[catch {lsort -dictionary $values} sorted]} {
    if {[catch {lsort $values} sorted]} {
      set sorted $values
    }
  }
  return $sorted
}

proc rtlgen_apply_macro_pin_activities {assignments} {
  set results {}
  if {[llength $assignments] == 0} {
    return $results
  }
  foreach assignment $assignments {
    if {[llength $assignment] < 4} {
      lappend results [list {} 0]
      continue
    }
    lassign $assignment pin_full_name pin density duty
    if {[catch {sta::set_power_pin_activity $pin $density $duty}]} {
      lappend results [list $pin_full_name 0]
      continue
    }
    lappend results [list $pin_full_name 1]
  }
  return $results
}

set power_corner [sta::cmd_corner]
set totals [sta::design_power $power_corner]
set design_power_category_names {total sequential combinational clock macro pad}
set design_power_category_count [expr {[llength $totals] / 4}]
set design_power_totals [lrange $totals 0 3]
set all_design_pins_unsorted {}
set macro_pin_transfer_query_error_count 0
if {[catch {set all_design_pins_unsorted [get_pins -hierarchical *]}]} {
  incr macro_pin_transfer_query_error_count
  set all_design_pins_unsorted {}
}
set all_design_pins [rtlgen_sorted_list $all_design_pins_unsorted]
set macro_pin_transfer_scanned_pin_count [llength $all_design_pins]
set macro_pin_transfer_name_match_count 0
set macro_pin_transfer_input_pin_count 0
set macro_pin_transfer_connected_pin_count 0
set macro_pin_transfer_no_net_count 0
set macro_pin_transfer_driver_pin_count 0
set macro_pin_transfer_no_driver_count 0
set macro_pin_transfer_driver_origin_vcd_count 0
set macro_pin_transfer_driver_origin_propagated_count 0
set macro_pin_transfer_driver_origin_clock_count 0
set macro_pin_transfer_driver_origin_constant_count 0
set macro_pin_transfer_driver_origin_other_count 0
set macro_pin_transfer_scan_sample_limit 16
set macro_pin_transfer_scan_samples {}

set macro_pin_transfer_peer_pin_count 0
set macro_pin_transfer_peer_eligible_count 0
set macro_pin_transfer_peer_origin_vcd_count 0
set macro_pin_transfer_peer_origin_propagated_count 0
set macro_pin_transfer_peer_origin_clock_count 0
set macro_pin_transfer_peer_origin_constant_count 0
set macro_pin_transfer_peer_origin_other_count 0

set macro_pin_transfer_candidate_count 0
set macro_pin_transfer_applied_count 0
set macro_pin_transfer_source_vcd_count 0
set macro_pin_transfer_source_propagated_count 0
set macro_pin_transfer_active_count 0
set macro_pin_transfer_zero_count 0
set macro_pin_transfer_apply_error_count 0
set macro_pin_transfer_records {}
set macro_pin_transfer_updates {}
set macro_pin_transfer_candidate_source_by_full_name {}
set macro_pin_transfer_candidate_source_kind_by_full_name {}
set macro_pin_transfer_candidate_toggle_by_full_name {}
set macro_pin_transfer_source_by_full_name {}
set macro_pin_transfer_toggle_by_full_name {}
set macro_pin_transfer_source_kind_by_full_name {}
set macro_pin_transfer_apply_results {}
foreach macro_pin $all_design_pins {
  if {[catch {set is_hierarchical [get_property $macro_pin is_hierarchical]}]} {
    incr macro_pin_transfer_query_error_count
    continue
  }
  if {$is_hierarchical} {
    continue
  }
  if {[catch {set macro_pin_full_name [get_property $macro_pin full_name]}]} {
    incr macro_pin_transfer_query_error_count
    continue
  }
  if {![string match "*u_group_*" $macro_pin_full_name]} {
    continue
  }
  incr macro_pin_transfer_name_match_count
  if {[catch {set direction [get_property $macro_pin direction]}]} {
    incr macro_pin_transfer_query_error_count
    continue
  }
  if {$direction ne "input"} {
    continue
  }
  incr macro_pin_transfer_input_pin_count
  if {[catch {set macro_nets [get_nets -of_objects $macro_pin]}]} {
    incr macro_pin_transfer_query_error_count
    if {[llength $macro_pin_transfer_scan_samples] < $macro_pin_transfer_scan_sample_limit} {
      lappend macro_pin_transfer_scan_samples [list $macro_pin_full_name none]
    }
    continue
  }
  if {[llength $macro_nets] == 0} {
    incr macro_pin_transfer_no_net_count
    if {[llength $macro_pin_transfer_scan_samples] < $macro_pin_transfer_scan_sample_limit} {
      lappend macro_pin_transfer_scan_samples [list $macro_pin_full_name none]
    }
    continue
  }
  incr macro_pin_transfer_connected_pin_count
  set macro_pin_has_driver 0
  set selected_driver_origin_observed none
  set selected_driver_origin ""
  set selected_driver_source_kind none
  set selected_driver_toggle 0.0
  set selected_driver_duty 0.0
  set macro_nets_sorted [rtlgen_sorted_list $macro_nets]
  foreach macro_net $macro_nets_sorted {
    if {[catch {set driver_pins [sta::net_driver_pins $macro_net]}]} {
      incr macro_pin_transfer_query_error_count
      continue
    }
    if {[llength $driver_pins] == 0} {
      continue
    }
    set macro_pin_has_driver 1
    set driver_pins_sorted [rtlgen_sorted_list $driver_pins]
    foreach driver_pin $driver_pins_sorted {
      if {[catch {set driver_activity [get_property $driver_pin activity]}]} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {[llength $driver_activity] < 3} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      set driver_toggle [lindex $driver_activity 0]
      set driver_duty [lindex $driver_activity 1]
      set driver_origin [lindex $driver_activity [expr {[llength $driver_activity] - 1}]]
      set driver_origin_bucket [rtlgen_activity_origin_bucket $driver_origin]
      if {$selected_driver_origin_observed eq "none"} {
        set selected_driver_origin_observed $driver_origin_bucket
      }
      if {![rtlgen_is_finite_power_value $driver_toggle] ||
          ![rtlgen_is_finite_power_value $driver_duty]} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$driver_toggle < 0.0} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$driver_duty < 0.0 || $driver_duty > 1.0} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$driver_origin_bucket == "vcd" || $driver_origin_bucket == "propagated"} {
        if {$driver_origin_bucket == "vcd"} {
          incr macro_pin_transfer_driver_origin_vcd_count
        } else {
          incr macro_pin_transfer_driver_origin_propagated_count
        }
        set selected_driver_origin $driver_origin_bucket
        set selected_driver_source_kind driver
        set selected_driver_toggle $driver_toggle
        set selected_driver_duty $driver_duty
        break
      }
      if {$driver_origin_bucket == "clock"} {
        incr macro_pin_transfer_driver_origin_clock_count
      } elseif {$driver_origin_bucket == "constant"} {
        incr macro_pin_transfer_driver_origin_constant_count
      } else {
        incr macro_pin_transfer_driver_origin_other_count
      }
    }
    if {$selected_driver_origin ne ""} {
      break
    }
    if {[catch {set peer_pins [get_pins -of_objects $macro_net]}]} {
      incr macro_pin_transfer_query_error_count
      continue
    }
    set peer_pins_sorted [rtlgen_sorted_list $peer_pins]
    foreach peer_pin $peer_pins_sorted {
      if {$peer_pin eq $macro_pin} {
        continue
      }
      incr macro_pin_transfer_peer_pin_count
      if {[catch {set peer_activity [get_property $peer_pin activity]}]} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {[llength $peer_activity] < 3} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      set peer_toggle [lindex $peer_activity 0]
      set peer_duty [lindex $peer_activity 1]
      set peer_origin [lindex $peer_activity [expr {[llength $peer_activity] - 1}]]
      set peer_origin_bucket [rtlgen_activity_origin_bucket $peer_origin]
      if {$peer_origin_bucket == "vcd"} {
        incr macro_pin_transfer_peer_origin_vcd_count
      } elseif {$peer_origin_bucket == "propagated"} {
        incr macro_pin_transfer_peer_origin_propagated_count
      } elseif {$peer_origin_bucket == "clock"} {
        incr macro_pin_transfer_peer_origin_clock_count
      } elseif {$peer_origin_bucket == "constant"} {
        incr macro_pin_transfer_peer_origin_constant_count
      } else {
        incr macro_pin_transfer_peer_origin_other_count
      }
      if {![rtlgen_is_finite_power_value $peer_toggle] ||
          ![rtlgen_is_finite_power_value $peer_duty]} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$peer_toggle < 0.0} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$peer_duty < 0.0 || $peer_duty > 1.0} {
        incr macro_pin_transfer_query_error_count
        continue
      }
      if {$peer_origin_bucket == "vcd" || $peer_origin_bucket == "propagated"} {
        incr macro_pin_transfer_peer_eligible_count
        set selected_driver_origin $peer_origin_bucket
        set selected_driver_source_kind net_peer
        set selected_driver_toggle $peer_toggle
        set selected_driver_duty $peer_duty
        break
      }
    }
    if {$selected_driver_origin ne ""} {
      break
    }
  }
  if {$macro_pin_has_driver} {
    incr macro_pin_transfer_driver_pin_count
  } else {
    incr macro_pin_transfer_no_driver_count
  }
  if {[llength $macro_pin_transfer_scan_samples] < $macro_pin_transfer_scan_sample_limit} {
    if {$selected_driver_origin ne ""} {
      lappend macro_pin_transfer_scan_samples \
        [list $macro_pin_full_name $selected_driver_origin $selected_driver_source_kind]
    } elseif {$selected_driver_origin_observed ne "none"} {
      lappend macro_pin_transfer_scan_samples \
        [list $macro_pin_full_name $selected_driver_origin_observed $selected_driver_source_kind]
    } else {
      lappend macro_pin_transfer_scan_samples [list $macro_pin_full_name none none]
    }
  }
  if {$selected_driver_origin ne ""} {
    incr macro_pin_transfer_candidate_count
    lappend macro_pin_transfer_updates \
      [list $macro_pin_full_name $macro_pin $selected_driver_toggle $selected_driver_duty]
    dict set macro_pin_transfer_candidate_source_by_full_name $macro_pin_full_name $selected_driver_origin
    dict set macro_pin_transfer_candidate_source_kind_by_full_name $macro_pin_full_name $selected_driver_source_kind
    dict set macro_pin_transfer_candidate_toggle_by_full_name $macro_pin_full_name $selected_driver_toggle
  }
}

if {[llength $macro_pin_transfer_updates] > 0} {
  set macro_pin_transfer_apply_results [rtlgen_apply_macro_pin_activities $macro_pin_transfer_updates]
  set macro_pin_transfer_record_full_names {}
  foreach macro_pin_transfer_apply_result $macro_pin_transfer_apply_results {
    lassign $macro_pin_transfer_apply_result pin_full_name applied
    if {$applied} {
      if {![dict exists $macro_pin_transfer_candidate_source_by_full_name $pin_full_name]} {
        incr macro_pin_transfer_apply_error_count
        continue
      }
      incr macro_pin_transfer_applied_count
      lappend macro_pin_transfer_record_full_names $pin_full_name
      set pin_source [dict get $macro_pin_transfer_candidate_source_by_full_name $pin_full_name]
      if {[dict exists $macro_pin_transfer_candidate_source_kind_by_full_name $pin_full_name]} {
        set pin_source_kind [dict get $macro_pin_transfer_candidate_source_kind_by_full_name $pin_full_name]
      } else {
        set pin_source_kind none
      }
      set pin_toggle [dict get $macro_pin_transfer_candidate_toggle_by_full_name $pin_full_name]
      dict set macro_pin_transfer_source_by_full_name $pin_full_name $pin_source
      dict set macro_pin_transfer_source_kind_by_full_name $pin_full_name $pin_source_kind
      dict set macro_pin_transfer_toggle_by_full_name $pin_full_name $pin_toggle
      if {$pin_source == "vcd"} {
        incr macro_pin_transfer_source_vcd_count
      } else {
        incr macro_pin_transfer_source_propagated_count
      }
      if {$pin_toggle > 0.0} {
        incr macro_pin_transfer_active_count
      } else {
        incr macro_pin_transfer_zero_count
      }
    } else {
      incr macro_pin_transfer_apply_error_count
    }
  }
  if {[llength $macro_pin_transfer_record_full_names] > 0} {
    set macro_pin_transfer_record_full_names [rtlgen_sorted_list $macro_pin_transfer_record_full_names]
    if {[llength $macro_pin_transfer_record_full_names] > 16} {
      set macro_pin_transfer_record_full_names [lrange $macro_pin_transfer_record_full_names 0 15]
    }
    foreach macro_pin_transfer_full_name $macro_pin_transfer_record_full_names {
      if {[dict exists $macro_pin_transfer_source_by_full_name $macro_pin_transfer_full_name]} {
        lappend macro_pin_transfer_records \
          [list \
            $macro_pin_transfer_full_name \
            [dict get $macro_pin_transfer_source_by_full_name $macro_pin_transfer_full_name] \
            [dict get $macro_pin_transfer_source_kind_by_full_name $macro_pin_transfer_full_name] \
          ]
      }
    }
  }
}

set totals [sta::design_power $power_corner]
set design_power_category_count [expr {[llength $totals] / 4}]
set design_power_totals [lrange $totals 0 3]
set has_nonfinite_design_total 0
foreach value $design_power_totals {
  if {![rtlgen_is_finite_power_value $value]} {
    set has_nonfinite_design_total 1
    break
  }
}
set design_power_entries {}
set design_power_index 0
foreach design_power_name $design_power_category_names {
  if {$design_power_index < $design_power_category_count} {
    set offset [expr {$design_power_index * 4}]
    set design_power_row [lrange $totals $offset [expr {$offset + 3}]]
  } else {
    set design_power_row {}
  }
  lassign $design_power_row design_power_internal design_power_switching design_power_leakage design_power_total
  lappend design_power_entries \
    [list \
      $design_power_name \
      [rtlgen_json_number $design_power_internal] \
      [rtlgen_json_number $design_power_switching] \
      [rtlgen_json_number $design_power_leakage] \
      [rtlgen_json_number $design_power_total] \
    ]
  incr design_power_index
}

set design_power_lines {}
foreach design_power_entry $design_power_entries {
  lassign $design_power_entry design_name design_internal_w design_switching_w design_leakage_w design_total_w
  lappend design_power_lines "    \"$design_name\": {\"internal_w\": $design_internal_w, \"switching_w\": $design_switching_w, \"leakage_w\": $design_leakage_w, \"total_w\": $design_total_w}"
}

set annotatable 0
set trace_backed_count 0
set macro_annotatable 0
set macro_trace_active_count 0
set macro_trace_backed_count 0
set macro_trace_backed_zero_toggle_count 0
set macro_transferred_origin_count 0
set leaf_vcd_origin_count 0
set leaf_propagated_origin_count 0
set leaf_clock_origin_count 0
set leaf_constant_origin_count 0
set leaf_other_origin_count 0
set macro_vcd_origin_count 0
set macro_propagated_origin_count 0
set macro_clock_origin_count 0
set macro_constant_origin_count 0
set macro_other_origin_count 0
set non_finite_leaf_instance_power_count 0
set non_finite_leaf_instance_power_candidate_cell_count 0
set non_finite_leaf_instance_power_checked_count 0
set non_finite_leaf_instance_power_query_error_count 0
set non_finite_leaf_instance_power_non_leaf_skip_count 0
set non_finite_leaf_instance_power_bad_shape_row_count 0
set non_finite_leaf_instance_power_finite_row_count 0
set non_finite_leaf_instance_power_internal_sum 0.0
set non_finite_leaf_instance_power_switching_sum 0.0
set non_finite_leaf_instance_power_leakage_sum 0.0
set non_finite_leaf_instance_power_total_sum 0.0
set non_finite_leaf_instance_samples {}
foreach pin $all_design_pins {
  if {[get_property $pin is_hierarchical]} {
    continue
  }
  set direction [get_property $pin direction]
  if {$direction == "internal"} {
    continue
  }
  incr annotatable
  set activity [get_property $pin activity]
  set origin [lindex $activity 2]
  set toggle_rate [lindex $activity 0]
  if {![string is double -strict $toggle_rate]} {
    set toggle_rate 0.0
  }
  set origin_bucket [rtlgen_activity_origin_bucket $origin]
  if {$origin_bucket == "vcd"} {
    incr leaf_vcd_origin_count
  } elseif {$origin_bucket == "propagated"} {
    incr leaf_propagated_origin_count
  } elseif {$origin_bucket == "clock"} {
    incr leaf_clock_origin_count
  } elseif {$origin_bucket == "constant"} {
    incr leaf_constant_origin_count
  } else {
    incr leaf_other_origin_count
  }
  if {$origin_bucket == "vcd" || $origin_bucket == "propagated"} {
    incr trace_backed_count
  }
  if {[catch {set full_name [get_property $pin full_name]}]} {
    set full_name $pin
  }
  set macro_pin_origin_bucket $origin_bucket
  set macro_pin_toggle_for_macro_activity $toggle_rate
  if {[dict exists $macro_pin_transfer_source_by_full_name $full_name]} {
    set macro_pin_origin_bucket "transferred"
    set macro_pin_toggle_for_macro_activity \
      [dict get $macro_pin_transfer_toggle_by_full_name $full_name]
  }
  if {[string match "*u_group_*" $full_name]} {
    incr macro_annotatable
    if {$macro_pin_origin_bucket == "vcd"} {
      incr macro_vcd_origin_count
    } elseif {$macro_pin_origin_bucket == "propagated"} {
      incr macro_propagated_origin_count
    } elseif {$macro_pin_origin_bucket == "transferred"} {
      incr macro_transferred_origin_count
    } elseif {$origin_bucket == "clock"} {
      incr macro_clock_origin_count
    } elseif {$origin_bucket == "constant"} {
      incr macro_constant_origin_count
    } else {
      incr macro_other_origin_count
    }
    if {$macro_pin_origin_bucket == "vcd" || $macro_pin_origin_bucket == "propagated" || $macro_pin_origin_bucket == "transferred"} {
      incr macro_trace_backed_count
      if {$macro_pin_toggle_for_macro_activity > 0.0} {
        incr macro_trace_active_count
      } else {
        incr macro_trace_backed_zero_toggle_count
      }
    }
  }
}

if {$has_nonfinite_design_total} {
  set leaf_cells {}
  if {[catch {set leaf_cells [sta::network_leaf_instances]}]} {
    incr non_finite_leaf_instance_power_query_error_count
    set leaf_cells {}
  }
  set leaf_cells_unsorted $leaf_cells
  if {[catch {set leaf_cells [lsort -dictionary $leaf_cells_unsorted]}]} {
    if {[catch {set leaf_cells [lsort $leaf_cells_unsorted]}]} {
      # Keep original order as best effort if sorting is unsupported for this object type.
      set leaf_cells $leaf_cells_unsorted
    }
  }
  set non_finite_leaf_instance_power_candidate_cell_count [llength $leaf_cells]
  foreach leaf $leaf_cells {
    set instance_power_error [catch {sta::instance_power "$leaf" $power_corner} instance_power]
    if {$instance_power_error} {
      incr non_finite_leaf_instance_power_query_error_count
      continue
    }
    if {[llength $instance_power] != 4} {
      incr non_finite_leaf_instance_power_bad_shape_row_count
      continue
    }
    incr non_finite_leaf_instance_power_checked_count
    set internal_power_value [lindex $instance_power 0]
    set switching_power_value [lindex $instance_power 1]
    set leakage_power_value [lindex $instance_power 2]
    set total_power_value [lindex $instance_power 3]
    if {![rtlgen_is_finite_power_value $internal_power_value] ||
        ![rtlgen_is_finite_power_value $switching_power_value] ||
        ![rtlgen_is_finite_power_value $leakage_power_value] ||
        ![rtlgen_is_finite_power_value $total_power_value]} {
      incr non_finite_leaf_instance_power_count
      if {[llength $non_finite_leaf_instance_samples] < 16} {
        if {[catch {set leaf_name [get_full_name $leaf]}]} {
          if {[catch {set leaf_name [get_property $leaf name]}]} {
            set leaf_name $leaf
          }
        }
        lappend non_finite_leaf_instance_samples \
          [list \
            $leaf_name \
            $internal_power_value \
            $switching_power_value \
            $leakage_power_value \
            $total_power_value \
          ]
      }
    } else {
      incr non_finite_leaf_instance_power_finite_row_count
      set non_finite_leaf_instance_power_internal_sum \
        [expr {$non_finite_leaf_instance_power_internal_sum + $internal_power_value}]
      set non_finite_leaf_instance_power_switching_sum \
        [expr {$non_finite_leaf_instance_power_switching_sum + $switching_power_value}]
      set non_finite_leaf_instance_power_leakage_sum \
        [expr {$non_finite_leaf_instance_power_leakage_sum + $leakage_power_value}]
      set non_finite_leaf_instance_power_total_sum \
        [expr {$non_finite_leaf_instance_power_total_sum + $total_power_value}]
    }
  }
}

set sdc_clock_period_ns "null"
set clocks [get_clocks *]
if {[llength $clocks] > 0} {
  set sdc_clock_period_ns [rtlgen_json_number [get_property [lindex $clocks 0] period]]
}
lassign $design_power_totals design_power_internal_w design_power_switching_w design_power_leakage_w design_power_total_w
set internal_w [rtlgen_json_number $design_power_internal_w]
set switching_w [rtlgen_json_number $design_power_switching_w]
set leakage_w [rtlgen_json_number $design_power_leakage_w]
set total_w [rtlgen_json_number $design_power_total_w]

set fp [open $::env(RTLGEN_ACTIVITY_RESULT) w]
puts $fp "{"
puts $fp "  \"internal_w\": $internal_w,"
puts $fp "  \"switching_w\": $switching_w,"
puts $fp "  \"leakage_w\": $leakage_w,"
puts $fp "  \"total_w\": $total_w,"
puts $fp "  \"design_power_quartets\": {"
set design_power_lines_count [llength $design_power_lines]
set design_power_index 0
foreach design_power_line $design_power_lines {
  incr design_power_index
  if {$design_power_index < $design_power_lines_count} {
    puts $fp "$design_power_line,"
  } else {
    puts $fp "$design_power_line"
  }
}
puts $fp "  },"
puts $fp "  \"sdc_clock_period_ns\": $sdc_clock_period_ns,"
puts $fp "  \"annotatable_pin_count\": $annotatable,"
puts $fp "  \"leaf_annotatable_pin_count\": $annotatable,"
puts $fp "  \"leaf_trace_backed_pin_count\": $trace_backed_count,"
puts $fp "  \"vcd_annotated_pin_count\": $trace_backed_count,"
puts $fp "  \"trace_backed_pin_count\": $trace_backed_count,"
puts $fp "  \"leaf_activity_origin_counts\": {"
puts $fp "    \"vcd\": $leaf_vcd_origin_count,"
puts $fp "    \"propagated\": $leaf_propagated_origin_count,"
puts $fp "    \"clock\": $leaf_clock_origin_count,"
puts $fp "    \"constant\": $leaf_constant_origin_count,"
puts $fp "    \"other\": $leaf_other_origin_count"
puts $fp "  },"
puts $fp "  \"macro_annotatable_pin_count\": $macro_annotatable,"
puts $fp "  \"macro_activity_origin_counts\": {"
puts $fp "    \"vcd\": $macro_vcd_origin_count,"
puts $fp "    \"propagated\": $macro_propagated_origin_count,"
puts $fp "    \"transferred\": $macro_transferred_origin_count,"
puts $fp "    \"clock\": $macro_clock_origin_count,"
puts $fp "    \"constant\": $macro_constant_origin_count,"
puts $fp "    \"other\": $macro_other_origin_count"
puts $fp "  },"
puts $fp "  \"macro_trace_backed_pin_count\": $macro_trace_backed_count,"
puts $fp "  \"macro_trace_active_pin_count\": $macro_trace_active_count,"
puts $fp "  \"macro_trace_backed_zero_toggle_pin_count\": $macro_trace_backed_zero_toggle_count"
puts $fp ","
puts $fp "  \"macro_pin_transfer\": {"
puts $fp "    \"candidate_count\": $macro_pin_transfer_candidate_count,"
puts $fp "    \"applied_count\": $macro_pin_transfer_applied_count,"
puts $fp "    \"query_error_count\": $macro_pin_transfer_query_error_count,"
puts $fp "    \"apply_error_count\": $macro_pin_transfer_apply_error_count,"
puts $fp "    \"source_vcd_count\": $macro_pin_transfer_source_vcd_count,"
puts $fp "    \"source_propagated_count\": $macro_pin_transfer_source_propagated_count,"
puts $fp "    \"peer_pin_examined_count\": $macro_pin_transfer_peer_pin_count,"
puts $fp "    \"peer_eligible_count\": $macro_pin_transfer_peer_eligible_count,"
puts $fp "    \"peer_origin_counts\": {"
puts $fp "      \"vcd\": $macro_pin_transfer_peer_origin_vcd_count,"
puts $fp "      \"propagated\": $macro_pin_transfer_peer_origin_propagated_count,"
puts $fp "      \"clock\": $macro_pin_transfer_peer_origin_clock_count,"
puts $fp "      \"constant\": $macro_pin_transfer_peer_origin_constant_count,"
puts $fp "      \"other\": $macro_pin_transfer_peer_origin_other_count"
puts $fp "    },"
puts $fp "    \"active_count\": $macro_pin_transfer_active_count,"
puts $fp "    \"zero_count\": $macro_pin_transfer_zero_count,"
puts $fp "    \"scanned_pin_count\": $macro_pin_transfer_scanned_pin_count,"
puts $fp "    \"name_match_pin_count\": $macro_pin_transfer_name_match_count,"
puts $fp "    \"input_pin_count\": $macro_pin_transfer_input_pin_count,"
puts $fp "    \"connected_pin_count\": $macro_pin_transfer_connected_pin_count,"
puts $fp "    \"no_net_pin_count\": $macro_pin_transfer_no_net_count,"
puts $fp "    \"driver_pin_count\": $macro_pin_transfer_driver_pin_count,"
puts $fp "    \"no_driver_pin_count\": $macro_pin_transfer_no_driver_count,"
puts $fp "    \"driver_origin_counts\": {"
puts $fp "      \"vcd\": $macro_pin_transfer_driver_origin_vcd_count,"
puts $fp "      \"propagated\": $macro_pin_transfer_driver_origin_propagated_count,"
puts $fp "      \"clock\": $macro_pin_transfer_driver_origin_clock_count,"
puts $fp "      \"constant\": $macro_pin_transfer_driver_origin_constant_count,"
puts $fp "      \"other\": $macro_pin_transfer_driver_origin_other_count"
puts $fp "    },"
puts $fp "    \"scan_samples\": \["
set macro_pin_transfer_scan_sample_count [llength $macro_pin_transfer_scan_samples]
set macro_pin_transfer_scan_sample_index 0
foreach macro_pin_transfer_scan_sample $macro_pin_transfer_scan_samples {
  set macro_pin_transfer_scan_sample_full_name [lindex $macro_pin_transfer_scan_sample 0]
  set macro_pin_transfer_scan_sample_origin [lindex $macro_pin_transfer_scan_sample 1]
  set macro_pin_transfer_scan_sample_source_kind [lindex $macro_pin_transfer_scan_sample 2]
  set escaped_full_name [rtlgen_json_escape_array_literal_chars [rtlgen_json_escape $macro_pin_transfer_scan_sample_full_name]]
  set macro_pin_transfer_scan_sample_line "      {\"full_name\": \"$escaped_full_name\", \"driver_origin\": \"$macro_pin_transfer_scan_sample_origin\", \"source_kind\": \"$macro_pin_transfer_scan_sample_source_kind\"}"
  incr macro_pin_transfer_scan_sample_index
  if {$macro_pin_transfer_scan_sample_index < $macro_pin_transfer_scan_sample_count} {
    puts $fp "$macro_pin_transfer_scan_sample_line,"
  } else {
    puts $fp "$macro_pin_transfer_scan_sample_line"
  }
}
puts $fp "    \],"
puts $fp "    \"transferred\": \["
set macro_pin_transfer_records_count [llength $macro_pin_transfer_records]
set macro_pin_transfer_record_index 0
foreach macro_pin_transfer_record $macro_pin_transfer_records {
  set macro_pin_transfer_full_name [lindex $macro_pin_transfer_record 0]
  set macro_pin_transfer_source [lindex $macro_pin_transfer_record 1]
  set macro_pin_transfer_record_source_kind [lindex $macro_pin_transfer_record 2]
  set escaped_full_name [rtlgen_json_escape_array_literal_chars [rtlgen_json_escape $macro_pin_transfer_full_name]]
  set macro_pin_transfer_record_line "      {\"full_name\": \"$escaped_full_name\", \"source\": \"$macro_pin_transfer_source\", \"source_kind\": \"$macro_pin_transfer_record_source_kind\"}"
  incr macro_pin_transfer_record_index
  if {$macro_pin_transfer_record_index < $macro_pin_transfer_records_count} {
    puts $fp "$macro_pin_transfer_record_line,"
  } else {
    puts $fp "$macro_pin_transfer_record_line"
  }
}
  puts $fp "    \]"
puts $fp "  }"
if {$has_nonfinite_design_total} {
  puts $fp ","
  puts $fp "  \"non_finite_leaf_instance_power\": {"
  puts $fp "    \"instance_count\": $non_finite_leaf_instance_power_count,"
  puts $fp "    \"candidate_cell_count\": $non_finite_leaf_instance_power_candidate_cell_count,"
  puts $fp "    \"checked_instance_power_count\": $non_finite_leaf_instance_power_checked_count,"
  puts $fp "    \"query_error_count\": $non_finite_leaf_instance_power_query_error_count,"
  puts $fp "    \"non_leaf_skip_count\": $non_finite_leaf_instance_power_non_leaf_skip_count,"
  puts $fp "    \"bad_shape_row_count\": $non_finite_leaf_instance_power_bad_shape_row_count,"
  puts $fp "    \"finite_row_count\": $non_finite_leaf_instance_power_finite_row_count,"
  puts $fp "    \"finite_component_sums\": {"
  puts $fp "      \"internal_w\": [rtlgen_json_number $non_finite_leaf_instance_power_internal_sum],"
  puts $fp "      \"switching_w\": [rtlgen_json_number $non_finite_leaf_instance_power_switching_sum],"
  puts $fp "      \"leakage_w\": [rtlgen_json_number $non_finite_leaf_instance_power_leakage_sum],"
  puts $fp "      \"total_w\": [rtlgen_json_number $non_finite_leaf_instance_power_total_sum]"
  puts $fp "    },"
  puts $fp "    \"samples\": \["
  set sample_count [llength $non_finite_leaf_instance_samples]
  set sample_index 0
  foreach sample $non_finite_leaf_instance_samples {
    lassign $sample \
      leaf_name \
      leaf_internal_power \
      leaf_switching_power \
      leaf_leakage_power \
      leaf_total_power
    set leaf_internal_power_json [rtlgen_json_number $leaf_internal_power]
    set leaf_switching_power_json [rtlgen_json_number $leaf_switching_power]
    set leaf_leakage_power_json [rtlgen_json_number $leaf_leakage_power]
    set leaf_total_power_json [rtlgen_json_number $leaf_total_power]
    incr sample_index
    set escaped_leaf_name [rtlgen_json_escape $leaf_name]
    set sample_line "      {\"full_name\": \"$escaped_leaf_name\", \"internal_w\": $leaf_internal_power_json, \"switching_w\": $leaf_switching_power_json, \"leakage_w\": $leaf_leakage_power_json, \"total_w\": $leaf_total_power_json}"
    if {$sample_index < $sample_count} {
      puts $fp "$sample_line,"
    } else {
      puts $fp "$sample_line"
    }
  }
  puts $fp "    \]"
  puts $fp "  }"
}
puts $fp "}"
close $fp

report_activity_annotation
report_power
'''


def _run_openroad_phase(
    *,
    design_config: Path,
    flow_variant: str,
    vcd: Path,
    scope: str,
    tcl: Path,
    result: Path,
    timeout_seconds: int,
) -> JsonDict:
    resolved_config = design_config.resolve()
    if not resolved_config.is_file():
        raise FileNotFoundError(f"ORFS design config does not exist: {resolved_config}")
    try:
        config_arg = str(resolved_config.relative_to(ORFS_FLOW.resolve()))
    except ValueError:
        # ORFS includes DESIGN_CONFIG directly, so an absolute out-of-tree
        # config is valid and useful for isolated workspaces.
        config_arg = str(resolved_config)
    recipe = (
        ".PHONY: rtlgen_activity_power\n"
        "rtlgen_activity_power:\n"
        f"\t@RTLGEN_ACTIVITY_VCD='{vcd}' "
        f"RTLGEN_ACTIVITY_SCOPE='{scope}' "
        f"RTLGEN_ACTIVITY_RESULT='{result}' "
        f"$(OPENROAD_CMD) '{tcl}'\n"
    )
    command = [
        "make",
        "--no-print-directory",
        f"DESIGN_CONFIG={config_arg}",
        f"FLOW_VARIANT={flow_variant}",
        "--eval",
        recipe,
        "rtlgen_activity_power",
    ]
    completed = subprocess.run(
        command,
        cwd=ORFS_FLOW,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode:
        raise RuntimeError(
            "post-route VCD power failed:\n"
            f"command: {' '.join(command[:4])} ...\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    if not result.is_file():
        raise RuntimeError("OpenROAD completed without writing the activity power result")
    payload = _load_json(result)
    annotation_counts = _activity_annotation_counts(completed.stdout)
    if annotation_counts:
        payload["activity_annotation_counts"] = annotation_counts
        direct_annotatable = sum(annotation_counts.values())
        direct_vcd = annotation_counts.get("vcd", 0)
        payload["direct_annotatable_pin_count"] = direct_annotatable
        payload["direct_vcd_pin_count"] = direct_vcd
        # Optional backward-compatible aliases.
        payload["leaf_direct_annotatable_pin_count"] = direct_annotatable
        payload["leaf_direct_vcd_pin_count"] = direct_vcd
        payload["leaf_vcd_annotated_pin_count"] = annotation_counts.get("vcd", 0)
        for category, count in annotation_counts.items():
            payload[f"direct_{category}_pin_count"] = count
    return payload


def _portable_repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve()))
    except ValueError:
        return path.name


def _orfs_relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ORFS_FLOW.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return path.name


def build_report(
    *,
    manifest: JsonDict,
    manifest_path: Path,
    design_config: Path,
    flow_variant: str,
    scope: str,
    min_vcd_coverage: float,
    min_vcd_pins: int,
    min_macro_active_coverage: float,
    min_macro_active_pins: int,
    timeout_seconds: int,
) -> JsonDict:
    clock_period_ns = float(manifest.get("clock_period_ns", 0.0))
    if clock_period_ns <= 0.0:
        raise ValueError("activity manifest requires positive clock_period_ns")
    phases = _phase_rows(manifest, manifest_path)
    measured: list[JsonDict] = []
    with tempfile.TemporaryDirectory(prefix="rtlgen-vcd-power-") as temp_text:
        temp = Path(temp_text)
        tcl = temp / "activity_power.tcl"
        tcl.write_text(_tcl_script(), encoding="utf-8")
        for phase in phases:
            result = temp / f"{phase['phase']}.json"
            power = _run_openroad_phase(
                design_config=design_config,
                flow_variant=flow_variant,
                vcd=Path(str(phase["_resolved_vcd"])),
                scope=scope,
                tcl=tcl,
                result=result,
                timeout_seconds=timeout_seconds,
            )
            leaf_annotatable = int(
                power.get(
                    "leaf_annotatable_pin_count",
                    power.get("annotatable_pin_count", 0),
                )
            )
            trace_backed = int(
                power.get(
                    "leaf_trace_backed_pin_count",
                    power.get("vcd_annotated_pin_count", 0),
                )
            )
            direct_annotatable = int(
                power.get(
                    "direct_annotatable_pin_count",
                    power.get("leaf_direct_annotatable_pin_count", 0),
                )
            )
            direct_vcd = int(
                power.get(
                    "direct_vcd_pin_count",
                    power.get("leaf_direct_vcd_pin_count", 0),
                )
            )
            trace_coverage = (
                trace_backed / leaf_annotatable
                if leaf_annotatable
                else 0.0
            )
            direct_coverage = (
                direct_vcd / direct_annotatable
                if direct_annotatable
                else 0.0
            )
            macro_active = int(power.get("macro_trace_active_pin_count", 0))
            macro_annotatable = int(power.get("macro_annotatable_pin_count", 0))
            macro_coverage = (
                macro_active / macro_annotatable if macro_annotatable else 0.0
            )
            direct_pin_gate_pass = direct_vcd >= min_vcd_pins
            trace_coverage_gate_pass = trace_coverage >= min_vcd_coverage
            annotation_gate_pass = (
                direct_pin_gate_pass and trace_coverage_gate_pass
            )
            macro_pass = not phase["requires_macro_activity"] or (
                macro_active >= min_macro_active_pins
                and macro_coverage >= min_macro_active_coverage
            )
            sdc_period_value = power.get("sdc_clock_period_ns")
            sdc_period_ns = (
                float(sdc_period_value) if sdc_period_value is not None else 0.0
            )
            clock_period_pass = abs(sdc_period_ns - clock_period_ns) <= 1e-6
            component_names = ("internal_w", "switching_w", "leakage_w", "total_w")
            component_values = [power.get(name) for name in component_names]
            power_numeric_pass = all(
                value is not None and math.isfinite(float(value)) and float(value) >= 0.0
                for value in component_values
            )
            total_value = power.get("total_w")
            total_w = float(total_value) if total_value is not None else 0.0
            power_numeric_pass = power_numeric_pass and total_w > 0.0
            full_cycles = int(phase["full_context_cycles"])
            energy_j = total_w * full_cycles * clock_period_ns * 1e-9
            measured.append(
                {
                    **{key: value for key, value in phase.items() if not key.startswith("_")},
                    "power": power,
                    "direct_vcd_annotation_coverage": direct_coverage,
                    "trace_backed_vcd_annotation_coverage": trace_coverage,
                    "vcd_annotation_coverage": trace_coverage,
                    "direct_vcd_annotation_pin_gate_pass": direct_pin_gate_pass,
                    "trace_coverage_gate_pass": trace_coverage_gate_pass,
                    "annotation_gate_pass": annotation_gate_pass,
                    "macro_activity_gate_pass": macro_pass,
                    "macro_trace_active_coverage": macro_coverage,
                    "clock_period_gate_pass": clock_period_pass,
                    "power_numeric_gate_pass": power_numeric_pass,
                    "phase_gate_pass": annotation_gate_pass
                    and macro_pass
                    and clock_period_pass
                    and power_numeric_pass,
                    "full_context_energy_j": energy_j,
                }
            )
    gate_pass = all(bool(row["phase_gate_pass"]) for row in measured)
    total_cycles = sum(int(row["full_context_cycles"]) for row in measured)
    total_energy_j = sum(float(row["full_context_energy_j"]) for row in measured)
    return {
        "version": 1,
        "model": "postroute_phase_vcd_power_v1",
        "status": "activity_backed" if gate_pass else "rejected_annotation_gate",
        "promotion_gate_pass": gate_pass,
        "clock_period_ns": clock_period_ns,
        "scope": scope,
        "flow_variant": flow_variant,
        "orfs_design_config": _orfs_relative_path(design_config),
        "min_vcd_annotation_coverage": min_vcd_coverage,
        "min_vcd_annotated_pins": min_vcd_pins,
        "min_macro_trace_active_coverage": min_macro_active_coverage,
        "min_macro_trace_active_pins": min_macro_active_pins,
        "full_context_cycles": total_cycles,
        "full_context_latency_s": total_cycles * clock_period_ns * 1e-9,
        "full_context_energy_j": total_energy_j if gate_pass else None,
        "phases": measured,
        "source_activity_manifest": _portable_repo_path(manifest_path),
        "source_activity_manifest_sha256": _sha256(manifest_path),
        "orfs_design_config_sha256": _sha256(design_config),
        "remaining_abstractions": [
            "FakeRAM power uses the Nangate45 proxy Liberty model, not SRAM compiler signoff.",
            "RTL-generated VCD is mapped onto the post-route netlist; annotation coverage is explicit and gated.",
            "Off-cluster value-memory, NoC, and HBM energy are outside this cluster power result.",
        ],
    }


def write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        "# Post-route Phase VCD Power",
        "",
        f"- status: `{payload['status']}`",
        f"- promotion_gate_pass: `{payload['promotion_gate_pass']}`",
        f"- clock_period_ns: `{payload['clock_period_ns']}`",
        f"- full_context_cycles: `{payload['full_context_cycles']}`",
        f"- full_context_latency_s: `{payload['full_context_latency_s']}`",
        f"- full_context_energy_j: `{payload['full_context_energy_j']}`",
        "",
        "| phase | measured cycles | full cycles | total W | direct/trace-backed VCD coverage | macro active pins | energy J | gate |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in payload["phases"]:
        power = row["power"]
        lines.append(
            "| {phase} | {measured_cycles} | {full_context_cycles} | {total_w} | "
            "{direct_coverage:.6f} / {coverage:.6f} | {macro_pins} | {energy} | {gate} |".format(
                phase=row["phase"],
                measured_cycles=row["measured_cycles"],
                full_context_cycles=row["full_context_cycles"],
                total_w=power.get("total_w"),
                coverage=row["trace_backed_vcd_annotation_coverage"],
                direct_coverage=row["direct_vcd_annotation_coverage"],
                macro_pins=power.get("macro_trace_active_pin_count", 0),
                energy=row["full_context_energy_j"],
                gate=row["phase_gate_pass"],
            )
        )
    diagnostics = []
    for row in payload["phases"]:
        power = row["power"]
        diag = power.get("non_finite_leaf_instance_power")
        if not isinstance(diag, dict):
            continue
        sample_names = [
            sample.get("full_name")
            for sample in diag.get("samples", [])
            if isinstance(sample, dict) and sample.get("full_name")
        ]
        diagnostics.append(
            (
                row["phase"],
                int(diag.get("instance_count", 0)),
                sample_names,
            )
        )
    if diagnostics:
        lines.extend(["", "## Power Diagnostics", ""])
        for phase, instance_count, sample_names in diagnostics:
            lines.append(
                f"- `{phase}` non-finite leaf-instance power samples: `{instance_count}` instances"
            )
            if sample_names:
                lines.append(
                    "  - sample instances: "
                    + ", ".join(f"`{name}`" for name in sample_names)
                )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity-manifest", type=Path, required=True)
    parser.add_argument("--design-config", type=Path, required=True)
    parser.add_argument("--flow-variant", required=True)
    parser.add_argument("--scope", default="tb/dut")
    parser.add_argument("--min-vcd-coverage", type=float, default=0.05)
    parser.add_argument("--min-vcd-pins", type=int, default=32)
    parser.add_argument("--min-macro-active-coverage", type=float, default=0.01)
    parser.add_argument("--min-macro-active-pins", type=int, default=16)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()
    if not 0.0 < args.min_vcd_coverage <= 1.0:
        parser.error("--min-vcd-coverage must be in (0, 1]")
    if args.min_vcd_pins <= 0:
        parser.error("--min-vcd-pins must be positive")
    if not 0.0 < args.min_macro_active_coverage <= 1.0:
        parser.error("--min-macro-active-coverage must be in (0, 1]")
    if args.min_macro_active_pins <= 0:
        parser.error("--min-macro-active-pins must be positive")
    manifest = _load_json(args.activity_manifest)
    payload = build_report(
        manifest=manifest,
        manifest_path=args.activity_manifest,
        design_config=args.design_config,
        flow_variant=args.flow_variant,
        scope=args.scope,
        min_vcd_coverage=args.min_vcd_coverage,
        min_vcd_pins=args.min_vcd_pins,
        min_macro_active_coverage=args.min_macro_active_coverage,
        min_macro_active_pins=args.min_macro_active_pins,
        timeout_seconds=args.timeout_seconds,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md:
        write_markdown(payload, args.out_md)
    return 0 if payload["promotion_gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
