from __future__ import annotations

import argparse
import types
from pathlib import Path

import pytest

from npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention import (
    _collect_reference_rows,
    _decision,
    _iter_llama_attention_modules,
    _load_runtime_modules,
    _load_prompts,
    _parse_candidate_list,
    _parse_candidate_spec,
    _run_model_eval,
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
    lut_q16_w16 = _rtl_quantized_softmax(
        logits,
        score_bits=32,
        weight_bits=16,
        softmax_mode="rtl_recip_lut_q16",
    )

    assert len(exact) == len(logits)
    assert len(pow2sum) == len(logits)
    assert len(lut) == len(logits)
    assert len(lut_q16_w16) == len(logits)
    assert max(range(len(exact)), key=exact.__getitem__) == 1
    assert max(range(len(pow2sum)), key=pow2sum.__getitem__) == 1
    assert max(range(len(lut)), key=lut.__getitem__) == 1
    assert max(range(len(lut_q16_w16)), key=lut_q16_w16.__getitem__) == 1
    assert all(0.0 <= value <= 1.0 for value in exact)
    assert all(0.0 <= value <= 1.0 for value in pow2sum)
    assert all(0.0 <= value <= 1.0 for value in lut)
    assert all(0.0 <= value <= 1.0 for value in lut_q16_w16)


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


def test_collect_reference_rows_preserves_teacher_forced_input_token(monkeypatch: pytest.MonkeyPatch) -> None:
    import npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention as evaluator

    class _NoGrad:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *args: object) -> None:
            return None

    class _FakeTensor:
        def __init__(self, value: list[list[int]] | list[int]) -> None:
            self.value = value

        def to(self, _device: str) -> "_FakeTensor":
            return self

        def __getitem__(self, index: int) -> "_FakeTensor":
            value = self.value[index]  # type: ignore[index]
            return _FakeTensor(value)

        def tolist(self) -> list[int] | list[list[int]]:
            return self.value

    class _FakeTorch:
        long = int

        @staticmethod
        def tensor(value: list[list[int]], dtype=None, device=None) -> _FakeTensor:
            return _FakeTensor(value)

        @staticmethod
        def no_grad() -> _NoGrad:
            return _NoGrad()

    class _FakeTokenizer:
        def __call__(self, _prompt: str, return_tensors: str) -> dict[str, _FakeTensor]:
            assert return_tensors == "pt"
            return {"input_ids": _FakeTensor([[10, 20]])}

    calls: list[list[int] | list[list[int]]] = []

    def _fake_single_inference(_model: object, *, input_ids: _FakeTensor, **_kwargs: object):
        calls.append(input_ids.tolist())
        if len(calls) == 1:
            return "past0", [0.0, 1.0, 0.5], [0.2, 0.5, 0.3], [1, 2]
        return "past1", [0.1, 0.2, 1.2], [0.2, 0.2, 0.6], [2, 1]

    monkeypatch.setattr(evaluator, "_run_single_inference", _fake_single_inference)

    rows, _prompt_records = _collect_reference_rows(
        object(),
        _FakeTokenizer(),
        ["prompt"],
        generation_steps=2,
        topk=2,
        device="cpu",
        torch_module=_FakeTorch(),
    )

    assert calls == [[[10, 20]], [[1]]]
    assert rows[0]["input_ids"] == [10, 20]
    assert rows[0]["reference_top1"] == 1
    assert rows[1]["input_ids"] == [1]
    assert rows[1]["reference_top1"] == 2


def test_parse_candidate_spec_and_list_compatibility() -> None:
    candidate = _parse_candidate_spec("qkv8_float_softmax:q8,k8,v8,s24,w16,float_quantized")
    assert candidate.candidate_id == "qkv8_float_softmax"
    assert candidate.q_bits == 8
    assert candidate.score_bits == 24

    generated = _parse_candidate_spec("q8,k8,v8,s8,w8,rtl_recip_lut_q10")
    assert generated.candidate_id == "q8_k8_v8_s8_w8_rtl_recip_lut_q10"

    q12_pwl = _parse_candidate_spec(
        "qkv8_q12_pwl_recip_q12_bucket8:q8,k8,v8,s12,w12,pwl_recip_lut_q12_bucket8"
    )
    assert q12_pwl.candidate_id == "qkv8_q12_pwl_recip_q12_bucket8"
    assert q12_pwl.score_bits == 12
    assert q12_pwl.weight_bits == 12
    assert q12_pwl.softmax_mode == "pwl_recip_lut_q12_bucket8"

    q16_rtl = _parse_candidate_spec("score32_w16_rtl_recip_q16:q8,k8,v8,s32,w16,rtl_recip_lut_q16")
    assert q16_rtl.candidate_id == "score32_w16_rtl_recip_q16"
    assert q16_rtl.score_bits == 32
    assert q16_rtl.weight_bits == 16
    assert q16_rtl.softmax_mode == "rtl_recip_lut_q16"

    with pytest.raises(ValueError):
        _parse_candidate_spec("qkv8_score8:r8")


def test_parse_candidate_list_from_semicolon_values() -> None:
    candidates = _parse_candidate_list(
        "qkv8_reference:q8,k8,v8,s24,w16,float_exact;qkv8_approx:q8,k8,v8,s8,w8,rtl_recip_lut_q8"
    )

    assert len(candidates) == 2
    assert candidates[0].candidate_id == "qkv8_reference"
    assert candidates[1].candidate_id == "qkv8_approx"
    assert candidates[1].softmax_mode == "rtl_recip_lut_q8"


