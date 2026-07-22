#!/usr/bin/env python3
"""Validate exact-state decode-score multivalue-cluster rows for binary-FSM PNR."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import cast

EXPECTED_CLOCK_PERIOD = 8
EXPECTED_TAG_PREFIX = "decode_score_multivalue_cluster_v1_8ns_binary_fsm"
EXPECTED_FLOW_VARIANT = "decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500"
EXPECTED_DIE_AREA = "0 0 2500 2500"
EXPECTED_CORE_AREA = "50 50 2450 2450"
EXPECTED_PLACE_DENSITY = "0.4"
EXPECTED_SYNTH_HIERARCHICAL = "1"
EXPECTED_SYNTH_MEMORY_MAX_BITS = "65536"
EXPECTED_SYNTH_ARGS = "-nofsm"
EXPECTED_RESULT_PATH_TOKEN = "attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv"
DEFAULT_SYNTH_RESULTS_DIR = Path("/orfs/flow/results")

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


def _netlist_has_required_signal_widths(path: Path) -> None:
    evidence = _load_netlist_signal_evidence(path)
    for signal in EXPECTED_SIGNAL_INDICES:
        expected_indices = EXPECTED_SIGNAL_INDICES[signal]
        try:
            observed = _load_signal_indices_or_widths(signal, evidence[signal])
        except ValueError as exc:
            raise ValueError(f"{exc} in {path}") from exc
        if not observed:
            raise ValueError(f"missing declaration for {signal} in {path}")
        if observed != expected_indices:
            missing = sorted(expected_indices - observed)
            if missing:
                raise ValueError(
                    f"missing declaration for {signal} in {path}: missing indices {missing}"
                )
            extra = sorted(observed - expected_indices)
            if extra:
                raise ValueError(
                    f"invalid width for {signal} in {path}: out-of-range indices {extra}"
                )


def _derive_synth_netlist_path(
    *,
    platform: str,
    design: str,
    flow_variant: str,
    synth_results_dir: Path,
) -> Path:
    platform_dir = synth_results_dir / platform / design
    return platform_dir / flow_variant / "1_synth.v"


def _parse_critical_path(row: dict[str, str]) -> float:
    value = float(row.get("critical_path_ns", "inf"))
    return float(value)


def _iter_metrics_rows(metrics_path: Path):
    with metrics_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row is not None:
                yield row


def _candidate_binary_fsm_row(
    row: dict[str, str],
    *,
    synth_results_dir: Path,
) -> tuple[bool, str | None]:
    try:
        params = _parse_params_json(_to_str(row.get("params_json", "")))
    except Exception:
        return False, None

    if _to_str(row.get("status")).lower() != "ok":
        return False, None
    if not _to_str(row.get("tag")).startswith(EXPECTED_TAG_PREFIX):
        return False, None
    if _to_str(params.get("FLOW_VARIANT")) != EXPECTED_FLOW_VARIANT:
        return False, None
    if _to_str(params.get("PLACE_DENSITY")) != EXPECTED_PLACE_DENSITY:
        return False, None
    if _to_str(params.get("SYNTH_HIERARCHICAL")) != EXPECTED_SYNTH_HIERARCHICAL:
        return False, None
    if _to_str(params.get("SYNTH_MEMORY_MAX_BITS")) != EXPECTED_SYNTH_MEMORY_MAX_BITS:
        return False, None
    if _to_str(params.get("SYNTH_ARGS")) != EXPECTED_SYNTH_ARGS:
        return False, None
    if _to_str(params.get("DIE_AREA")) != EXPECTED_DIE_AREA:
        return False, None
    if _to_str(params.get("CORE_AREA")) != EXPECTED_CORE_AREA:
        return False, None
    if _to_str(row.get("result_path")).find(EXPECTED_RESULT_PATH_TOKEN) == -1:
        return False, None

    try:
        if float(_to_str(params.get("CLOCK_PERIOD", ""))) != float(EXPECTED_CLOCK_PERIOD):
            return False, None
        if _parse_critical_path(row) > 8:
            return False, None
    except Exception:
        return False, None

    flow_variant = _to_str(params.get("FLOW_VARIANT"))
    if not flow_variant:
        return False, None

    netlist_path = _derive_synth_netlist_path(
        platform=_to_str(row.get("platform")),
        design=_to_str(row.get("design")),
        flow_variant=flow_variant,
        synth_results_dir=synth_results_dir,
    )
    if not netlist_path.exists():
        return False, f"missing exact netlist: {netlist_path}"

    try:
        _netlist_has_required_signal_widths(netlist_path)
    except ValueError as exc:
        return False, str(exc)
    return True, None


def validate_binary_fsm_metrics(
    *,
    metrics_path: Path,
    synth_results_dir: Path = DEFAULT_SYNTH_RESULTS_DIR,
) -> int:
    if not metrics_path.exists():
        raise ValueError(f"missing metrics.csv: {metrics_path}")

    last_candidate_error: str | None = None
    for row in _iter_metrics_rows(metrics_path):
        matches, candidate_error = _candidate_binary_fsm_row(
            row,
            synth_results_dir=synth_results_dir,
        )
        if candidate_error is not None:
            last_candidate_error = candidate_error
        if matches:
            return 0

    if last_candidate_error is not None:
        raise ValueError(
            "missing required 8ns exact-state binary-FSM decode-score multivalue-cluster row "
            "(status=ok, TAG=decode_score_multivalue_cluster_v1_8ns_binary_fsm*, "
            "FLOW_VARIANT=decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500, "
            "DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, SYNTH_ARGS=-nofsm, "
            "PLACE_DENSITY=0.4, SYNTH_HIERARCHICAL=1, SYNTH_MEMORY_MAX_BITS=65536, "
            "critical_path_ns<=8); details: " + last_candidate_error
        )

    raise ValueError(
        "missing required 8ns exact-state binary-FSM decode-score multivalue-cluster row "
        "(status=ok, TAG=decode_score_multivalue_cluster_v1_8ns_binary_fsm*, "
        "FLOW_VARIANT=decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500, "
        "DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, SYNTH_ARGS=-nofsm, "
        "PLACE_DENSITY=0.4, SYNTH_HIERARCHICAL=1, SYNTH_MEMORY_MAX_BITS=65536, "
        "critical_path_ns<=8)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument(
        "--synth-results-dir",
        type=Path,
        default=DEFAULT_SYNTH_RESULTS_DIR,
        help="Optional override for ORFS results root (default: /orfs/flow/results)",
    )
    args = parser.parse_args()
    validate_binary_fsm_metrics(
        metrics_path=args.metrics_path,
        synth_results_dir=args.synth_results_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
