# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`

## Evaluations Consumed
- work item id: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- run key: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1_run_7a9e3e4183791924`
- source commit: `36f8bae95d3df28a19037d3b8ad1fb934d8acf68`

## Baseline Comparison
- HBM floor source:
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- measured compute sources:
  `l2_decoder_attention_kv_measured_compute_llama7b_v1` and
  `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`.

## Result
- result: iterate
- best measured density: `nm64_flat`, 70.9436 MAC/cycle/mm2.
- maximum measured compute throughput: 17024 MAC/cycle.
- first HBM-bound floor: 131072 MAC/cycle.
- all measured points remain below the HBM-bound floor.
- gap by die:
  - 400 mm2: 5632 measured MAC/cycle versus 131072 floor, 23.27x gap.
  - 800 mm2: 11328 measured MAC/cycle versus 131072 floor, 11.57x gap.
  - 1200 mm2: 17024 measured MAC/cycle versus 131072 floor, 7.70x gap.
- at best measured density, reaching 131072 MAC/cycle requires about
  1847.552 mm2 of compute area. That is 4.62x a 400 mm2 die, 2.31x an
  800 mm2 die, and 1.54x a 1200 mm2 die.

## Failures and Caveats
- No evaluator command failure was observed.
- The HBM floor is still a planning-model floor, not a routed HBM controller
  result.
- The measured compute architecture is the current nm-style block family; a
  purpose-built dense array could change the density.

## Recommendation
- iterate
- Do not deepen global NoC/SRAM arbitration as the immediate next job. First
  define and evaluate a denser compute architecture target capable of approaching
  the 131072 MAC/cycle floor within plausible die logic area.
