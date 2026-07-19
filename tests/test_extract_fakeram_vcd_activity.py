#!/usr/bin/env python3
"""Tests for Fakeram VCD extractor."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from npu.eval.extract_fakeram_vcd_activity import extract_fakeram_vcd_activity


def _write_vcd(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


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
