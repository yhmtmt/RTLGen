# Evaluation Gate

Reject any report that omits `head_dimension=128` or
`score_accumulation_beats_per_block=128`.

The one-group report must record `1,048,576` producer handshakes. The
four-group report must record `4,194,304`. SRAM fill, SRAM response, cluster
row, and root row counts remain those of the existing GQA8 schedule because
head dimension changes score accumulation depth, not value residency shape.

Require exact structured row equality, zero protocol/sticky errors, serial
producer replay, and the checked canonical global numerator packing. Treat
timeout, OOM, or resource termination as inconclusive. Preserve the old
artifacts as retracted audit evidence; do not overwrite or delete them.

Both replacement runs require an exclusive evaluator worker.  The one-group
task is bounded at 8 GiB memory, 300% CPU, 2,400 seconds outer runtime, and a
1,500-second stall timeout.  The four-group task uses the same memory, CPU, and
stall limits with a 7,200-second outer runtime.  Exceeding a bound must produce
an explicit inconclusive failure artifact rather than automatic promotion or
an unbounded retry.
