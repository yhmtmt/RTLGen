# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 23.8349 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 24.1263 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[3]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.7100`
- data_arrival_time: `24.1300`
- data_required_time: `10.4200`

```text
Startpoint: seed_state[3]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.71    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire77512/A (BUF_X8)
     1   44.93    0.01    0.03    0.04 ^ wire77512/Z (BUF_X8)
                                         net77511 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.74    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.38    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   34.54    0.03    0.06    0.25 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_9_0_clk (net)
                  0.05    0.00   10.40 ^ clkbuf_leaf_262_clk/A (CLKBUF_X3)
     5   12.23    0.01    0.05   10.45 ^ clkbuf_leaf_262_clk/Z (CLKBUF_X3)
                                         clknet_leaf_262_clk (net)
                  0.01    0.00   10.45 ^ u_softmax/weight_hash[8]$_DFF_P_/CK (DFF_X1)
                          0.00   10.45   clock reconvergence pessimism
                         -0.04   10.42   library setup time
                                 10.42   data required time
-----------------------------------------------------------------------------
                                 10.42   data required time
                                -24.13   data arrival time
-----------------------------------------------------------------------------
                                -13.71   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `u_value_stream_0/value_accum[25]$_DFF_P_`
- endpoint: `u_value_stream_0/value_hash[25]$_DFF_P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.5100`
- data_required_time: `0.4200`

```text
Startpoint: u_value_stream_0/value_accum[25]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_value_stream_0/value_hash[25]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.71    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire77512/A (BUF_X8)
     1   44.93    0.01    0.03    0.04 ^ wire77512/Z (BUF_X8)
                                         net77511 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.74    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.38    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   31.18    0.03    0.06    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3_0_clk (net)
                  0.02    0.00    0.38 ^ clkbuf_leaf_245_clk/A (CLKBUF_X3)
     8    9.80    0.01    0.04    0.42 ^ clkbuf_leaf_245_clk/Z (CLKBUF_X3)
                                         clknet_leaf_245_clk (net)
                  0.01    0.00    0.42 ^ u_value_stream_0/value_hash[25]$_DFF_P_/CK (DFF_X1)
                          0.00    0.42   clock reconvergence pessimism
                          0.00    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0[242]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6500`
- data_arrival_time: `2.3800`
- data_required_time: `0.7300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0[242]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.95    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input349/A (CLKBUF_X3)
     1   13.13    0.01    0.03    2.03 ^ input349/Z (CLKBUF_X3)
                                         net348 (net)
                  0.01    0.00    2.04 ^ place77410/A (BUF_X1)
     1   22.88    0.05    0.07    2.11 ^ place77410/Z (BUF_X1)
                                         net77409 (net)
                  0.05    0.01    2.12 ^ place77411/A (BUF_X1)
     1   28.29    0.06    0.09    2.21 ^ place77411/Z (BUF_X1)
                                         net77410 (net)
                  0.07    0.02    2.23 ^ place77412/A (BUF_X1)
     1    6.63    0.02    0.04    2.27 ^ place77412/Z (BUF_X1)
...
                                         clknet_3_7_0_clk (net)
                  0.04    0.00    0.34 ^ clkbuf_5_30_0_clk/A (CLKBUF_X3)
     7   51.39    0.04    0.08    0.42 ^ clkbuf_5_30_0_clk/Z (CLKBUF_X3)
                                         clknet_5_30_0_clk (net)
                  0.04    0.00    0.43 ^ clkbuf_leaf_146_clk/A (CLKBUF_X3)
     4   15.39    0.02    0.05    0.48 ^ clkbuf_leaf_146_clk/Z (CLKBUF_X3)
                                         clknet_leaf_146_clk (net)
                  0.02    0.00    0.48 ^ stream_buf_0[242]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.48   clock reconvergence pessimism
                          0.25    0.73   library removal time
                                  0.73   data required time
-----------------------------------------------------------------------------
                                  0.73   data required time
                                 -2.38   data arrival time
