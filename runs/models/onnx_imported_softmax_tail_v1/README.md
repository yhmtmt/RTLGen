Imported ONNX Softmax-Tail Set v1
=================================

Purpose
-------
Validate the first non-GEMM terminal lowering path in the mapper using a real
external ONNX classifier graph.

Contents
--------
- `logistic_regression`: imported from `chris-chris/mina-zkml` at commit
  `6d3e5bf9865388c343a9b652adc9912ffbbabc0f`

Operator shape
--------------
The imported graph includes:
- `Cast -> Gemm -> Softmax`
- auxiliary label branch: `ArgMax -> Gather`

The mapper currently lowers only the probability path (`Softmax` output) and
records the ignored auxiliary output names in `mapper_notes`.

Fetcher flow
------------
Materialize the model into `runs/model_cache/onnx_imported_softmax_tail_v1/`
with:

```sh
python3 npu/eval/fetch_models.py --manifest runs/models/onnx_imported_softmax_tail_v1/manifest.json
```

Campaign note
-------------
The paired campaign uses `mapper_extra_args = ["--batch-override", "256"]` to
exercise the `num_modules` row-parallel path on the dynamic-batch input.
