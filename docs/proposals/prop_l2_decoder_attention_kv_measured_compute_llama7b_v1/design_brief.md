# Design Brief

The previous Llama7B physical-HBM compute sensitivity swept abstract throughput values up to 524288 MAC/cycle. The corrected compute PPA ladder shows those values are far above what one measured NPU block can provide, and iso-utilization checks suggest the nm64 delay is mostly structural rather than a floorplan-utilization artifact.

This proposal therefore converts each merged measured compute block into a die-budgeted replica count. For each die/SRAM/logic split, the evaluator estimates:

- how many measured blocks fit in the logic area budget,
- the resulting MAC/cycle and vector-op/cycle proxy,
- the measured block clock period,
- compute area and compute power,
- and the resulting Llama7B attention/KV latency under the existing physical-HBM memory/NoC service model.

The ranking remains quality-backed: native-GQA KV8 only.

