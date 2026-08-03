# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c2_r2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 401d35a8 | attention_score32_exact_partial_tree_folded_mersenne_cluster_v1_401d35a8 | ok | 7.7728 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7300`
- data_required_time: `0.6700`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
     1   37.33    0.01    0.02    0.03 ^ wire6784/Z (BUF_X8)
                                         net6784 (net)
                  0.02    0.01    0.05 ^ wire6783/A (BUF_X16)
     1   44.62    0.01    0.02    0.07 ^ wire6783/Z (BUF_X16)
                                         net6783 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.74    0.02    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   18.42    0.02    0.05    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_10_0_clk (net)
                  0.04    0.01    0.62 ^ clkbuf_leaf_169_clk/A (CLKBUF_X3)
     6    8.25    0.01    0.05    0.66 ^ clkbuf_leaf_169_clk/Z (CLKBUF_X3)
                                         clknet_leaf_169_clk (net)
                  0.01    0.00    0.66 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_0/active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `u_node_0/active_merged_value_q[201]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.8400`
- data_arrival_time: `7.7700`
- data_required_time: `8.6100`

```text
Startpoint: u_node_0/active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/active_merged_value_q[201]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
     1   37.33    0.01    0.02    0.03 ^ wire6784/Z (BUF_X8)
                                         net6784 (net)
                  0.02    0.01    0.05 ^ wire6783/A (BUF_X16)
     1   44.62    0.01    0.02    0.07 ^ wire6783/Z (BUF_X16)
                                         net6783 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.74    0.02    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   18.42    0.02    0.05    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_28_0_clk (net)
                  0.04    0.00    8.61 ^ clkbuf_leaf_301_clk/A (CLKBUF_X3)
     7    9.02    0.01    0.05    8.65 ^ clkbuf_leaf_301_clk/Z (CLKBUF_X3)
                                         clknet_leaf_301_clk (net)
                  0.01    0.00    8.65 ^ u_node_0/active_merged_value_q[201]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.65   clock reconvergence pessimism
                         -0.04    8.61   library setup time
                                  8.61   data required time
-----------------------------------------------------------------------------
                                  8.61   data required time
                                 -7.77   data arrival time
-----------------------------------------------------------------------------
                                  0.84   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_0/active_right_value_q[206]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.1700`
- data_arrival_time: `2.0700`
- data_required_time: `0.9100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_0/active_right_value_q[206]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    9.20    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
     3   46.63    0.03    0.04    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.05    0.03    2.07 ^ u_node_0/active_right_value_q[206]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
...
                                         clknet_4_5_0_clk (net)
                  0.01    0.00    0.54 ^ clkbuf_5_11_0_clk/A (CLKBUF_X3)
    15   54.82    0.04    0.07    0.61 ^ clkbuf_5_11_0_clk/Z (CLKBUF_X3)
                                         clknet_5_11_0_clk (net)
                  0.04    0.01    0.62 ^ clkbuf_leaf_123_clk/A (CLKBUF_X3)
     6    8.81    0.01    0.05    0.67 ^ clkbuf_leaf_123_clk/Z (CLKBUF_X3)
                                         clknet_leaf_123_clk (net)
                  0.01    0.00    0.67 ^ u_node_0/active_right_value_q[206]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.67   clock reconvergence pessimism
                          0.24    0.91   library removal time
                                  0.91   data required time
-----------------------------------------------------------------------------
                                  0.91   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.17   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_0/out_value_q[100]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.0700`
- data_arrival_time: `3.6500`
- data_required_time: `8.7200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_0/out_value_q[100]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    9.20    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
     3   46.63    0.03    0.04    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.05    0.04    2.08 ^ place6692/A (BUF_X2)
     1   28.32    0.03    0.05    2.13 ^ place6692/Z (BUF_X2)
                                         net6692 (net)
                  0.04    0.02    2.15 ^ place6693/A (BUF_X2)
     7   48.34    0.04    0.05    2.21 ^ place6693/Z (BUF_X2)
                                         net6693 (net)
                  0.08    0.05    2.26 ^ place6695/A (BUF_X1)
    10   38.47    0.09    0.12    2.38 ^ place6695/Z (BUF_X1)
...
                                         clknet_4_15_0_clk (net)
                  0.02    0.00    8.55 ^ clkbuf_5_31_0_clk/A (CLKBUF_X3)
    21   60.59    0.05    0.08    8.62 ^ clkbuf_5_31_0_clk/Z (CLKBUF_X3)
                                         clknet_5_31_0_clk (net)
                  0.05    0.00    8.63 ^ clkbuf_leaf_193_clk/A (CLKBUF_X3)
     7    8.58    0.01    0.05    8.68 ^ clkbuf_leaf_193_clk/Z (CLKBUF_X3)
                                         clknet_leaf_193_clk (net)
                  0.01    0.00    8.68 ^ u_node_0/out_value_q[100]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.68   clock reconvergence pessimism
                          0.04    8.72   library recovery time
                                  8.72   data required time
-----------------------------------------------------------------------------
                                  8.72   data required time
                                 -3.65   data arrival time
-----------------------------------------------------------------------------
                                  5.07   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_node_0/active_merged_value_q[279]$_DFFE_PN0P_`
