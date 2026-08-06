#!/usr/bin/env python3
"""Generate a deterministic c1/c2 integrated-service VCD and portable activity manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import probe_attention_decode_score_multivalue_integrated_service as probe  # noqa: E402
from npu.rtlgen.gen_attention_decode_score_multivalue_service import generate as generate_service  # noqa: E402

JsonDict = dict[str, Any]

_DEFAULT_CLOCK_PERIOD_NS = 10.0
_OUTPUT_VCD_NAME = "attention_decode_score_multivalue_service_activity.vcd"
_OUTPUT_MANIFEST_NAME = "attention_decode_score_multivalue_service_activity_manifest.json"
_OUTPUT_TOP_NAME = "top.v"
_OUTPUT_CONFIG_NAME = "config.json"
_OUTPUT_SERVICE_MANIFEST_NAME = "attention_decode_score_multivalue_service_manifest.json"
_OUTPUT_MACRO_MANIFEST_NAME = "macro_manifest.json"
_VALUE_MODEL_PATH = REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"
_C1_CASE = next(case for case in probe.DEFAULT_CASES if str(case["case_id"]) == "c1_p128_b4_rr")
_SUPPORTED_CASE_IDS = ("c1_p128_b4_rr", "c2_p128_b4_rr")
_SUPPORTED_CASES = {
    str(case["case_id"]): json.loads(json.dumps(case))
    for case in probe.DEFAULT_CASES
    if str(case["case_id"]) in _SUPPORTED_CASE_IDS
}
_SUPPORTED_CASES_BY_CLUSTER_COUNT = {
    int(case["cluster_count"]): dict(case) for case in _SUPPORTED_CASES.values()
}
_REQUIRED_SERVICE_FIELDS = {
    "cluster_count": int(_C1_CASE["cluster_count"]),
    "max_blocks": int(probe._workload_contract()["max_blocks"]),
    "packet_w": int(_C1_CASE["packet_w"]),
    "banks": int(_C1_CASE["banks"]),
    "req_queue_depth": int(_C1_CASE["req_queue_depth"]),
    "resp_queue_depth": int(_C1_CASE["resp_queue_depth"]),
    "bank_queue_depth": int(_C1_CASE["bank_queue_depth"]),
    "read_latency": int(_C1_CASE["read_latency"]),
    "arb_mode": str(_C1_CASE["arb_mode"]),
    "locality_burst_max": int(_C1_CASE["locality_burst_max"]),
    "score_scale_lanes_per_cycle": 1,
    "value_memory_backend": "macro_banked_4x16x64x32",
}


def _required_service_fields(case: JsonDict) -> JsonDict:
    return {
        "cluster_count": int(case["cluster_count"]),
        "max_blocks": int(probe._workload_contract()["max_blocks"]),
        "packet_w": int(case["packet_w"]),
        "banks": int(case["banks"]),
        "req_queue_depth": int(case["req_queue_depth"]),
        "resp_queue_depth": int(case["resp_queue_depth"]),
        "bank_queue_depth": int(case["bank_queue_depth"]),
        "read_latency": int(case["read_latency"]),
        "arb_mode": str(case["arb_mode"]),
        "locality_burst_max": int(case["locality_burst_max"]),
        "score_scale_lanes_per_cycle": 1,
        "value_memory_backend": "macro_banked_4x16x64x32",
    }


def _supported_case(*, case_id: str | None = None, cluster_count: int | None = None) -> JsonDict:
    if case_id is not None:
        case = _SUPPORTED_CASES.get(str(case_id).strip())
        if case is None:
            raise ValueError(f"unsupported case_id: {case_id}")
        return dict(case)
    if cluster_count is None:
        raise ValueError("case selection requires case_id or cluster_count")
    case = _SUPPORTED_CASES_BY_CLUSTER_COUNT.get(int(cluster_count))
    if case is None:
        raise ValueError(
            f"unsupported cluster_count {cluster_count}; expected one of {sorted(_SUPPORTED_CASES_BY_CLUSTER_COUNT)}"
        )
    return dict(case)


def _load(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_vcd(path: Path) -> None:
    tmp_path = path.with_suffix(path.suffix + ".normalized")
    in_date_block = False
    date_rewritten = False
    with path.open("r", encoding="utf-8") as src, tmp_path.open("w", encoding="utf-8") as dst:
        for line in src:
            if not date_rewritten and not in_date_block and line.strip() == "$date":
                dst.write("$date\n")
                dst.write("  deterministic_activity_capture_v1\n")
                in_date_block = True
                date_rewritten = True
                continue
            if in_date_block:
                if line.strip() == "$end":
                    dst.write("$end\n")
                    in_date_block = False
                continue
            dst.write(line)
    tmp_path.replace(path)


def _normalize_config_with_case(
    config: JsonDict,
    *,
    case_id: str | None = None,
) -> tuple[JsonDict, JsonDict]:
    top_name = str(config.get("top_name") or "").strip()
    if not top_name:
        raise ValueError("config requires non-empty top_name")
    body = config.get("attention_decode_score_multivalue_service")
    if not isinstance(body, dict):
        raise ValueError("config requires attention_decode_score_multivalue_service object")
    cluster_count = int(body.get("cluster_count", 0))
    case = _supported_case(case_id=case_id, cluster_count=cluster_count)
    normalized_body: JsonDict = {}
    for key, expected in _required_service_fields(case).items():
        value = body.get(key, expected)
        if value != expected:
            raise ValueError(f"attention_decode_score_multivalue_service.{key} must be {expected!r}")
        normalized_body[key] = expected
    return {"top_name": top_name, "attention_decode_score_multivalue_service": normalized_body}, case


def _normalize_config(config: JsonDict) -> JsonDict:
    normalized, _ = _normalize_config_with_case(config)
    return normalized


def _scaled_expected_counts(workload_contract: JsonDict, *, cluster_count: int) -> JsonDict:
    expected_counts = dict(probe._workload_expected_counts(workload_contract))
    for key in ("score_row_count", "request_count", "wide_response_count", "result_count"):
        expected_counts[key] = int(expected_counts[key]) * int(cluster_count)
    return expected_counts


def _sequential_memory_dumpvars(case: JsonDict) -> list[str]:
    cluster_count = int(case["cluster_count"])
    banks = int(case["banks"])
    req_queue_depth = int(case["req_queue_depth"])
    resp_queue_depth = int(case["resp_queue_depth"])
    bank_queue_depth = int(case["bank_queue_depth"])
    targets: list[str] = []
    for cluster in range(cluster_count):
        cluster_root = f"dut.gen_cluster[{cluster}].u_cluster"
        targets.extend(
            f"{cluster_root}.reducer.numerator_accum[{index}]"
            for index in range(int(probe._workload_contract()["value_dim"]))
        )
        targets.extend(f"{cluster_root}.reducer.block_weight[{index}]" for index in range(8))
        targets.extend(f"{cluster_root}.score_tile.accum[{index}]" for index in range(8))
        targets.extend(
            f"dut.u_router.gen_req_fifo[{cluster}].u_req_fifo.mem[{index}]"
            for index in range(req_queue_depth)
        )
        targets.extend(
            f"dut.u_router.gen_resp_fifo[{cluster}].u_resp_fifo.mem[{index}]"
            for index in range(resp_queue_depth)
        )
        for name in ("request_tag_q", "expected_tag_q", "expected_addr_q", "expected_slice_q", "expected_source_q"):
            targets.append(f"dut.{name}[{cluster}]")
    for bank in range(banks):
        for name in (
            "active_tag",
            "active_addr",
            "active_slice",
            "active_matrix",
            "active_fragment",
            "bank_latency",
        ):
            targets.append(f"dut.u_service.{name}[{bank}]")
        targets.extend(
            f"dut.u_service.gen_bank_fifo[{bank}].u_bank_fifo.mem[{index}]"
            for index in range(bank_queue_depth)
        )
    return targets


def _compile_and_run(*, sources: list[Path], timeout: int = 240) -> str:
    with tempfile.TemporaryDirectory(prefix="multivalue-service-activity-run-") as tmp_text:
        simv = Path(tmp_text) / "simv"
        compiled = subprocess.run(
            [probe._tool("iverilog"), "-g2012", "-s", "tb", "-o", str(simv), *[str(src) for src in sources]],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if compiled.returncode:
            raise RuntimeError(f"iverilog failed:\n{compiled.stderr}")
        run = subprocess.run([probe._tool("vvp"), str(simv)], capture_output=True, text=True, timeout=timeout)
        if run.returncode:
            raise RuntimeError(f"simulation failed:\n{run.stdout}\n{run.stderr}")
        return run.stdout


def _run_macro_integrated(
    config: JsonDict,
    out_dir: Path,
    *,
    case: JsonDict,
    clock_period_ns: float,
) -> JsonDict:
    values = probe._shared_value_matrices()
    with tempfile.TemporaryDirectory(prefix="multivalue-service-activity-") as tmp_text:
        tmp = Path(tmp_text)
        rtl_dir = tmp / "rtl"
        tb_path = tmp / "tb.sv"
        generate_service(json.loads(json.dumps(config)), rtl_dir)
        top_path = rtl_dir / "top.v"
        service_manifest_path = rtl_dir / _OUTPUT_SERVICE_MANIFEST_NAME
        macro_manifest_path = rtl_dir / _OUTPUT_MACRO_MANIFEST_NAME
        top_text = top_path.read_text(encoding="utf-8")
        if "fakeram45_2048x39" not in top_text:
            raise RuntimeError("generated RTL is missing fakeram45_2048x39 instances")
        if "fakeram45_64x32" not in top_text:
            raise RuntimeError("generated RTL is missing fakeram45_64x32 instances")
        tb_text = probe._integrated_testbench(
            top_name=str(config["top_name"]),
            cluster_count=int(case["cluster_count"]),
            values=values,
            vcd_path=str((out_dir / _OUTPUT_VCD_NAME).resolve()),
            vcd_dumpvars=["dut", *_sequential_memory_dumpvars(case)],
            clock_period_ns=clock_period_ns,
        )
        tb_path.write_text(tb_text, encoding="utf-8")
        stdout = _compile_and_run(sources=[top_path, tb_path, _VALUE_MODEL_PATH])
        generated_paths = {
            _OUTPUT_CONFIG_NAME: rtl_dir / "config.json",
            _OUTPUT_TOP_NAME: top_path,
            _OUTPUT_SERVICE_MANIFEST_NAME: service_manifest_path,
            _OUTPUT_MACRO_MANIFEST_NAME: macro_manifest_path,
        }
        for name, src in generated_paths.items():
            (out_dir / name).write_bytes(src.read_bytes())

    vcd_path = out_dir / _OUTPUT_VCD_NAME
    if not vcd_path.is_file():
        raise RuntimeError("simulation did not emit VCD")
    _normalize_vcd(vcd_path)

    shared_match = next(
        (match for line in stdout.splitlines() if (match := probe._INT_SHARED_RE.fullmatch(line.strip()))),
        None,
    )
    if shared_match is None:
        raise RuntimeError("integrated shared counter line missing")
    shared = {
        "completion_cycle": int(shared_match.group(1)),
        "protocol_error": bool(int(shared_match.group(2))),
        "router_injection_stall_cycles": int(shared_match.group(3)),
        "router_arbitration_contention_cycles": int(shared_match.group(4)),
        "router_response_block_cycles": int(shared_match.group(5)),
        "router_req_current_occupancy": int(shared_match.group(6)),
        "router_req_max_occupancy": int(shared_match.group(7)),
        "router_resp_current_occupancy": int(shared_match.group(8)),
        "router_resp_max_occupancy": int(shared_match.group(9)),
        "service_accepted_req_count": int(shared_match.group(10)),
        "service_emitted_resp_count": int(shared_match.group(11)),
        "service_bank_conflict_count": int(shared_match.group(12)),
        "service_response_block_cycles": int(shared_match.group(13)),
        "service_req_current_occupancy": int(shared_match.group(14)),
        "service_req_max_occupancy": int(shared_match.group(15)),
        "service_resp_current_occupancy": int(shared_match.group(16)),
        "service_resp_max_occupancy": int(shared_match.group(17)),
        "result_arbitration_contention_cycles": int(shared_match.group(18)),
        "result_egress_block_cycles": int(shared_match.group(19)),
        "result_back_to_back_fire_seen": bool(int(shared_match.group(20))),
    }
    return {
        "score_rows": probe._parse_score_lines(stdout, probe._INT_SCORE_RE),
        "request_rows": [
            {
                "cluster": int(match.group(1)),
                "tag": int(match.group(2)),
                "addr": int(match.group(3)),
                "slice": int(match.group(4)),
                "cycle": int(match.group(5)),
            }
            for line in stdout.splitlines()
            if (match := probe._INT_REQ_RE.fullmatch(line.strip()))
        ],
        "wide_rows": [
            {
                "cluster": int(match.group(1)),
                "source": int(match.group(2)),
                "tag": int(match.group(3)),
                "addr": int(match.group(4)),
                "slice": int(match.group(5)),
                "cycle": int(match.group(6)),
                "matrix_hex": match.group(7).lower(),
                "protocol_error": bool(int(match.group(8))),
            }
            for line in stdout.splitlines()
            if (match := probe._INT_WIDE_RE.fullmatch(line.strip()))
        ],
        "results": probe._parse_result_lines(stdout, probe._INT_RESULT_RE),
        "done_rows": {
            int(match.group(1)): {
                "cycle": int(match.group(2)),
                "accepted": int(match.group(3)),
                "completed": int(match.group(4)),
            }
            for line in stdout.splitlines()
            if (match := probe._INT_DONE_RE.fullmatch(line.strip()))
        },
        "counter_rows": {
            int(match.group(1)): {
                "input_stall_cycles": int(match.group(2)),
                "input_starvation_cycles": int(match.group(3)),
                "result_egress_block_cycles": int(match.group(4)),
                "request_count": int(match.group(5)),
                "wide_response_count": int(match.group(6)),
            }
            for line in stdout.splitlines()
            if (match := probe._INT_COUNTER_RE.fullmatch(line.strip()))
        },
        "shared": shared,
        "manifest": _load(out_dir / _OUTPUT_SERVICE_MANIFEST_NAME),
        "macro_manifest": _load(out_dir / _OUTPUT_MACRO_MANIFEST_NAME),
        "top_sha256": _sha256_file(out_dir / _OUTPUT_TOP_NAME),
        "clock_period_ns": clock_period_ns,
    }


def _assert_reference_equivalence(reference: JsonDict, candidate: JsonDict) -> None:
    comparable = (
        ("score rows", probe._canonical_scores(reference["score_rows"]), probe._canonical_scores(candidate["score_rows"])),
        ("results", probe._canonical_results(reference["results"]), probe._canonical_results(candidate["results"])),
        ("requests", probe._canonical_requests(reference["request_rows"]), probe._canonical_requests(candidate["request_rows"])),
        ("wide responses", probe._canonical_wide(reference["wide_rows"]), probe._canonical_wide(candidate["wide_rows"])),
        ("done rows", reference["done_rows"], candidate["done_rows"]),
        ("per-cluster counters", reference["counter_rows"], candidate["counter_rows"]),
        ("shared counters", reference["shared"], candidate["shared"]),
    )
    for label, expected, observed in comparable:
        if observed != expected:
            raise RuntimeError(f"macro-backed simulation diverged from reference {label}")


def _assert_portable_manifest_strings(payload: object) -> None:
    if isinstance(payload, dict):
        for value in payload.values():
            _assert_portable_manifest_strings(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _assert_portable_manifest_strings(value)
        return
    if not isinstance(payload, str):
        return
    if payload.startswith("/"):
        raise RuntimeError(f"portable manifest field contains absolute path: {payload}")
    evaluator_root = str((REPO_ROOT / "npu/eval").resolve())
    if evaluator_root in payload:
        raise RuntimeError("portable manifest field contains absolute evaluator path")


def generate_activity(
    config: JsonDict,
    out_dir: Path,
    *,
    clock_period_ns: float = _DEFAULT_CLOCK_PERIOD_NS,
    case_id: str | None = None,
) -> JsonDict:
    if clock_period_ns <= 0.0:
        raise ValueError("clock_period_ns must be > 0")
    normalized_config, case = _normalize_config_with_case(config, case_id=case_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    values = probe._shared_value_matrices()
    workload_contract = probe._workload_contract()
    expected_counts = _scaled_expected_counts(workload_contract, cluster_count=int(case["cluster_count"]))
    reference = probe._run_integrated(dict(case), values)
    macro = _run_macro_integrated(
        normalized_config,
        out_dir,
        case=case,
        clock_period_ns=clock_period_ns,
    )
    _assert_reference_equivalence(reference, macro)

    request_rows = probe._canonical_requests(macro["request_rows"])
    score_rows = probe._canonical_scores(macro["score_rows"])
    result_rows = probe._canonical_results(macro["results"])
    wide_rows = probe._canonical_wide(macro["wide_rows"])
    if len(score_rows) != int(expected_counts["score_row_count"]):
        raise RuntimeError("generated activity score rows do not match the workload contract")
    if len(request_rows) != int(expected_counts["request_count"]):
        raise RuntimeError("generated activity request rows do not match the workload contract")
    if len(wide_rows) != int(expected_counts["wide_response_count"]):
        raise RuntimeError("generated activity wide-response rows do not match the workload contract")
    if len(result_rows) != int(expected_counts["result_count"]):
        raise RuntimeError("generated activity result rows do not match the workload contract")
    request_banks = sorted({int(row["addr"]) % int(case["banks"]) for row in request_rows})
    preload_banks = sorted({int(entry["addr"]) % int(case["banks"]) for entry in probe._preload_entries(values)})
    inactive_banks = sorted(set(range(int(case["banks"]))) - set(request_banks))
    if "fakeram45_2048x39" not in (out_dir / _OUTPUT_TOP_NAME).read_text(encoding="utf-8"):
        raise RuntimeError("generated top.v no longer contains fakeram45_2048x39")
    if "fakeram45_64x32" not in (out_dir / _OUTPUT_TOP_NAME).read_text(encoding="utf-8"):
        raise RuntimeError("generated top.v no longer contains fakeram45_64x32")

    manifest = {
        "version": 1,
        "model": "attention_decode_score_multivalue_service_activity_v1",
        "generator": "npu/eval/generate_attention_decode_score_multivalue_service_activity.py",
        "case_id": str(case["case_id"]),
        "workload_contract": workload_contract,
        "artifacts": {
            "config_json": _OUTPUT_CONFIG_NAME,
            "top_verilog": _OUTPUT_TOP_NAME,
            "service_manifest_json": _OUTPUT_SERVICE_MANIFEST_NAME,
            "macro_manifest_json": _OUTPUT_MACRO_MANIFEST_NAME,
            "vcd": _OUTPUT_VCD_NAME,
        },
        "hashes": {
            "case_sha256": _hash_json(case),
            "config_sha256": _hash_json(normalized_config),
            "top_sha256": macro["top_sha256"],
            "vcd_sha256": _sha256_file(out_dir / _OUTPUT_VCD_NAME),
            "score_hash": _hash_json(score_rows),
            "final_hash": _hash_json(result_rows),
            "request_hash": _hash_json(request_rows),
            "wide_response_matrix_hash": _hash_json(wide_rows),
        },
        "clock_period_ns": clock_period_ns,
        "cycle_count": int(macro["shared"]["completion_cycle"]),
        "request_result_protocol_counters": {
            "request_count": len(request_rows),
            "wide_response_count": len(wide_rows),
            "result_count": len(result_rows),
            "shared": dict(macro["shared"]),
            "per_cluster": dict(macro["counter_rows"]),
        },
        "shared_result_egress": {
            "architecture": macro["manifest"]["shared_result_egress"],
            "documented_initiation_interval": macro["manifest"]["shared_result_egress_initiation_interval"],
            "stall_semantics": macro["manifest"]["shared_result_egress_stall_semantics"],
        },
        "value_bank_coverage": {
            "request_banks": request_banks,
            "preload_banks": preload_banks,
            "addressed_banks_over_trace": request_banks,
            "inactive_banks": inactive_banks,
            "inactive_reason": "three_block_reference_workload",
        },
        "compiled_behavioral_models": ["fakeram45_2048x39", "fakeram45_64x32"],
        "scope": {
            "exercised": [
                f"one deterministic {case['case_id']} integrated-service command",
                "macro-backed value-memory backend macro_banked_4x16x64x32",
                "bounded DUT VCD from reset release through command completion",
                "active workload contract is 3 blocks x 8 context tokens = 24 active context tokens at value_dim=128",
                (
                    "dynamic switching observed on addressed value-memory banks only under the exact "
                    "three-block reference workload"
                ),
            ],
            "remaining": [
                "no power audit, SAIF extraction, or post-route activity processing",
                (
                    "no non-c1/c2 cases, no alternate arbitration points, and no broader sequence "
                    "composition outside this exact workload"
                ),
                (
                    f"{case['case_id']} dynamic power from this exact workload may not cover every bank's "
                    "switching while leakage remains present in total composed PPA/power"
                ),
            ],
        },
    }
    if str(case["case_id"]) == "c1_p128_b4_rr" and manifest["value_bank_coverage"]["addressed_banks_over_trace"] != [0, 1, 2]:
        raise RuntimeError("exact c1 workload must address only banks 0, 1, and 2 over the trace")
    if str(case["case_id"]) == "c1_p128_b4_rr" and manifest["value_bank_coverage"]["inactive_banks"] != [3]:
        raise RuntimeError("exact c1 workload must leave bank3 inactive")
    _assert_portable_manifest_strings(manifest)
    (out_dir / _OUTPUT_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=_DEFAULT_CLOCK_PERIOD_NS)
    parser.add_argument("--case-id", type=str)
    args = parser.parse_args()
    generate_activity(
        _load(args.config),
        args.out_dir,
        clock_period_ns=args.clock_period_ns,
        case_id=args.case_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
