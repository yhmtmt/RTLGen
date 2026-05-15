# Decoder Producer/Ranker Policy Calibration

- model: `decoder_output_projection_producer_ranker_policy_calibration_v1`
- decision: `producer_ranker_policy_calibration_completed`
- old_best_us: `5046.275694`
- calibrated_best_us: `301.065`
- old_to_calibrated_speedup: `16.761416`
- producer_dominant_rows: `576`
- ranker_dominant_rows: `0`

## Best Row

| metric | old | calibrated |
|---|---:|---:|
| coupled_us | 5046.275694 | 301.065 |
| producer_us | 301.452 | 301.065 |
| ranker_us | 5046.275694 | 8.80302 |
| lanes | 64 | 128 |
| selected_path |  | threshold_serial_lpc1 |

## Checks

| check | passed | observed |
|---|---|---|
| wrapper_physical_measured | `True` | `output_projection_ranker_wrapper_physical_measured` |
| policy_promoted | `True` | `output_projection_ranker_policy_promoted` |
| measured_wrapper_lane_rows_calibrated | `True` | `{'ok': 576, 'missing_wrapper_physical': 288, 'missing_wrapper_service_measurement': 0, 'total': 864}` |

## Assumptions

- The measured policy wrapper service is used only for ranker service after a producer tile reaches the ranker.
- Producer latency and II remain from the existing output-projection service model.
- Exact policy rows are used when available; otherwise the serial_lpc1 threshold is applied conservatively.
- This calibration replaces the older streaming ranker hierarchy latency for output-projection policy-wrapper coupling.
