#!/usr/bin/env python3
"""Evaluate native-GQA checkpoint sensitivity to quantized KV cache feedback."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]
CandidateKey = tuple[int, str]

DEFAULT_PROMPTS = [
    "The capital of France is",
    "Two plus two equals",
    "In a transformer decoder, the key value cache stores",
    "The next word in the sequence Monday Tuesday Wednesday is",
    "If a system has a narrow top-token margin, quantization can",
    "A hardware accelerator with limited SRAM should",
    "The color of the clear daytime sky is",
    "When comparing approximate inference results, the safest metric is",
]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_exp_softmax(logits: list[float]) -> list[float]:
    if not logits:
        return []
    top = max(logits)
    exps = [math.exp(min(80.0, value - top)) for value in logits]
    denom = sum(exps)
    return [value / denom for value in exps]


def _topk(values: list[float], k: int) -> list[int]:
    return sorted(range(len(values)), key=lambda idx: values[idx], reverse=True)[: max(1, min(k, len(values)))]


def _cosine(a: list[float], b: list[float]) -> float:
    aa = math.sqrt(sum(value * value for value in a))
    bb = math.sqrt(sum(value * value for value in b))
    if aa == 0.0 or bb == 0.0:
        return 1.0 if aa == bb else 0.0
    return sum(x * y for x, y in zip(a, b)) / (aa * bb)


def _kl_divergence(reference: list[float], candidate: list[float]) -> float:
    eps = 1e-12
    return sum(p * math.log(max(eps, p) / max(eps, q)) for p, q in zip(reference, candidate))


def _summarize_rows(rows: list[JsonDict]) -> JsonDict:
    if not rows:
        return {
            "comparison_count": 0,
            "top1_match_rate": 0.0,
            "topk_contains_rate": 0.0,
            "mean_logit_cosine": 0.0,
            "mean_probability_kl": 0.0,
            "mean_reference_margin": 0.0,
            "min_reference_margin": 0.0,
            "max_abs_logit_delta_mean": 0.0,
            "max_abs_logit_delta_max": 0.0,
        }
    return {
        "comparison_count": len(rows),
        "top1_match_rate": _mean([_float(row.get("top1_match")) for row in rows]),
        "topk_contains_rate": _mean([_float(row.get("topk_contains")) for row in rows]),
        "mean_logit_cosine": _mean([_float(row.get("logit_cosine")) for row in rows]),
        "mean_probability_kl": _mean([_float(row.get("probability_kl")) for row in rows]),
        "mean_reference_margin": _mean([_float(row.get("reference_margin")) for row in rows]),
        "min_reference_margin": min(_float(row.get("reference_margin")) for row in rows),
        "max_abs_logit_delta_mean": _mean([_float(row.get("max_abs_logit_delta")) for row in rows]),
        "max_abs_logit_delta_max": max(_float(row.get("max_abs_logit_delta")) for row in rows),
    }


def _decision(candidate_summary: list[JsonDict], *, expected_gqa_group_size: int, actual_gqa_group_size: float) -> JsonDict:
    blockers: list[str] = []
    cautions: list[str] = []
    if expected_gqa_group_size > 0 and abs(actual_gqa_group_size - expected_gqa_group_size) > 1e-6:
        blockers.append(
            f"model_gqa_group_size {actual_gqa_group_size:g} does not match expected {expected_gqa_group_size}"
        )
    kv4_candidates = [row for row in candidate_summary if int(row.get("kv_bits", 0)) == 4]
    kv8_candidates = [row for row in candidate_summary if int(row.get("kv_bits", 0)) == 8]
    kv4 = max(kv4_candidates, key=_candidate_rank_key) if kv4_candidates else {}
    kv8 = max(kv8_candidates, key=_candidate_rank_key) if kv8_candidates else {}
    kv4_granularity = str(kv4.get("kv_granularity", "tensor") or "tensor")
    if kv8 and _float(kv8.get("top1_match_rate")) < 0.995:
        cautions.append("KV8 changed at least one top-1 decision; check model/runtime determinism before trusting KV4")
    if not kv4:
        blockers.append("KV4 candidate was not evaluated")
    elif _float(kv4.get("top1_match_rate")) < 0.98 or _float(kv4.get("topk_contains_rate")) < 0.995:
        blockers.append("Best KV4 candidate changed too many native-checkpoint next-token rankings")
    elif _float(kv4.get("mean_logit_cosine")) < 0.999:
        cautions.append("Best KV4 ranking mostly holds, but logit cosine is below the promotion caution line")
    if blockers:
        status = "hold_for_qat_or_safer_kv_format"
        next_step = "Run QAT/fine-tuning recovery or move the frontier back to KV8 for the native GQA checkpoint."
    elif kv4_granularity != "tensor":
        status = "kv4_granularity_recovery_promising"
        next_step = "Price the recovered KV4 scale granularity in hardware metadata/bandwidth before larger-model confirmation."
    else:
        status = "native_checkpoint_kv4_promising"
        next_step = "Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation."
    return {
        "status": status,
        "blockers": blockers,
        "cautions": cautions,
        "next_step": next_step,
        "selected_kv4_granularity": kv4_granularity if kv4 else "",
        "thresholds": {
            "kv4_top1_match_min": 0.98,
            "kv4_topk_contains_min": 0.995,
            "kv4_mean_logit_cosine_caution_below": 0.999,
            "kv8_top1_match_caution_below": 0.995,
        },
    }


def _load_prompts(path: str) -> list[str]:
    if not path:
        return list(DEFAULT_PROMPTS)
    prompts: list[str] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            if text.startswith("{"):
                doc = json.loads(text)
                text = str(doc.get("prompt") or doc.get("text") or "").strip()
            if text:
                prompts.append(text)
    if not prompts:
        raise SystemExit(f"no prompts loaded from {path}")
    return prompts


def _parse_bits(value: str) -> list[int]:
    bits = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not bits or any(bit < 2 for bit in bits):
        raise argparse.ArgumentTypeError("expected comma-separated KV bit widths >= 2")
    return bits


def _parse_granularities(value: str) -> list[str]:
    allowed = {"tensor", "kv_head", "token_vector"}
    granularities = [item.strip() for item in value.split(",") if item.strip()]
    if not granularities:
        raise argparse.ArgumentTypeError("expected comma-separated KV quantization granularities")
    invalid = sorted(set(granularities) - allowed)
    if invalid:
        raise argparse.ArgumentTypeError(f"unsupported KV quantization granularities: {', '.join(invalid)}")
    return granularities


def _candidate_rank_key(row: JsonDict) -> tuple[float, float, float, float]:
    return (
        _float(row.get("top1_match_rate")),
        _float(row.get("topk_contains_rate")),
        _float(row.get("mean_logit_cosine")),
        -_float(row.get("mean_probability_kl")),
    )


def _write_report_md(payload: JsonDict) -> str:
    lines = [
        "# Native GQA KV Quantization Quality",
        "",
        f"- model_id: `{payload['model']['model_id']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Model",
        "",
        f"- attention_heads: `{payload['model']['attention_heads']}`",
        f"- kv_heads: `{payload['model']['kv_heads']}`",
        f"- gqa_group_size: `{payload['model']['gqa_group_size']}`",
        "",
        "## Candidates",
        "",
        "| kv_bits | granularity | comparisons | top1 | topk | cosine | kl | min_margin | max_delta |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["candidate_summary"]:
        lines.append(
            "| {kv_bits} | {granularity} | {comparison_count} | {top1:.6f} | {topk:.6f} | {cosine:.6f} | {kl:.6f} | {margin:.6f} | {delta:.6f} |".format(
                kv_bits=row["kv_bits"],
                granularity=row.get("kv_granularity", "tensor"),
                comparison_count=row["comparison_count"],
                top1=row["top1_match_rate"],
                topk=row["topk_contains_rate"],
                cosine=row["mean_logit_cosine"],
                kl=row["mean_probability_kl"],
                margin=row["min_reference_margin"],
                delta=row["max_abs_logit_delta_max"],
            )
        )
    if payload["decision"].get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in payload["decision"]["blockers"])
    if payload["decision"].get("cautions"):
        lines.extend(["", "## Cautions", ""])
        lines.extend(f"- {item}" for item in payload["decision"]["cautions"])
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    return "\n".join(lines) + "\n"


def _run_model_eval(args: argparse.Namespace) -> JsonDict:
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "missing runtime dependency for model-native KV quality: install torch and transformers"
        ) from exc

    model_id = args.model_id or os.environ.get("RTLGEN_MODEL_NATIVE_GQA_MODEL_ID") or "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device.startswith("cuda") else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
    model.to(device)
    model.eval()

    config = model.config
    attention_heads = int(getattr(config, "num_attention_heads", 0) or getattr(config, "n_head", 0) or 0)
    kv_heads = int(getattr(config, "num_key_value_heads", 0) or attention_heads)
    if attention_heads <= 0 or kv_heads <= 0:
        raise SystemExit("model config does not expose attention and KV head counts")
    gqa_group_size = attention_heads / kv_heads
    prompts = _load_prompts(args.prompt_file)[: args.max_prompts]

    levels_by_bits = {bits: (1 << (bits - 1)) - 1 for bits in args.kv_bits_list}

    def quantize_tensor_slice(tensor: Any, bits: int) -> Any:
        if not torch.is_tensor(tensor):
            return tensor
        levels = levels_by_bits[bits]
        data = tensor.detach()
        max_abs = torch.amax(torch.abs(data)).item() if data.numel() else 0.0
        if max_abs == 0.0:
            return data.clone()
        scale = max_abs / float(levels)
        return torch.clamp(torch.round(data / scale), -levels, levels).to(data.dtype) * scale

    def quantize_tensor(tensor: Any, bits: int, granularity: str) -> Any:
        if not torch.is_tensor(tensor):
            return tensor
        data = tensor.detach()
        if granularity == "tensor" or data.ndim < 4:
            return quantize_tensor_slice(data, bits)
        if granularity == "kv_head":
            out = data.clone()
            for batch in range(data.shape[0]):
                for head in range(data.shape[1]):
                    out[batch, head, :, :] = quantize_tensor_slice(data[batch, head, :, :], bits)
            return out
        if granularity == "token_vector":
            out = data.clone()
            for batch in range(data.shape[0]):
                for head in range(data.shape[1]):
                    for token in range(data.shape[2]):
                        out[batch, head, token, :] = quantize_tensor_slice(data[batch, head, token, :], bits)
            return out
        raise SystemExit(f"unsupported KV quantization granularity: {granularity}")

    def quantize_past(past: Any, bits: int, granularity: str) -> Any:
        if past is None:
            return None
        if torch.is_tensor(past):
            return quantize_tensor(past, bits, granularity)
        if isinstance(past, tuple):
            return tuple(quantize_past(item, bits, granularity) for item in past)
        if isinstance(past, list):
            return [quantize_past(item, bits, granularity) for item in past]
        if hasattr(past, "to_legacy_cache"):
            legacy = past.to_legacy_cache()
            return tuple(quantize_past(item, bits, granularity) for item in legacy)
        return past

    candidate_keys: list[CandidateKey] = [
        (bits, granularity) for bits in args.kv_bits_list for granularity in args.kv_granularity_list
    ]
    rows_by_candidate: dict[CandidateKey, list[JsonDict]] = {key: [] for key in candidate_keys}
    prompt_records: list[JsonDict] = []
    with torch.no_grad():
        for prompt_index, prompt in enumerate(prompts):
            encoded = tokenizer(prompt, return_tensors="pt")
            input_ids = encoded["input_ids"].to(device)
            prefill = model(input_ids=input_ids, use_cache=True)
            fp_past = prefill.past_key_values
            ref_logits = prefill.logits[:, -1, :].float().cpu().reshape(-1).tolist()
            ref_top = _topk(ref_logits, max(2, args.topk))
            prompt_records.append(
                {
                    "prompt_index": prompt_index,
                    "prompt": prompt,
                    "prefill_reference_top1": ref_top[0],
                    "prefill_reference_margin": ref_logits[ref_top[0]] - ref_logits[ref_top[1]],
                }
            )
            candidate_past = {
                key: quantize_past(fp_past, key[0], key[1])
                for key in candidate_keys
            }
            next_input = torch.tensor([[ref_top[0]]], dtype=torch.long, device=device)
            for step in range(args.generation_steps):
                ref_out = model(input_ids=next_input, past_key_values=fp_past, use_cache=True)
                fp_past = ref_out.past_key_values
                ref_logits = ref_out.logits[:, -1, :].float().cpu().reshape(-1).tolist()
                ref_probs = _safe_exp_softmax(ref_logits)
                ref_order = _topk(ref_logits, max(2, args.topk))
                ref_next = ref_order[0]
                ref_margin = ref_logits[ref_order[0]] - ref_logits[ref_order[1]]
                for bits, granularity in candidate_keys:
                    key = (bits, granularity)
                    cand_out = model(input_ids=next_input, past_key_values=candidate_past[key], use_cache=True)
                    candidate_past[key] = quantize_past(cand_out.past_key_values, bits, granularity)
                    cand_logits = cand_out.logits[:, -1, :].float().cpu().reshape(-1).tolist()
                    cand_probs = _safe_exp_softmax(cand_logits)
                    cand_order = _topk(cand_logits, args.topk)
                    rows_by_candidate[key].append(
                        {
                            "prompt_index": prompt_index,
                            "step": step,
                            "kv_bits": bits,
                            "kv_granularity": granularity,
                            "reference_top1": ref_next,
                            "candidate_top1": cand_order[0],
                            "top1_match": 1.0 if cand_order[0] == ref_next else 0.0,
                            "topk_contains": 1.0 if ref_next in cand_order else 0.0,
                            "reference_margin": ref_margin,
                            "logit_cosine": _cosine(ref_logits, cand_logits),
                            "probability_kl": _kl_divergence(ref_probs, cand_probs),
                            "max_abs_logit_delta": max(abs(a - b) for a, b in zip(ref_logits, cand_logits)),
                        }
                    )
                next_input = torch.tensor([[ref_next]], dtype=torch.long, device=device)

    candidate_summary: list[JsonDict] = []
    for bits, granularity in candidate_keys:
        summary = _summarize_rows(rows_by_candidate[(bits, granularity)])
        summary["kv_bits"] = bits
        summary["kv_granularity"] = granularity
        candidate_summary.append(summary)
    best_kv4_candidates = [row for row in candidate_summary if int(row.get("kv_bits", 0)) == 4]
    best_kv4 = max(best_kv4_candidates, key=_candidate_rank_key) if best_kv4_candidates else None
    return {
        "version": 0.2,
        "model": {
            "model_id": model_id,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "gqa_group_size": gqa_group_size,
            "device": device,
            "dtype": str(dtype),
        },
        "prompt_count": len(prompts),
        "generation_steps": args.generation_steps,
        "topk": args.topk,
        "kv_granularity_list": args.kv_granularity_list,
        "prompt_records": prompt_records,
        "candidate_summary": candidate_summary,
        "best_kv4_candidate": best_kv4,
        "decision": _decision(
            candidate_summary,
            expected_gqa_group_size=args.expected_gqa_group_size,
            actual_gqa_group_size=gqa_group_size,
        ),
        "assumptions": [
            "This is post-training native-checkpoint KV cache quantization, not QAT.",
            "Teacher-forced reference tokens isolate KV-cache perturbation from divergent generated text.",
            "The evaluator must have Hugging Face model access; generated model weights are not committed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--max-prompts", type=int, default=8)
    parser.add_argument("--generation-steps", type=int, default=8)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--kv-bits-list", type=_parse_bits, default=[8, 4])
    parser.add_argument("--kv-granularity-list", type=_parse_granularities, default=["tensor"])
    parser.add_argument("--expected-gqa-group-size", type=int, default=8)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()
    if args.max_prompts <= 0 or args.generation_steps <= 0 or args.topk <= 0:
        raise SystemExit("max-prompts, generation-steps, and topk must be positive")
    payload = _run_model_eval(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = Path(args.out_md)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_write_report_md(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
