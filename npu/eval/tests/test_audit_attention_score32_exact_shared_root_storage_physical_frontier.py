from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest


_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "audit_attention_score32_exact_shared_root_storage_physical_frontier.py"
)
_SPEC = importlib.util.spec_from_file_location("storage_physical_frontier", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _bank_report() -> dict:
    cycles = {2: 4120, 4: 3077, 8: 2855, 15: 2620}
    macros = {2: 32, 4: 32, 8: 64, 15: 120}
    return {
        "semantic_profile": "score32_exact_stats_once_banked_root_macro_v2",
        "rtl_macro_points": [
            {
                "physical_banks": banks,
                "fakeram45_64x32_macros": macros[banks],
                "full_chain_final_cycle": cycles[banks],
                "bit_exact": True,
            }
            for banks in (2, 4, 8, 15)
        ],
    }


def _write_metrics(root: Path, *, banks: int, cp_ns: float, power_mw: float, stdcell_area: float) -> None:
    macro_count = {2: 32, 4: 32, 8: 64, 15: 120}[banks]
    macro_area = macro_count * _MODULE._MACRO_AREA_UM2
    path = (
        root
        / f"attention_score32_exact_shared_root_storage_macro_b{banks}"
        / "metrics.csv"
    )
    path.parent.mkdir(parents=True)
    row = {
        "status": "ok",
        "tag": f"b{banks}_8ns",
        "critical_path_ns": cp_ns,
        "total_power_mw": power_mw,
        "stdcell_area_um2": stdcell_area,
        "macro_area_um2": macro_area,
        "instance_area_um2": stdcell_area + macro_area,
        "macro_count": macro_count,
        "blackbox_instance_counts": json.dumps({_MODULE._MACRO_NAME: macro_count}),
        "missing_blackboxes": "[]",
        "macro_manifest_path": "verilog/macro_manifest.json",
        "params_json": json.dumps({"CLOCK_PERIOD": 8.0}),
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def test_physical_frontier_keeps_separate_area_energy_and_latency_winners(tmp_path: Path) -> None:
    design_root = tmp_path / "designs"
    _write_metrics(design_root, banks=2, cp_ns=5.0, power_mw=1.5, stdcell_area=13000.0)
    _write_metrics(design_root, banks=4, cp_ns=5.2, power_mw=1.2, stdcell_area=8000.0)
    _write_metrics(design_root, banks=8, cp_ns=5.5, power_mw=1.6, stdcell_area=9000.0)
    _write_metrics(design_root, banks=15, cp_ns=6.0, power_mw=2.5, stdcell_area=14000.0)

    report = _MODULE.build_report(
        bank_report=_bank_report(),
        design_root=design_root,
        clock_floor_ns=8.0,
        clock_floor_source="measured_mesh_tree_floor.json",
    )

    assert report["selection_status"] == "physical_bank_frontier_measured_no_scalar_weighting"
    winners = report["dimension_winners"]
    assert winners["full_chain_latency"] == ["shared_root_storage_b15_b15_8ns"]
    assert winners["embodied_instance_area"] == ["shared_root_storage_b4_b4_8ns"]
    assert winners["vectorless_storage_energy_screen"] == [
        "shared_root_storage_b4_b4_8ns"
    ]
    assert set(report["pareto_candidate_ids"]) == {
        "shared_root_storage_b4_b4_8ns",
        "shared_root_storage_b8_b8_8ns",
        "shared_root_storage_b15_b15_8ns",
    }
    assert all(row["bit_exact"] for row in report["measured_rows"])


def test_physical_frontier_rejects_erased_macro_inventory(tmp_path: Path) -> None:
    design_root = tmp_path / "designs"
    for banks in (2, 4, 8, 15):
        _write_metrics(design_root, banks=banks, cp_ns=6.0, power_mw=1.0, stdcell_area=1000.0)
    path = design_root / "attention_score32_exact_shared_root_storage_macro_b4" / "metrics.csv"
    text = path.read_text(encoding="utf-8").replace(",32,", ",31,", 1)
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="macro_count mismatch"):
        _MODULE.build_report(
            bank_report=_bank_report(),
            design_root=design_root,
            clock_floor_ns=8.0,
            clock_floor_source="measured_mesh_tree_floor.json",
        )


def test_physical_frontier_does_not_ignore_slower_system_clock_floor(tmp_path: Path) -> None:
    design_root = tmp_path / "designs"
    for banks in (2, 4, 8, 15):
        _write_metrics(design_root, banks=banks, cp_ns=6.0, power_mw=1.0, stdcell_area=1000.0)

    with pytest.raises(ValueError, match="no measured row meets"):
        _MODULE.build_report(
            bank_report=_bank_report(),
            design_root=design_root,
            clock_floor_ns=9.0,
            clock_floor_source="measured_mesh_tree_floor.json",
        )