-----------------------------------------------------------------------------
                                  1.65   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0[992]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.3400`
- data_arrival_time: `3.1500`
- data_required_time: `10.4900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0[992]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.95    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input349/A (CLKBUF_X3)
     1   13.13    0.01    0.03    2.03 ^ input349/Z (CLKBUF_X3)
                                         net348 (net)
                  0.01    0.00    2.04 ^ place77410/A (BUF_X1)
     1   22.88    0.05    0.07    2.11 ^ place77410/Z (BUF_X1)
                                         net77409 (net)
                  0.05    0.01    2.12 ^ place77411/A (BUF_X1)
     1   28.29    0.06    0.09    2.21 ^ place77411/Z (BUF_X1)
                                         net77410 (net)
                  0.07    0.02    2.23 ^ place77412/A (BUF_X1)
     1    6.63    0.02    0.04    2.27 ^ place77412/Z (BUF_X1)
...
                                         clknet_3_1_0_clk (net)
                  0.04    0.00   10.33 ^ clkbuf_5_4_0_clk/A (CLKBUF_X3)
    10   45.42    0.04    0.07   10.40 ^ clkbuf_5_4_0_clk/Z (CLKBUF_X3)
                                         clknet_5_4_0_clk (net)
                  0.04    0.00   10.40 ^ clkbuf_leaf_26_clk/A (CLKBUF_X3)
     6    8.90    0.01    0.04   10.45 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
                                         clknet_leaf_26_clk (net)
                  0.01    0.00   10.45 ^ stream_buf_0[992]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.45   clock reconvergence pessimism
                          0.04   10.49   library recovery time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                 -3.15   data arrival time
-----------------------------------------------------------------------------
                                  7.34   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `seed_state[0]$_DFF_PN1_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.2200`
- data_arrival_time: `29.1700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[0]$_DFF_PN1_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[0]$_DFF_PN1_/CK (DFFS_X1)
     5   15.36    0.04    0.12    0.12 ^ seed_state[0]$_DFF_PN1_/Q (DFFS_X1)
                                         seed_state[0] (net)
                  0.04    0.00    0.12 ^ _15428_/A (XOR2_X2)
     2    6.80    0.03    0.06    0.18 ^ _15428_/Z (XOR2_X2)
                                         _06505_ (net)
                  0.03    0.00    0.18 ^ _15429_/A (BUF_X4)
    10   27.39    0.02    0.04    0.22 ^ _15429_/Z (BUF_X4)
                                         _06506_ (net)
                  0.02    0.00    0.22 ^ _15430_/A (BUF_X4)
    10   25.74    0.02    0.04    0.25 ^ _15430_/Z (BUF_X4)
                                         _06507_ (net)
                  0.02    0.00    0.25 ^ _15712_/B (XNOR2_X1)
...
                                 29.17   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[8]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -29.17   data arrival time
-----------------------------------------------------------------------------
                                -19.22   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8700`
- data_arrival_time: `24.8300`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X1)
     3    9.77    0.01    0.10    0.10 v seed_state[9]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[9] (net)
                  0.01    0.00    0.10 v _17974_/A (XOR2_X2)
     3   19.20    0.02    0.06    0.16 v _17974_/Z (XOR2_X2)
                                         _07482_ (net)
                  0.02    0.01    0.17 v place72761/A (BUF_X4)
     3   40.11    0.01    0.04    0.20 v place72761/Z (BUF_X4)
                                         net72760 (net)
                  0.03    0.02    0.23 v place72765/A (BUF_X4)
     2    5.51    0.01    0.03    0.26 v place72765/Z (BUF_X4)
                                         net72764 (net)
                  0.01    0.00    0.26 v _18908_/B (XNOR2_X1)
...
                                 24.83   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -24.83   data arrival time
-----------------------------------------------------------------------------
                                -14.87   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `seed_state[2]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8600`
- data_arrival_time: `24.8200`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[2]$_DFF_PN0_/CK (DFFR_X1)
     3   10.23    0.03    0.12    0.12 ^ seed_state[2]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[2] (net)
                  0.03    0.00    0.12 ^ _15536_/B (XOR2_X2)
     2   20.37    0.06    0.09    0.21 ^ _15536_/Z (XOR2_X2)
                                         _06579_ (net)
                  0.06    0.00    0.21 ^ place73237/A (BUF_X1)
     2   10.17    0.03    0.05    0.27 ^ place73237/Z (BUF_X1)
                                         net73236 (net)
                  0.03    0.00    0.27 ^ place73238/A (BUF_X1)
     2    5.64    0.02    0.04    0.30 ^ place73238/Z (BUF_X1)
                                         net73237 (net)
                  0.02    0.00    0.30 ^ _16807_/B (XNOR2_X1)
