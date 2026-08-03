# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c4_r2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 401d35a8 | attention_score32_exact_partial_tree_folded_mersenne_cluster_v1_401d35a8 | ok | 7.7280 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_2/active_merged_value_q[80]$_DFFE_PN0P_`
- endpoint: `u_node_2/out_value_q[80]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.9000`
- data_required_time: `0.8400`

```text
Startpoint: u_node_2/active_merged_value_q[80]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/out_value_q[80]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire12357/A (BUF_X16)
     1   46.82    0.01    0.02    0.04 ^ wire12357/Z (BUF_X16)
                                         net12357 (net)
                  0.02    0.02    0.06 ^ wire12356/A (BUF_X16)
     1   46.10    0.01    0.02    0.09 ^ wire12356/Z (BUF_X16)
                                         net12356 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   31.18    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.25    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net12364 (net)
                  0.02    0.02    0.80 ^ clkbuf_leaf_1130_clk/A (CLKBUF_X3)
     7    8.74    0.01    0.04    0.84 ^ clkbuf_leaf_1130_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1130_clk (net)
                  0.01    0.00    0.84 ^ u_node_2/out_value_q[80]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.84   clock reconvergence pessimism
                          0.01    0.84   library hold time
                                  0.84   data required time
-----------------------------------------------------------------------------
                                  0.84   data required time
                                 -0.90   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_0/active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `u_node_0/active_merged_value_q[76]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9600`
- data_arrival_time: `7.7300`
- data_required_time: `8.6900`

```text
Startpoint: u_node_0/active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/active_merged_value_q[76]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire12357/A (BUF_X16)
     1   46.82    0.01    0.02    0.04 ^ wire12357/Z (BUF_X16)
                                         net12357 (net)
                  0.02    0.02    0.06 ^ wire12356/A (BUF_X16)
     1   46.10    0.01    0.02    0.09 ^ wire12356/Z (BUF_X16)
                                         net12356 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   31.18    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.25    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_119__leaf_clk (net)
                  0.02    0.00    8.69 ^ clkbuf_leaf_827_clk/A (CLKBUF_X3)
     8   10.95    0.01    0.04    8.73 ^ clkbuf_leaf_827_clk/Z (CLKBUF_X3)
                                         clknet_leaf_827_clk (net)
                  0.01    0.00    8.73 ^ u_node_0/active_merged_value_q[76]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.73   clock reconvergence pessimism
                         -0.04    8.69   library setup time
                                  8.69   data required time
-----------------------------------------------------------------------------
                                  8.69   data required time
                                 -7.73   data arrival time
-----------------------------------------------------------------------------
                                  0.96   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_2/out_value_q[113]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `0.9900`
- data_arrival_time: `2.0600`
- data_required_time: `1.0700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_2/out_value_q[113]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   17.81    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input1682/A (CLKBUF_X3)
     7   34.45    0.02    0.05    2.05 ^ input1682/Z (CLKBUF_X3)
                                         net1682 (net)
                  0.03    0.01    2.06 ^ u_node_2/out_value_q[113]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire12357/A (BUF_X16)
...
                                         net12361 (net)
                  0.02    0.02    0.76 ^ wire12360/A (BUF_X16)
    11   54.69    0.01    0.02    0.79 ^ wire12360/Z (BUF_X16)
                                         net12360 (net)
                  0.03    0.02    0.81 ^ clkbuf_leaf_1183_clk/A (CLKBUF_X3)
     6    9.94    0.01    0.04    0.85 ^ clkbuf_leaf_1183_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1183_clk (net)
                  0.01    0.00    0.85 ^ u_node_2/out_value_q[113]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.85   clock reconvergence pessimism
                          0.22    1.07   library removal time
                                  1.07   data required time
-----------------------------------------------------------------------------
                                  1.07   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  0.99   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_0/active_left_value_q[309]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `4.9100`
- data_arrival_time: `3.8500`
- data_required_time: `8.7600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_0/active_left_value_q[309]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   17.81    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input1682/A (CLKBUF_X3)
     7   34.45    0.02    0.05    2.05 ^ input1682/Z (CLKBUF_X3)
                                         net1682 (net)
                  0.03    0.02    2.07 ^ place12017/A (BUF_X2)
     8   29.00    0.03    0.05    2.12 ^ place12017/Z (BUF_X2)
                                         net12017 (net)
                  0.03    0.01    2.13 ^ place12018/A (BUF_X1)
     1   39.28    0.08    0.09    2.22 ^ place12018/Z (BUF_X1)
                                         net12018 (net)
                  0.09    0.04    2.26 ^ place12019/A (BUF_X1)
     4   39.47    0.08    0.11    2.37 ^ place12019/Z (BUF_X1)
...
                                         clknet_6_11_0_clk (net)
                  0.01    0.00    8.64 ^ clkbuf_7_23__f_clk/A (CLKBUF_X3)
     6   16.22    0.02    0.04    8.68 ^ clkbuf_7_23__f_clk/Z (CLKBUF_X3)
                                         clknet_7_23__leaf_clk (net)
                  0.02    0.00    8.68 ^ clkbuf_leaf_605_clk/A (CLKBUF_X3)
     6    8.74    0.01    0.04    8.72 ^ clkbuf_leaf_605_clk/Z (CLKBUF_X3)
                                         clknet_leaf_605_clk (net)
                  0.01    0.00    8.72 ^ u_node_0/active_left_value_q[309]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.72   clock reconvergence pessimism
                          0.04    8.76   library recovery time
                                  8.76   data required time
-----------------------------------------------------------------------------
                                  8.76   data required time
                                 -3.85   data arrival time
