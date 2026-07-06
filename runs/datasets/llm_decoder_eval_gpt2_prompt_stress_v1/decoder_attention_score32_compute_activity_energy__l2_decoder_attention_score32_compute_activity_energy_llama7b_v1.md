# Score32 Compute Activity Energy

- decision: `score32_compute_activity_energy_still_energy_worse`
- compute active duty: `0.957495485`
- wall-time compute energy mJ/token: `360.550392645`
- best clock-gated compute energy mJ/token: `345.225372946`
- best clock-gated total energy mJ/token: `479.505988187`
- measured-FP16 energy reference mJ/token: `81.66413005453946`
- clock-gated score32 / measured-FP16 energy ratio: `5.871684274`

## Scenarios

| idle power fraction | compute mJ | total mJ | reduction vs wall |
|---:|---:|---:|---:|
| 0.0 | 345.225372946 | 479.505988187 | 0.030970209 |
| 0.05 | 345.991623931 | 480.272239172 | 0.029421698 |
| 0.1 | 346.757874916 | 481.038490157 | 0.027873188 |
| 0.25 | 349.05662787 | 483.337243111 | 0.023227657 |
| 1.0 | 360.550392645 | 494.831007886 | 0.0 |

## Assumptions

- Score32 compute power is inherited from measured dual-stream composed PPA and measured command-control recost.
- Active compute cycles use replica_recost_tile_service_cycles * tile_waves per layer.
- Idle energy is swept as a fraction of the non-active wall-time compute-energy remainder.
- HBM energy is unchanged from the score32 HBM/DRAM service closure.
