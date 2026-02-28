# Campaign ONNX Models

Generate baseline ONNX models for this campaign:

```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out runs/campaigns/npu/e2e_eval_v0/models/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out runs/campaigns/npu/e2e_eval_v0/models/mlp2.onnx
```
