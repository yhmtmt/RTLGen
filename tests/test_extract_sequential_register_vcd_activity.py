#!/usr/bin/env python3
"""Tests for sequential-register VCD extractor."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from npu.eval.extract_sequential_register_vcd_activity import (
    extract_sequential_register_vcd_activity,
)


def _write_vcd(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _mini_vcd() -> str:
    return "\n".join(
        [
            "$date",
            " Sequential register VCD",
            "$end",
            "$version",
            "  test",
            "$end",
            "$timescale",
            " 1ns/1ps",
            "$end",
            "$scope module tb $end",
            "$scope module dut $end",
            "$scope module reducer $end",
            "$var reg 3 a \\numerator_accum[56] [2:0] $end",
            "$upscope $end",
            "$scope module score_tile $end",
            "$var reg 2 b \\accum[3] [1:0] $end",
            "$upscope $end",
            "$upscope $end",
            "$enddefinitions",
            "#0",
            "b000 a",
            "b00 b",
            "#10",
            "$dumpon",
            "#20",
            "b010 a",
            "b10 b",
            "#30",
            "b01 b",
            "#35",
            "$dumpoff",
        ]
    )


def test_extract_sequential_register_activity_mini_vcd_semantics(tmp_path: Path) -> None:
    vcd_path = tmp_path / "mini.vcd"
    _write_vcd(vcd_path, _mini_vcd())
    payload = extract_sequential_register_vcd_activity(
        vcd_path,
        source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
        scope="tb/dut",
    )

    assert payload["version"] == 1
    assert payload["model"] == "sequential_register_vcd_activity_v1"
    assert payload["scope"] == "tb/dut"
    assert payload["source_vcd"] == vcd_path.name
    assert payload["timescale_seconds"] == 1e-12
    assert payload["active_start_tick"] == 10
    assert payload["active_end_tick"] == 35
    assert payload["active_end_tick"] > payload["active_start_tick"]
    assert len(payload["register_bits"]) == 5

    rows = {row["full_name"]: row for row in payload["register_bits"]}
    assert rows["reducer/numerator_accum[56][1]"]["transition_count"] == 1.0
    assert rows["reducer/numerator_accum[56][1]"]["duty_cycle"] == pytest.approx(0.6)
    assert rows["score_tile/accum[3][1]"]["transition_count"] == 2.0
    assert rows["score_tile/accum[3][1]"]["duty_cycle"] == pytest.approx(0.4)
    assert rows["score_tile/accum[3][0]"]["transition_count"] == 1.0
    assert rows["score_tile/accum[3][0]"]["duty_cycle"] == pytest.approx(0.2)


def test_extract_sequential_register_activity_rejects_bad_hash(tmp_path: Path) -> None:
    vcd_path = tmp_path / "mini.vcd"
    _write_vcd(vcd_path, _mini_vcd())
    with pytest.raises(ValueError, match="source_vcd_sha256 does not match"):
        extract_sequential_register_vcd_activity(
            vcd_path,
            source_vcd_sha256=hashlib.sha256(b"wrong").hexdigest(),
            scope="tb/dut",
        )


def test_extract_sequential_register_activity_rejects_missing_active_window(tmp_path: Path) -> None:
    vcd_path = tmp_path / "missing_active.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module reducer $end",
                "$var reg 1 a signal $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                "0a",
            ]
        ),
    )
    with pytest.raises(ValueError, match="missing active dumpon/dumpoff interval"):
        extract_sequential_register_vcd_activity(
            vcd_path,
            source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
            scope="tb/dut",
        )


def test_extract_sequential_register_activity_rejects_malformed_range(tmp_path: Path) -> None:
    vcd_path = tmp_path / "bad_range.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module reducer $end",
                "$var reg 2 a \\accum [1:0:0] $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                "b00 a",
                "#10",
                "$dumpon",
                "#20",
                "b11 a",
                "#30",
                "$dumpoff",
            ]
        ),
    )
    with pytest.raises(ValueError, match="malformed"):
        extract_sequential_register_vcd_activity(
            vcd_path,
            source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
            scope="tb/dut",
        )


def test_extract_sequential_register_activity_rejects_duplicate_declaration(tmp_path: Path) -> None:
    vcd_path = tmp_path / "duplicate.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut $end",
                "$scope module reducer $end",
                "$var reg 1 b bit $end",
                "$var reg 1 b other $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                "0b",
                "1b",
                "#10",
                "$dumpon",
                "#20",
                "0b",
                "#25",
                "$dumpoff",
            ]
        ),
    )
    with pytest.raises(ValueError, match="duplicate declaration"):
        extract_sequential_register_vcd_activity(
            vcd_path,
            source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
            scope="tb/dut",
        )


def test_extract_sequential_register_activity_ignores_adjacent_scope(tmp_path: Path) -> None:
    vcd_path = tmp_path / "adjacent_scope.vcd"
    _write_vcd(
        vcd_path,
        "\n".join(
            [
                "$timescale",
                "1ns/1ps",
                "$end",
                "$scope module tb $end",
                "$scope module dut_shadow $end",
                "$var reg 1 outside ignored $end",
                "$upscope $end",
                "$scope module dut $end",
                "$var reg 1 inside kept $end",
                "$upscope $end",
                "$upscope $end",
                "$enddefinitions",
                "#0",
                "0outside",
                "0inside",
                "#10",
                "$dumpon",
                "#20",
                "1outside",
                "1inside",
                "#30",
                "$dumpoff",
            ]
        ),
    )

    payload = extract_sequential_register_vcd_activity(
        vcd_path,
        source_vcd_sha256=hashlib.sha256(vcd_path.read_bytes()).hexdigest(),
        scope="tb/dut",
    )

    assert [row["full_name"] for row in payload["register_bits"]] == ["kept"]