def test_run_model_eval_multiple_candidates_and_primary_summary_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeTorch:
        float16 = "float16"
        float32 = "float32"
        bfloat16 = "bfloat16"

        class cuda:
            @staticmethod
            def is_available() -> bool:
                return False

        @staticmethod
        def no_grad() -> types.SimpleNamespace:
            return types.SimpleNamespace(__enter__=lambda self: None, __exit__=lambda self, *args: None)

        @staticmethod
        def tensor(value: list[int], dtype=None, device=None):
            return value

        long = int

    class _FakeConfig:
        num_attention_heads = 8
        num_key_value_heads = 4

    class _FakeModel:
        def __init__(self) -> None:
            self.config = _FakeConfig()

        def to(self, device: str) -> "_FakeModel":
            return self

        def eval(self) -> "_FakeModel":
            return self

    class _FakeAutoModel:
        @staticmethod
        def from_pretrained(*args, **kwargs) -> _FakeModel:
            return _FakeModel()

    class _FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            return object()

    candidate_rows_by_id = {
        "baseline": [
            {
                "candidate_id": "baseline",
                "top1_match": 1.0,
                "topk_contains": 1.0,
                "logit_cosine": 0.9999,
                "probability_kl": 0.001,
                "reference_margin": 0.2,
                "max_abs_logit_delta": 0.01,
                "prompt_index": 0,
                "step": 0,
            },
            {
                "candidate_id": "baseline",
                "top1_match": 1.0,
                "topk_contains": 1.0,
                "logit_cosine": 0.9997,
                "probability_kl": 0.0012,
                "reference_margin": 0.2,
                "max_abs_logit_delta": 0.02,
                "prompt_index": 0,
                "step": 1,
            },
        ],
        "ablated": [
            {
                "candidate_id": "ablated",
                "top1_match": 0.2,
                "topk_contains": 0.2,
                "logit_cosine": 0.95,
                "probability_kl": 0.02,
                "reference_margin": 0.2,
                "max_abs_logit_delta": 0.1,
                "prompt_index": 0,
                "step": 0,
            },
            {
                "candidate_id": "ablated",
                "top1_match": 0.0,
                "topk_contains": 0.0,
                "logit_cosine": 0.94,
                "probability_kl": 0.04,
                "reference_margin": 0.2,
                "max_abs_logit_delta": 0.2,
                "prompt_index": 0,
                "step": 1,
            },
        ],
    }

    def _fake_collect_reference_rows(*args, **kwargs):
        return [
            {"prompt_index": 0, "step": 0},
            {"prompt_index": 0, "step": 1},
        ], [
            {
                "prompt_index": 0,
                "prompt": "sample",
                "prefill_reference_top1": 1,
                "prefill_reference_margin": 0.2,
            }
        ]

    def _fake_evaluate_candidate_rows(_reference_rows, _candidate_model, candidate, **_kwargs):
        return [row.copy() for row in candidate_rows_by_id[candidate.candidate_id]]

    def _fake_supports_attention_quantization(model: object) -> bool:
        return True

    monkeypatch.setattr(
        "npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention._load_runtime_modules",
        lambda: (_FakeTorch(), _FakeAutoModel, _FakeAutoTokenizer),
    )
    monkeypatch.setattr(
        "npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention._collect_reference_rows",
        _fake_collect_reference_rows,
    )
    monkeypatch.setattr(
        "npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention._evaluate_candidate_rows",
        _fake_evaluate_candidate_rows,
    )
    monkeypatch.setattr(
        "npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention._supports_attention_quantization",
        _fake_supports_attention_quantization,
    )

    args = argparse.Namespace(
        model_id="",
        prompt_file="",
        max_prompts=1,
        generation_steps=2,
        topk=5,
        expected_gqa_group_size=2,
        q_bits=8,
        k_bits=8,
        v_bits=8,
        score_bits=8,
        weight_bits=8,
        softmax_mode="rtl_recip_lut_q8",
        candidate=[
            _parse_candidate_spec("baseline:q8,k8,v8,s24,w16,float_quantized"),
            _parse_candidate_spec("ablated:q8,k8,v8,s8,w8,float_quantized"),
        ],
        candidate_list=[],
        primary_candidate_id="baseline",
        device="cpu",
        dtype="auto",
        out="out.json",
        out_md="out.md",
    )

    payload = _run_model_eval(args)

    assert len(payload["candidate_summaries"]) == 2
    assert payload["best_candidate"]["candidate_id"] == "baseline"
    assert payload["candidate_summary"]["candidate_id"] == "baseline"
    assert payload["summary"]["candidate_id"] == "baseline"
    assert payload["precision"]["candidate_id"] == "baseline"
    assert payload["candidate_summary"]["decision_status"] == payload["decision"]["status"]
    assert payload["candidate_rows"]
    assert all(row["candidate_id"] in {"baseline", "ablated"} for row in payload["candidate_rows"])


def test_load_runtime_modules_without_transformers_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention as evaluator

    real_import_module = evaluator.importlib.import_module

    def _fake_import_module(name: str):
        if name == "transformers":
            raise ModuleNotFoundError("No module named 'transformers'")
        return real_import_module(name)

    monkeypatch.setattr(evaluator.importlib, "import_module", _fake_import_module)

    with pytest.raises(SystemExit):
        _load_runtime_modules()
