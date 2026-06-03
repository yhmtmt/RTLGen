# All-Measured Llama7B Attention L2 Schedule

This proposal records the L2 schedule retry that replaces the remaining local
L1 attention cost abstractions with measured or promoted costs:

- measured `fp16_nm1` and `fp16_nm2` compute-array PPA
- full-value attention tile datapath costs
- exact-int softmax weight generator costs
- FIFO/router local NoC anchor costs

The target workload is the Llama7B 131k native-GQA KV8 clustered attention
schedule. SRAM capacity/service and global NoC arbitration remain analytic L2
service terms and are tracked as residual assumptions.