-----------------------------------------------------------------------------
                                  4.91   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_node_2/left_value_hold_q[85]$_DFFE_PN0P_`
- endpoint: `u_node_2/active_left_value_q[85]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `1.0000`
- data_required_time: `0.9700`

```text
Startpoint: u_node_2/left_value_hold_q[85]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/active_left_value_q[85]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   69.29    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire12357/A (BUF_X16)
     1   64.31    0.01    0.03    0.05 ^ wire12357/Z (BUF_X16)
                                         net12357 (net)
                  0.03    0.02    0.07 ^ wire12356/A (BUF_X16)
     1   67.70    0.01    0.03    0.10 ^ wire12356/Z (BUF_X16)
                                         net12356 (net)
                  0.03    0.03    0.13 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.74    0.03    0.07    0.20 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.15    0.02    0.06    0.26 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net12363 (net)
                  0.03    0.02    0.92 ^ clkbuf_leaf_415_clk/A (CLKBUF_X3)
     7    9.56    0.01    0.04    0.96 ^ clkbuf_leaf_415_clk/Z (CLKBUF_X3)
                                         clknet_leaf_415_clk (net)
                  0.01    0.00    0.96 ^ u_node_2/active_left_value_q[85]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.96   clock reconvergence pessimism
                          0.01    0.97   library hold time
                                  0.97   data required time
-----------------------------------------------------------------------------
                                  0.97   data required time
                                 -1.00   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_node_2/left_value_hold_q[85]$_DFFE_PN0P_`
- endpoint: `u_node_2/active_left_value_q[85]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0400`
- data_arrival_time: `1.0000`
- data_required_time: `0.9600`

```text
Startpoint: u_node_2/left_value_hold_q[85]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/active_left_value_q[85]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   69.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire12357/A (BUF_X16)
     1   64.36    0.01    0.03    0.05 ^ wire12357/Z (BUF_X16)
                                         net12357 (net)
                  0.03    0.02    0.07 ^ wire12356/A (BUF_X16)
     1   67.92    0.01    0.03    0.10 ^ wire12356/Z (BUF_X16)
                                         net12356 (net)
                  0.03    0.02    0.13 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.55    0.03    0.07    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.41    0.02    0.06    0.26 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net12363 (net)
                  0.02    0.02    0.91 ^ clkbuf_leaf_415_clk/A (CLKBUF_X3)
     7    9.34    0.01    0.04    0.96 ^ clkbuf_leaf_415_clk/Z (CLKBUF_X3)
                                         clknet_leaf_415_clk (net)
                  0.01    0.00    0.96 ^ u_node_2/active_left_value_q[85]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.96   clock reconvergence pessimism
                          0.01    0.96   library hold time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -1.00   data arrival time
-----------------------------------------------------------------------------
                                  0.04   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_2/active_merged_value_q[80]$_DFFE_PN0P_`
- endpoint: `u_node_2/out_value_q[80]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.9000`
- data_required_time: `0.8400`

```text
Startpoint: u_node_2/active_merged_value_q[80]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/out_value_q[80]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire12357/A (BUF_X16)
     1   46.82    0.01    0.02    0.04 ^ wire12357/Z (BUF_X16)
                                         net12357 (net)
                  0.02    0.02    0.06 ^ wire12356/A (BUF_X16)
     1   46.10    0.01    0.02    0.09 ^ wire12356/Z (BUF_X16)
                                         net12356 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   31.18    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.25    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net12364 (net)
                  0.02    0.02    0.80 ^ clkbuf_leaf_1130_clk/A (CLKBUF_X3)
     7    8.74    0.01    0.04    0.84 ^ clkbuf_leaf_1130_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1130_clk (net)
                  0.01    0.00    0.84 ^ u_node_2/out_value_q[80]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.84   clock reconvergence pessimism
                          0.01    0.84   library hold time
                                  0.84   data required time
-----------------------------------------------------------------------------
                                  0.84   data required time
                                 -0.90   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/2_floorplan_final.rpt`
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
                                         u_node_0/_23830_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_detailed_place.rpt`
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
                                         u_node_0/_23830_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_global_place.rpt`
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
                                         u_node_0/_23830_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_resizer.rpt`
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
                                         u_node_0/_23830_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c4_r2/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_node_0/active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `u_node_0/active_merged_value_q[76]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.7400`
- data_arrival_time: `7.2100`
- data_required_time: `7.9500`

```text
Startpoint: u_node_0/active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_0/active_merged_value_q[76]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_node_0/active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     6   17.44    0.02    0.11    0.11 v u_node_0/active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_node_0/active_lane_index_q[1] (net)
                  0.02    0.00    0.11 v u_node_0/_55509_/B (HA_X1)
    10   17.75    0.02    0.06    0.17 v u_node_0/_55509_/CO (HA_X1)
                                         u_node_0/_11821_ (net)
                  0.02    0.00    0.17 v u_node_0/_35655_/A (INV_X1)
    10   37.29    0.08    0.10    0.27 ^ u_node_0/_35655_/ZN (INV_X1)
                                         u_node_0/_17907_ (net)
                  0.08    0.00    0.27 ^ u_node_0/_35711_/A2 (NOR2_X4)
    13   41.84    0.03    0.03    0.30 v u_node_0/_35711_/ZN (NOR2_X4)
                                         u_node_0/_17962_ (net)
                  0.03    0.00    0.31 v place10329/A (BUF_X1)
...
                                  7.21   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_node_0/active_merged_value_q[76]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    7.95   library setup time
                                  7.95   data required time
-----------------------------------------------------------------------------
                                  7.95   data required time
                                 -7.21   data arrival time
-----------------------------------------------------------------------------
                                  0.74   slack (MET)



```
