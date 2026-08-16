# Finite-Endpoint Composed Recost

This proposal joins the corrected complete Phase 2 schedule, finite endpoint
performance/RTL equivalence, and aggregate endpoint/mesh PPA. It produces the
first score32 frontier point whose NoC timing includes endpoint cadence and
whose area and vectorless power replace the earlier primitive estimates.

The result remains a partial energy closure. SRAM access energy, workload
activity, HBM/DRAM, and synthesized workload-scheduler PPA stay explicit.
The output also records that its 32-head/4-KV-head GQA8 model is a
Llama7B-shaped proxy, not exact Llama-2-7B MHA.
