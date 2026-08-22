# Shared-SRAM K Window Scheduler Contract

This contract closes the K-prefetch scheduler boundary identified by the
Phase-2 shared-stream transport contract.  It covers one Llama7B GQA8 KV head
for one 1024-token tile.  The shared-SRAM capacity remains a separately
accounted physical macro array; the scheduler and its live compute window are
synthesizable RTL.

## Checked Geometry

- K head dimension: 128
- compute dimensions per beat group: 16
- dimension groups per head: 8
- shared word width: 1024 bits
- K words per dimension group: 128
- physical shared-SRAM banks: 17
- complete K requests and responses per head: 1,024

The sole tensor-layout authority is
`npu/sim/perf/attention_shared_sram_gqa8_tensor_layout.py`.  For dimension
group `g` and global word slot `s`, the shared word address is:

```text
base_word + 8*s + g
```

This block-major stride-8 mapping is intentionally not the contiguous
`base_word + 128*g + s` layout.  Since 8 and 17 are coprime, any consecutive
17-word round has one request per bank.  Round seven contains the remaining
nine words.

Every response carries buffer, group, round, and global-word-slot metadata.
The RTL fails closed on a response that is stale, duplicated, outside the
active round, or returned by the wrong bank.  A window cannot be overwritten
until its final compute beat has been accepted.

## Architecture Points

### Full 128-word windows

`attention_shared_sram_k_window_scheduler.sv` holds two complete 128-word
windows:

- live storage: `2 * 128 * 1024 = 262,144` bits (32 KiB)
- compute boundary: `128 * 64 = 8,192` bits
- compute beats: `8 groups * 16 dimensions = 128`
- ideal SRAM issue lower bound: eight cycles per group

The executable model and RTL tests prove exact request addresses, exact data,
ordered compute beats, backpressure behavior, and fail-closed response
metadata.  This point is not a physical result.  Two local Yosys elaboration
runs expanded the resettable array into registers and exceeded approximately
6.8 GiB RSS before technology mapping; both were terminated.  It is recorded
as `synthesis_infeasible_flat_register_window`, not as a failed timing point.

### 17-word round windows

`attention_shared_sram_k_round_scheduler.sv` holds two bank-width windows and
serializes each dimension group over eight rounds:

- live storage: `2 * 17 * 1024 = 34,816` bits (4.25 KiB)
- compute boundary: `17 * 64 = 1,088` bits plus a 17-bit valid mask
- rounds: `8 groups * 8 rounds = 64`
- compute beats: `64 rounds * 16 dimensions = 1,024`
- complete requests and responses: 1,024, unchanged from the full-window point

The Python model and RTL agree on all 64 windows and 1,024 compute beats.  The
testbench checks every request address and bank, every output lane, the final
nine-word mask, independent bank/output backpressure, counters, and malformed
metadata rejection.

Each physical bank's two live words are implemented by
`attention_shared_sram_k_round_bank.sv`.  This explicit hierarchy fixes each
response bank's write target and moves the bank permutation to the 64-bit
compute lanes.

A memory-bounded Yosys `proc; opt; check; stat` diagnostic of the initial
logical-slot implementation completed in 59.4 s with 1.188 GiB peak RSS and
zero structural errors.  An initial bounded generic technology-mapping run
reached its 180 s limit at 2.103 GiB peak RSS before ABC.  Those diagnostics
led to three structural changes: payload reset removal, storage by physical
bank rather than logical slot, and explicit 17-way bank-leaf hierarchy.

The resulting hierarchy completed bounded Nangate45 generic technology
mapping in 152.43 s with 2.223 GiB peak RSS and zero post-map structural
problems.  The mapped estimate contains 298,988 cells and 34,816 payload
flip-flops.  Its area decomposition is:

- one bank leaf: 17,352.244 um2
- scheduler, validation, and compute-side permutation excluding leaves:
  108,934.714 um2
