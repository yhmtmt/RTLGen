# Finite-Endpoint Final Frontier

This proposal replaces the score32 entry in the quality-aware Llama7B
frontier with finite endpoint timing and aggregate composed NoC accounting.
It compares that point with measured exact FP16 without mixing invalid or
planning-only candidates into the promotable ranks.

The report keeps throughput, area, energy, and precision as separate
dimensions and identifies Pareto and conditional winners. It also checks
whether checkpoint GQA structure matches the physical architecture; arithmetic
quality on Mistral GQA4 does not by itself promote a GQA8 hardware point.
