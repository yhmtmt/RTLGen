# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- `title`: Llama7B clustered attention schedule with measured L1 local costs

## Why This Gate Is Required
This job changes architecture ranking by cost accounting only. It does not
change Llama quality assumptions: the sweep remains native GQA8 and KV8, and
does not promote MQA or KV4.

## Checks
- native GQA8/KV8 only: pass
- no new approximation or quality-degraded KV sharing: pass
- full value datapath not claimed: pass

## Local Commands
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: pass
- note: Quality risk remains in future structural KV changes, not in this measured-cost substitution.
