# Quality Gate

This L1 proposal does not rerun model-quality gates. It inherits quality context
from the q8 normalization frontier and only calibrates arithmetic cost terms.

Any later calibrated ranking must continue to require exact next-token and
top-k preservation on the prompt-stress suite before comparing hardware costs.
