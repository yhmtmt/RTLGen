#!/usr/bin/env python3
"""Validate exact-state decode-score multivalue-cluster rows for binary-FSM PNR."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

EXPECTED_CLOCK_PERIOD = 8
EXPECTED_DIE_AREA = "0 0 2500 2500"
EXPECTED_CORE_AREA = "50 50 2450 2450"
EXPECTED_PLACE_DENSITY = "0.4"
EXPECTED_SYNTH_HIERARCHICAL = "1"
EXPECTED_SYNTH_MEMORY_MAX_BITS = "65536"
EXPECTED_PLATFORM = "nangate45"
EXPECTED_DESIGN = "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
EXPECTED_RESULT_PATH_TOKEN = EXPECTED_DESIGN
DEFAULT_SYNTH_RESULTS_DIR = Path("/orfs/flow/results")


@dataclass(frozen=True)
class BinaryFsmProfile:
    name: str
    tag_prefix: str
    flow_variant: str
    synth_args: str
    checker_id: str


PROFILES = {
    "v4_nofsm": BinaryFsmProfile(
        name="v4_nofsm",
        tag_prefix="decode_score_multivalue_cluster_v1_8ns_binary_fsm",
        flow_variant="decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4_proxy_die_2500",
        synth_args="-nofsm",
        checker_id="attention_decode_score_multivalue_cluster_binary_fsm_v4",
    ),
    "targeted_binary": BinaryFsmProfile(
        name="targeted_binary",
        tag_prefix="decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm",
        flow_variant=(
            "decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500"
        ),
        synth_args="",
        checker_id="attention_decode_score_multivalue_cluster_targeted_binary_fsm_v1",
    ),
}
DEFAULT_PROFILE = "v4_nofsm"
EXPECTED_TAG_PREFIX = PROFILES[DEFAULT_PROFILE].tag_prefix
EXPECTED_FLOW_VARIANT = PROFILES[DEFAULT_PROFILE].flow_variant
EXPECTED_SYNTH_ARGS = PROFILES[DEFAULT_PROFILE].synth_args

EXPECTED_SIGNAL_INDICES = {
    "state_q": {0, 1, 2},
    "reducer.state": {0, 1, 2, 3},
}

_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)
_DECL_KEYWORD_RE = re.compile(r"\b(?:wire|reg|logic|output|input|inout|tri)\b")
_DECL_ITEM_RE = re.compile(
    r"""
    ^
    (?:(?:\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\])\s*)?
    (?P<name>\\[^\s,;\[]+|[A-Za-z_][A-Za-z0-9_$./]*)
    (?:\[\s*(?P<bit>\d+)\s*\]\s*)?
    (?:$|,|\s)
    """,
    re.VERBOSE,
)
_ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])/(?:[^\s:]+/?)+")

_SignalEvidence = dict[str, dict[str, set[int] | set[tuple[int, int]]]]


def _parse_params_json(value: str) -> dict[str, object]:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty params_json")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            parsed = json.loads(text[1:-1].replace('""', '"'))
        else:
            raise
    if not isinstance(parsed, dict):
        raise ValueError("params_json did not decode to a JSON object")
    return parsed


def _to_str(value: object) -> str:
    return str(value or "").strip()


def _strip_verilog_comments(text: str) -> str:
    return _COMMENT_RE.sub("", text)


def _normalize_verilog_identifier(identifier: str) -> str:
    return identifier.replace("\\", "").replace("/", ".").replace("\t", " ").strip()


def _iter_declaration_items(statement: str):
    keyword_match = _DECL_KEYWORD_RE.search(statement)
    if not keyword_match:
        return

    body = statement[keyword_match.end() :].strip()
    if not body:
        return

    for item in body.split(","):
        if not item:
            continue
        match = _DECL_ITEM_RE.match(item.strip())
        if match is None:
            continue
        yield match


def _load_netlist_signal_evidence(path: Path) -> _SignalEvidence:
    evidence: _SignalEvidence = {
        signal: {"packed": set(), "bits": set()}
        for signal in EXPECTED_SIGNAL_INDICES
    }
    text = _strip_verilog_comments(path.read_text(encoding="utf-8"))
    for statement in text.split(";"):
        for match in _iter_declaration_items(statement):
            name = _normalize_verilog_identifier(match.group("name"))
            if name not in EXPECTED_SIGNAL_INDICES:
                continue
            signal_data = evidence[name]
            msb = match.group("msb")
            lsb = match.group("lsb")
            bit = match.group("bit")
            if msb is not None and lsb is not None:
                packed = cast(set[tuple[int, int]], signal_data["packed"])
                packed.add((int(msb), int(lsb)))
            elif bit is not None:
                bits = cast(set[int], signal_data["bits"])
                bits.add(int(bit))

    return evidence


def _load_signal_indices_or_widths(
    signal: str, signal_data: dict[str, set[int] | set[tuple[int, int]]]
) -> set[int]:
    expected_indices = EXPECTED_SIGNAL_INDICES[signal]
    packed = signal_data["packed"]
    bits = signal_data["bits"]
    if not isinstance(packed, set) or not isinstance(bits, set):
        raise TypeError(f"invalid internal evidence for {signal}")

    if packed:
        if len(packed) != 1:
            raise ValueError(
                f"invalid declaration for {signal}: multiple packed ranges present"
            )
        msb, lsb = next(iter(packed))
        expected_width = len(expected_indices)
        observed_width = abs(msb - lsb) + 1
        low = min(msb, lsb)
        high = max(msb, lsb)
        if observed_width != expected_width or low != 0 or high != expected_width - 1:
            raise ValueError(
                f"invalid width for {signal}: packed range [{msb}:{lsb}] is "
                f"incompatible with allowed indices {sorted(expected_indices)}"
            )
        return set(range(expected_width))

    if not bits:
        return set()

    out_of_range = set(bits) - expected_indices
    if out_of_range:
        raise ValueError(
            f"invalid width for {signal}: bit indices include out-of-range indices {sorted(out_of_range)}"
        )
    return set(bits)


def _portable_text(value: object) -> str | None:
    text = _to_str(value)
    if not text:
        return None
    return _ABSOLUTE_PATH_RE.sub("<absolute-path>", text)


def _optional_int(value: object) -> int | str | None:
    text = _to_str(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return _portable_text(text)


def _serialize_signal_evidence(evidence: _SignalEvidence) -> dict[str, object]:
    serialized: dict[str, object] = {}
    for signal, signal_data in evidence.items():
        packed = cast(set[tuple[int, int]], signal_data["packed"])
        bits = cast(set[int], signal_data["bits"])
        serialized[signal] = {
            "expected_bit_indices": sorted(EXPECTED_SIGNAL_INDICES[signal]),
            "observed_packed_ranges": [
                {"msb": msb, "lsb": lsb} for msb, lsb in sorted(packed)
            ],
            "observed_bit_indices": sorted(bits),
        }
    return serialized


def _inspect_netlist_widths(path: Path) -> tuple[dict[str, object], bool, list[str]]:
    empty = {
        signal: {"packed": set(), "bits": set()}
        for signal in EXPECTED_SIGNAL_INDICES
    }
    try:
        evidence = _load_netlist_signal_evidence(path)
    except (OSError, UnicodeError) as exc:
        return _serialize_signal_evidence(empty), False, [
            f"netlist_read_failed:{type(exc).__name__}"
        ]

    reasons: list[str] = []
    for signal in EXPECTED_SIGNAL_INDICES:
        try:
            observed = _load_signal_indices_or_widths(signal, evidence[signal])
        except ValueError as exc:
            reasons.append(str(exc))
            continue
        if not observed:
            reasons.append(f"missing declaration for {signal}")
        elif observed != EXPECTED_SIGNAL_INDICES[signal]:
            missing = sorted(EXPECTED_SIGNAL_INDICES[signal] - observed)
            extra = sorted(observed - EXPECTED_SIGNAL_INDICES[signal])
            if missing:
                reasons.append(f"missing declaration for {signal}: missing indices {missing}")
            if extra:
                reasons.append(f"invalid width for {signal}: out-of-range indices {extra}")
    return _serialize_signal_evidence(evidence), not reasons, reasons


def _derive_synth_netlist_path(
    *,
    platform: str,
    design: str,
    flow_variant: str,
    synth_results_dir: Path,
) -> Path:
    platform_dir = synth_results_dir / platform / design
    return platform_dir / flow_variant / "1_synth.v"


def _logical_synth_netlist_path(*, platform: str, design: str, flow_variant: str) -> str:
    return (Path("results") / platform / design / flow_variant / "1_synth.v").as_posix()


def _parse_critical_path(row: dict[str, str]) -> float:
    value = float(row.get("critical_path_ns", "inf"))
    if not math.isfinite(value):
        raise ValueError("critical path is not finite")
    return float(value)


def _iter_metrics_rows(metrics_path: Path):
    with metrics_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row is not None:
                yield row


def _exact_binary_fsm_identity(
    row: dict[str, str], profile: BinaryFsmProfile
) -> dict[str, object] | None:
    try:
        params = _parse_params_json(_to_str(row.get("params_json", "")))
    except Exception:
        return None

    if not _to_str(row.get("tag")).startswith(profile.tag_prefix):
        return None
    if _to_str(params.get("FLOW_VARIANT")) != profile.flow_variant:
        return None
    if _to_str(params.get("PLACE_DENSITY")) != EXPECTED_PLACE_DENSITY:
        return None
    if _to_str(params.get("SYNTH_HIERARCHICAL")) != EXPECTED_SYNTH_HIERARCHICAL:
        return None
    if _to_str(params.get("SYNTH_MEMORY_MAX_BITS")) != EXPECTED_SYNTH_MEMORY_MAX_BITS:
        return None
    if _to_str(params.get("SYNTH_ARGS")) != profile.synth_args:
        return None
    if _to_str(params.get("DIE_AREA")) != EXPECTED_DIE_AREA:
        return None
    if _to_str(params.get("CORE_AREA")) != EXPECTED_CORE_AREA:
        return None
    if _to_str(row.get("result_path")).find(EXPECTED_RESULT_PATH_TOKEN) == -1:
        return None
    if _to_str(row.get("platform")) != EXPECTED_PLATFORM:
        return None
    if _to_str(row.get("design")) != EXPECTED_DESIGN:
        return None

    try:
        if float(_to_str(params.get("CLOCK_PERIOD", ""))) != float(EXPECTED_CLOCK_PERIOD):
            return None
    except Exception:
        return None

    return params


def _row_diagnostic(
    row: dict[str, str],
    *,
    params: dict[str, object],
    synth_results_dir: Path,
) -> dict[str, object]:
    platform = _to_str(row.get("platform"))
    design = _to_str(row.get("design"))
    flow_variant = _to_str(params.get("FLOW_VARIANT"))
    netlist_path = _derive_synth_netlist_path(
        platform=platform,
        design=design,
        flow_variant=flow_variant,
        synth_results_dir=synth_results_dir,
    )
    logical_netlist_path = _logical_synth_netlist_path(
        platform=platform,
        design=design,
        flow_variant=flow_variant,
    )
    netlist_exists = netlist_path.is_file()
    signal_evidence: dict[str, object] = {
        signal: {
            "expected_bit_indices": sorted(indices),
            "observed_packed_ranges": [],
            "observed_bit_indices": [],
        }
        for signal, indices in EXPECTED_SIGNAL_INDICES.items()
    }
    width_valid = False
    promotion_reasons: list[str] = []
    if netlist_exists:
        signal_evidence, width_valid, width_reasons = _inspect_netlist_widths(netlist_path)
        promotion_reasons.extend(width_reasons)
    else:
        promotion_reasons.append("missing exact netlist")

    status = _to_str(row.get("status")).lower()
    if status != "ok":
        promotion_reasons.append(f"status is {status or 'missing'}, not ok")

    critical_path_ns: float | None = None
    try:
        critical_path_ns = _parse_critical_path(row)
        if critical_path_ns > EXPECTED_CLOCK_PERIOD:
            promotion_reasons.append(
                f"critical path {critical_path_ns:g}ns exceeds {EXPECTED_CLOCK_PERIOD}ns"
            )
    except (TypeError, ValueError):
        promotion_reasons.append("critical path is missing or invalid")

    promotion_valid = (
        status == "ok"
        and critical_path_ns is not None
        and critical_path_ns <= EXPECTED_CLOCK_PERIOD
        and netlist_exists
        and width_valid
    )
    return {
        "selected_exact_row": {
            "design": design,
            "platform": platform,
            "config_hash": _to_str(row.get("config_hash")) or None,
            "param_hash": _to_str(row.get("param_hash")) or None,
            "tag": _to_str(row.get("tag")),
            "status": status or None,
            "flow_variant": flow_variant,
            "clock_period_ns": float(EXPECTED_CLOCK_PERIOD),
            "critical_path_ns": critical_path_ns,
            "die_area": _to_str(params.get("DIE_AREA")),
            "core_area": _to_str(params.get("CORE_AREA")),
            "place_density": _to_str(params.get("PLACE_DENSITY")),
            "synth_hierarchical": _to_str(params.get("SYNTH_HIERARCHICAL")),
            "synth_memory_max_bits": _to_str(params.get("SYNTH_MEMORY_MAX_BITS")),
            "synth_args": _to_str(params.get("SYNTH_ARGS")),
            "failure_stage": _portable_text(row.get("failure_stage")),
            "failure_returncode": _optional_int(row.get("failure_returncode")),
            "failure_signature": _portable_text(row.get("failure_signature")),
        },
        "expected_logical_netlist_path": logical_netlist_path,
        "netlist_exists": netlist_exists,
        "signals": signal_evidence,
        "width_valid": width_valid,
        "promotion_valid": promotion_valid,
        "promotion_reasons": promotion_reasons,
    }


def _write_diagnostic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_binary_fsm_metrics(
    *,
    metrics_path: Path,
    diagnostic_out: Path,
    profile_name: str = DEFAULT_PROFILE,
    synth_results_dir: Path = DEFAULT_SYNTH_RESULTS_DIR,
) -> int:
    try:
        profile = PROFILES[profile_name]
    except KeyError as exc:
        raise ValueError(f"unknown binary-FSM checker profile: {profile_name}") from exc
    diagnostic: dict[str, object] = {
        "version": 1,
        "checker": profile.checker_id,
        "profile": profile.name,
        "expected_flow_variant": profile.flow_variant,
        "selected_exact_row": None,
        "expected_logical_netlist_path": None,
        "netlist_exists": False,
        "signals": {
            signal: {
                "expected_bit_indices": sorted(indices),
                "observed_packed_ranges": [],
                "observed_bit_indices": [],
            }
            for signal, indices in EXPECTED_SIGNAL_INDICES.items()
        },
        "width_valid": False,
        "promotion_valid": False,
        "promotion_reasons": [],
    }
    if not metrics_path.exists():
        diagnostic["promotion_reasons"] = ["missing metrics.csv"]
        _write_diagnostic(diagnostic_out, diagnostic)
        raise ValueError(f"missing metrics.csv: {metrics_path}")

    exact_rows: list[tuple[dict[str, str], dict[str, object]]] = []
    for row in _iter_metrics_rows(metrics_path):
        params = _exact_binary_fsm_identity(row, profile)
        if params is not None:
            exact_rows.append((row, params))

    row_diagnostics = [
        _row_diagnostic(
            row,
            params=params,
            synth_results_dir=synth_results_dir,
        )
        for row, params in exact_rows
    ]
    promoted = [item for item in row_diagnostics if item["promotion_valid"]]
    if promoted:
        diagnostic.update(promoted[-1])
        _write_diagnostic(diagnostic_out, diagnostic)
        return 0

    if row_diagnostics:
        diagnostic.update(row_diagnostics[-1])
    else:
        diagnostic["promotion_reasons"] = [f"no exact {profile.name} identity row"]
    _write_diagnostic(diagnostic_out, diagnostic)

    reasons = cast(list[str], diagnostic["promotion_reasons"])
    detail = "; ".join(reasons)
    if detail:
        detail = "; details: " + detail
    raise ValueError(
        "missing required 8ns exact-state binary-FSM decode-score multivalue-cluster row "
        f"(profile={profile.name}, status=ok, TAG={profile.tag_prefix}*, "
        f"FLOW_VARIANT={profile.flow_variant}, "
        "DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, "
        f"SYNTH_ARGS={profile.synth_args or '<empty/default>'}, "
        "PLACE_DENSITY=0.4, SYNTH_HIERARCHICAL=1, SYNTH_MEMORY_MAX_BITS=65536, "
        "critical_path_ns<=8, exact 3/4-bit state widths)" + detail
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument("--diagnostic-out", type=Path, required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), default=DEFAULT_PROFILE)
    parser.add_argument(
        "--synth-results-dir",
        type=Path,
        default=DEFAULT_SYNTH_RESULTS_DIR,
        help="Optional override for ORFS results root (default: /orfs/flow/results)",
    )
    args = parser.parse_args()
    validate_binary_fsm_metrics(
        metrics_path=args.metrics_path,
        diagnostic_out=args.diagnostic_out,
        profile_name=args.profile,
        synth_results_dir=args.synth_results_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
