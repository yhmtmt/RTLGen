# Evaluation Gate

Before dispatch:

1. run the direct merge manifest/port regression
2. run exhaustive exp-scale regression
3. run randomized RTL/software equivalence on the folded merge
4. run the cycle/backpressure regression against the explicit service contract
5. run the standalone guard on the checked-in config and sweep

Promotion requires:

- exact RTL/software equivalence for the folded merge
- no protocol errors on valid traffic
- the generated artifacts to match the checked-in config and manifest contract
- one completed Nangate45 standalone pair-merge PPA row
