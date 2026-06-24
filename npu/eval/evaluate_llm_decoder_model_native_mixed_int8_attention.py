#!/usr/bin/env python3
"""Evaluate native-checkpoint LLM logits with a patched mixed/int8 attention path."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

JsonDict = dict[str, Any]

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


def _safe_exp_softmax(logits: list[float]) -> list[float]:
    if not logits:
        return []
    top = max(logits)
    exps = [math.exp(min(80.0, value - top)) for value in logits]
    denom = sum(exps)
    return [value / denom for value in exps]


def _topk(values: list[float], k: int) -> list[int]:
    return sorted(range(len(values)), key=lambda idx: values[idx], reverse=True)[: max(1, min(k, len(values)))]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


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
            "max_abs_logit_delta_mean": 0.0,
            "max_abs_logit_delta_max": 0.0,
            "min_reference_margin": 0.0,
            "max_reference_margin": 0.0,
        }
    return {
        "comparison_count": len(rows),
        "top1_match_rate": _mean([_float(row.get("top1_match")) for row in rows]),
        "topk_contains_rate": _mean([_float(row.get("topk_contains")) for row in rows]),
        "mean_logit_cosine": _mean([_float(row.get("logit_cosine")) for row in rows]),
        "mean_probability_kl": _mean([_float(row.get("probability_kl")) for row in rows]),
        "max_abs_logit_delta_mean": _mean([_float(row.get("max_abs_logit_delta")) for row in rows]),
        "max_abs_logit_delta_max": max(_float(row.get("max_abs_logit_delta")) for row in rows),
        "min_reference_margin": min(_float(row.get("reference_margin")) for row in rows),
        "max_reference_margin": max(_float(row.get("reference_margin")) for row in rows),
    }


def _rtl_reciprocal_bits(mode: str) -> int:
    prefix = "rtl_recip_lut_q"
    if not mode.startswith(prefix):
        return 0
    try:
        bits = int(mode[len(prefix) :])
    except ValueError as exc:
        raise ValueError(f"unsupported softmax mode: {mode}") from exc
    if bits <= 0 or bits > 24:
        raise ValueError(f"unsupported softmax mode: {mode}")
    return bits


def _quantize_symmetric_list(values: list[float], bits: int) -> tuple[list[int], float]:
    if bits >= 24:
        return [int(round(value * 1024.0)) for value in values], 1.0 / 1024.0
    levels = (1 << (bits - 1)) - 1
    max_abs = max((abs(value) for value in values), default=0.0)
    if max_abs == 0.0:
        return [0 for _ in values], 1.0
    scale = max_abs / levels
    return [max(-levels, min(levels, int(round(value / scale)))) for value in values], scale


def _rtl_quantized_softmax(
    logits: list[float],
    *,
    score_bits: int,
    weight_bits: int,
    softmax_mode: str,
) -> list[float]:
    if softmax_mode not in {"rtl_exact", "rtl_pow2sum"}:
        reciprocal_bits = _rtl_reciprocal_bits(softmax_mode)
        if reciprocal_bits == 0:
            raise ValueError(f"unsupported softmax mode: {softmax_mode}")
    else:
        reciprocal_bits = 0

    if weight_bits > 8:
        raise ValueError("RTL softmax mode expects integer output weights (weight_bits <= 8)")

    q_logits, _ = _quantize_symmetric_list(logits, score_bits)
    if not q_logits:
        return []

    max_shift = 7
    output_scale = (1 << weight_bits) - 1
    row_max = max(q_logits)
    exp_weights: list[int] = []
    for value in q_logits:
        delta = row_max - value
        if delta < 0:
            delta = 0
        if delta > max_shift:
            delta = max_shift
        exp_weights.append(1 << (max_shift - delta))

    sum_weight = sum(exp_weights)
    if sum_weight <= 0:
        return _safe_exp_softmax(logits)

    if softmax_mode == "rtl_exact":
        lanes = [
            min(output_scale, ((weight * output_scale) + (sum_weight >> 1)) // sum_weight)
            for weight in exp_weights
        ]
    elif softmax_mode == "rtl_pow2sum":
        denom_shift = 0
        for index in range(32):
            if sum_weight > (1 << index):
                denom_shift = index + 1
        lanes = [min(output_scale, (weight * output_scale) >> denom_shift) for weight in exp_weights]
    else:
        reciprocal_q = ((output_scale << reciprocal_bits) + (sum_weight >> 1)) // sum_weight
        lanes = [
            min(output_scale, ((weight * reciprocal_q) + (1 << (reciprocal_bits - 1))) >> reciprocal_bits)
            for weight in exp_weights
        ]

    return [lane / float(output_scale) for lane in lanes]


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


def _parse_positive_int(value: str) -> int:
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("expected positive integer")
    return value


def _parse_softmax_mode(value: str) -> str:
    supported = {"float_quantized", "rtl_exact", "rtl_pow2sum", "rtl_recip_lut_q8"}
    if value.startswith("rtl_recip_lut_q"):
        bits = _rtl_reciprocal_bits(value)
        if bits <= 0:
            raise argparse.ArgumentTypeError(f"unsupported softmax mode: {value}")
        return value
    if value in supported:
        return value
    raise argparse.ArgumentTypeError(f"unsupported softmax mode: {value}")


def _resolve_torch_dtype(torch_module: Any, *, device: str, dtype_name: str) -> Any:
    if dtype_name == "auto":
        return torch_module.float16 if device.startswith("cuda") else torch_module.float32
    if dtype_name == "float32":
        return torch_module.float32
    if dtype_name == "float16":
        return torch_module.float16
    if dtype_name == "bfloat16":
        return torch_module.bfloat16
    raise SystemExit(f"unsupported dtype: {dtype_name}")


def _dtype_label(dtype: Any) -> str:
    text = str(dtype)
    return text.split(".", 1)[-1] if "." in text else text


def _decision(summary: JsonDict, *, expected_gqa_group_size: int, actual_gqa_group_size: float) -> JsonDict:
    blockers: list[str] = []
    cautions: list[str] = []

    if expected_gqa_group_size > 0 and abs(actual_gqa_group_size - expected_gqa_group_size) > 1e-6:
        blockers.append(
            f"model_gqa_group_size {actual_gqa_group_size:g} does not match expected {expected_gqa_group_size}"
        )

    top1_rate = _float(summary.get("top1_match_rate"))
    topk_rate = _float(summary.get("topk_contains_rate"))
    cosine = _float(summary.get("mean_logit_cosine"))
    kl = _float(summary.get("mean_probability_kl"))

    if top1_rate < 0.99 or topk_rate < 0.995:
        blockers.append("attention-shadow top-rank drift is too large for quality-gate promotion")
    if kl > 0.02:
        cautions.append("probability KL is above the mixed/int8 attention shadow comfort band")
    if cosine < 0.998:
        cautions.append("average logit cosine dropped below the mixed/int8 attention shadow caution line")

    if blockers:
        status = "mixed_int8_native_attention_shadow_hold"
        next_step = (
            "Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling."
        )
    elif cautions:
        status = "mixed_int8_native_attention_shadow_caution"
        next_step = (
            "This candidate is borderline for an attention-shadow gate; review per-probe misses before promotion and compare against a larger prompt set."
        )
    else:
        status = "mixed_int8_native_attention_shadow_pass"
        next_step = "Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling."

    return {
        "status": status,
        "blockers": blockers,
        "cautions": cautions,
        "next_step": next_step,
        "thresholds": {
            "top1_match_min": 0.99,
            "topk_contains_min": 0.995,
            "mean_probability_kl_caution_above": 0.02,
            "mean_logit_cosine_caution_below": 0.998,
            "attention_shadow_only": True,
            "not_full_perplexity_gate": True,
        },
    }


def _iter_llama_attention_modules(model: Any) -> Iterable[Any]:
    seen: set[int] = set()
    for module in model.modules():
        if id(module) in seen:
            continue
        if module.__class__.__name__ in {"LlamaAttention", "DecoderLayer"}:
            if hasattr(module, "self_attn"):
                attn = getattr(module, "self_attn")
                if all(hasattr(attn, key) for key in ("q_proj", "k_proj", "v_proj")):
                    seen.add(id(attn))
                    yield attn
        elif all(hasattr(module, key) for key in ("q_proj", "k_proj", "v_proj")):
            seen.add(id(module))
            yield module


def _install_attention_wrappers(
    model: Any,
    *,
    q_bits: int,
    k_bits: int,
    v_bits: int,
) -> list[tuple[Any, str, Any]]:
    import torch

    class _QuantizedProjection(torch.nn.Module):
        def __init__(self, original: Any, bits: int) -> None:
            super().__init__()
            self._original = original
            self._bits = bits

        def forward(self, x: Any) -> Any:
            out = self._original(x)
            flat = out.reshape(-1).detach().to(torch.float64)
            if flat.numel() == 0:
                return out
            max_abs = torch.max(torch.abs(flat)).item()
            if max_abs <= 0.0:
                return out
            levels = (1 << (self._bits - 1)) - 1
            scale = max_abs / levels
            q = torch.clamp(torch.round(out / scale), -levels, levels)
            return (q * scale).to(dtype=out.dtype)

    def quantize_projection(module: Any, bits: int) -> Any:
        return _QuantizedProjection(module, bits)

    patched: list[tuple[Any, str, Any]] = []
    for attn in _iter_llama_attention_modules(model):
        for name, bits in (("q_proj", q_bits), ("k_proj", k_bits), ("v_proj", v_bits)):
            proj = getattr(attn, name, None)
            if proj is None:
                continue
            if not isinstance(proj, torch.nn.Module):
                continue
            if getattr(proj, "_rtl_attention_quantized", False):
                continue
            wrapper = quantize_projection(proj, bits)
            wrapper._rtl_attention_quantized = True
            wrapper._rtl_attention_patch_info = {"bits": bits}
            patched.append((attn, name, proj))
            setattr(attn, name, wrapper)
    return patched


def _restore_attention_wrappers(patches: list[tuple[Any, str, Any]]) -> None:
    for module, name, original in reversed(patches):
        setattr(module, name, original)


def _module_has_linear_projection(module: Any, name: str) -> bool:
    value = getattr(module, name, None)
    if value is None:
        return False
    return callable(getattr(value, "forward", None))


def _supports_attention_quantization(model: Any) -> bool:
    return any(_module_has_linear_projection(module, "q_proj") for module in _iter_llama_attention_modules(model))


def _softmax_patch(score_bits: int, weight_bits: int, softmax_mode: str):
    import torch
    import torch.nn.functional as F

    def _row_softmax(row: torch.Tensor) -> torch.Tensor:
        if not row.numel():
            return row
        if row.dtype == torch.float16:
            row = row.float()
        values = row.reshape(-1).tolist()
        if softmax_mode == "float_quantized":
            q_values, scale = _quantize_symmetric_list(values, score_bits)
            out = [value * scale for value in q_values]
            out = _safe_exp_softmax(out)
            return torch.tensor(out, dtype=torch.float32, device=row.device).reshape(row.shape)
        out = _rtl_quantized_softmax(values, score_bits=score_bits, weight_bits=weight_bits, softmax_mode=softmax_mode)
        return torch.tensor(out, dtype=row.dtype if row.dtype.is_floating_point else torch.float32, device=row.device).reshape(row.shape)

    @contextlib.contextmanager
    def patcher():
        original_softmax = F.softmax
        original_torch_softmax = torch.softmax

        def patched_softmax(input_tensor: torch.Tensor, dim: int | None = None, dtype=None):
            if dim != -1 or dim is None or input_tensor.dim() < 2:
                return original_softmax(input_tensor, dim=dim, dtype=dtype)
            if input_tensor.size(-1) <= 1:
                return original_softmax(input_tensor, dim=dim, dtype=dtype)
            if input_tensor.dim() in {3, 4}:
                flat = input_tensor.reshape(-1, input_tensor.size(-1))
                rows = [_row_softmax(row) for row in flat]
                if rows:
                    stacked = torch.stack(rows, dim=0)
                    return stacked.reshape(input_tensor.shape)
            return original_softmax(input_tensor, dim=dim, dtype=dtype)

        F.softmax = patched_softmax  # type: ignore[assignment]
        torch.softmax = patched_softmax  # type: ignore[assignment]
        try:
            yield
        finally:
            F.softmax = original_softmax
            torch.softmax = original_torch_softmax

    return patcher


def _run_single_inference(
    model: Any,
    *,
    input_ids: Any,
    past_key_values: Any,
    topk: int,
    **kwargs: Any,
) -> tuple[Any, list[float], list[float], list[int]]:
    out = model(input_ids=input_ids, past_key_values=past_key_values, use_cache=True, **kwargs)
    logits = out.logits[:, -1, :].float().cpu().reshape(-1).tolist()
    probs = _safe_exp_softmax(logits)
    order = _topk(logits, topk)
    return out.past_key_values, logits, probs, order


def _run_model_eval(args: argparse.Namespace) -> JsonDict:
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("missing runtime dependency for mixed/int8 attention quality: install torch and transformers") from exc

    model_id = args.model_id or "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = _resolve_torch_dtype(torch, device=device, dtype_name=args.dtype)

    def load_model() -> Any:
        try:
            return AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=dtype,
                attn_implementation="eager",
            )
        except TypeError:
            return AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    reference_model = load_model().to(device)
    candidate_model = load_model().to(device)
    reference_model.eval()
    candidate_model.eval()

    if not _supports_attention_quantization(candidate_model):
        raise SystemExit("candidate model does not expose q/k/v projection modules for this mixed/int8 attention gate")

    config = reference_model.config
    attention_heads = int(getattr(config, "num_attention_heads", 0) or getattr(config, "n_head", 0) or 0)
    kv_heads = int(getattr(config, "num_key_value_heads", 0) or attention_heads)
    if attention_heads <= 0 or kv_heads <= 0:
        raise SystemExit("model config does not expose attention and KV head counts")
    if attention_heads % kv_heads != 0:
        raise SystemExit("model uses non-integer GQA group size; expected divisible attention and KV heads")
    gqa_group_size = attention_heads / kv_heads

    prompts = _load_prompts(args.prompt_file)[: args.max_prompts]
    if not prompts:
        raise SystemExit("no prompts to evaluate")

    patches = _install_attention_wrappers(
        candidate_model,
        q_bits=args.q_bits,
        k_bits=args.k_bits,
        v_bits=args.v_bits,
    )

    candidate_rows: list[JsonDict] = []
    prompt_records: list[JsonDict] = []
    try:
        softmax_ctx = _softmax_patch(
            score_bits=args.score_bits,
            weight_bits=args.weight_bits,
            softmax_mode=args.softmax_mode,
        )

        for prompt_index, prompt in enumerate(prompts):
            encoded = tokenizer(prompt, return_tensors="pt")
            input_ids = encoded["input_ids"].to(device)

            with torch.no_grad():
                ref_past, ref_logits, ref_probs, _ = _run_single_inference(
                    reference_model,
                    input_ids=input_ids,
                    past_key_values=None,
                    topk=max(2, args.topk),
                )
            ref_order = _topk(ref_logits, max(2, args.topk))
            ref_top1 = ref_order[0]
            ref_margin = ref_logits[ref_order[0]] - ref_logits[ref_order[1]] if len(ref_order) > 1 else 0.0
            prompt_records.append(
                {
                    "prompt_index": prompt_index,
                    "prompt": prompt,
                    "prefill_reference_top1": ref_top1,
                    "prefill_reference_margin": ref_margin,
                }
            )

            with torch.no_grad():
                with softmax_ctx():
                    cand_past, cand_logits, cand_probs, cand_order = _run_single_inference(
                        candidate_model,
                        input_ids=input_ids,
                        past_key_values=None,
                        topk=args.topk,
                    )
                next_id = ref_order[0]
                cand_top1 = cand_order[0]
                candidate_rows.append(
                    {
                        "prompt_index": prompt_index,
                        "step": 0,
                        "reference_top1": ref_top1,
                        "candidate_top1": cand_top1,
                        "top1_match": 1.0 if cand_top1 == ref_top1 else 0.0,
                        "topk_contains": 1.0 if ref_top1 in cand_order else 0.0,
                        "reference_margin": ref_margin,
                        "logit_cosine": _cosine(ref_logits, cand_logits),
                        "probability_kl": _kl_divergence(ref_probs, cand_probs),
                        "max_abs_logit_delta": max(abs(a - b) for a, b in zip(ref_logits, cand_logits)),
                    }
                )

            for step in range(1, args.generation_steps):
                next_input = torch.tensor([[next_id]], dtype=torch.long, device=device)
                with torch.no_grad():
                    ref_past, ref_logits, ref_probs, ref_order = _run_single_inference(
                        reference_model,
                        input_ids=next_input,
                        past_key_values=ref_past,
                        topk=max(2, args.topk),
                    )
                ref_margin = ref_logits[ref_order[0]] - ref_logits[ref_order[1]] if len(ref_order) > 1 else 0.0

                with torch.no_grad():
                    with softmax_ctx():
                        cand_past, cand_logits, cand_probs, cand_order = _run_single_inference(
                            candidate_model,
                            input_ids=next_input,
                            past_key_values=cand_past,
                            topk=args.topk,
                        )

                next_id = ref_order[0]
                candidate_rows.append(
                    {
                        "prompt_index": prompt_index,
                        "step": step,
                        "reference_top1": next_id,
                        "candidate_top1": cand_order[0],
                        "top1_match": 1.0 if cand_order[0] == next_id else 0.0,
                        "topk_contains": 1.0 if next_id in cand_order else 0.0,
                        "reference_margin": ref_margin,
                        "logit_cosine": _cosine(ref_logits, cand_logits),
                        "probability_kl": _kl_divergence(ref_probs, cand_probs),
                        "max_abs_logit_delta": max(abs(a - b) for a, b in zip(ref_logits, cand_logits)),
                    }
                )

    finally:
        _restore_attention_wrappers(patches)

    candidate_summary = _summarize_rows(candidate_rows)
    candidate_summary.update(
        {
            "q_bits": args.q_bits,
            "k_bits": args.k_bits,
            "v_bits": args.v_bits,
            "score_bits": args.score_bits,
            "weight_bits": args.weight_bits,
            "softmax_mode": args.softmax_mode,
            "comparison_count": len(candidate_rows),
        }
    )

    decision = _decision(
        candidate_summary,
        expected_gqa_group_size=args.expected_gqa_group_size,
        actual_gqa_group_size=gqa_group_size,
    )

    return {
        "version": 0.1,
        "quality_gate": "mixed_int8_attention_shadow",
        "model": {
            "model_id": model_id,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "gqa_group_size": gqa_group_size,
            "device": device,
            "dtype": _dtype_label(dtype),
            "requested_dtype": args.dtype,
        },
        "prompt_count": len(prompts),
        "generation_steps": args.generation_steps,
        "topk": args.topk,
        "expected_gqa_group_size": args.expected_gqa_group_size,
        "candidate_rows": candidate_rows,
        "prompt_records": prompt_records,
        "candidate_summary": candidate_summary,
        "summary": candidate_summary,
        "precision": {
            "q_bits": args.q_bits,
            "k_bits": args.k_bits,
            "v_bits": args.v_bits,
            "score_bits": args.score_bits,
            "weight_bits": args.weight_bits,
            "softmax_mode": args.softmax_mode,
        },
        "decision": decision,
        "assumptions": [
            "This is a native-checkpoint attention-shadow gate, not a full QAT or perplexity study.",
            "Teacher-forced next-token inputs isolate attention-path ranking drift from decoding-policy variance.",
            "Only Llama-style q/k/v projection + attention-softmax control is patched (QKV quantization + RTL-style int8 softmax).",
            "Q/K/V quantization and RTL softmax are applied in an in-process attention shadow, not reflected in training-time weights.",
        ],
    }


def _write_report_md(payload: JsonDict) -> str:
    lines = [
        "# Native-Checkpoint Mixed/Int8 Attention Shadow Quality",
        "",
        f"- model_id: `{payload['model']['model_id']}`",
        f"- decision: `{payload['decision']['status']}`",
        f"- attention_head_count: `{payload['model']['attention_heads']}`",
        f"- kv_head_count: `{payload['model']['kv_heads']}`",
        f"- gqa_group_size: `{payload['model']['gqa_group_size']}`",
        f"- expected_gqa_group_size: `{payload['expected_gqa_group_size']}`",
        "",
        "## Candidate",
        "",
        f"- q_bits: `{payload['candidate_summary']['q_bits']}`",
        f"- k_bits: `{payload['candidate_summary']['k_bits']}`",
        f"- v_bits: `{payload['candidate_summary']['v_bits']}`",
        f"- score_bits: `{payload['candidate_summary']['score_bits']}`",
        f"- weight_bits: `{payload['candidate_summary']['weight_bits']}`",
        f"- softmax_mode: `{payload['candidate_summary']['softmax_mode']}`",
        "",
        "## Candidate Metrics",
        "",
        "| comparisons | top1_match | topk_contains | mean_cosine | mean_kl | min_margin | max_delta |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        "| {comparison_count} | {top1_match_rate:.6f} | {topk_contains_rate:.6f} | {mean_logit_cosine:.6f} | {mean_probability_kl:.6f} | {min_reference_margin:.6f} | {max_abs_logit_delta_max:.6f} |".format(
            **payload["candidate_summary"]
        ),
        "",
        f"- decision: `{payload['decision']['status']}`",
        f"- next_step: {payload['decision']['next_step']}",
    ]

    if payload["decision"].get("blockers"):
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in payload["decision"]["blockers"])
    if payload["decision"].get("cautions"):
        lines.extend(["", "## Cautions", ""])
        lines.extend(f"- {item}" for item in payload["decision"]["cautions"])
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    lines.extend(["", "## Thresholds", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in payload["decision"]["thresholds"].items())
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--max-prompts", type=int, default=8)
    parser.add_argument("--generation-steps", type=int, default=8)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--expected-gqa-group-size", type=int, default=8)
    parser.add_argument("--q-bits", type=_parse_positive_int, default=8)
    parser.add_argument("--k-bits", type=_parse_positive_int, default=8)
    parser.add_argument("--v-bits", type=_parse_positive_int, default=8)
    parser.add_argument("--score-bits", type=_parse_positive_int, default=8)
    parser.add_argument("--weight-bits", type=_parse_positive_int, default=8)
    parser.add_argument("--softmax-mode", type=_parse_softmax_mode, default="rtl_recip_lut_q8")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--dtype", default="auto", choices=["auto", "float32", "float16", "bfloat16"])
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
