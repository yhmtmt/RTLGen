# Evaluation Gate

- Run `l2_decoder_output_projection_service_v1`.
- Confirm producer II is reported as an integer cycle count derived from compute and memory service.
- Confirm the report identifies whether each point is compute-limited or weight-memory-limited.
- Use the service curve as input to producer/ranker coupling; do not interpret it as a measured RTL result.
