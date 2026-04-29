# LLM Decoder Survivor Cost Proxy

- `proposal_id`: `prop_l2_decoder_survivor_cost_proxy_v1`
- `item_id`: `l2_decoder_survivor_cost_proxy_v1`
- layer: `layer2`
- abstraction: `decoder_survivor_cost_proxy`

## Motivation

The prompt-stress sweep showed several exact-safe survivors, but quality alone
does not choose the next hardware direction. Exact softmax paths still carry
exp/normalization cost even if final probability storage is narrowed. A rough
cost proxy makes that tradeoff explicit before we spend evaluator time on RTL or
OpenROAD work.

## Evaluation Shape

The evaluator should read
`decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json` and emit:

- `decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json`
- `decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.md`

The ranking must gate on 24/24 next-token and 24/24 top-k prompt-stress quality,
then score exact exp, PWL, normalization, datapath-width, and probability-write
terms with the model documented in the artifact.

## Interpretation

This is a planning proxy. It can select a small frontier for implementation-cost
work, but it must not be reported as physical PPA or final format acceptance.
