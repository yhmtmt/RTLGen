Imported ONNX MLP Set v1
========================

Purpose
-------
Exercise the num-modules-aware mapper/perf path on real imported ONNX graphs
without storing large model binaries in Git.

Contents
--------
- `mnist_mlp`: imported from `chris-chris/mina-zkml` at commit
  `6d3e5bf9865388c343a9b652adc9912ffbbabc0f`
- `armor_mlp`: imported from `Ericsii/rm_vision` at commit
  `5d55864a9c535414967107e711caa82138d3683c`

Fetcher flow
------------
Materialize the models into `runs/model_cache/onnx_imported_mlp_v1/` with:

```sh
python3 npu/eval/fetch_models.py --manifest runs/models/onnx_imported_mlp_v1/manifest.json
```

Model notes
-----------
Both graphs lower through the extended mapper path:
- optional `Flatten`
- sequential `Gemm -> Relu -> Gemm -> Relu -> Gemm`

The paired campaign uses:
- `mnist_mlp`: `mapper_extra_args = ["--batch-override", "64"]`
- `armor_mlp`: no batch override

This keeps the dynamic-batch model explicitly rebatched while leaving the
fixed-batch model at its exported batch.
