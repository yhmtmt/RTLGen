# LLM Practical Scale Model Set (`llm_practical_scale_v1`)

Purpose: bounded decoder-style scale proxy after `llm_practical_v1`.

What changed relative to `llm_practical_v1`:
- active tokens increase from 32 to 64;
- KV-context score width increases from 512 to 1024 and 2048;
- repeated attention episodes include six- and eight-block cases.

This is still an ONNX-lite graph proxy, not a trained LLM. It is intended to
test whether larger active-token and KV-score pressure changes the current
`fp16_nm1` vs `fp16_nm2` PPA trend before investing in wider compute-array
design points.

Regenerate:

```sh
python3 npu/mapper/examples/gen_llm_practical_scale_suite_lite.py \
  --out-dir runs/models/llm_practical_scale_v1
```
