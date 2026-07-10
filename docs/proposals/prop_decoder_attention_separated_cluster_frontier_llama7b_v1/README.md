# Precision-Aligned Separated Attention Cluster Frontier

This proposal replaces the replicated synthetic attention wrapper with a bounded semantic tile that computes real q8 QK scores, score32 exp-LUT/div weights, and every weighted-V output lane. Exact perf/RTL stage and ready/valid equivalence is the mandatory gate before Nangate45 PPA.

The physical sweep measures `1:1`, `2:1`, `4:1`, `8:1`, `4:2`, and `8:2` producer-to-consumer points. These rows quantify both consumer sharing and the wide payload/arbitration cost; they do not by themselves claim full Llama7B performance.
