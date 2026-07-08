# Score32 HBM Controller Replay

This proposal replaces the score32 schedule-wrapper frontier's analytic HBM
service formula with deterministic cycle-level replay of the burst stream.

The job does not add new PPA or quality evaluation. It consumes the merged
score32 HBM service closure and schedule-wrapper recost, then sweeps controller
parameters for channel queues, row-window locality, request overhead, row-miss
penalty, scheduler gap, and outstanding requests.

The result is intended to feed a follow-on integrated frontier ranking. Remaining
abstractions after this step are HBM controller RTL timing, vendor current
signoff, and measured address-trace locality.
