#!/usr/bin/env python3
"""Extract per-bit sequential-register activity from RTL VCD traces."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

_TARGET_SCOPE_PREFIX = "tb/dut"
_VAR_RE = re.compile(r"^\$var\s+(\S+)\s+(\d+)\s+(\S+)\s+(.*?)\s+\$end$")
_SCOPE_RE = re.compile(r"^\$scope\s+\S+\s+(\S+)\s+\$end$")
_SCALAR_UPDATE_RE = re.compile(r"^([01xXzZ])(\S+)$")
_VECTOR_UPDATE_RE = re.compile(r"^b([01xXzZ]+)\s+(\S+)$")


@dataclass
class _RegisterBitActivity:
    full_name: str
    last_value: str | None
    last_tick: int
    transition_count: float
    high_ticks: int


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
        raise ValueError(f"malformed range expression: {raw!r}")
    start = int(match.group(1))
    end = int(match.group(2))
    if width <= 0:
        raise ValueError("signal width must be > 0")
    step = -1 if start > end else 1
    bit_indices = list(range(start, end + step, step))
    if len(bit_indices) != width:
        raise ValueError(
            f"vector range has {len(bit_indices)} bits but declaration reports width {width}: [{start}:{end}]"
        )
    return bit_indices


def _parse_var_name_and_range(raw: str) -> tuple[str, str | None]:
    text = raw.strip()
    if not text:
        raise ValueError("malformed $var declaration: missing name")
    if text.startswith("\\"):
        pieces = text.split(None, 1)
        name = pieces[0]
        range_expr = pieces[1].strip() if len(pieces) == 2 else None
        if range_expr is not None and not re.fullmatch(r"\[\s*[+-]?\d+\s*:\s*[+-]?\d+\s*\]", range_expr):
            raise ValueError(f"malformed escaped $var declaration: {raw!r}")
    else:
        tokens = text.split()
        if len(tokens) == 0:
            raise ValueError(f"malformed $var declaration: {raw!r}")
        if len(tokens) > 2:
            raise ValueError(f"malformed $var declaration: {raw!r}")
        name = tokens[0]
        range_expr = tokens[1] if len(tokens) == 2 else None
    return name.lstrip("\\"), range_expr


def _normalize_scope_tail(scope_path: str) -> str:
    if scope_path == _TARGET_SCOPE_PREFIX:
        return ""
    if not scope_path.startswith(f"{_TARGET_SCOPE_PREFIX}/"):
        raise ValueError(f"signal declaration outside scope '{_TARGET_SCOPE_PREFIX}': {scope_path}")
    return scope_path[len(_TARGET_SCOPE_PREFIX) + 1 :]


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
        raise ValueError(f"vector update has {len(value)} bits but declaration width is {width}")
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


def extract_sequential_register_vcd_activity(
    vcd_path: Path,
    *,
    source_vcd_sha256: str,
    scope: str = _TARGET_SCOPE_PREFIX,
) -> JsonDict:
    if scope != _TARGET_SCOPE_PREFIX:
        raise ValueError(f"scope must be {_TARGET_SCOPE_PREFIX}")
    if not source_vcd_sha256:
        raise ValueError("source_vcd_sha256 is required")

    vcd_text = vcd_path.read_text(encoding="utf-8", errors="replace")
    actual_hash = _sha256_file(vcd_path)
    if actual_hash != source_vcd_sha256.lower():
        raise ValueError("source_vcd_sha256 does not match actual vcd content")

    timescale_seconds = _parse_timescale(vcd_text)
    if not math.isfinite(timescale_seconds) or timescale_seconds <= 0.0:
        raise ValueError("timescale_seconds must be a positive finite value")

    id_to_full_names: dict[str, tuple[str, ...]] = {}
    full_name_specs: dict[str, tuple[str, int]] = {}
    scope_stack: list[str] = []
    lines = vcd_text.splitlines()

    # Parse declarations.
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
        signal_type = match.group(1)
        if signal_type != "reg":
            continue
        width = int(match.group(2))
        var_id = match.group(3)
        raw = match.group(4).strip()

        if width <= 0:
            raise ValueError(f"invalid width {width} for {var_id}")

        scope_path = "/".join(scope_stack)
        if scope_path != scope and not scope_path.startswith(f"{scope}/"):
            continue

        scope_tail = _normalize_scope_tail(scope_path)

        name_raw, range_expr = _parse_var_name_and_range(raw)
        if not name_raw:
            raise ValueError(f"invalid symbol name in {stripped}")
        bit_indices = _parse_range_indices(range_expr, width)

        base_name = name_raw if not scope_tail else f"{scope_tail}/{name_raw}"
        if width == 1:
            full_names = (base_name,)
        else:
            if len(bit_indices) != width:
                raise ValueError(
                    f"{scope_path}/{name_raw}: expected {width} bits, got range mapping of {len(bit_indices)}"
                )
            full_names = tuple(f"{base_name}[{index}]" for index in bit_indices)

        if var_id in id_to_full_names:
            raise ValueError(f"duplicate declaration for id {var_id}")

        for bit_index, full_name in enumerate(full_names):
            existing = full_name_specs.get(full_name)
            if existing is not None:
                existing_id, existing_bit_index = existing
                raise ValueError(
                    f"duplicate declaration for {full_name} (first {existing_id}[{existing_bit_index}], now {var_id}[{bit_index}])"
                )
            full_name_specs[full_name] = (var_id, bit_index)

        id_to_full_names[var_id] = full_names

    if not id_to_full_names:
        raise ValueError("no target reg declarations found")

    # Replay value transitions and active sampling region.
    active_start: int | None = None
    active_end: int | None = None
    current_time = 0
    dumping = False
    full_name_state: dict[str, str | None] = {
        full_name: None for full_name in full_name_specs
    }
    pin_rows: dict[str, _RegisterBitActivity] = {}

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
                full_name: _RegisterBitActivity(
                    full_name=full_name,
                    last_value=value,
                    last_tick=current_time,
                    transition_count=0.0,
                    high_ticks=0,
                )
                for full_name, value in full_name_state.items()
            }
            continue
        if stripped == "$dumpoff":
            if not dumping:
                raise ValueError("found $dumpoff without active $dumpon")
            active_end = current_time
            dumping = False
            break
        if current_time is None:
            continue

        scalar_update = _SCALAR_UPDATE_RE.match(stripped)
        if scalar_update is not None:
            new_value = _sanitize_bit(scalar_update.group(1))
            var_id = scalar_update.group(2)
            if var_id not in id_to_full_names:
                continue
            target_full_names = id_to_full_names[var_id]
            if len(target_full_names) != 1:
                raise ValueError(f"scalar update received for vector declaration {var_id}")
            full_name = target_full_names[0]
            full_name_state[full_name] = new_value
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
            target_full_names = id_to_full_names[var_id]
            bit_values = _normalize_vector_update(bits, len(target_full_names))
            if len(bit_values) != len(target_full_names):
                raise ValueError(
                    f"vector update width mismatch for {var_id}: expected {len(target_full_names)}, got {len(bit_values)}"
                )
            for index, full_name in enumerate(target_full_names):
                new_value = bit_values[index]
                full_name_state[full_name] = new_value
                if not dumping:
                    continue
                row = pin_rows[full_name]
                if row.last_value is not None:
                    row.transition_count += _transition_delta(row.last_value, new_value)
                row.high_ticks += _value_to_tick_delta(row.last_value, current_time - row.last_tick)
                row.last_value = new_value
                row.last_tick = current_time
            continue

    if active_start is None or active_end is None:
        raise ValueError("missing active dumpon/dumpoff interval")
    if active_end <= active_start:
        raise ValueError("active_end_tick must be greater than active_start_tick")

    duration = active_end - active_start
    for row in pin_rows.values():
        if row.last_value is not None:
            row.high_ticks += _value_to_tick_delta(row.last_value, active_end - row.last_tick)

    register_bits: list[dict[str, Any]] = []
    for row in sorted(pin_rows.values(), key=lambda entry: entry.full_name):
        duty = row.high_ticks / duration
        density = row.transition_count / (duration * timescale_seconds)
        if not math.isfinite(row.transition_count) or row.transition_count < 0.0:
            raise ValueError(f"non-finite transition_count for {row.full_name}")
        if not math.isfinite(duty) or duty < 0.0 or duty > 1.0:
            raise ValueError(f"non-finite or out-of-range duty_cycle for {row.full_name}")
        if not math.isfinite(density) or density < 0.0:
            raise ValueError(f"non-finite or negative density_hz for {row.full_name}")
        register_bits.append(
            {
                "full_name": row.full_name,
                "density_hz": density,
                "duty_cycle": duty,
                "transition_count": row.transition_count,
                "source": "vcd",
            }
        )

    return {
        "version": 1,
        "model": "sequential_register_vcd_activity_v1",
        "scope": scope,
        "source_vcd": vcd_path.name,
        "source_vcd_sha256": actual_hash,
        "timescale_seconds": timescale_seconds,
        "active_start_tick": active_start,
        "active_end_tick": active_end,
        "register_bits": register_bits,
    }


def write_sequential_register_vcd_activity(
    vcd_path: Path, *, output_path: Path, **kwargs: Any
) -> JsonDict:
    payload = extract_sequential_register_vcd_activity(vcd_path, **kwargs)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    raise SystemExit("extractor is library-only")
