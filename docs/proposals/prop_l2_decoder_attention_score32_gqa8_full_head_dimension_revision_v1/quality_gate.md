# Quality Gate

- Accept exactly 128 signed query/key beats per token block and assert
  `input_last` only on the final dimension.
- Compute every reference score as the sum of all 128 signed products.
- Require 1,048,576 producer handshakes for one group and 4,194,304 for all
  four GQA8 groups.
- Compare every structured cluster and root row, not only hashes or totals.
- Require zero protocol and sticky errors and canonical numerator packing.
- Classify timeout, OOM, and external termination as inconclusive, never pass.
- Preserve the one-dimensional artifacts as retracted audit history.
