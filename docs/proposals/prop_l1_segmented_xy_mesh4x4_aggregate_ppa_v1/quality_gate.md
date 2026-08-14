# Quality Gate

- Generator recognizes only the exact five-port, four-VC, four-bit endpoint-ID mesh contract.
- Generated top exposes only `clk`, `rst_n`, 16 observed-valid bits, and a 256-bit signature.
- Payload state advances only on accepted ready/valid transfers.
- Destinations, VCs, tags, fragments, payloads, and sink readiness vary.
- Every endpoint is observed within the bounded RTL harness test.
- No observed signature contains unknown data.
- Existing router and mesh performance-model/RTL equivalence tests remain green.
