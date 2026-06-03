# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1`
- `title`: `Llama7B attention/KV compute ceiling envelope`

## Problem
The previous compute-floor-gap result showed that the measured RTLGen compute
density is far below the first HBM-bound Llama7B 131k attention/KV point.
However, architecture decisions should also consider plausible external
compute-density references before deciding whether the next work is compute,
memory, or NoC dominated.

## Hypothesis
The measured RTLGen density remains compute-bound, while only aggressive
custom-array density envelopes reach the HBM floor at large logic budgets.

## Evaluation Scope
- inputs: merged compute-sensitivity and measured-compute artifacts.
- registry citations: internal measurements, external measurements, and the
  compute-density comparison claim.
- density envelopes: measured RTLGen best plus 150 and 300 MAC/cycle/mm2.
- die sizes: 400, 800, and 1200 mm2.
- logic fractions: 0.2, 0.4, and 0.6.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-03T10:35:00Z
- note: This is a low-cost analytic planning gate over merged artifacts.