- scheduler plus all 17 leaves: 403,922.862 um2

The final structural check must load the Liberty cell declarations with
`read_liberty -lib`; passing the Liberty path only to `dfflibmap` and `abc`
does not provide mapped-cell port directions to `check` and produces false
undriven-output warnings.  The three remaining synthesis warnings report only
that small scheduler metadata arrays were lowered to registers.

This is a pre-route standard-cell estimate, not routed area, timing, or power.
The point still requires the proposal-backed OpenROAD sweep before it may
replace a measured component in the Llama7B frontier.

The physical sweep uses a 1,000-by-1,000 um core at placement density 0.50.
The hierarchy's pre-route area is already 40.39% of that core, making the
earlier 0.40 density physically infeasible after harness and implementation
overhead.  The narrow-I/O response source repeats a metadata-derived 64-bit
lane across each 1024-bit word so stimulus generation does not dominate the
calibration.

The generated top completes the same bounded mapping in 156.98 s with 2.217
GiB peak RSS and zero structural problems.  It retains all 34,816 payload
flip-flops and estimates 414,621.116 um2 total area.  The wrapper contributes
10,698.254 um2, or 2.58% of that estimate, for total pre-route core utilization
of 41.46% before placement buffers and routing.

## Throughput Interpretation

The round point trades eight times more compute-interface cycles for 7.53
times less live storage and a 7.53 times narrower compute boundary.  At SRAM
response latency no greater than the sixteen compute cycles of one round,
double buffering sustains one accepted compute beat per cycle after initial
fill.  Longer response latency or bank/output backpressure creates explicit
stalls in both the executable model and RTL counters.

The 1,024 scheduler beats are not automatically 1,024 additional end-to-end
attention cycles.  The consumer arithmetic must accept the 17 parallel K
words for one dimension each cycle for the scheduler rate to be realizable.
Frontier recosting must use the slower of this measured interface schedule and
the composed score-compute service.

## Physical Accounting and Remaining Abstraction

Physical reports must separate:

- scheduler standard-cell area and power, including the concrete live windows
- 17 shared-SRAM bank macro area and access energy
- full shared-SRAM capacity macro area and access energy
- downstream score-compute standard-cell area and power

The shared-SRAM macro contents are not duplicated as resettable RTL state.
HBM/DRAM and its controller remain external.  Until routed PPA exists, the
round scheduler must not replace a measured component in the Llama7B frontier
ranking.

## Verification Commands

```bash
PYTHONPATH=. pytest \
  npu/sim/perf/tests/test_attention_shared_sram_k_round_scheduler.py \
  tests/test_attention_shared_sram_k_round_scheduler_rtl.py -q

iverilog -g2012 -s attention_shared_sram_k_round_scheduler \
  -o /tmp/k-round.vvp \
  npu/sim/rtl/attention_shared_sram_k_round_bank.sv \
  npu/sim/rtl/attention_shared_sram_k_round_scheduler.sv

verilator --lint-only -Wall -Wno-fatal \
  --top-module attention_shared_sram_k_round_scheduler \
  npu/sim/rtl/attention_shared_sram_k_round_bank.sv \
  npu/sim/rtl/attention_shared_sram_k_round_scheduler.sv

yosys -p 'read_liberty -lib \
    /orfs/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; \
  read_verilog -sv \
    npu/sim/rtl/attention_shared_sram_k_round_bank.sv \
    npu/sim/rtl/attention_shared_sram_k_round_scheduler.sv; \
  hierarchy -top attention_shared_sram_k_round_scheduler; \
  synth -noabc -top attention_shared_sram_k_round_scheduler; \
  dfflibmap -liberty \
    /orfs/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; \
  opt; setundef -zero; \
  abc -fast -liberty \
    /orfs/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; \
  splitnets; opt_clean -purge; \
  stat -liberty \
    /orfs/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib; \
  check'
```
