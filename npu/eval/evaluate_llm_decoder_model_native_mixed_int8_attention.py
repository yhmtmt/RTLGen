#!/usr/bin/env python3
"""Evaluate native-checkpoint LLM logits with a patched mixed/int8 attention path."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import math
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CandidateConfig:
    candidate_id: str
    q_bits: int
    k_bits: int
    v_bits: int
    score_bits: int
    weight_bits: int
    softmax_mode: str


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


def _pwl_reciprocal_mode(mode: str) -> tuple[int, int]:
    prefix = "pwl_recip_lut_q"
    bucket_token = "_bucket"
    if not mode.startswith(prefix) or bucket_token not in mode:
        return 0, 0
    bits_text, bucket_text = mode[len(prefix) :].split(bucket_token, 1)
    try:
        reciprocal_bits = int(bits_text)
        bucket_shift = int(bucket_text)
    except ValueError as exc:
        raise ValueError(f"unsupported softmax mode: {mode}") from exc
    if reciprocal_bits <= 0 or reciprocal_bits > 24 or bucket_shift < 0 or bucket_shift > 12:
        raise ValueError(f"unsupported softmax mode: {mode}")
    return reciprocal_bits, bucket_shift


def _quantize_symmetric_list(values: list[float], bits: int) -> tuple[list[int], float]:
    if bits >= 24:
        return [int(round(value * 1024.0)) for value in values], 1.0 / 1024.0
    levels = (1 << (bits - 1)) - 1
    max_abs = max((abs(value) for value in values), default=0.0)
    if max_abs == 0.0:
        return [0 for _ in values], 1.0
    scale = max_abs / levels
    return [max(-levels, min(levels, int(round(value / scale)))) for value in values], scale


def _pwl_recip_lut_softmax(
    logits: list[float],
    *,
    score_bits: int,
    weight_bits: int,
    reciprocal_bits: int,
    bucket_shift: int,
    input_frac_bits: int = 8,
) -> list[float]:
    if score_bits < 2 or score_bits > 24:
        raise ValueError("PWL reciprocal softmax expects score_bits in [2, 24]")
    if weight_bits < 2 or weight_bits > 24:
        raise ValueError("PWL reciprocal softmax expects weight_bits in [2, 24]")
    if not logits:
        return []

    input_scale = 1 << input_frac_bits
    output_scale = (1 << weight_bits) - 1
    min_score = -(1 << (score_bits - 1))
    max_score = (1 << (score_bits - 1)) - 1
    q_logits = [
        max(min_score, min(max_score, int(round(value * input_scale))))
        for value in logits
    ]
    row_max = max(q_logits)

    x2 = 2 * input_scale
    x4 = 4 * input_scale
    x8 = 8 * input_scale
    y0 = output_scale
    y2 = int(math.exp(-2.0) * output_scale + 0.5)
    y4 = int(math.exp(-4.0) * output_scale + 0.5)
    y8 = int(math.exp(-8.0) * output_scale + 0.5)

    def pwl_weight(delta_in: int) -> int:
        clamped_delta = max(0, delta_in)
        if clamped_delta > x8:
            return 0
        if clamped_delta == x8:
            return y8
        if clamped_delta <= x2:
            seg_x0 = 0
            seg_width = x2
            y0_seg = y0
            y1_seg = y2
        elif clamped_delta <= x4:
            seg_x0 = x2
            seg_width = x4 - x2
            y0_seg = y2
            y1_seg = y4
        else:
            seg_x0 = x4
            seg_width = x8 - x4
            y0_seg = y4
            y1_seg = y8
        ydiff = y0_seg - y1_seg
        interp_num = ((clamped_delta - seg_x0) * ydiff) + (seg_width >> 1)
        return y0_seg - (interp_num // seg_width)

    exp_weights = [pwl_weight(row_max - value) for value in q_logits]
    sum_weight = sum(exp_weights)
    if sum_weight <= 0:
        return _safe_exp_softmax(logits)

    bucket_step = 1 << bucket_shift
    reciprocal_bucket = (sum_weight + bucket_step - 1) >> bucket_shift
    if reciprocal_bucket <= 0:
        reciprocal_q = 0
    else:
        bucket_denom = reciprocal_bucket << bucket_shift
        reciprocal_q = ((output_scale << reciprocal_bits) + (bucket_denom >> 1)) // bucket_denom

    lanes: list[int] = []
    for weight in exp_weights:
        lane_scaled = (weight * reciprocal_q) + (1 << (reciprocal_bits - 1))
        lane_scaled >>= reciprocal_bits
        lanes.append(min(output_scale, lane_scaled))
    return [lane / float(output_scale) for lane in lanes]


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


def _candidate_id_from_bits(*, q_bits: int, k_bits: int, v_bits: int, score_bits: int, weight_bits: int, softmax_mode: str) -> str:
    return f"q{q_bits}_k{k_bits}_v{v_bits}_s{score_bits}_w{weight_bits}_{softmax_mode}"


def _parse_candidate_token_pair(token: str) -> tuple[str, int]:
    token = token.strip()
    if len(token) < 2:
        raise ValueError(f"invalid candidate token: {token!r}")
    key = token[0].lower()
    return key, int(token[1:])


def _parse_candidate_spec(spec: Any) -> CandidateConfig:
    if isinstance(spec, dict):
        candidate_id = str(spec.get("candidate_id", "")).strip()
        q_bits = int(spec["q_bits"])
        k_bits = int(spec["k_bits"])
        v_bits = int(spec["v_bits"])
        score_bits = int(spec["score_bits"])
        weight_bits = int(spec["weight_bits"])
        softmax_mode = str(spec["softmax_mode"])
    else:
        spec = str(spec).strip()
        if not spec:
            raise ValueError("empty candidate spec")

        candidate_id = ""
        spec_body = spec
        if "{" in spec_body and spec_body.rstrip().endswith("}"):
            data = json.loads(spec_body)
            if not isinstance(data, dict):
                raise ValueError("candidate spec JSON object must be an object")
            candidate_id = str(data.get("candidate_id", "")).strip()
            q_bits = int(data["q_bits"])
            k_bits = int(data["k_bits"])
            v_bits = int(data["v_bits"])
            score_bits = int(data["score_bits"])
            weight_bits = int(data["weight_bits"])
            softmax_mode = str(data["softmax_mode"])
        else:
            if ":" in spec_body:
                candidate_id, spec_body = spec_body.split(":", 1)
                candidate_id = candidate_id.strip()
            parts = [item.strip() for item in spec_body.split(",") if item.strip()]
            if len(parts) != 6:
                raise ValueError(f"candidate spec {spec!r} must contain q,k,v,s,w and softmax mode")
            values: dict[str, int] = {}
            softmax_mode = ""
            for part in parts:
                if len(part) == 0:
                    continue
                if (
                    part in {"float_quantized", "float_exact", "rtl_exact", "rtl_pow2sum"}
                    or part.startswith("rtl_recip_lut_q")
                    or part.startswith("pwl_recip_lut_q")
                ):
                    if softmax_mode:
                        raise ValueError(f"candidate spec {spec!r} has duplicate softmax mode tokens")
                    softmax_mode = part
                    continue
                key, value = _parse_candidate_token_pair(part)
                if key in values:
                    raise ValueError(f"duplicate candidate token key {key!r} in {spec!r}")
                if key == "s":
                    score_bits = value
                    values[key] = value
                elif key in {"q", "k", "v", "w"}:
                    values[key] = value
                else:
                    if softmax_mode:
                        raise ValueError(f"candidate spec {spec!r} has an unknown token {part!r}")
                    softmax_mode = part
            if "q" not in values or "k" not in values or "v" not in values or "s" not in values or "w" not in values:
                raise ValueError(f"candidate spec {spec!r} must include q,k,v,s,w,mode")
            q_bits = values["q"]
            k_bits = values["k"]
            v_bits = values["v"]
            weight_bits = values["w"]
            if not softmax_mode:
                raise ValueError(f"candidate spec {spec!r} missing softmax mode token")

    q_bits = _parse_positive_int(str(q_bits))
    k_bits = _parse_positive_int(str(k_bits))
    v_bits = _parse_positive_int(str(v_bits))
    score_bits = _parse_positive_int(str(score_bits))
    weight_bits = _parse_positive_int(str(weight_bits))
    if not candidate_id:
        candidate_id = _candidate_id_from_bits(
            q_bits=q_bits,
            k_bits=k_bits,
            v_bits=v_bits,
            score_bits=score_bits,
            weight_bits=weight_bits,
            softmax_mode=softmax_mode,
        )

    return CandidateConfig(
        candidate_id=candidate_id,
        q_bits=q_bits,
        k_bits=k_bits,
        v_bits=v_bits,
        score_bits=score_bits,
        weight_bits=weight_bits,
        softmax_mode=_parse_softmax_mode(softmax_mode),
    )


def _parse_candidate_list(value: str) -> list[CandidateConfig]:
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("["):
        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise argparse.ArgumentTypeError("candidate-list expects a JSON array or semicolon-separated spec values")
        return [_parse_candidate_spec(item) for item in payload]
    # preserve support for old shell-style repeated lists that contain commas in each spec
    items = [item.strip() for item in raw.replace("\n", ";").split(";") if item.strip()]
    if len(items) == 1:
        return [_parse_candidate_spec(items[0])]
    return [_parse_candidate_spec(item) for item in items]


def _parse_softmax_mode(value: str) -> str:
    supported = {"float_quantized", "float_exact", "rtl_exact", "rtl_pow2sum", "rtl_recip_lut_q8"}
    if value.startswith("pwl_recip_lut_q"):
        reciprocal_bits, _ = _pwl_reciprocal_mode(value)
        if reciprocal_bits <= 0:
            raise argparse.ArgumentTypeError(f"unsupported softmax mode: {value}")
        return value
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


def _load_runtime_modules() -> tuple[Any, Any, Any]:
    try:
        torch_module = importlib.import_module("torch")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "missing runtime dependency for mixed/int8 attention quality: install torch and transformers"
        ) from exc

    try:
        transformers = importlib.import_module("transformers")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "missing runtime dependency for mixed/int8 attention quality: install torch and transformers"
        ) from exc

    auto_model_cls = getattr(transformers, "AutoModelForCausalLM", None)
    auto_tokenizer_cls = getattr(transformers, "AutoTokenizer", None)
    if auto_model_cls is None or auto_tokenizer_cls is None:
        raise SystemExit(
            "transformers package does not expose AutoModelForCausalLM/AutoTokenizer for mixed/int8 attention quality"
        )

    return torch_module, auto_model_cls, auto_tokenizer_cls


def _candidate_precision(candidate: CandidateConfig) -> JsonDict:
    return {
        "candidate_id": candidate.candidate_id,
        "q_bits": candidate.q_bits,
        "k_bits": candidate.k_bits,
        "v_bits": candidate.v_bits,
        "score_bits": candidate.score_bits,
        "weight_bits": candidate.weight_bits,
        "softmax_mode": candidate.softmax_mode,
    }


def _resolve_candidates(args: argparse.Namespace) -> list[CandidateConfig]:
    candidates: list[CandidateConfig] = []
    if args.candidate:
        candidates.extend(args.candidate)
    for chunk in args.candidate_list:
        if chunk:
            candidates.extend(chunk)

    if not candidates:
        candidates.append(
            CandidateConfig(
                candidate_id=_candidate_id_from_bits(
                    q_bits=args.q_bits,
                    k_bits=args.k_bits,
                    v_bits=args.v_bits,
                    score_bits=args.score_bits,
                    weight_bits=args.weight_bits,
                    softmax_mode=args.softmax_mode,
                ),
                q_bits=args.q_bits,
                k_bits=args.k_bits,
                v_bits=args.v_bits,
                score_bits=args.score_bits,
                weight_bits=args.weight_bits,
                softmax_mode=args.softmax_mode,
            )
        )
    return candidates


def _candidate_quality_rank(candidate_summary: JsonDict) -> tuple[int, float, float, float, float, float, float]:
    status = str(candidate_summary.get("decision_status", ""))
    if status == "mixed_int8_native_attention_shadow_pass":
        status_score = 3
    elif status == "mixed_int8_native_attention_shadow_caution":
        status_score = 2
    else:
        status_score = 1
    return (
        status_score,
        _float(candidate_summary.get("top1_match_rate"), 0.0),
        _float(candidate_summary.get("topk_contains_rate"), 0.0),
        _float(candidate_summary.get("mean_logit_cosine"), 0.0),
        -_float(candidate_summary.get("mean_probability_kl"), 0.0),
        -_float(candidate_summary.get("max_abs_logit_delta_mean"), 0.0),
        -_float(candidate_summary.get("comparison_count"), 0.0),
    )


def _pick_primary_summary(candidate_summaries: list[JsonDict], *, primary_candidate_id: str) -> JsonDict:
    if primary_candidate_id:
        for summary in candidate_summaries:
            if summary.get("candidate_id") == primary_candidate_id:
                return summary
        raise SystemExit(f"primary candidate id not found: {primary_candidate_id}")
    return candidate_summaries[0]


def _summarize_candidate_rows(*, candidate: CandidateConfig, rows: list[JsonDict], decision: JsonDict) -> JsonDict:
    summary = _summarize_rows(rows)
    summary.update(
        {
            "candidate_id": candidate.candidate_id,
            **_candidate_precision(candidate),
            "decision_status": decision["status"],
            "decision": decision,
        }
    )
    return summary


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
        if softmax_mode == "float_exact":
            out = _safe_exp_softmax(values)
            return torch.tensor(out, dtype=torch.float32, device=row.device).reshape(row.shape)
        if softmax_mode.startswith("pwl_recip_lut_q"):
            reciprocal_bits, bucket_shift = _pwl_reciprocal_mode(softmax_mode)
            out = _pwl_recip_lut_softmax(
                values,
                score_bits=score_bits,
                weight_bits=weight_bits,
                reciprocal_bits=reciprocal_bits,
                bucket_shift=bucket_shift,
            )
            return torch.tensor(out, dtype=row.dtype if row.dtype.is_floating_point else torch.float32, device=row.device).reshape(row.shape)
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


def _collect_reference_rows(
    reference_model: Any,
    tokenizer: Any,
    prompts: list[str],
    *,
    generation_steps: int,
    topk: int,
    device: str,
    torch_module: Any,
) -> tuple[list[JsonDict], list[JsonDict]]:
    rows: list[JsonDict] = []
    prompt_records: list[JsonDict] = []

    for prompt_index, prompt in enumerate(prompts):
        encoded = tokenizer(prompt, return_tensors="pt")
        prompt_input_ids = encoded["input_ids"].to(device)

        with torch_module.no_grad():
            ref_past, ref_logits, ref_probs, _ = _run_single_inference(
                reference_model,
                input_ids=prompt_input_ids,
                past_key_values=None,
                topk=max(2, topk),
            )

        ref_order = _topk(ref_logits, max(2, topk))
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
        rows.append(
            {
                "prompt_index": prompt_index,
                "step": 0,
                "input_ids": prompt_input_ids[0].tolist(),
                "reference_top1": ref_top1,
                "reference_margin": ref_margin,
                "reference_logits": ref_logits,
                "reference_probs": ref_probs,
            }
        )

        for step in range(1, generation_steps):
            input_token = ref_top1
            next_input = torch_module.tensor([[input_token]], dtype=torch_module.long, device=device)
            with torch_module.no_grad():
                ref_past, ref_logits, ref_probs, ref_order = _run_single_inference(
                    reference_model,
                    input_ids=next_input,
                    past_key_values=ref_past,
                    topk=max(2, topk),
                )
            ref_margin = ref_logits[ref_order[0]] - ref_logits[ref_order[1]] if len(ref_order) > 1 else 0.0
            ref_top1 = ref_order[0]
            rows.append(
                {
                    "prompt_index": prompt_index,
                    "step": step,
                    "input_ids": [input_token],
                    "reference_top1": ref_top1,
                    "reference_margin": ref_margin,
                    "reference_logits": ref_logits,
                    "reference_probs": ref_probs,
                }
            )

    return rows, prompt_records


def _evaluate_candidate_rows(
    reference_rows: list[JsonDict],
    candidate_model: Any,
    candidate: CandidateConfig,
    *,
    tokenizer: Any,
    device: str,
    torch_module: Any,
    topk: int,
) -> list[JsonDict]:
    del tokenizer
    softmax_ctx = _softmax_patch(
        score_bits=candidate.score_bits,
        weight_bits=candidate.weight_bits,
        softmax_mode=candidate.softmax_mode,
    )
    candidate_rows: list[JsonDict] = []
    past_by_prompt: dict[int, Any] = {}
    patches = _install_attention_wrappers(
        candidate_model,
        q_bits=candidate.q_bits,
        k_bits=candidate.k_bits,
        v_bits=candidate.v_bits,
    )

    try:
        for row in reference_rows:
            prompt_index = int(row["prompt_index"])
            step = int(row["step"])
            input_ids = row["input_ids"]
            past = None if step == 0 else past_by_prompt[prompt_index]

            with torch_module.no_grad():
                with softmax_ctx():
                    cand_past, cand_logits, cand_probs, cand_order = _run_single_inference(
                        candidate_model,
                        input_ids=torch_module.tensor([input_ids], dtype=torch_module.long, device=device),
                        past_key_values=past,
                        topk=topk,
                    )

            past_by_prompt[prompt_index] = cand_past
            ref_top1 = int(row["reference_top1"])
            cand_top1 = int(cand_order[0])
            reference_logits = [float(value) for value in row["reference_logits"]]
            reference_probs = [float(value) for value in row["reference_probs"]]
            candidate_rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "prompt_index": prompt_index,
                    "step": step,
                    "reference_top1": ref_top1,
                    "candidate_top1": cand_top1,
                    "top1_match": 1.0 if cand_top1 == ref_top1 else 0.0,
                    "topk_contains": 1.0 if ref_top1 in cand_order else 0.0,
                    "reference_margin": float(row["reference_margin"]),
                    "logit_cosine": _cosine(reference_logits, cand_logits),
                    "probability_kl": _kl_divergence(reference_probs, cand_probs),
                    "max_abs_logit_delta": max(abs(a - b) for a, b in zip(reference_logits, cand_logits)),
                }
            )

    finally:
        _restore_attention_wrappers(patches)

    return candidate_rows


def _run_model_eval(args: argparse.Namespace) -> JsonDict:
    torch, AutoModelForCausalLM, AutoTokenizer = _load_runtime_modules()

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

    candidates = _resolve_candidates(args)
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise SystemExit(f"candidate ids must be unique: {candidate_ids}")

    reference_rows, prompt_records = _collect_reference_rows(
        reference_model,
        tokenizer,
        prompts,
        generation_steps=args.generation_steps,
        topk=args.topk,
        device=device,
        torch_module=torch,
    )

    candidate_rows: list[JsonDict] = []
    candidate_summaries: list[JsonDict] = []
    for candidate in candidates:
        rows = _evaluate_candidate_rows(
            reference_rows,
            candidate_model,
            candidate,
            tokenizer=tokenizer,
            device=device,
            torch_module=torch,
            topk=args.topk,
        )
        decision = _decision(
            _summarize_rows(rows),
            expected_gqa_group_size=args.expected_gqa_group_size,
            actual_gqa_group_size=gqa_group_size,
        )
        candidate_summary = _summarize_candidate_rows(candidate=candidate, rows=rows, decision=decision)
        candidate_rows.extend(rows)
        candidate_summaries.append(candidate_summary)

    if not candidate_summaries:
        raise SystemExit("no candidates were configured")

    best_candidate = max(candidate_summaries, key=_candidate_quality_rank)
    primary_summary = _pick_primary_summary(candidate_summaries, primary_candidate_id=args.primary_candidate_id)

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
        "candidate_summaries": candidate_summaries,
        "candidate_summary": primary_summary,
        "best_candidate": {
            "candidate_id": best_candidate["candidate_id"],
            "decision_status": best_candidate["decision_status"],
            "top1_match_rate": best_candidate["top1_match_rate"],
            "topk_contains_rate": best_candidate["topk_contains_rate"],
            "mean_logit_cosine": best_candidate["mean_logit_cosine"],
            "mean_probability_kl": best_candidate["mean_probability_kl"],
        },
        "summary": primary_summary,
        "precision": _candidate_precision(next(candidate for candidate in candidates if candidate.candidate_id == primary_summary["candidate_id"])),
        "decision": primary_summary["decision"],
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
        f"- best_candidate: `{payload['best_candidate']['candidate_id']}` ({payload['best_candidate']['decision_status']})",
        f"- attention_head_count: `{payload['model']['attention_heads']}`",
        f"- kv_head_count: `{payload['model']['kv_heads']}`",
        f"- gqa_group_size: `{payload['model']['gqa_group_size']}`",
        f"- expected_gqa_group_size: `{payload['expected_gqa_group_size']}`",
        "",
        "## Candidates",
        "",
        "| candidate_id | q_bits | k_bits | v_bits | score_bits | weight_bits | softmax_mode | top1_match | topk_contains | mean_cosine | mean_kl | decision |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in payload['candidate_summaries']:
        lines.append(
            "| {candidate_id} | {q_bits} | {k_bits} | {v_bits} | {score_bits} | {weight_bits} | {softmax_mode} | "
            "{top1_match_rate:.6f} | {topk_contains_rate:.6f} | {mean_logit_cosine:.6f} | {mean_probability_kl:.6f} | "
            "{decision_status} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Primary Candidate Metrics",
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
    )

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
    parser.add_argument("--candidate", action="append", type=_parse_candidate_spec, default=[])
    parser.add_argument("--candidate-list", action="append", type=_parse_candidate_list, default=[])
    parser.add_argument("--primary-candidate-id", default="")
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
