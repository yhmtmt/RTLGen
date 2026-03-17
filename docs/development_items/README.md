# Development Items

## Purpose

This directory is the canonical intake backlog for preliminary development
ideas in both Layer 1 and Layer 2.

Use it for:
- early candidate ideas
- paper-driven opportunities
- discussion-derived hypotheses
- partially formed implementation directions
- mapper-only follow-on work that becomes necessary after an evaluated
  architecture result exposes heuristic mapping limits

Do not use it for:
- approved proposal execution state
- implementation checkpoints
- remote evaluation results

Those belong in:
- `docs/developer_loop/`

## Structure

- `index.md`
  - append-friendly registry of all intake items
- `items/<item_id>.md`
  - one structured page per intake item
- `items/_template.md`
  - starting template for a new item

## Lifecycle

1. capture a new idea here as an intake item
2. add papers, discussion notes, and rough evaluation thoughts
3. clarify until the item reaches `ready_for_proposal`
4. if an evaluated proposal ended in `iterate` because of mapper limitations,
   capture or update the bounded mapper follow-on item here before starting a
   new mapper proposal
5. promote it into `docs/developer_loop/<proposal_id>/`
6. update the intake item with:
   - `status: promoted_to_proposal`
   - `proposal_id`
   - `proposal_path`

## Mapper Follow-On Rule

When a completed Layer 1 or Layer 2 proposal fails to answer the architecture
question cleanly because the mapper heuristic is likely suboptimal:
- do not silently fold the next mapper idea into an unrelated new architecture
  proposal
- create or update a mapper intake item here first
- link the triggering proposal id, PR, run key, and analysis artifacts
- bound the mapper scope narrowly enough that the next developer-loop proposal
  can answer a specific scheduling or legality question

## Status Values

- `seed`
- `triage`
- `ready_for_proposal`
- `promoted_to_proposal`
- `parked`
- `rejected`
- `merged`

## ID Rule

Use:

```text
item_<layer>_<topic>_<change>_vN
```

Examples:
- `item_l1_prefix_fanout_balance_v1`
- `item_l2_softmax_tail_fused_output_v1`
- `item_l2_mapper_tile_scheduler_v1`