- endpoint: `u_node_0/out_value_q[279]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.8800`
- data_required_time: `0.8600`

```text
Startpoint: u_node_0/active_merged_value_q[279]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/out_value_q[279]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.66    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
     1   50.84    0.01    0.03    0.04 ^ wire6784/Z (BUF_X8)
                                         net6784 (net)
                  0.02    0.01    0.05 ^ wire6783/A (BUF_X16)
     1   68.07    0.01    0.03    0.08 ^ wire6783/Z (BUF_X16)
                                         net6783 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.49    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.29    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_27_0_clk (net)
                  0.09    0.01    0.80 ^ clkbuf_leaf_290_clk/A (CLKBUF_X3)
     7    9.14    0.01    0.06    0.86 ^ clkbuf_leaf_290_clk/Z (CLKBUF_X3)
                                         clknet_leaf_290_clk (net)
                  0.01    0.00    0.86 ^ u_node_0/out_value_q[279]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.86   clock reconvergence pessimism
                          0.01    0.86   library hold time
                                  0.86   data required time
-----------------------------------------------------------------------------
                                  0.86   data required time
                                 -0.88   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_node_0/active_merged_value_q[279]$_DFFE_PN0P_`
- endpoint: `u_node_0/out_value_q[279]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.8900`
- data_required_time: `0.8700`

```text
Startpoint: u_node_0/active_merged_value_q[279]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/out_value_q[279]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
     1   50.89    0.01    0.03    0.04 ^ wire6784/Z (BUF_X8)
                                         net6784 (net)
                  0.02    0.02    0.06 ^ wire6783/A (BUF_X16)
     1   68.02    0.01    0.03    0.08 ^ wire6783/Z (BUF_X16)
                                         net6783 (net)
                  0.03    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.96    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.05    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_27_0_clk (net)
                  0.09    0.02    0.81 ^ clkbuf_leaf_290_clk/A (CLKBUF_X3)
     7    9.62    0.01    0.06    0.86 ^ clkbuf_leaf_290_clk/Z (CLKBUF_X3)
                                         clknet_leaf_290_clk (net)
                  0.01    0.00    0.86 ^ u_node_0/out_value_q[279]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.86   clock reconvergence pessimism
                          0.01    0.87   library hold time
                                  0.87   data required time
-----------------------------------------------------------------------------
                                  0.87   data required time
                                 -0.89   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_node_0/_23284_ (net)
                  0.01    0.00    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_node_0/_23284_ (net)
                  0.01    0.00    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_node_0/_23284_ (net)
                  0.01    0.00    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_node_0/_23284_ (net)
                  0.01    0.00    0.06 ^ u_node_0/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_0/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7300`
- data_required_time: `0.6700`

```text
Startpoint: u_node_0/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire6784/A (BUF_X8)
     1   37.33    0.01    0.02    0.03 ^ wire6784/Z (BUF_X8)
                                         net6784 (net)
                  0.02    0.01    0.05 ^ wire6783/A (BUF_X16)
     1   44.62    0.01    0.02    0.07 ^ wire6783/Z (BUF_X16)
                                         net6783 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.74    0.02    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   18.42    0.02    0.05    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_10_0_clk (net)
                  0.04    0.01    0.62 ^ clkbuf_leaf_169_clk/A (CLKBUF_X3)
     6    8.25    0.01    0.05    0.66 ^ clkbuf_leaf_169_clk/Z (CLKBUF_X3)
                                         clknet_leaf_169_clk (net)
                  0.01    0.00    0.66 ^ u_node_0/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c2_r2/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_node_0/active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `u_node_0/active_merged_value_q[168]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.7700`
- data_arrival_time: `7.1900`
- data_required_time: `7.9600`

```text
Startpoint: u_node_0/active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/active_merged_value_q[168]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     7   18.63    0.02    0.11    0.11 v u_node_0/active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_node_0/active_lane_index_q[1] (net)
                  0.02    0.00    0.11 v u_node_0/_54356_/B (HA_X1)
     3    9.88    0.01    0.05    0.16 v u_node_0/_54356_/CO (HA_X1)
                                         u_node_0/_11604_ (net)
                  0.01    0.00    0.16 v u_node_0/_34880_/A (INV_X2)
     9   31.63    0.04    0.05    0.21 ^ u_node_0/_34880_/ZN (INV_X2)
                                         u_node_0/_17608_ (net)
                  0.04    0.00    0.21 ^ place5867/A (BUF_X1)
     2    8.80    0.02    0.05    0.26 ^ place5867/Z (BUF_X1)
                                         net5867 (net)
                  0.02    0.00    0.26 ^ u_node_0/_34955_/A2 (NOR2_X4)
...
                                  7.19   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_node_0/active_merged_value_q[168]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    7.96   library setup time
                                  7.96   data required time
-----------------------------------------------------------------------------
                                  7.96   data required time
                                 -7.19   data arrival time
-----------------------------------------------------------------------------
                                  0.77   slack (MET)



```
