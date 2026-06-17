# Softmax-Recip Dual-Stream Physical Feasibility

This proposal checks whether the fast softmax-recip subtile schedule is
physically valid under the measured Nangate45 logic budget.

Result:
- decision: `dual_stream_area_blocked`
- requested fastest mode: `dual_mac`, `1575.373891 us`
- requested slack: `-397947652.4116 um2`
- compute area over budget: `397947652.4116 um2`
- required compute density gain: `2.008939`
- best physically feasible mode: `split_mac`, `2042.378179 us`

The current physically valid frontier is therefore the split-MAC subtile
schedule, not the optimistic dual-MAC schedule.
