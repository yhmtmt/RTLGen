LLM Decoder Tiny v1
===================

Purpose
-------
Reference-side model contract for the first decoder-quality stage.

Current status
--------------
Planned exact-reference source selected.

What exists now:
- `model_contract.json`
- placeholder backend configs for `reference` and `candidate` roles
- an executable backend interface that can call an external CPU, emulation, or hardware-target runner via `command_json_v1`
- an explicit ONNX exact-reference binding scaffold:
  - `reference_onnx_binding.json`
- a GPT-2-style BPE tokenizer bundle scaffold paired with that future exact-reference path
- a concrete planned upstream tiny decoder family selection:
  - model: `sshleifer/tiny-gpt2`
  - tokenizer family: `gpt2`

What does not exist yet:
- fetched/pinned ONNX decoder weights
- model-faithful tokenizer assets
- runnable exact-reference inference from checked-in artifacts
- approximation-aware candidate backend for the same model pair

This contract now makes the intended exact-reference pair explicit: a future ONNX export plus the model-native tokenizer bundle. The planned first upstream pair is `sshleifer/tiny-gpt2` with the GPT-2 tokenizer family. The assets are not present yet, so the binding is still inactive by design.
