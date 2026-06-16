# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 16.1489 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 16.2597 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[3][5]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.6200`
- data_arrival_time: `16.1500`
- data_required_time: `10.5300`

```text
Startpoint: u_softmax/exp_weight_q[3][5]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   30.01    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   36.72    0.01    0.02    0.03 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.04 ^ wire54452/A (BUF_X16)
     1   53.85    0.01    0.02    0.07 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.10    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   19.29    0.02    0.05    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_16_0_clk/A (CLKBUF_X3)
     5   44.15    0.03    0.06   10.55 ^ clkbuf_6_16_0_clk/Z (CLKBUF_X3)
                                         clknet_6_16_0_clk (net)
                  0.04    0.01   10.56 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.56   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -16.15   data arrival time
-----------------------------------------------------------------------------
                                 -5.62   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.6900`
- data_required_time: `0.6700`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   30.01    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   36.72    0.01    0.02    0.03 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.04 ^ wire54452/A (BUF_X16)
     1   53.85    0.01    0.02    0.07 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.10    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   20.62    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_59_0_clk (net)
                  0.05    0.02    0.61 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.57    0.01    0.05    0.66 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.66 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.69   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_0[738]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5400`
- data_arrival_time: `2.5300`
- data_required_time: `0.9800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_0[738]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.57    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input153/A (CLKBUF_X3)
     1   27.51    0.02    0.04    2.04 ^ input153/Z (CLKBUF_X3)
                                         net152 (net)
                  0.03    0.02    2.06 ^ place54274/A (BUF_X1)
     1   26.74    0.06    0.08    2.14 ^ place54274/Z (BUF_X1)
                                         net54273 (net)
                  0.06    0.02    2.16 ^ place54275/A (BUF_X1)
     1   27.19    0.06    0.08    2.24 ^ place54275/Z (BUF_X1)
                                         net54274 (net)
                  0.06    0.02    2.26 ^ place54276/A (BUF_X1)
     3   30.93    0.07    0.10    2.36 ^ place54276/Z (BUF_X1)
...
                                         clknet_4_12_0_clk (net)
                  0.03    0.00    0.52 ^ clkbuf_6_49_0_clk/A (CLKBUF_X3)
    13   62.78    0.05    0.08    0.60 ^ clkbuf_6_49_0_clk/Z (CLKBUF_X3)
                                         clknet_6_49_0_clk (net)
                  0.05    0.01    0.61 ^ clkbuf_leaf_181_clk/A (CLKBUF_X3)
     6   12.33    0.01    0.05    0.66 ^ clkbuf_leaf_181_clk/Z (CLKBUF_X3)
                                         clknet_leaf_181_clk (net)
                  0.01    0.00    0.66 ^ stream_buf_1_pipe_0[738]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.66   clock reconvergence pessimism
                          0.32    0.98   library removal time
                                  0.98   data required time
-----------------------------------------------------------------------------
                                  0.98   data required time
                                 -2.53   data arrival time
-----------------------------------------------------------------------------
                                  1.54   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_1_out[34]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4700`
- data_arrival_time: `3.1800`
- data_required_time: `10.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_1_out[34]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.57    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input153/A (CLKBUF_X3)
     1   27.51    0.02    0.04    2.04 ^ input153/Z (CLKBUF_X3)
                                         net152 (net)
                  0.03    0.02    2.06 ^ place54274/A (BUF_X1)
     1   26.74    0.06    0.08    2.14 ^ place54274/Z (BUF_X1)
                                         net54273 (net)
                  0.06    0.02    2.16 ^ place54275/A (BUF_X1)
     1   27.19    0.06    0.08    2.24 ^ place54275/Z (BUF_X1)
                                         net54274 (net)
                  0.06    0.02    2.26 ^ place54276/A (BUF_X1)
     3   30.93    0.07    0.10    2.36 ^ place54276/Z (BUF_X1)
...
                                         clknet_4_2_0_clk (net)
                  0.02    0.00   10.48 ^ clkbuf_6_8_0_clk/A (CLKBUF_X3)
     8   43.05    0.03    0.06   10.54 ^ clkbuf_6_8_0_clk/Z (CLKBUF_X3)
                                         clknet_6_8_0_clk (net)
                  0.04    0.01   10.55 ^ clkbuf_leaf_439_clk/A (CLKBUF_X3)
     6    8.69    0.01    0.04   10.60 ^ clkbuf_leaf_439_clk/Z (CLKBUF_X3)
                                         clknet_leaf_439_clk (net)
                  0.01    0.00   10.60 ^ value_accum_1_out[34]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.60   clock reconvergence pessimism
                          0.05   10.65   library recovery time
                                 10.65   data required time
