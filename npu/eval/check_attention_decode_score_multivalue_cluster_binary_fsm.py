#!/usr/bin/env python3
"""Validate exact-state decode-score multivalue-cluster rows for strict FSM PNR profiles."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ExactStateProfile:
    name: str
    tag_prefix: str
    flow_variant: str
    synth_args: str
    checker_id: str
    expected_signal_indices: dict[str, set[int]]
    config_path: str
    expected_fsm_encoding: str


PROFILES = {
    "v4_nofsm": ExactStateProfile(
        name="v4_nofsm",
        tag_prefix="decode_score_multivalue_cluster_v1_8ns_binary_fsm",
        flow_variant="decode_score_multivalue_cluster_v1_8ns_binary_fsm_v4_proxy_die_2500",
        synth_args="-nofsm",
        checker_id="attention_decode_score_multivalue_cluster_binary_fsm_v4",
        expected_signal_indices={
            "state_q": {0, 1, 2},
            "reducer.state": {0, 1, 2, 3},
        },
        config_path=(
            "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
            "config.json"
        ),
        expected_fsm_encoding="default",
    ),
    "targeted_binary": ExactStateProfile(
        name="targeted_binary",
        tag_prefix="decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm",
        flow_variant="decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500",
        synth_args="",
        checker_id="attention_decode_score_multivalue_cluster_targeted_binary_fsm_v1",
        expected_signal_indices={
            "state_q": {0, 1, 2},
            "reducer.state": {0, 1, 2, 3},
        },
        config_path=(
            "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
            "config_targeted_binary_fsm.json"
        ),
        expected_fsm_encoding="binary",
    ),
    "explicit_onehot": ExactStateProfile(
        name="explicit_onehot",
        tag_prefix="decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm",
        flow_variant="decode_score_multivalue_cluster_v1_8ns_explicit_onehot_fsm_v1_proxy_die_2500",
        synth_args="",
        checker_id="attention_decode_score_multivalue_cluster_explicit_onehot_fsm_v1",
        expected_signal_indices={
            "state_q": set(range(7)),
            "reducer.state": set(range(11)),
        },
        config_path=(
            "runs/designs/npu_blocks/attention_decode_score_multivalue_cluster_int8_m1x8_iterdiv/"
            "config_explicit_onehot_fsm.json"
        ),
        expected_fsm_encoding="explicit_onehot",
    ),
}
DEFAULT_PROFILE = "v4_nofsm"

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

_DeclarationEvidence = dict[str, dict[str, set[int] | set[tuple[int, int]]]]


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


def _empty_declaration_evidence() -> dict[str, set[int] | set[tuple[int, int]]]:
    return {"packed": set(), "bits": set()}


def _load_netlist_signal_evidence(path: Path) -> _DeclarationEvidence:
    evidence: _DeclarationEvidence = {}
    text = _strip_verilog_comments(path.read_text(encoding="utf-8"))
    for statement in text.split(";"):
        for match in _iter_declaration_items(statement):
            name = _normalize_verilog_identifier(match.group("name"))
            signal_data = evidence.setdefault(name, _empty_declaration_evidence())
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


def _candidate_signal_names(
    signal: str, evidence: _DeclarationEvidence
) -> list[tuple[str, str]]:
    if signal in evidence:
        return [(signal, "exact")]
    suffix = f".{signal}"
    return [
        (name, "qualified_suffix")
        for name in sorted(evidence)
        if name.endswith(suffix)
    ]


def _serialize_signal_candidate(
    *,
    candidate_name: str,
    match_type: str,
    signal_data: dict[str, set[int] | set[tuple[int, int]]],
    width_valid: bool,
    reasons: list[str],
) -> dict[str, object]:
    packed = cast(set[tuple[int, int]], signal_data["packed"])
    bits = cast(set[int], signal_data["bits"])
    return {
        "name": candidate_name,
        "match_type": match_type,
        "width_valid": width_valid,
        "reasons": reasons,
        "observed_packed_ranges": [
            {"msb": msb, "lsb": lsb} for msb, lsb in sorted(packed)
        ],
        "observed_bit_indices": sorted(bits),
    }


def _serialize_signal_evidence(
    *,
    expected_indices: set[int],
    selected_name: str | None = None,
    match_type: str | None = None,
    selected_data: dict[str, set[int] | set[tuple[int, int]]] | None = None,
    candidate_declarations: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    packed: set[tuple[int, int]] = set()
    bits: set[int] = set()
    if selected_data is not None:
        packed = cast(set[tuple[int, int]], selected_data["packed"])
        bits = cast(set[int], selected_data["bits"])
    return {
        "expected_bit_indices": sorted(expected_indices),
        "matched_declaration": selected_name,
        "match_type": match_type,
        "observed_packed_ranges": [
            {"msb": msb, "lsb": lsb} for msb, lsb in sorted(packed)
        ],
        "observed_bit_indices": sorted(bits),
        "candidate_declarations": list(candidate_declarations or []),
    }


def _empty_serialized_signal_evidence(
    expected_signal_indices: dict[str, set[int]]
) -> dict[str, dict[str, object]]:
    return {
        signal: _serialize_signal_evidence(expected_indices=indices)
        for signal, indices in expected_signal_indices.items()
    }


def _load_signal_indices_or_widths(
    *,
    signal: str,
    candidate_name: str,
    signal_data: dict[str, set[int] | set[tuple[int, int]]],
    expected_signal_indices: dict[str, set[int]],
) -> set[int]:
    expected_indices = expected_signal_indices[signal]
    packed = signal_data["packed"]
    bits = signal_data["bits"]
    if not isinstance(packed, set) or not isinstance(bits, set):
        raise TypeError(f"invalid internal evidence for {signal}")

    if packed and bits:
        raise ValueError(
            f"invalid declaration for {signal}: candidate {candidate_name} mixes packed and bit declarations"
        )
    if packed:
        if len(packed) != 1:
            raise ValueError(
                f"invalid declaration for {signal}: candidate {candidate_name} has multiple packed ranges present"
            )
        msb, lsb = next(iter(packed))
        expected_width = len(expected_indices)
        observed_width = abs(msb - lsb) + 1
        low = min(msb, lsb)
        high = max(msb, lsb)
        if observed_width != expected_width or low != 0 or high != expected_width - 1:
            raise ValueError(
                f"invalid width for {signal}: candidate {candidate_name} packed range [{msb}:{lsb}] is "
                f"incompatible with allowed indices {sorted(expected_indices)}"
            )
        return set(range(expected_width))

    if not bits:
        return set()

    out_of_range = set(bits) - expected_indices
    if out_of_range:
        raise ValueError(
            f"invalid width for {signal}: candidate {candidate_name} bit indices include out-of-range indices {sorted(out_of_range)}"
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


def _inspect_netlist_widths(
    path: Path, expected_signal_indices: dict[str, set[int]]
) -> tuple[dict[str, object], bool, list[str]]:
    empty = _empty_serialized_signal_evidence(expected_signal_indices)
    try:
        evidence = _load_netlist_signal_evidence(path)
    except (OSError, UnicodeError) as exc:
        return empty, False, [
            f"netlist_read_failed:{type(exc).__name__}"
        ]

    reasons: list[str] = []
    serialized: dict[str, object] = {}
    for signal in expected_signal_indices:
        candidates = _candidate_signal_names(signal, evidence)
        if not candidates:
            serialized[signal] = _serialize_signal_evidence(
                expected_indices=expected_signal_indices[signal]
            )
            reasons.append(f"missing declaration for {signal}")
            continue

        candidate_declarations: list[dict[str, object]] = []
        valid_candidates: list[tuple[str, str, dict[str, set[int] | set[tuple[int, int]]]]] = []
        candidate_reasons: list[str] = []
        for candidate_name, match_type in candidates:
            candidate_data = evidence[candidate_name]
            try:
                observed = _load_signal_indices_or_widths(
                    signal=signal,
                    candidate_name=candidate_name,
                    signal_data=candidate_data,
                    expected_signal_indices=expected_signal_indices,
                )
            except ValueError as exc:
                reason_list = [str(exc)]
                candidate_reasons.extend(reason_list)
                candidate_declarations.append(
                    _serialize_signal_candidate(
                        candidate_name=candidate_name,
                        match_type=match_type,
                        signal_data=candidate_data,
                        width_valid=False,
                        reasons=reason_list,
                    )
                )
                continue

            reason_list: list[str] = []
            if not observed:
                reason_list = [f"missing declaration for {signal}"]
            elif observed != expected_signal_indices[signal]:
                missing = sorted(expected_signal_indices[signal] - observed)
                if missing:
                    reason_list.append(
                        f"missing declaration for {signal}: candidate {candidate_name} missing indices {missing}"
                    )
            if reason_list:
                candidate_reasons.extend(reason_list)
            else:
                valid_candidates.append((candidate_name, match_type, candidate_data))
            candidate_declarations.append(
                _serialize_signal_candidate(
                    candidate_name=candidate_name,
                    match_type=match_type,
                    signal_data=candidate_data,
                    width_valid=not reason_list,
                    reasons=reason_list,
                )
            )

        if candidates[0][1] == "exact":
            candidate_name, match_type = candidates[0]
            candidate_data = evidence[candidate_name]
            serialized[signal] = _serialize_signal_evidence(
                expected_indices=expected_signal_indices[signal],
                selected_name=candidate_name,
                match_type=match_type,
                selected_data=candidate_data,
                candidate_declarations=candidate_declarations,
            )
            if not valid_candidates:
                reasons.extend(candidate_reasons or [f"missing declaration for {signal}"])
            continue

        if len(valid_candidates) == 1:
            candidate_name, match_type, candidate_data = valid_candidates[0]
            serialized[signal] = _serialize_signal_evidence(
                expected_indices=expected_signal_indices[signal],
                selected_name=candidate_name,
                match_type=match_type,
                selected_data=candidate_data,
                candidate_declarations=candidate_declarations,
            )
            continue

        serialized[signal] = _serialize_signal_evidence(
            expected_indices=expected_signal_indices[signal],
            candidate_declarations=candidate_declarations,
        )
        if len(valid_candidates) > 1:
            reasons.append(
                f"ambiguous qualified declaration for {signal}: multiple exact-width candidates "
                f"{sorted(name for name, _, _ in valid_candidates)}"
            )
        else:
            reasons.extend(candidate_reasons or [f"missing declaration for {signal}"])
    return serialized, not reasons, reasons


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_expected_config(profile: ExactStateProfile) -> tuple[Path, bool, str | None, str | None]:
    config_path = REPO_ROOT / profile.config_path
    if not config_path.is_file():
        return config_path, False, None, None
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return config_path, True, _sha256_file(config_path), None
    body = payload.get("attention_decode_score_multivalue_cluster")
    if not isinstance(body, dict):
        return config_path, True, _sha256_file(config_path), None
    return (
        config_path,
        True,
        _sha256_file(config_path),
        str(body.get("fsm_encoding", "default")).strip().lower(),
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
    row: dict[str, str], profile: ExactStateProfile
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
    profile: ExactStateProfile,
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
    signal_evidence: dict[str, object] = _empty_serialized_signal_evidence(
        profile.expected_signal_indices
    )
    width_valid = False
    promotion_reasons: list[str] = []
    netlist_sha256: str | None = None
    if netlist_exists:
        signal_evidence, width_valid, width_reasons = _inspect_netlist_widths(
            netlist_path, profile.expected_signal_indices
        )
        promotion_reasons.extend(width_reasons)
        netlist_sha256 = _sha256_file(netlist_path)
    else:
        promotion_reasons.append("missing exact netlist")

    config_path, config_exists, config_sha256, config_fsm_encoding = _load_expected_config(profile)
    if not config_exists:
        promotion_reasons.append("expected config is missing")
    elif config_fsm_encoding != profile.expected_fsm_encoding:
        promotion_reasons.append(
            f"config fsm_encoding {config_fsm_encoding or '<missing>'} does not match "
            f"{profile.expected_fsm_encoding}"
        )

    status = _to_str(row.get("status")).lower()
    if status != "ok":
        promotion_reasons.append(f"status is {status or 'missing'}, not ok")

    failure_stage = _portable_text(row.get("failure_stage"))
    failure_returncode = _optional_int(row.get("failure_returncode"))
    failure_signature = _portable_text(row.get("failure_signature"))
    if failure_stage or failure_returncode is not None or failure_signature:
        promotion_reasons.append("selected row carries failure-stage metadata")

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
        and config_exists
        and config_fsm_encoding == profile.expected_fsm_encoding
        and not failure_stage
        and failure_returncode is None
        and not failure_signature
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
            "failure_stage": failure_stage,
            "failure_returncode": failure_returncode,
            "failure_signature": failure_signature,
        },
        "expected_config_path": profile.config_path,
        "config_exists": config_exists,
        "config_sha256": config_sha256,
        "config_fsm_encoding": config_fsm_encoding,
        "expected_logical_netlist_path": logical_netlist_path,
        "netlist_exists": netlist_exists,
        "netlist_sha256": netlist_sha256,
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
        raise ValueError(f"unknown exact-state checker profile: {profile_name}") from exc
    diagnostic: dict[str, object] = {
        "version": 1,
        "checker": profile.checker_id,
        "profile": profile.name,
        "expected_flow_variant": profile.flow_variant,
        "expected_config_path": profile.config_path,
        "selected_exact_row": None,
        "config_exists": False,
        "config_sha256": None,
        "config_fsm_encoding": None,
        "expected_logical_netlist_path": None,
        "netlist_exists": False,
        "netlist_sha256": None,
        "signals": _empty_serialized_signal_evidence(profile.expected_signal_indices),
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
            profile=profile,
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
        "missing required 8ns exact-state decode-score multivalue-cluster row "
        f"(profile={profile.name}, status=ok, TAG={profile.tag_prefix}*, "
        f"FLOW_VARIANT={profile.flow_variant}, "
        "DIE_AREA=0 0 2500 2500, CORE_AREA=50 50 2450 2450, "
        f"SYNTH_ARGS={profile.synth_args or '<empty/default>'}, "
        "PLACE_DENSITY=0.4, SYNTH_HIERARCHICAL=1, SYNTH_MEMORY_MAX_BITS=65536, "
        f"critical_path_ns<=8, exact state widths={{{', '.join(f'{name}:{len(bits)}' for name, bits in profile.expected_signal_indices.items())}}})"
        + detail
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
