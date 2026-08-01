# Design Brief

The block merges two exact-partial beats with unchanged ready/valid semantics and
unchanged exact arithmetic, but schedules the work as:

1. capture the pair and compute exact max plus exp-scale factors
2. scale left exp-sum, then right exp-sum
3. for each of 8 lanes, scale left lane, then scale right lane, then saturating-add
4. publish the merged beat into a one-entry output buffer

This preserves the software merge bit pattern while removing the previous
parallel fanout of `16 x signed 41x24` lane scaling from one cycle.
