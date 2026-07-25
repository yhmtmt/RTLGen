#!/usr/bin/env python3
"""Tests for Fakeram VCD extractor."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.extract_fakeram_vcd_activity import (
    extract_fakeram_vcd_activity,
    extract_multivalue_service_fakeram_vcd_activity,
)
from npu.eval.generate_attention_decode_score_multivalue_service_activity import (
    _REQUIRED_SERVICE_FIELDS,
    generate_activity,
)


def _write_vcd(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def _service_config() -> dict[str, object]:
    return {
        "top_name": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_macro_activity",
        "attention_decode_score_multivalue_service": dict(_REQUIRED_SERVICE_FIELDS),
    }


def _mini_vcd() -> str:
    zero_11 = "0" * 11
    one_11 = "10000000001"
    zero_39 = "0" * 39
    return "\n".join(
        [
            "$date",
            " Mini activity vcd",
            "$end",
            "$version",
            "  test",
            "$end",
            "$timescale",
            " 1ns/1ps",
            "$end",
            "$scope module tb $end",
            "$scope module dut $end",
            "$scope module outer $end",
            "$scope module score_bank $end",
            "$scope module u_group_0_slice_0 $end",
            "$var reg 11 a addr_in [10:0] $end",
            "$var reg 39 b wd_in [38:0] $end",
            "$var reg 39 c w_mask_in [38:0] $end",
            "$var reg 1 d we_in $end",
            "$var reg 1 e ce_in $end",
            "$var reg 1 f \\ alias_we_in $end",
            "$upscope $end",
            "$upscope $end",
            "$upscope $end",
            "$upscope $end",
            "$upscope $end",
            "$enddefinitions",
            "#0",
            f"b{zero_11} a",
            f"b{zero_39} b",
            f"b{zero_39} c",
            "0d",
            "1e",
            "#10",
            "$dumpon",
            "#15",
            f"b{one_11} a",
            "1d",
            "#20",
            "xd",
            "#25",
            f"b{zero_11} a",  # addr_in[10] goes low again
            "#30",
            "xd",
            "#35",
            "#40",
            "1d",
            "#50",
            "0d",
            "#55",
            "zd",
            "#60",
            "$dumpoff",
        ]
    )


def test_extract_fakeram_activity_mini_vcd_semantics(tmp_path: Path) -> None:
    vcd_path = tmp_path / "mini.vcd"
    _write_vcd(vcd_path, _mini_vcd())
    payload = extract_fakeram_vcd_activity(
        vcd_path,
        source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
        scope="tb/dut",
        group_indices=(0,),
        slice_indices=(0,),
        expected_pin_count=91,
    )

    assert payload["version"] == 1
    assert payload["model"] == "fakeram_macro_pin_vcd_activity_v1"
    assert payload["scope"] == "tb/dut"
    assert payload["source_vcd"] == vcd_path.name
    assert payload["timescale_seconds"] == 1e-12
    assert payload["active_start_tick"] == 10
    assert payload["active_end_tick"] == 60
    assert payload["active_end_tick"] > payload["active_start_tick"]
    assert len(payload["pins"]) == 91

    ordered = [row["full_name"] for row in payload["pins"]]
    assert ordered == sorted(ordered)

    by_name = {row["full_name"]: row for row in payload["pins"]}
    assert "score_bank/u_group_0_slice_0/addr_in[10]" in by_name
    assert "score_bank/u_group_0_slice_0/addr_in[0]" in by_name
    assert by_name["score_bank/u_group_0_slice_0/addr_in[10]"]["transition_count"] == 2.0
    assert by_name["score_bank/u_group_0_slice_0/addr_in[0]"]["transition_count"] == 2.0
    assert by_name["score_bank/u_group_0_slice_0/we_in"]["transition_count"] == 3.5
    assert by_name["score_bank/u_group_0_slice_0/we_in"]["duty_cycle"] == pytest.approx(0.3)
    assert by_name["score_bank/u_group_0_slice_0/we_in"]["density_hz"] == pytest.approx(
        3.5 / (50 * 1e-12)
    )
    assert "score_bank/u_group_0_slice_0/alias_we_in" not in by_name


def test_extract_fakeram_activity_rejects_bad_hash(tmp_path: Path) -> None:
    vcd_path = tmp_path / "mini.vcd"
    _write_vcd(vcd_path, _mini_vcd())
    wrong_hash = hashlib.sha256(b"wrong").hexdigest()
    with pytest.raises(ValueError, match="source_vcd_sha256 does not match"):
        extract_fakeram_vcd_activity(vcd_path, source_vcd_sha256=wrong_hash, expected_pin_count=91)


def test_extract_fakeram_activity_rejects_missing_active_window(tmp_path: Path) -> None:
    path = tmp_path / "missing_active.vcd"
    _write_vcd(
        path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module score_bank $end",
                "$scope module u_group_0_slice_0 $end",
                "$var reg 11 a addr_in [10:0] $end",
                "$var reg 1 d we_in $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                "b00000000000 a",
                "0d",
            ]
        ),
    )
    with pytest.raises(ValueError, match="missing active dumpon/dumpoff interval"):
        extract_fakeram_vcd_activity(path, source_vcd_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), expected_pin_count=12)


def test_extract_fakeram_activity_accepts_exact_duplicate_declarations(tmp_path: Path) -> None:
    vcd_path = tmp_path / "duplicate_declaration.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module outer $end",
                "$scope module score_bank $end",
                "$scope module u_group_0_slice_0 $end",
                "$var reg 11 a addr_in [10:0] $end",
                "$var reg 11 a addr_in [10:0] $end",
                "$var reg 39 b wd_in [38:0] $end",
                "$var reg 39 b wd_in [38:0] $end",
                "$var reg 39 c w_mask_in [38:0] $end",
                "$var reg 39 c w_mask_in [38:0] $end",
                "$var reg 1 d we_in $end",
                "$var reg 1 d we_in $end",
                "$var reg 1 e ce_in $end",
                "$var reg 1 e ce_in $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                f"b{'0'*11} a",
                f"b{'0'*39} b",
                f"b{'0'*39} c",
                "0d",
                "0e",
                "#1",
                "$dumpon",
                "#2",
                "1d",
                "#3",
                "0d",
                "#4",
                "$dumpoff",
            ]
        ),
    )
    payload = extract_fakeram_vcd_activity(
        vcd_path,
        source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
        scope="tb/dut",
        group_indices=(0,),
        slice_indices=(0,),
        expected_pin_count=91,
    )
    assert len(payload["pins"]) == 91
    row = {row["full_name"]: row for row in payload["pins"]}["score_bank/u_group_0_slice_0/we_in"]
    assert row["transition_count"] == 2.0


def test_extract_fakeram_activity_rejects_inconsistent_duplicate_full_name(tmp_path: Path) -> None:
    vcd_path = tmp_path / "bad_duplicate.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module outer $end",
                "$scope module score_bank $end",
                "$scope module u_group_0_slice_0 $end",
                "$var reg 11 a addr_in [10:0] $end",
                "$var reg 11 b addr_in [10:0] $end",
                "$var reg 39 c wd_in [38:0] $end",
                "$var reg 39 d w_mask_in [38:0] $end",
                "$var reg 1 e we_in $end",
                "$var reg 1 f ce_in $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                f"b{'0'*11} a",
                f"b{'0'*39} c",
                f"b{'0'*39} d",
                "0e",
                "0f",
                "#1",
                "$dumpon",
                "#2",
                "$dumpoff",
            ]
        ),
    )
    with pytest.raises(ValueError, match="duplicate declaration for .*addr_in"):
        extract_fakeram_vcd_activity(
            vcd_path,
            source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
            scope="tb/dut",
            group_indices=(0,),
            slice_indices=(0,),
            expected_pin_count=91,
        )


def test_extract_multivalue_service_activity_tracks_both_macro_classes(tmp_path: Path) -> None:
    vcd_path = tmp_path / "service_macro.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module wrapper $end",
                "$scope module score_bank $end",
                "$scope module u_group_0_slice_0 $end",
                "$var reg 11 a addr_in [10:0] $end",
                "$var reg 39 b wd_in [38:0] $end",
                "$var reg 39 c w_mask_in [38:0] $end",
                "$var reg 1 d we_in $end",
                "$var reg 1 e ce_in $end",
                "$upscope $end",
                "$upscope $end",
                "$scope begin gen_value_macro_backend $end",
                "$scope begin gen_value_bank[0] $end",
                "$scope begin gen_value_lane[0] $end",
                "$scope module u_value_mem_lane $end",
                "$var reg 6 f addr_in [5:0] $end",
                "$var reg 32 g wd_in [31:0] $end",
                "$var reg 32 h w_mask_in [31:0] $end",
                "$var reg 1 i we_in $end",
                "$var reg 1 j ce_in $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                f"b{'0'*11} a",
                f"b{'0'*39} b",
                f"b{'0'*39} c",
                "0d",
                "1e",
                f"b{'0'*6} f",
                f"b{'0'*32} g",
                f"b{'0'*32} h",
                "0i",
                "0j",
                "#10",
                "$dumpon",
                "#20",
                f"b{'1' + '0'*10} a",
                "1d",
                f"b{'1' + '0'*5} f",
                "1j",
                "#40",
                "0d",
                "0j",
                "#50",
                "$dumpoff",
            ]
        ),
    )
    payload = extract_multivalue_service_fakeram_vcd_activity(
        vcd_path,
        source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
        scope="tb/dut",
        group_indices=(0,),
        slice_indices=(0,),
        value_bank_indices=(0,),
        value_lane_indices=(0,),
        expected_pin_count=163,
    )

    assert payload["target_profile"] == "multivalue_service_c1_v1"
    assert len(payload["pins"]) == 163
    by_name = {row["full_name"]: row for row in payload["pins"]}
    assert "score_bank/u_group_0_slice_0/we_in" in by_name
    assert "gen_value_macro_backend/gen_value_bank[0]/gen_value_lane[0]/u_value_mem_lane/ce_in" in by_name
    contract = payload["structural_macro_contract"]
    assert contract["total_assignment_count"] == 163
    classes = {row["macro_name"]: row for row in contract["macro_classes"]}
    assert classes["fakeram45_2048x39"]["assignment_count"] == 91
    assert classes["fakeram45_64x32"]["assignment_count"] == 72


@pytest.mark.skipif(not _iverilog_available(), reason="iverilog/vvp unavailable")
def test_extract_multivalue_service_activity_real_generated_vcd_sidecar(tmp_path: Path) -> None:
    activity_dir = tmp_path / "activity"
    manifest = generate_activity(_service_config(), activity_dir)
    vcd_path = activity_dir / manifest["artifacts"]["vcd"]
    payload = extract_multivalue_service_fakeram_vcd_activity(
        vcd_path,
        source_vcd_sha256=manifest["hashes"]["vcd_sha256"],
        scope="tb/dut",
    )

    assert payload["source_vcd"] == vcd_path.name
    assert payload["source_vcd_sha256"] == manifest["hashes"]["vcd_sha256"]
    assert payload["target_profile"] == "multivalue_service_c1_v1"
    assert len(payload["pins"]) == 9704
    classes = {row["macro_name"]: row for row in payload["structural_macro_contract"]["macro_classes"]}
    assert classes["fakeram45_2048x39"]["instance_count"] == 56
    assert classes["fakeram45_2048x39"]["assignment_count"] == 5096
    assert classes["fakeram45_64x32"]["instance_count"] == 64
    assert classes["fakeram45_64x32"]["assignment_count"] == 4608
    assert payload["structural_macro_contract"]["total_assignment_count"] == 9704
    full_names = {row["full_name"] for row in payload["pins"]}
    assert "score_bank/u_group_7_slice_6/ce_in" in full_names
    assert (
        "gen_value_macro_backend/gen_value_bank[3]/gen_value_lane[15]/u_value_mem_lane/ce_in"
        in full_names
    )
