LLM Decoder Tiny v1
===================

Purpose
-------
Reference-only model contract for the first decoder-quality stage.

Current status
--------------
File-backed tokenizer stub contract.

What exists now:
- `model_contract.json`
- placeholder backend configs for `reference` and `candidate` roles
- an executable backend interface that can call an external CPU, emulation, or hardware-target runner via `command_json_v1`
- an opt-in exact-reference ONNX template (`reference_onnx`) that targets `npu/eval/run_llm_decoder_onnx_reference.py` once `onnxruntime` and a pinned decoder export exist

What does not exist yet:
- trained weights
- tokenizer-faithful model export
- runnable mapper lowering
- real decoder inference path

This contract exists so dataset artifacts can bind to a specific model identity, a file-backed tokenizer bundle contract, a backend interface, and a reference-output schema without pretending a real small decoder is already integrated into the repository. The ONNX runner template is exact-reference only and should be paired later with a separate approximation-aware candidate backend for hardware evaluation.
