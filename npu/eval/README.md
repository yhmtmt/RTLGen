# NPU Evaluation Contract (System-Level)

## Purpose
This directory defines the contract for end-to-end NPU evaluation campaigns:
- ONNX model mapping inputs
- physical mapping (OpenROAD) outputs
- performance simulation outputs
- merged PPA + model-level metrics rows

It is the first step toward a reproducible closed-loop flow:
`ONNX -> mapper -> physical -> perf -> report`.

## Files
- `npu/eval/contract.md`: human-readable contract and field definitions.
- `npu/eval/campaign.schema.json`: JSON schema for campaign manifests.
- `npu/eval/result_row.schema.json`: JSON schema for merged result rows.
- `npu/eval/validate.py`: lightweight validator for campaign/result JSON.
- `npu/eval/examples/`: minimal examples.

## Validation
Validate campaign manifest:
```sh
python3 npu/eval/validate.py --campaign npu/eval/examples/minimal_campaign.json
```

Validate merged result row:
```sh
python3 npu/eval/validate.py --result-row npu/eval/examples/minimal_result_row.json
```

Optionally verify path-like fields exist:
```sh
python3 npu/eval/validate.py --campaign <campaign.json> --check_paths
```
