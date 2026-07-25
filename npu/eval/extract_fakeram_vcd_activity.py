#!/usr/bin/env python3
"""Extract per-pin activity from Fakeram VCD for structural macro annotations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Any

JsonDict = dict[str, Any]

TARGET_SCOPE_PREFIX = "tb/dut"
_TARGET_GROUP_SCOPE_RE = re.compile(r"^u_group_(\d+)_slice_(\d+)$")
_VALUE_BANK_SCOPE_RE = re.compile(r"^gen_value_bank\[(\d+)\]$")
_VALUE_LANE_SCOPE_RE = re.compile(r"^gen_value_lane\[(\d+)\]$")
_VAR_RE = re.compile(r"^\$var\s+\S+\s+(\d+)\s+(\S+)\s+(.*?)\s+\$end$")
_SCOPE_RE = re.compile(r"^\$scope\s+\S+\s+(\S+)\s+\$end$")
_SCALAR_UPDATE_RE = re.compile(r"^([01xXzZ])(\S+)$")
_VECTOR_UPDATE_RE = re.compile(r"^b([01xXzZ]+)\s+(\S+)$")

_SCORE_PIN_WIDTHS = {
    "addr_in": 11,
    "wd_in": 39,
    "w_mask_in": 39,
    "we_in": 1,
    "ce_in": 1,
}
_VALUE_PIN_WIDTHS = {
    "addr_in": 6,
    "wd_in": 32,
    "w_mask_in": 32,
    "we_in": 1,
    "ce_in": 1,
}


@dataclass(frozen=True)
class _MacroClassSpec:
    macro_name: str
    pin_widths: dict[str, int]
    instance_scope_prefix: str


@dataclass
class _PinActivity:
    full_name: str
    last_value: str | None
    last_tick: int
    transition_count: float
    high_ticks: int


_SCORE_MACRO_SPEC = _MacroClassSpec(
    macro_name="fakeram45_2048x39",
    pin_widths=_SCORE_PIN_WIDTHS,
    instance_scope_prefix="score_bank",
)
_VALUE_MACRO_SPEC = _MacroClassSpec(
    macro_name="fakeram45_64x32",
    pin_widths=_VALUE_PIN_WIDTHS,
    instance_scope_prefix="gen_value_macro_backend",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_float_bits(value: str, unit: str) -> float:
    factors = {
        "s": 1.0,
        "ms": 1e-3,
        "us": 1e-6,
        "ns": 1e-9,
        "ps": 1e-12,
        "fs": 1e-15,
    }
    unit_key = unit.strip().lower()
    if unit_key not in factors:
        raise ValueError(f"unsupported timescale unit: {unit}")
    try:
        return float(value) * factors[unit_key]
    except ValueError as exc:
        raise ValueError(f"invalid timescale value: {value}") from exc


def _parse_timescale(vcd_text: str) -> float:
    match = re.search(r"\$timescale\b(.*?)\$end", vcd_text, flags=re.S | re.I)
    if match is None:
        raise ValueError("missing $timescale declaration")
    body = " ".join(match.group(1).split())
    range_match = re.fullmatch(r"([0-9]+)\s*([A-Za-z]+)\s*/\s*([0-9]+)\s*([A-Za-z]+)", body)
    if range_match:
        return _safe_float_bits(range_match.group(3), range_match.group(4))
    direct_match = re.fullmatch(r"([0-9]+)\s*([A-Za-z]+)", body)
    if direct_match:
        return _safe_float_bits(direct_match.group(1), direct_match.group(2))
    raise ValueError(f"unrecognized $timescale format: {body!r}")


def _parse_range_indices(raw: str | None, width: int) -> list[int]:
    if raw is None:
        return list(range(width))
    match = re.fullmatch(r"\[\s*([+-]?\d+)\s*:\s*([+-]?\d+)\s*\]", raw)
    if match is None:
        return list(range(width))
    start = int(match.group(1))
    end = int(match.group(2))
    if width <= 0:
        raise ValueError("signal width must be > 0")
    step = -1 if start > end else 1
    expected = list(range(start, end + step, step))
    if len(expected) != width:
        raise ValueError(
            f"vector range has {len(expected)} bits but declaration reports width {width}: [{start}:{end}]"
        )
    return expected


def _score_scope_result(
    parts: list[str],
    *,
    group_indices: tuple[int, ...],
    slice_indices: tuple[int, ...],
) -> tuple[str, _MacroClassSpec] | None:
    for index, part in enumerate(parts):
        if part != "score_bank":
            continue
        if index + 1 >= len(parts):
            return None
        group_scope = parts[index + 1]
        match = _TARGET_GROUP_SCOPE_RE.fullmatch(group_scope)
        if match is None:
            continue
        group_idx = int(match.group(1))
        slice_idx = int(match.group(2))
        if group_idx not in group_indices or slice_idx not in slice_indices:
            continue
        if index + 2 != len(parts):
            continue
        return (f"score_bank/{group_scope}", _SCORE_MACRO_SPEC)
    return None


def _value_scope_result(
    parts: list[str],
    *,
    value_bank_indices: tuple[int, ...],
    value_lane_indices: tuple[int, ...],
) -> tuple[str, _MacroClassSpec] | None:
    for index, part in enumerate(parts):
        if part != "gen_value_macro_backend":
            continue
        if index + 3 >= len(parts):
            return None
        bank_scope = parts[index + 1]
        lane_scope = parts[index + 2]
        leaf_scope = parts[index + 3]
        bank_match = _VALUE_BANK_SCOPE_RE.fullmatch(bank_scope)
        lane_match = _VALUE_LANE_SCOPE_RE.fullmatch(lane_scope)
        if bank_match is None or lane_match is None or leaf_scope != "u_value_mem_lane":
            continue
        bank_idx = int(bank_match.group(1))
        lane_idx = int(lane_match.group(1))
        if bank_idx not in value_bank_indices or lane_idx not in value_lane_indices:
            continue
        if index + 4 != len(parts):
            continue
        return (
            f"gen_value_macro_backend/{bank_scope}/{lane_scope}/{leaf_scope}",
            _VALUE_MACRO_SPEC,
        )
    return None


def _parse_target_scope(
    scope_path: str,
    *,
    root_scope: str,
    group_indices: tuple[int, ...],
    slice_indices: tuple[int, ...],
    include_value_memory: bool,
    value_bank_indices: tuple[int, ...],
    value_lane_indices: tuple[int, ...],
) -> tuple[str, _MacroClassSpec] | None:
    if scope_path == root_scope:
        return None
    if not scope_path.startswith(f"{root_scope}/"):
        return None
    remainder = scope_path[len(root_scope) + 1 :]
    if not remainder:
        return None
    parts = remainder.split("/")
    score_result = _score_scope_result(
        parts,
        group_indices=group_indices,
        slice_indices=slice_indices,
    )
    if score_result is not None:
        return score_result
    if not include_value_memory:
        return None
    return _value_scope_result(
        parts,
        value_bank_indices=value_bank_indices,
        value_lane_indices=value_lane_indices,
    )


def _sanitize_bit(value: str) -> str:
    val = value.lower()
    if val not in {"0", "1", "x", "z"}:
        raise ValueError(f"unsupported logic value: {value!r}")
    return val


def _transition_delta(old: str, new: str) -> float:
    if old == new:
        return 0.0
    if (old in {"0", "1"}) and (new in {"0", "1"}):
        return 1.0
    return 0.5


def _normalize_vector_update(value: str, width: int) -> list[str]:
    if len(value) > width:
        raise ValueError(f"vector value has {len(value)} bits but declared width is {width}")
    bits = [_sanitize_bit(ch) for ch in value]
    if len(bits) == width:
        return bits
    if len(bits) < width:
        if set(bits) == {"x"}:
            return ["x"] * width
        if set(bits) == {"z"}:
            return ["z"] * width
        return ["0"] * (width - len(bits)) + bits
    return bits


def _value_to_tick_delta(value: str | None, tick_delta: int) -> int:
    if tick_delta < 0:
        raise ValueError("timestamps in VCD must be nondecreasing")
    if tick_delta == 0 or value != "1":
        return 0
    return tick_delta


def _pins_per_instance(spec: _MacroClassSpec) -> int:
    return sum(spec.pin_widths.values())


def _contract_rows(
    *,
    include_value_memory: bool,
    group_indices: tuple[int, ...],
    slice_indices: tuple[int, ...],
    value_bank_indices: tuple[int, ...],
    value_lane_indices: tuple[int, ...],
    instance_names_by_macro: dict[str, set[str]],
    pin_count_by_macro: dict[str, int],
) -> tuple[list[JsonDict], int]:
    expected: list[tuple[_MacroClassSpec, int]] = [
        (_SCORE_MACRO_SPEC, len(group_indices) * len(slice_indices)),
    ]
    if include_value_memory:
        expected.append((_VALUE_MACRO_SPEC, len(value_bank_indices) * len(value_lane_indices)))

    rows: list[JsonDict] = []
    total_assignment_count = 0
    for spec, expected_instance_count in expected:
        pins_per_instance = _pins_per_instance(spec)
        expected_assignment_count = pins_per_instance * expected_instance_count
        observed_instance_count = len(instance_names_by_macro.get(spec.macro_name, set()))
        observed_assignment_count = pin_count_by_macro.get(spec.macro_name, 0)
        if observed_instance_count != expected_instance_count:
            raise ValueError(
                f"{spec.macro_name} structural instance count mismatch: expected "
                f"{expected_instance_count}, got {observed_instance_count}"
            )
        if observed_assignment_count != expected_assignment_count:
            raise ValueError(
                f"{spec.macro_name} structural pin count mismatch: expected "
                f"{expected_assignment_count}, got {observed_assignment_count}"
            )
        total_assignment_count += observed_assignment_count
        rows.append(
            {
                "macro_name": spec.macro_name,
                "instance_scope_prefix": spec.instance_scope_prefix,
                "instance_count": observed_instance_count,
                "pins_per_instance": pins_per_instance,
                "assignment_count": observed_assignment_count,
            }
        )
    return rows, total_assignment_count


def _extract_macro_vcd_activity(
    vcd_path: Path,
    *,
    source_vcd_sha256: str,
    scope: str,
    group_indices: tuple[int, ...],
    slice_indices: tuple[int, ...],
    expected_pin_count: int | None,
    include_value_memory: bool,
    value_bank_indices: tuple[int, ...],
    value_lane_indices: tuple[int, ...],
    target_profile: str,
) -> JsonDict:
    if not source_vcd_sha256:
        raise ValueError("source_vcd_sha256 is required")

    required_pin_names = set(_SCORE_PIN_WIDTHS)
    if include_value_memory:
        required_pin_names.update(_VALUE_PIN_WIDTHS)

    vcd_text = vcd_path.read_text(encoding="utf-8", errors="replace")
    actual_hash = _sha256_file(vcd_path)
    if actual_hash != source_vcd_sha256.lower():
        raise ValueError("source_vcd_sha256 does not match actual vcd content")

    timescale_seconds = _parse_timescale(vcd_text)
    if not math.isfinite(timescale_seconds) or timescale_seconds <= 0:
        raise ValueError("timescale_seconds must be a positive finite value")

    id_to_full_names: dict[str, tuple[str, ...]] = {}
    id_to_specs: dict[str, tuple[str, int]] = {}
    all_pin_last_values: dict[str, str | None] = {}
    full_name_specs: dict[str, tuple[str, int]] = {}
    instance_names_by_macro: dict[str, set[str]] = {}
    pin_count_by_macro: dict[str, int] = {}
    scope_stack: list[str] = []

    lines = vcd_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped == "$enddefinitions":
            break
        if stripped.startswith("$scope "):
            scope_match = _SCOPE_RE.match(stripped)
            if scope_match:
                scope_stack.append(scope_match.group(1).strip())
            continue
        if stripped == "$upscope" or stripped == "$upscope $end":
            if scope_stack:
                scope_stack.pop()
            continue
        if not (stripped.startswith("$var ") and stripped.endswith("$end")):
            continue

        match = _VAR_RE.match(stripped)
        if match is None:
            continue
        width = int(match.group(1))
        var_id = match.group(2)
        body = match.group(3).strip()
        decl_tokens = body.split()
        if not decl_tokens:
            continue
        name = decl_tokens[0]
        if name.startswith("\\"):
            continue
        if width <= 0 or name not in required_pin_names:
            continue

        scope_path = "/".join(scope_stack)
        scope_result = _parse_target_scope(
            scope_path,
            root_scope=scope,
            group_indices=group_indices,
            slice_indices=slice_indices,
            include_value_memory=include_value_memory,
            value_bank_indices=value_bank_indices,
            value_lane_indices=value_lane_indices,
        )
        if scope_result is None:
            continue
        full_scope, macro_spec = scope_result
        if name not in macro_spec.pin_widths:
            continue

        expected_width = macro_spec.pin_widths[name]
        if width != expected_width:
            raise ValueError(f"{scope_path}/{name} width mismatch: expected {expected_width}, got {width}")

        if len(decl_tokens) > 1:
            range_expr = decl_tokens[1]
            if range_expr.startswith("[") and range_expr.endswith("]"):
                bit_indices = _parse_range_indices(range_expr, width)
            else:
                bit_indices = list(range(width))
        else:
            bit_indices = list(range(width))

        if width == 1:
            full_names = (f"{full_scope}/{name}",)
        else:
            if len(bit_indices) != width:
                raise ValueError(f"{scope_path}/{name} requires {width} bits but range mapping was {len(bit_indices)}")
            full_names = tuple(f"{full_scope}/{name}[{index}]" for index in bit_indices)

        def _signal_base(full_name: str) -> str:
            leaf = full_name.rsplit("/", 1)[-1]
            return leaf.split("[", 1)[0]

        unique_full_names: list[str] = []
        for bit_index, full_name in enumerate(full_names):
            existing = full_name_specs.get(full_name)
            if existing is None:
                full_name_specs[full_name] = (var_id, bit_index)
                all_pin_last_values[full_name] = None
                pin_count_by_macro[macro_spec.macro_name] = pin_count_by_macro.get(macro_spec.macro_name, 0) + 1
                unique_full_names.append(full_name)
                continue
            existing_var_id, existing_bit_index = existing
            if existing_var_id != var_id or existing_bit_index != bit_index:
                raise ValueError(f"duplicate declaration for {full_name}")

        if unique_full_names:
            instance_names_by_macro.setdefault(macro_spec.macro_name, set()).add(full_scope)

        if var_id in id_to_full_names:
            existing = id_to_full_names[var_id]
            expected_base, expected_width = id_to_specs[var_id]
            signal_base = _signal_base(full_names[0]) if full_names else ""
            if signal_base != expected_base or len(full_names) != expected_width:
                raise ValueError(f"duplicate id {var_id} with mismatched width/bit-count")
            if {_signal_base(existing_name) for existing_name in existing} != {
                _signal_base(current_name) for current_name in full_names
            }:
                raise ValueError(f"duplicate id {var_id} with inconsistent target names")
            if unique_full_names:
                id_to_full_names[var_id] = existing + tuple(unique_full_names)
        else:
            id_to_full_names[var_id] = tuple(unique_full_names)
            id_to_specs[var_id] = (_signal_base(full_names[0]), len(full_names))

    if expected_pin_count is None:
        expected_pin_count = _pins_per_instance(_SCORE_MACRO_SPEC) * len(group_indices) * len(slice_indices)
        if include_value_memory:
            expected_pin_count += _pins_per_instance(_VALUE_MACRO_SPEC) * len(value_bank_indices) * len(
                value_lane_indices
            )

    active_start: int | None = None
    active_end: int | None = None
    current_time = 0
    dumping = False
    state_by_pin = {name: None for name in all_pin_last_values}
    pin_rows: dict[str, _PinActivity] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_time = int(stripped[1:])
            continue
        if stripped == "$dumpon":
            if active_end is not None:
                raise ValueError("found $dumpon after $dumpoff")
            if dumping:
                raise ValueError("found nested $dumpon without $dumpoff")
            active_start = current_time
            dumping = True
            pin_rows = {
                full_name: _PinActivity(
                    full_name=full_name,
                    last_value=value,
                    last_tick=current_time,
                    transition_count=0.0,
                    high_ticks=0,
                )
                for full_name, value in state_by_pin.items()
            }
            continue
        if stripped == "$dumpoff":
            if not dumping:
                raise ValueError("found $dumpoff without active $dumpon")
            active_end = current_time
            dumping = False
            break

        scalar_update = _SCALAR_UPDATE_RE.match(stripped)
        if scalar_update is not None:
            new_value = _sanitize_bit(scalar_update.group(1))
            var_id = scalar_update.group(2)
            if var_id not in id_to_full_names:
                continue
            for full_name in id_to_full_names[var_id]:
                state_by_pin[full_name] = new_value
                if not dumping:
                    continue
                row = pin_rows[full_name]
                if row.last_value is not None:
                    row.transition_count += _transition_delta(row.last_value, new_value)
                row.high_ticks += _value_to_tick_delta(row.last_value, current_time - row.last_tick)
                row.last_value = new_value
                row.last_tick = current_time
            continue

        vector_update = _VECTOR_UPDATE_RE.match(stripped)
        if vector_update is not None:
            bits = vector_update.group(1).lower()
            var_id = vector_update.group(2)
            if var_id not in id_to_full_names:
                continue
            full_names = id_to_full_names[var_id]
            bit_values = _normalize_vector_update(bits, len(full_names))
            if len(bit_values) != len(full_names):
                raise ValueError(f"vector update width mismatch for {var_id}: expected {len(full_names)}, got {len(bit_values)}")
            for index, full_name in enumerate(full_names):
                state_by_pin[full_name] = bit_values[index]
                if not dumping:
                    continue
                row = pin_rows[full_name]
                new_value = bit_values[index]
                if row.last_value is not None:
                    row.transition_count += _transition_delta(row.last_value, new_value)
                row.high_ticks += _value_to_tick_delta(row.last_value, current_time - row.last_tick)
                row.last_value = new_value
                row.last_tick = current_time
            continue

    if len(all_pin_last_values) != expected_pin_count:
        raise ValueError(
            "missing expected target pin declarations: "
            f"found {len(all_pin_last_values)} expected {expected_pin_count}"
        )
    if active_start is None or active_end is None:
        raise ValueError("missing active dumpon/dumpoff interval")
    if active_end <= active_start:
        raise ValueError("active_end_tick must be greater than active_start_tick")

    duration = active_end - active_start
    for row in pin_rows.values():
        if row.last_value is not None:
            row.high_ticks += _value_to_tick_delta(row.last_value, active_end - row.last_tick)

    pins: list[JsonDict] = []
    for row in sorted(pin_rows.values(), key=lambda entry: entry.full_name):
        duty = row.high_ticks / duration
        density = row.transition_count / (duration * timescale_seconds)
        if not math.isfinite(row.transition_count) or row.transition_count < 0:
            raise ValueError(f"non-finite transition count for {row.full_name}")
        if not math.isfinite(duty) or duty < 0.0 or duty > 1.0:
            raise ValueError(f"non-finite or out-of-range duty_cycle for {row.full_name}")
        if not math.isfinite(density) or density < 0.0:
            raise ValueError(f"non-finite density_hz for {row.full_name}")
        pins.append(
            {
                "full_name": row.full_name,
                "density_hz": density,
                "duty_cycle": duty,
                "transition_count": row.transition_count,
                "source": "vcd",
            }
        )

    contract_rows, total_assignment_count = _contract_rows(
        include_value_memory=include_value_memory,
        group_indices=group_indices,
        slice_indices=slice_indices,
        value_bank_indices=value_bank_indices,
        value_lane_indices=value_lane_indices,
        instance_names_by_macro=instance_names_by_macro,
        pin_count_by_macro=pin_count_by_macro,
    )

    return {
        "version": 1,
        "model": "fakeram_macro_pin_vcd_activity_v1",
        "target_profile": target_profile,
        "scope": scope,
        "source_vcd": vcd_path.name,
        "source_vcd_sha256": actual_hash,
        "timescale_seconds": timescale_seconds,
        "active_start_tick": active_start,
        "active_end_tick": active_end,
        "structural_macro_contract": {
            "profile": target_profile,
            "macro_classes": contract_rows,
            "total_assignment_count": total_assignment_count,
        },
        "pins": pins,
    }


def extract_fakeram_vcd_activity(
    vcd_path: Path,
    *,
    source_vcd_sha256: str,
    scope: str = TARGET_SCOPE_PREFIX,
    pin_widths: dict[str, int] | None = None,
    group_indices: tuple[int, ...] = tuple(range(8)),
    slice_indices: tuple[int, ...] = tuple(range(7)),
    expected_pin_count: int | None = None,
) -> JsonDict:
    if pin_widths is not None:
        unexpected = set(pin_widths) - set(_SCORE_PIN_WIDTHS)
        if unexpected:
            raise ValueError(f"unexpected pin_widths keys: {', '.join(sorted(unexpected))}")
        if dict(pin_widths) != _SCORE_PIN_WIDTHS:
            raise ValueError("score-bank extractor requires the default fakeram45_2048x39 pin widths")
    return _extract_macro_vcd_activity(
        vcd_path,
        source_vcd_sha256=source_vcd_sha256,
        scope=scope,
        group_indices=group_indices,
        slice_indices=slice_indices,
        expected_pin_count=expected_pin_count,
        include_value_memory=False,
        value_bank_indices=(),
        value_lane_indices=(),
        target_profile="score_bank_proxy_v1",
    )


def extract_multivalue_service_fakeram_vcd_activity(
    vcd_path: Path,
    *,
    source_vcd_sha256: str,
    scope: str = TARGET_SCOPE_PREFIX,
    group_indices: tuple[int, ...] = tuple(range(8)),
    slice_indices: tuple[int, ...] = tuple(range(7)),
    value_bank_indices: tuple[int, ...] = tuple(range(4)),
    value_lane_indices: tuple[int, ...] = tuple(range(16)),
    expected_pin_count: int | None = None,
) -> JsonDict:
    return _extract_macro_vcd_activity(
        vcd_path,
        source_vcd_sha256=source_vcd_sha256,
        scope=scope,
        group_indices=group_indices,
        slice_indices=slice_indices,
        expected_pin_count=expected_pin_count,
        include_value_memory=True,
        value_bank_indices=value_bank_indices,
        value_lane_indices=value_lane_indices,
        target_profile="multivalue_service_c1_v1",
    )


def write_fakeram_vcd_activity(vcd_path: Path, *, output_path: Path, **kwargs: Any) -> JsonDict:
    payload = extract_fakeram_vcd_activity(vcd_path, **kwargs)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    raise SystemExit("extractor is library-only")
