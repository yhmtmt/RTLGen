# Evaluation Gate

Run both matched candidates at identical Nangate45 clock, utilization, density,
seed, and flow settings. A comparison is valid only when both rows are timing
feasible and their generated source commit and tool provenance match.

Report the paired area, critical path, and vectorless power deltas. Also report
the exact traffic reduction of 89 flits per group and scale codec pair PPA by 15
for the current 16-cluster reduction topology. Do not interpret vectorless
power as workload energy without adding measured flit transport energy.
