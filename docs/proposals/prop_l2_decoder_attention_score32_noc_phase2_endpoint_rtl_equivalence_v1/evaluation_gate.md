# Evaluation Gate

- Use all eight declared waves; do not pass `--wave-limit`.
- Require every paired RX descriptor to handshake before TX release.
- Require concrete modulo-256 tags and zero endpoint protocol errors.
- Require all 11,576 canonical packets and 92,128 canonical flits unless the corrected source schedule changes at the required commit.
- Require exact performance/RTL agreement for packets, flits, drain cycles, contention, input stalls, and maximum occupancy.
- Enforce the bounded worker resource and timeout contract.
- Produce only the declared JSON and Markdown artifacts.
