# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- `candidate_id`: `l1_decoder_attention_two_pass_stream_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_two_pass_stream_ppa_v1`
- `l1_decoder_attention_two_pass_stream_ppa_v1_run_d88cdb5818618a63`
- source commit: `636d3d67ff149b5fa9066750d26240d7723c11b0`
- review: PR #1256

## Baseline Comparison
- outcome: `boundary_no_feasible_points`
- summary: All completed physical rows miss their declared clock period; retain them as timing-boundary evidence and do not promote a feasible design point.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: No timing-feasible Layer 1 rows were produced; completed flows that miss their declared clock period are retained as explicit timing-boundary evidence.

## Failures and Caveats
- every 10 ns point completed place-and-route but failed timing; the best
  critical paths were 42.7317/45.2992/47.3708/48.9200 ns for 1/2/4/8
  combinational divider lanes
- each longest path runs from divider control into `result_value`, so the
  external score-SRAM and KV-replay interfaces are not the timing cause
- the one-lane combinational point is also smallest and lowest power
  (138432 um2 standard-cell area and 7.35 mW at density 0.4), but is not a
  feasible clocked architecture

## Recommendation
- `iterate`
- reason: Accepted Layer 1 evidence merged, but no concrete promotion proposal entries were present.
- next_action: prove and measure one exact shared restoring divider; its 480
  finalization cycles add less than one percent to the 131072-token two-pass
  fill/replay schedule while removing the combinational divide path
