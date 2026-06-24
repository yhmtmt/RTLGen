from __future__ import annotations

from pathlib import Path

import pytest

from npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention import (
    _decision,
    _iter_llama_attention_modules,
    _load_prompts,
    _quantize_symmetric_list,
    _rtl_quantized_softmax,
    _summarize_rows,
    _install_attention_wrappers,
    _restore_attention_wrappers,
)


def test_load_prompts_reads_default_and_json_lines(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompts.jsonl"
    prompt_path.write_text(
        "hello world\n"
        + '{"prompt": "json prompt"}\n'
        + '{"text": "json text"}\n'
        + "\n",
        encoding="utf-8",
    )
    prompts = _load_prompts(str(prompt_path))

    assert prompts == ["hello world", "json prompt", "json text"]


def test_summarize_rows_and_rtl_thresholds_for_shadow_decision() -> None:
    rows = [
        {
            "top1_match": 1.0,
            "topk_contains": 1.0,
            "logit_cosine": 0.9995,
            "probability_kl": 0.001,
            "reference_margin": 0.2,
            "max_abs_logit_delta": 0.03,
        },
        {
            "top1_match": 0.8,
            "topk_contains": 1.0,
            "logit_cosine": 0.9991,
            "probability_kl": 0.001,
            "reference_margin": 0.15,
            "max_abs_logit_delta": 0.02,
        },
    ]

    summary = _summarize_rows(rows)
    decision = _decision(summary, expected_gqa_group_size=8, actual_gqa_group_size=8.0)

    assert summary["comparison_count"] == 2
    assert summary["top1_match_rate"] == 0.9
    assert summary["topk_contains_rate"] == 1.0
    assert summary["min_reference_margin"] == 0.15
    assert decision["status"] == "mixed_int8_native_attention_shadow_hold"
    assert any("top-rank drift" in item for item in decision["blockers"])


def test_quantized_softmax_variants_and_ranges() -> None:
    logits = [1.0, 2.0, 0.5, 1.8]

    exact = _rtl_quantized_softmax(logits, score_bits=8, weight_bits=8, softmax_mode="rtl_exact")
    pow2sum = _rtl_quantized_softmax(logits, score_bits=8, weight_bits=8, softmax_mode="rtl_pow2sum")
    lut = _rtl_quantized_softmax(logits, score_bits=8, weight_bits=8, softmax_mode="rtl_recip_lut_q10")

    assert len(exact) == len(logits)
    assert len(pow2sum) == len(logits)
    assert len(lut) == len(logits)
    assert max(range(len(exact)), key=exact.__getitem__) == 1
    assert max(range(len(pow2sum)), key=pow2sum.__getitem__) == 1
    assert max(range(len(lut)), key=lut.__getitem__) == 1
    assert all(0.0 <= value <= 1.0 for value in exact)
    assert all(0.0 <= value <= 1.0 for value in pow2sum)
    assert all(0.0 <= value <= 1.0 for value in lut)


def test_quantize_symmetric_list() -> None:
    values = [0.0, -1.2, 2.4]
    q, scale = _quantize_symmetric_list(values, bits=8)

    assert q[1] < 0
    assert q[2] > 0
    assert scale > 0.0


def test_fake_attention_patch_quantizes_qkv_once_and_restores() -> None:
    torch = pytest.importorskip("torch")

    class _Linear(torch.nn.Module):
        def __init__(self, factor: float) -> None:
            super().__init__()
            self.factor = factor

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x * self.factor

    class _Attention(torch.nn.Module):
        def __init__(self, factor: float) -> None:
            super().__init__()
            self.q_proj = _Linear(factor)
            self.k_proj = _Linear(factor + 1.0)
            self.v_proj = _Linear(factor + 2.0)
            self.o_proj = _Linear(1.0)

    class _Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.model = torch.nn.Module()
            self.model.layer = _Attention(1.0)
            self.model.self_attn = _Attention(1.0)

    model = _Model()
    modules = list(_iter_llama_attention_modules(model))
    assert any(mod.__class__.__name__ == "_Attention" for mod in modules)

    patches = _install_attention_wrappers(model, q_bits=4, k_bits=4, v_bits=4)
    try:
        assert patches
        sample = torch.tensor([[-1.0, 0.2, 0.7]], dtype=torch.float32)
        q = model.model.layer.q_proj(sample)
        assert torch.allclose(torch.max(torch.abs(q)), torch.tensor(1.0))
    finally:
        _restore_attention_wrappers(patches)

    assert model.model.layer.q_proj.__class__.__name__ == "_Linear"
    assert model.model.layer.k_proj.__class__.__name__ == "_Linear"
    assert model.model.layer.v_proj.__class__.__name__ == "_Linear"
