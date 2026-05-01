# Implementation Summary

- Added `npu/eval/diagnose_llm_decoder_pwl_failures.py` to read a decoder
  quality sweep and emit focused JSON/Markdown diagnosis for shared PWL misses.
- Added a Layer-2 task-generator abstraction,
  `decoder_pwl_failure_diagnosis`, that binds the diagnostic command to the
  merged broad-v2 sweep artifact.
- Added task-generator unit coverage for diagnostic inputs, outputs, and
  command manifest wiring.
