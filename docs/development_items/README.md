# Development Items

## Purpose

This directory is the canonical intake backlog for preliminary development
ideas in both Layer 1 and Layer 2.

Use it for:
- early candidate ideas
- paper-driven opportunities
- discussion-derived hypotheses
- partially formed implementation directions

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
4. promote it into `docs/developer_loop/<proposal_id>/`
5. update the intake item with:
   - `status: promoted_to_proposal`
   - `proposal_id`
   - `proposal_path`

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
