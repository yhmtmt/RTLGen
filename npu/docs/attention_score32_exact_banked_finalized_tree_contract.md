# Score32 Exact Banked Finalized Tree Contract

This phase keeps the exact radix-2 partial tree and replaces the single
throughput abstraction at the root with an ordered bank of identical iterative
finalizers.

## Workload Shape

- A full Llama7B layer wave is `32 heads x 16 value slices = 512` finalized
  root beats.
- With `16` clusters, the leaf side still carries `8192` exact-partial beats
  for that full wave.
- The emitted root beat order remains exact slice order inside each head and
  exact head order across the full wave.

## Ordering Contract

- Tree root beats are dispatched to finalizer banks in deterministic
  round-robin order.
- Dispatch never scans for an alternate ready bank. If the selected bank is
  busy, the tree root stalls in place.
- An explicit FIFO stores only issued bank IDs, one entry per accepted beat.
- Only the bank named at the FIFO head may see `out_ready` or drive the top
- level root output.
- Output order therefore matches tree-root acceptance order even under
  arbitrary top-level backpressure.

## Timing Boundary

- The iterative divider still performs `57` divide iterations per lane-8 beat.
- Measured RTL timing is not `57` cycles/beat:
  - accept at cycle `0`
  - output handshake earliest at cycle `58`
  - next re-accept earliest at cycle `59`
- The service boundary for bank wrap is therefore `59` banks, not `57` or `58`.
- Bank counts `57`, `58`, and `59` are all checked because:
  - `57` proves the divide-iteration count alone is insufficient
  - `58` proves the extra OUTPUT state still leaves a wrap bubble
  - `59` is the first wrap-free point for saturated lane-8 service with no
    output stall

## Recorded Full-Wave Evidence

- Source generator: `npu/eval/probe_attention_score32_exact_banked_finalized_tree.py`
- Source command form:
  `python npu/eval/probe_attention_score32_exact_banked_finalized_tree.py --clusters 16 --heads 32 --divider-lanes 8 --finalizer-banks <B> --saturated --root-ready-pattern 1 --json`
- Full-wave exact output hash for all rows below:
  `027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd`

| banks | first out | last out | drain cycles | interval cycles | cycles/beat |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 62 | 30211 | 30212 | 30149 | 59.0 |
| 57 | 62 | 589 | 590 | 527 | 1.031311 |
| 58 | 62 | 581 | 582 | 519 | 1.015656 |
| 59 | 62 | 573 | 574 | 511 | 1.0 |
| 64 | 62 | 573 | 574 | 511 | 1.0 |

- These measurements are kept here so direct full-512 RTL evidence remains in
  the checked-in contract without forcing CI to recompile every large bank
  count on every run.

## Remaining Abstractions

- The tree still uses direct `328`-bit exact-partial leaf/root payload links.
- No NoC closure is claimed for those links.
- No SRAM closure is claimed for those links.
- The design still reuses the existing single-entry iterative finalizer macro.
- No full-head monolithic state register is introduced at the root; only a
  compact bank-ID FIFO, aggregate counters, and compact bank masks are exposed.

## Reporting Contract

- Manifest service fields must distinguish:
  - divide iterations per group
  - earliest output latency
  - earliest re-accept interval
- Probe reports must compare every RTL output beat to the exact reference
  stream and its hash, not just counts.
- Saturated service claims must be stated from measured RTL cycles, not from
  divide-iteration counts alone.
- `exact_no_stall_full_wave_service` means `dispatch_stall_cycles == 0`, which
  also covers short waves where `root_beats <= finalizer_banks` even if banks
  are still below the steady-state `59`-cycle reuse interval.