-----------------------------------------------------------------------------
                                 10.65   data required time
                                 -3.18   data arrival time
-----------------------------------------------------------------------------
                                  7.47   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_softmax/exp_weight_q[2][6]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-8.0500`
- data_arrival_time: `18.0100`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/exp_weight_q[2][6]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[2][6]$_DFF_P_/CK (DFF_X1)
     4   14.01    0.02    0.09    0.09 v u_softmax/exp_weight_q[2][6]$_DFF_P_/QN (DFF_X1)
                                         u_softmax/_45181_ (net)
                  0.02    0.00    0.09 v u_softmax/_80766_/B (FA_X1)
     2    5.17    0.02    0.13    0.22 ^ u_softmax/_80766_/S (FA_X1)
                                         u_softmax/_01025_ (net)
                  0.02    0.00    0.22 ^ u_softmax/_66500_/A (INV_X1)
     1    2.66    0.01    0.01    0.23 v u_softmax/_66500_/ZN (INV_X1)
                                         u_softmax/_01031_ (net)
                  0.01    0.00    0.23 v u_softmax/_80769_/CI (FA_X1)
     1    1.70    0.01    0.11    0.34 ^ u_softmax/_80769_/S (FA_X1)
                                         u_softmax/_01033_ (net)
                  0.01    0.00    0.34 ^ u_softmax/_66291_/A (INV_X1)
...
                                 18.01   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -18.01   data arrival time
-----------------------------------------------------------------------------
                                 -8.05   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_softmax/exp_weight_q[3][1]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.2200`
- data_arrival_time: `16.1700`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/exp_weight_q[3][1]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[3][1]$_DFF_P_/CK (DFF_X1)
     3    7.88    0.01    0.09    0.09 v u_softmax/exp_weight_q[3][1]$_DFF_P_/Q (DFF_X1)
                                         u_softmax/exp_weight_q[3][1] (net)
                  0.01    0.00    0.09 v u_softmax/_80831_/B (FA_X1)
     2    3.94    0.02    0.12    0.21 ^ u_softmax/_80831_/S (FA_X1)
                                         u_softmax/_01144_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_66575_/A (INV_X1)
     1    3.87    0.01    0.01    0.23 v u_softmax/_66575_/ZN (INV_X1)
                                         u_softmax/_01225_ (net)
                  0.01    0.00    0.23 v u_softmax/_80875_/A (FA_X1)
     1    2.56    0.01    0.11    0.34 ^ u_softmax/_80875_/S (FA_X1)
                                         u_softmax/_01226_ (net)
                  0.01    0.00    0.34 ^ u_softmax/_66515_/A (INV_X1)
...
                                 16.17   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -16.17   data arrival time
-----------------------------------------------------------------------------
                                 -6.22   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_softmax/exp_weight_q[3][1]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.2200`
- data_arrival_time: `16.1700`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/exp_weight_q[3][1]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[3][1]$_DFF_P_/CK (DFF_X1)
     3    7.88    0.01    0.09    0.09 v u_softmax/exp_weight_q[3][1]$_DFF_P_/Q (DFF_X1)
                                         u_softmax/exp_weight_q[3][1] (net)
                  0.01    0.00    0.09 v u_softmax/_80831_/B (FA_X1)
     2    3.94    0.02    0.12    0.21 ^ u_softmax/_80831_/S (FA_X1)
                                         u_softmax/_01144_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_66575_/A (INV_X1)
     1    3.87    0.01    0.01    0.23 v u_softmax/_66575_/ZN (INV_X1)
                                         u_softmax/_01225_ (net)
                  0.01    0.00    0.23 v u_softmax/_80875_/A (FA_X1)
     1    2.56    0.01    0.11    0.34 ^ u_softmax/_80875_/S (FA_X1)
                                         u_softmax/_01226_ (net)
                  0.01    0.00    0.34 ^ u_softmax/_66515_/A (INV_X1)
...
                                 16.17   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -16.17   data arrival time
-----------------------------------------------------------------------------
                                 -6.22   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_softmax/exp_weight_q[3][1]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.9800`