...
                                 24.82   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -24.82   data arrival time
-----------------------------------------------------------------------------
                                -14.86   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `seed_state[2]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.6600`
- data_arrival_time: `24.6300`
- data_required_time: `9.9700`

```text
Startpoint: seed_state[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[2]$_DFF_PN0_/CK (DFFR_X1)
     3   10.75    0.03    0.12    0.12 ^ seed_state[2]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[2] (net)
                  0.03    0.00    0.12 ^ _15536_/B (XOR2_X2)
     2   19.99    0.06    0.09    0.21 ^ _15536_/Z (XOR2_X2)
                                         _06579_ (net)
                  0.06    0.00    0.22 ^ place73237/A (BUF_X1)
     2   10.15    0.03    0.05    0.27 ^ place73237/Z (BUF_X1)
                                         net73236 (net)
                  0.03    0.00    0.27 ^ place73238/A (BUF_X1)
     2    5.38    0.01    0.04    0.30 ^ place73238/Z (BUF_X1)
                                         net73237 (net)
                  0.01    0.00    0.30 ^ _16807_/B (XNOR2_X1)
...
                                 24.63   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[16]$_DFF_P_/CK (DFF_X1)
                         -0.03    9.97   library setup time
                                  9.97   data required time
-----------------------------------------------------------------------------
                                  9.97   data required time
                                -24.63   data arrival time
-----------------------------------------------------------------------------
                                -14.66   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[3]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.0100`
- data_arrival_time: `24.4500`
- data_required_time: `10.4400`

```text
Startpoint: seed_state[3]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   65.61    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire77512/A (BUF_X8)
     1   54.18    0.02    0.03    0.05 ^ wire77512/Z (BUF_X8)
                                         net77511 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.41    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   31.83    0.03    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.03    0.01    0.21 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   30.61    0.03    0.06    0.27 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.05    0.02   10.43 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     4    5.40    0.01    0.04   10.48 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00   10.48 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.04   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -24.45   data arrival time
-----------------------------------------------------------------------------
                                -14.01   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[3]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.8300`
- data_arrival_time: `24.2700`
- data_required_time: `10.4400`

```text
Startpoint: seed_state[3]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   64.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire77512/A (BUF_X8)
     1   51.98    0.01    0.03    0.05 ^ wire77512/Z (BUF_X8)
                                         net77511 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.09    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   31.88    0.03    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.03    0.01    0.21 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   30.64    0.03    0.06    0.26 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.05    0.01   10.43 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     4    5.53    0.01    0.05   10.47 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00   10.48 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.03   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -24.27   data arrival time
-----------------------------------------------------------------------------
                                -13.83   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[3]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.7100`
- data_arrival_time: `24.1300`
- data_required_time: `10.4200`

```text
Startpoint: seed_state[3]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.71    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire77512/A (BUF_X8)
     1   44.93    0.01    0.03    0.04 ^ wire77512/Z (BUF_X8)
                                         net77511 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.74    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.38    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   34.54    0.03    0.06    0.25 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_9_0_clk (net)
                  0.05    0.00   10.40 ^ clkbuf_leaf_262_clk/A (CLKBUF_X3)
     5   12.23    0.01    0.05   10.45 ^ clkbuf_leaf_262_clk/Z (CLKBUF_X3)
                                         clknet_leaf_262_clk (net)
                  0.01    0.00   10.45 ^ u_softmax/weight_hash[8]$_DFF_P_/CK (DFF_X1)
                          0.00   10.45   clock reconvergence pessimism
                         -0.04   10.42   library setup time
                                 10.42   data required time
-----------------------------------------------------------------------------
                                 10.42   data required time
                                -24.13   data arrival time
-----------------------------------------------------------------------------
                                -13.71   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cycle_ctr[0]$_DFF_PN0_`
- endpoint: `cycle_ctr[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.0800`
- data_required_time: `0.0100`

```text
Startpoint: cycle_ctr[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_ctr[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_ctr[0]$_DFF_PN0_/CK (DFFR_X1)
     3    8.10    0.02    0.08    0.08 ^ cycle_ctr[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _00080_ (net)
                  0.02    0.00    0.08 ^ cycle_ctr[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.08   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_ctr[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.08   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```
