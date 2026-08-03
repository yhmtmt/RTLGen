# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c16_r2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 401d35a8 | attention_score32_exact_partial_tree_folded_mersenne_cluster_v1_401d35a8 | ok | 7.9837 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_2/out_value_q[88]$_DFFE_PN0P_`
- endpoint: `u_node_9/left_value_hold_q[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `1.0600`
- data_required_time: `1.0100`

```text
Startpoint: u_node_2/out_value_q[88]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_9/left_value_hold_q[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   13.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire48734/A (BUF_X8)
     1   52.19    0.01    0.02    0.02 ^ wire48734/Z (BUF_X8)
                                         net48734 (net)
                  0.03    0.02    0.05 ^ wire48733/A (BUF_X16)
     1   53.86    0.01    0.03    0.07 ^ wire48733/Z (BUF_X16)
                                         net48733 (net)
                  0.03    0.02    0.10 ^ wire48732/A (BUF_X16)
     1   63.32    0.01    0.03    0.12 ^ wire48732/Z (BUF_X16)
                                         net48732 (net)
                  0.03    0.03    0.15 ^ wire48731/A (BUF_X32)
     1   49.43    0.01    0.02    0.17 ^ wire48731/Z (BUF_X32)
...
                                         clknet_9_247__leaf_clk (net)
                  0.06    0.00    0.95 ^ clkbuf_leaf_3353_clk/A (CLKBUF_X3)
     7    9.81    0.01    0.05    1.00 ^ clkbuf_leaf_3353_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3353_clk (net)
                  0.01    0.00    1.00 ^ u_node_9/left_value_hold_q[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.00   clock reconvergence pessimism
                          0.01    1.01   library hold time
                                  1.01   data required time
-----------------------------------------------------------------------------
                                  1.01   data required time
                                 -1.06   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_2/active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `u_node_2/active_merged_value_q[15]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9000`
- data_arrival_time: `7.9800`
- data_required_time: `8.8800`

```text
Startpoint: u_node_2/active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/active_merged_value_q[15]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   13.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire48734/A (BUF_X8)
     1   52.19    0.01    0.02    0.02 ^ wire48734/Z (BUF_X8)
                                         net48734 (net)
                  0.03    0.02    0.05 ^ wire48733/A (BUF_X16)
     1   53.86    0.01    0.03    0.07 ^ wire48733/Z (BUF_X16)
                                         net48733 (net)
                  0.03    0.02    0.10 ^ wire48732/A (BUF_X16)
     1   63.32    0.01    0.03    0.12 ^ wire48732/Z (BUF_X16)
                                         net48732 (net)
                  0.03    0.03    0.15 ^ wire48731/A (BUF_X32)
     1   49.43    0.01    0.02    0.17 ^ wire48731/Z (BUF_X32)
...
                                         clknet_9_420__leaf_clk (net)
                  0.02    0.00    8.88 ^ clkbuf_leaf_3487_clk/A (CLKBUF_X3)
     7    9.78    0.01    0.04    8.92 ^ clkbuf_leaf_3487_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3487_clk (net)
                  0.01    0.00    8.92 ^ u_node_2/active_merged_value_q[15]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.92   clock reconvergence pessimism
                         -0.04    8.88   library setup time
                                  8.88   data required time
-----------------------------------------------------------------------------
                                  8.88   data required time
                                 -7.98   data arrival time
-----------------------------------------------------------------------------
                                  0.90   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_7/cycle_count[23]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.1100`
- data_arrival_time: `2.3600`
- data_required_time: `1.2400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_7/cycle_count[23]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.71    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6722/A (CLKBUF_X3)
     1   26.19    0.02    0.04    2.04 ^ input6722/Z (CLKBUF_X3)
                                         net6722 (net)
                  0.03    0.02    2.06 ^ place46961/A (BUF_X1)
     1   21.87    0.05    0.07    2.13 ^ place46961/Z (BUF_X1)
                                         net46961 (net)
                  0.05    0.01    2.14 ^ place46962/A (BUF_X1)
     3   32.86    0.07    0.09    2.23 ^ place46962/Z (BUF_X1)
                                         net46962 (net)
                  0.07    0.01    2.24 ^ place46963/A (BUF_X2)
    21   70.20    0.08    0.10    2.34 ^ place46963/Z (BUF_X2)
...
                                         clknet_8_159_0_clk (net)
                  0.01    0.00    0.85 ^ clkbuf_9_318__f_clk/A (CLKBUF_X3)
     6   41.54    0.03    0.05    0.90 ^ clkbuf_9_318__f_clk/Z (CLKBUF_X3)
                                         clknet_9_318__leaf_clk (net)
                  0.04    0.02    0.91 ^ clkbuf_leaf_4688_clk/A (CLKBUF_X3)
     7    9.46    0.01    0.05    0.96 ^ clkbuf_leaf_4688_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4688_clk (net)
                  0.01    0.00    0.96 ^ u_node_7/cycle_count[23]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.96   clock reconvergence pessimism
                          0.28    1.24   library removal time
                                  1.24   data required time
-----------------------------------------------------------------------------
                                  1.24   data required time
                                 -2.36   data arrival time
-----------------------------------------------------------------------------
                                  1.11   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_7/active_right_value_q[269]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `4.9700`
- data_arrival_time: `4.0700`
- data_required_time: `9.0400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_7/active_right_value_q[269]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.71    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6722/A (CLKBUF_X3)
     1   26.19    0.02    0.04    2.04 ^ input6722/Z (CLKBUF_X3)
                                         net6722 (net)
                  0.03    0.02    2.06 ^ place46961/A (BUF_X1)
     1   21.87    0.05    0.07    2.13 ^ place46961/Z (BUF_X1)
                                         net46961 (net)
                  0.05    0.01    2.14 ^ place46962/A (BUF_X1)
     3   32.86    0.07    0.09    2.23 ^ place46962/Z (BUF_X1)
                                         net46962 (net)
                  0.08    0.03    2.26 ^ place47116/A (BUF_X1)
     5   33.74    0.07    0.11    2.36 ^ place47116/Z (BUF_X1)
...
                                         clknet_8_10_0_clk (net)
                  0.01    0.00    8.85 ^ clkbuf_9_20__f_clk/A (CLKBUF_X3)
    30   83.22    0.06    0.09    8.94 ^ clkbuf_9_20__f_clk/Z (CLKBUF_X3)
                                         clknet_9_20__leaf_clk (net)
                  0.06    0.01    8.95 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     8   10.57    0.01    0.05    9.00 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    9.00 ^ u_node_7/active_right_value_q[269]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    9.00   clock reconvergence pessimism
                          0.04    9.04   library recovery time
                                  9.04   data required time
-----------------------------------------------------------------------------
                                  9.04   data required time
                                 -4.07   data arrival time
-----------------------------------------------------------------------------
                                  4.97   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_node_2/out_value_q[88]$_DFFE_PN0P_`
- endpoint: `u_node_9/left_value_hold_q[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `1.1800`
- data_required_time: `1.1300`

```text
Startpoint: u_node_2/out_value_q[88]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_9/left_value_hold_q[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   17.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire48734/A (BUF_X8)
     1   70.55    0.02    0.03    0.03 ^ wire48734/Z (BUF_X8)
                                         net48734 (net)
                  0.04    0.03    0.06 ^ wire48733/A (BUF_X16)
     1   73.01    0.01    0.03    0.09 ^ wire48733/Z (BUF_X16)
                                         net48733 (net)
                  0.03    0.03    0.11 ^ wire48732/A (BUF_X16)
     1   79.98    0.01    0.03    0.14 ^ wire48732/Z (BUF_X16)
                                         net48732 (net)
                  0.04    0.03    0.17 ^ wire48731/A (BUF_X32)
     1   68.26    0.01    0.03    0.20 ^ wire48731/Z (BUF_X32)
...
                                         clknet_9_247__leaf_clk (net)
                  0.07    0.00    1.07 ^ clkbuf_leaf_3353_clk/A (CLKBUF_X3)
     7    9.66    0.01    0.05    1.12 ^ clkbuf_leaf_3353_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3353_clk (net)
                  0.01    0.00    1.12 ^ u_node_9/left_value_hold_q[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.12   clock reconvergence pessimism
                          0.01    1.13   library hold time
                                  1.13   data required time
-----------------------------------------------------------------------------
                                  1.13   data required time
                                 -1.18   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_node_2/out_value_q[88]$_DFFE_PN0P_`
- endpoint: `u_node_9/left_value_hold_q[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `1.1900`
- data_required_time: `1.1400`

```text
Startpoint: u_node_2/out_value_q[88]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_9/left_value_hold_q[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   17.13    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire48734/A (BUF_X8)
     1   70.06    0.01    0.02    0.03 ^ wire48734/Z (BUF_X8)
                                         net48734 (net)
                  0.04    0.03    0.06 ^ wire48733/A (BUF_X16)
     1   72.55    0.01    0.03    0.08 ^ wire48733/Z (BUF_X16)
                                         net48733 (net)
                  0.04    0.03    0.11 ^ wire48732/A (BUF_X16)
     1   79.83    0.01    0.03    0.14 ^ wire48732/Z (BUF_X16)
                                         net48732 (net)
                  0.04    0.03    0.18 ^ wire48731/A (BUF_X32)
     1   67.60    0.01    0.03    0.20 ^ wire48731/Z (BUF_X32)
...
                                         clknet_9_247__leaf_clk (net)
                  0.07    0.00    1.07 ^ clkbuf_leaf_3353_clk/A (CLKBUF_X3)
     7   10.08    0.01    0.05    1.13 ^ clkbuf_leaf_3353_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3353_clk (net)
                  0.01    0.00    1.13 ^ u_node_9/left_value_hold_q[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.13   clock reconvergence pessimism
                          0.01    1.14   library hold time
                                  1.14   data required time
-----------------------------------------------------------------------------
                                  1.14   data required time
                                 -1.19   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_2/out_value_q[88]$_DFFE_PN0P_`
- endpoint: `u_node_9/left_value_hold_q[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `1.0600`
- data_required_time: `1.0100`

```text
Startpoint: u_node_2/out_value_q[88]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_9/left_value_hold_q[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   13.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire48734/A (BUF_X8)
     1   52.19    0.01    0.02    0.02 ^ wire48734/Z (BUF_X8)
                                         net48734 (net)
                  0.03    0.02    0.05 ^ wire48733/A (BUF_X16)
     1   53.86    0.01    0.03    0.07 ^ wire48733/Z (BUF_X16)
                                         net48733 (net)
                  0.03    0.02    0.10 ^ wire48732/A (BUF_X16)
     1   63.32    0.01    0.03    0.12 ^ wire48732/Z (BUF_X16)
                                         net48732 (net)
                  0.03    0.03    0.15 ^ wire48731/A (BUF_X32)
     1   49.43    0.01    0.02    0.17 ^ wire48731/Z (BUF_X32)
...
                                         clknet_9_247__leaf_clk (net)
                  0.06    0.00    0.95 ^ clkbuf_leaf_3353_clk/A (CLKBUF_X3)
     7    9.81    0.01    0.05    1.00 ^ clkbuf_leaf_3353_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3353_clk (net)
                  0.01    0.00    1.00 ^ u_node_9/left_value_hold_q[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.00   clock reconvergence pessimism
                          0.01    1.01   library hold time
                                  1.01   data required time
-----------------------------------------------------------------------------
                                  1.01   data required time
                                 -1.06   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/2_floorplan_final.rpt`
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
                                         u_node_0/_23362_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_detailed_place.rpt`
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
                                         u_node_0/_23362_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_global_place.rpt`
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
                                         u_node_0/_23362_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_resizer.rpt`
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
                                         u_node_0/_23362_ (net)
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

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c16_r2/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_node_2/active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `u_node_2/active_merged_value_q[12]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.7900`
- data_arrival_time: `7.1700`
- data_required_time: `7.9600`

```text
Startpoint: u_node_2/active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/active_merged_value_q[12]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_2/active_lane_index_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     7   19.65    0.02    0.11    0.11 v u_node_2/active_lane_index_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_node_2/active_lane_index_q[0] (net)
                  0.02    0.00    0.11 v u_node_2/_54737_/A (HA_X1)
     3    7.16    0.01    0.04    0.15 v u_node_2/_54737_/CO (HA_X1)
                                         u_node_2/_12096_ (net)
                  0.01    0.00    0.15 v place44629/A (BUF_X1)
    14   28.44    0.03    0.06    0.22 v place44629/Z (BUF_X1)
                                         net44629 (net)
                  0.03    0.00    0.22 v u_node_2/_36172_/A (INV_X1)
     8   25.60    0.06    0.08    0.30 ^ u_node_2/_36172_/ZN (INV_X1)
                                         u_node_2/_18576_ (net)
                  0.06    0.00    0.30 ^ u_node_2/_36173_/A2 (NOR2_X4)
...
                                  7.17   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_node_2/active_merged_value_q[12]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    7.96   library setup time
                                  7.96   data required time
-----------------------------------------------------------------------------
                                  7.96   data required time
                                 -7.17   data arrival time
-----------------------------------------------------------------------------
                                  0.79   slack (MET)



```
