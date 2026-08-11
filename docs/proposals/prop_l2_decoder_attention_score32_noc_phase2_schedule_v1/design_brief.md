# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- title: Score32 segmented-mesh Phase 2 scheduling closure

## Problem
The score32 Llama7B path still uses a one-flow NoC shortcut, so its service
latency cannot support a composed architecture ranking under contention.

## Hypothesis
The checked-in traffic quantities can be routed through the concrete 4x4 mesh
model over all eight waves without violating finite buffering, backpressure,
flit conservation, or 8-bit tag lifetime safety.

## Evaluation Scope
- One evidence-only item covering all 128 tiles in all eight declared waves.
- Deterministic XY routing, four VCs, finite router FIFOs, and endpoint stalls.
- Checked-in exact-reduction traffic and measured L1 endpoint-cost inputs.
- Explicit conversion from the measured `48.6509 ns` compute-wrapper domain to
  a 1ns target NoC domain; the measured five-port router clock remains a
  follow-on substitution.
- No dependency on the historically failed recost DB record; materialized repo
  references are required instead.
- HBM/DRAM, measured SRAM placement, root-finalizer timing, and producer
  descriptor/control storage are explicitly excluded.

## Knowledge Inputs
- `npu/sim/perf/noc_segmented_mesh.py`
- `npu/eval/measure_llm_decoder_attention_score32_noc_phase2_schedule.py`
- checked-in score32 exact-reduction recost and measured endpoint costs

## Candidate Direction
Replace the scalar NoC estimate with cycle-level multi-flow routed service
evidence before reranking the score32 frontier.

## Direction Gate
- status: approved
- approved_by: user
- approved_utc: 2026-08-11T00:00:00Z
- note: Resume goal mode and proceed through remote evaluation.
