# Evaluation Gate

- All four RTL traces must exactly match the cycle model.
- Request and response beat counts must equal width-derived expectations.
- Every complete group must issue exactly one 1024-bit macro read.
- Physical comparison must use the unique timing-feasible 2 ns row.
- Any protocol error, missing physical row, or counter mismatch fails closed.
