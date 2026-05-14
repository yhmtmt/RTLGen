# Decoder Output-Projection Ranker Physical Wrapper

- model: `decoder_output_projection_ranker_wrapper_physical_v1`
- decision: `output_projection_ranker_wrapper_physical_measured`
- next_step: Use the measured wrapper overhead to decide whether the policy wrapper can be integrated into the producer block or whether path-specific wrappers should be retained.

## Variants

| lanes | top | sim serial | sim ranktree | metrics | critical path ns | area | power mW |
|---:|---|---|---|---|---:|---:|---:|
| 64 | `decoder_output_ranker_policy_r64_wrapper` | `ok` | `ok` | `ok` | 4.347542551572723 | 135943.0 | 0.0161417 |
| 128 | `decoder_output_ranker_policy_r128_wrapper` | `ok` | `ok` | `ok` | 4.43030684305195 | 277497.0 | 0.0304755 |