- data_arrival_time: `15.9300`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/exp_weight_q[3][1]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[3][1]$_DFF_P_/CK (DFF_X1)
     3    7.74    0.01    0.09    0.09 v u_softmax/exp_weight_q[3][1]$_DFF_P_/Q (DFF_X1)
                                         u_softmax/exp_weight_q[3][1] (net)
                  0.01    0.00    0.09 v u_softmax/_80831_/B (FA_X1)
     2    3.60    0.01    0.12    0.21 ^ u_softmax/_80831_/S (FA_X1)
                                         u_softmax/_01144_ (net)
                  0.01    0.00    0.21 ^ u_softmax/_66575_/A (INV_X1)
     1    3.78    0.01    0.01    0.23 v u_softmax/_66575_/ZN (INV_X1)
                                         u_softmax/_01225_ (net)
                  0.01    0.00    0.23 v u_softmax/_80875_/A (FA_X1)
     1    2.54    0.01    0.11    0.34 ^ u_softmax/_80875_/S (FA_X1)
                                         u_softmax/_01226_ (net)
                  0.01    0.00    0.34 ^ u_softmax/_66515_/A (INV_X1)
...
                                 15.93   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -15.93   data arrival time
-----------------------------------------------------------------------------
                                 -5.98   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `u_softmax/exp_weight_q[0][5]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.6900`
- data_arrival_time: `16.3000`
- data_required_time: `10.6000`

```text
Startpoint: u_softmax/exp_weight_q[0][5]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   43.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   47.02    0.01    0.03    0.04 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.05 ^ wire54452/A (BUF_X16)
     1   67.02    0.01    0.03    0.08 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.87    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   27.51    0.02    0.06    0.23 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_6_0_clk (net)
                  0.02    0.00   10.55 ^ clkbuf_6_24_0_clk/A (CLKBUF_X3)
     4   43.12    0.03    0.06   10.62 ^ clkbuf_6_24_0_clk/Z (CLKBUF_X3)
                                         clknet_6_24_0_clk (net)
                  0.04    0.02   10.63 ^ u_softmax/weights[0]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.63   clock reconvergence pessimism
                         -0.03   10.60   library setup time
                                 10.60   data required time
-----------------------------------------------------------------------------
                                 10.60   data required time
                                -16.30   data arrival time
-----------------------------------------------------------------------------
                                 -5.69   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_softmax/exp_weight_q[3][5]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.6700`
- data_arrival_time: `16.2800`
- data_required_time: `10.6100`

```text
Startpoint: u_softmax/exp_weight_q[3][5]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.30    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   47.13    0.01    0.03    0.04 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.05 ^ wire54452/A (BUF_X16)
     1   67.25    0.01    0.03    0.08 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.40    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   27.40    0.02    0.06    0.23 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.03    0.00   10.56 ^ clkbuf_6_16_0_clk/A (CLKBUF_X3)
     5   47.95    0.04    0.07   10.63 ^ clkbuf_6_16_0_clk/Z (CLKBUF_X3)
                                         clknet_6_16_0_clk (net)
                  0.04    0.02   10.64 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.64   clock reconvergence pessimism
                         -0.03   10.61   library setup time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                -16.28   data arrival time
-----------------------------------------------------------------------------
                                 -5.67   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[3][5]$_DFF_P_`
- endpoint: `u_softmax/weights[24]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.6200`
- data_arrival_time: `16.1500`
- data_required_time: `10.5300`

```text
Startpoint: u_softmax/exp_weight_q[3][5]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[24]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   30.01    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   36.72    0.01    0.02    0.03 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.04 ^ wire54452/A (BUF_X16)
     1   53.85    0.01    0.02    0.07 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.10    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   19.29    0.02    0.05    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_16_0_clk/A (CLKBUF_X3)
     5   44.15    0.03    0.06   10.55 ^ clkbuf_6_16_0_clk/Z (CLKBUF_X3)
                                         clknet_6_16_0_clk (net)
                  0.04    0.01   10.56 ^ u_softmax/weights[24]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.56   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -16.15   data arrival time
-----------------------------------------------------------------------------
                                 -5.62   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_split1/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.7400`
- data_required_time: `0.7200`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.30    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire54453/A (BUF_X8)
     1   47.13    0.01    0.03    0.04 ^ wire54453/Z (BUF_X8)
                                         net54452 (net)
                  0.02    0.01    0.05 ^ wire54452/A (BUF_X16)
     1   67.25    0.01    0.03    0.08 ^ wire54452/Z (BUF_X16)
                                         net54451 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.40    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.41    0.02    0.06    0.23 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_59_0_clk (net)
                  0.05    0.02    0.66 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.13    0.01    0.05    0.71 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.71 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.71   clock reconvergence pessimism
                          0.01    0.72   library hold time
                                  0.72   data required time
-----------------------------------------------------------------------------
                                  0.72   data required time
                                 -0.74   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```
