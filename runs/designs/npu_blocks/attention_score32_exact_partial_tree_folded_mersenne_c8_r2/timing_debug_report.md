# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c8_r2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 401d35a8 | attention_score32_exact_partial_tree_folded_mersenne_cluster_v1_401d35a8 | ok | 7.7750 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_3/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_3/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.8600`
- data_required_time: `0.8000`

```text
Startpoint: u_node_3/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_3/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.11    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire22528/A (BUF_X8)
     1   43.70    0.01    0.03    0.04 ^ wire22528/Z (BUF_X8)
                                         net22528 (net)
                  0.02    0.02    0.06 ^ wire22527/A (BUF_X16)
     1   53.90    0.01    0.02    0.08 ^ wire22527/Z (BUF_X16)
                                         net22527 (net)
                  0.03    0.02    0.10 ^ wire22526/A (BUF_X16)
     1   48.61    0.01    0.03    0.13 ^ wire22526/Z (BUF_X16)
                                         net22526 (net)
                  0.02    0.02    0.15 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   16.22    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_8_112_0_clk (net)
                  0.02    0.00    0.76 ^ clkbuf_leaf_2673_clk/A (CLKBUF_X3)
     7    8.44    0.01    0.04    0.79 ^ clkbuf_leaf_2673_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2673_clk (net)
                  0.01    0.00    0.79 ^ u_node_3/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.79   clock reconvergence pessimism
                          0.01    0.80   library hold time
                                  0.80   data required time
-----------------------------------------------------------------------------
                                  0.80   data required time
                                 -0.86   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_6/active_lane_index_q[2]$_DFFE_PN0P_`
- endpoint: `u_node_6/active_merged_value_q[224]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `1.0300`
- data_arrival_time: `7.7800`
- data_required_time: `8.8000`

```text
Startpoint: u_node_6/active_lane_index_q[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_6/active_merged_value_q[224]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.11    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire22528/A (BUF_X8)
     1   43.70    0.01    0.03    0.04 ^ wire22528/Z (BUF_X8)
                                         net22528 (net)
                  0.02    0.02    0.06 ^ wire22527/A (BUF_X16)
     1   53.90    0.01    0.02    0.08 ^ wire22527/Z (BUF_X16)
                                         net22527 (net)
                  0.03    0.02    0.10 ^ wire22526/A (BUF_X16)
     1   48.61    0.01    0.03    0.13 ^ wire22526/Z (BUF_X16)
                                         net22526 (net)
                  0.02    0.02    0.15 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   16.22    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_8_213_0_clk (net)
                  0.05    0.02    8.80 ^ clkbuf_leaf_2221_clk/A (CLKBUF_X3)
     7    8.82    0.01    0.05    8.85 ^ clkbuf_leaf_2221_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2221_clk (net)
                  0.01    0.00    8.85 ^ u_node_6/active_merged_value_q[224]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.85   clock reconvergence pessimism
                         -0.04    8.80   library setup time
                                  8.80   data required time
-----------------------------------------------------------------------------
                                  8.80   data required time
                                 -7.78   data arrival time
-----------------------------------------------------------------------------
                                  1.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_4/completed_count[26]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.0400`
- data_arrival_time: `2.2100`
- data_required_time: `1.1700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_4/completed_count[26]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   24.10    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input3362/A (CLKBUF_X3)
     3   43.29    0.02    0.05    2.06 ^ input3362/Z (CLKBUF_X3)
                                         net3362 (net)
                  0.05    0.03    2.09 ^ place21710/A (BUF_X1)
    18   38.91    0.09    0.12    2.21 ^ place21710/Z (BUF_X1)
                                         net21710 (net)
                  0.09    0.00    2.21 ^ u_node_4/completed_count[26]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.21   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_8_119_0_clk (net)
                  0.03    0.01    0.80 ^ wire22529/A (BUF_X8)
     2   30.17    0.01    0.03    0.83 ^ wire22529/Z (BUF_X8)
                                         net22529 (net)
                  0.01    0.01    0.84 ^ clkbuf_leaf_2636_clk/A (CLKBUF_X3)
     7    9.44    0.01    0.04    0.88 ^ clkbuf_leaf_2636_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2636_clk (net)
                  0.01    0.00    0.88 ^ u_node_4/completed_count[26]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.88   clock reconvergence pessimism
                          0.29    1.17   library removal time
                                  1.17   data required time
-----------------------------------------------------------------------------
                                  1.17   data required time
                                 -2.21   data arrival time
-----------------------------------------------------------------------------
                                  1.04   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_0/right_value_hold_q[81]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `4.8500`
- data_arrival_time: `3.9900`
- data_required_time: `8.8400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_0/right_value_hold_q[81]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   24.10    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input3362/A (CLKBUF_X3)
     3   43.29    0.02    0.05    2.06 ^ input3362/Z (CLKBUF_X3)
                                         net3362 (net)
                  0.06    0.04    2.10 ^ place21735/A (BUF_X1)
     1    6.20    0.02    0.04    2.14 ^ place21735/Z (BUF_X1)
                                         net21735 (net)
                  0.02    0.00    2.14 ^ place21736/A (BUF_X1)
    13   38.51    0.09    0.11    2.25 ^ place21736/Z (BUF_X1)
                                         net21736 (net)
                  0.09    0.01    2.26 ^ load_slew22525/A (BUF_X4)
     2   28.48    0.01    0.04    2.30 ^ load_slew22525/Z (BUF_X4)
...
                                         clknet_6_42_0_clk (net)
                  0.02    0.00    8.70 ^ clkbuf_8_170_0_clk/A (CLKBUF_X3)
    13   30.80    0.03    0.06    8.76 ^ clkbuf_8_170_0_clk/Z (CLKBUF_X3)
                                         clknet_8_170_0_clk (net)
                  0.03    0.00    8.76 ^ clkbuf_leaf_1341_clk/A (CLKBUF_X3)
     6    8.38    0.01    0.04    8.80 ^ clkbuf_leaf_1341_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1341_clk (net)
                  0.01    0.00    8.80 ^ u_node_0/right_value_hold_q[81]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.80   clock reconvergence pessimism
                          0.05    8.84   library recovery time
                                  8.84   data required time
-----------------------------------------------------------------------------
                                  8.84   data required time
                                 -3.99   data arrival time
-----------------------------------------------------------------------------
                                  4.85   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/2_floorplan_final.rpt`
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
                                         u_node_0/_23356_ (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_detailed_place.rpt`
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
                                         u_node_0/_23356_ (net)
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

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_global_place.rpt`
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
                                         u_node_0/_23356_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/3_resizer.rpt`
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
                                         u_node_0/_23356_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_node_2/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_2/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.9900`
- data_required_time: `0.9300`

```text
Startpoint: u_node_2/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   57.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire22528/A (BUF_X8)
     1   58.49    0.01    0.03    0.05 ^ wire22528/Z (BUF_X8)
                                         net22528 (net)
                  0.03    0.02    0.07 ^ wire22527/A (BUF_X16)
     1   72.87    0.01    0.03    0.10 ^ wire22527/Z (BUF_X16)
                                         net22527 (net)
                  0.03    0.03    0.12 ^ wire22526/A (BUF_X16)
     1   68.02    0.01    0.03    0.15 ^ wire22526/Z (BUF_X16)
                                         net22526 (net)
                  0.03    0.02    0.18 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.90    0.02    0.05    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_8_115_0_clk (net)
                  0.02    0.00    0.88 ^ clkbuf_leaf_2660_clk/A (CLKBUF_X3)
     4    8.48    0.01    0.04    0.92 ^ clkbuf_leaf_2660_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2660_clk (net)
                  0.01    0.00    0.92 ^ u_node_2/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.92   clock reconvergence pessimism
                          0.01    0.93   library hold time
                                  0.93   data required time
-----------------------------------------------------------------------------
                                  0.93   data required time
                                 -0.99   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_node_2/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_2/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.9900`
- data_required_time: `0.9300`

```text
Startpoint: u_node_2/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_2/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   57.27    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire22528/A (BUF_X8)
     1   58.46    0.01    0.03    0.05 ^ wire22528/Z (BUF_X8)
                                         net22528 (net)
                  0.03    0.02    0.07 ^ wire22527/A (BUF_X16)
     1   72.59    0.01    0.03    0.09 ^ wire22527/Z (BUF_X16)
                                         net22527 (net)
                  0.04    0.03    0.12 ^ wire22526/A (BUF_X16)
     1   67.69    0.01    0.03    0.15 ^ wire22526/Z (BUF_X16)
                                         net22526 (net)
                  0.03    0.03    0.18 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   23.02    0.02    0.05    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_8_115_0_clk (net)
                  0.02    0.00    0.88 ^ clkbuf_leaf_2660_clk/A (CLKBUF_X3)
     4    8.57    0.01    0.04    0.92 ^ clkbuf_leaf_2660_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2660_clk (net)
                  0.01    0.00    0.92 ^ u_node_2/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.92   clock reconvergence pessimism
                          0.01    0.93   library hold time
                                  0.93   data required time
-----------------------------------------------------------------------------
                                  0.93   data required time
                                 -0.99   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_node_3/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_node_3/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.8600`
- data_required_time: `0.8000`

```text
Startpoint: u_node_3/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_node_3/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.11    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire22528/A (BUF_X8)
     1   43.70    0.01    0.03    0.04 ^ wire22528/Z (BUF_X8)
                                         net22528 (net)
                  0.02    0.02    0.06 ^ wire22527/A (BUF_X16)
     1   53.90    0.01    0.02    0.08 ^ wire22527/Z (BUF_X16)
                                         net22527 (net)
                  0.03    0.02    0.10 ^ wire22526/A (BUF_X16)
     1   48.61    0.01    0.03    0.13 ^ wire22526/Z (BUF_X16)
                                         net22526 (net)
                  0.02    0.02    0.15 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   16.22    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_8_112_0_clk (net)
                  0.02    0.00    0.76 ^ clkbuf_leaf_2673_clk/A (CLKBUF_X3)
     7    8.44    0.01    0.04    0.79 ^ clkbuf_leaf_2673_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2673_clk (net)
                  0.01    0.00    0.79 ^ u_node_3/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.79   clock reconvergence pessimism
                          0.01    0.80   library hold time
                                  0.80   data required time
-----------------------------------------------------------------------------
                                  0.80   data required time
                                 -0.86   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_tree_folded_mersenne_c8_r2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_node_4/completed_count[26]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `0.8800`
- data_arrival_time: `2.2100`
- data_required_time: `1.3300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_node_4/completed_count[26]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   25.05    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input3362/A (CLKBUF_X3)
     3   41.56    0.02    0.05    2.06 ^ input3362/Z (CLKBUF_X3)
                                         net3362 (net)
                  0.05    0.03    2.09 ^ place21710/A (BUF_X1)
    18   40.32    0.09    0.12    2.21 ^ place21710/Z (BUF_X1)
                                         net21710 (net)
                  0.09    0.00    2.21 ^ u_node_4/completed_count[26]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.21   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_8_119_0_clk (net)
                  0.05    0.02    0.95 ^ wire22529/A (BUF_X8)
     2   44.94    0.01    0.03    0.98 ^ wire22529/Z (BUF_X8)
                                         net22529 (net)
                  0.02    0.01    1.00 ^ clkbuf_leaf_2636_clk/A (CLKBUF_X3)
     7    9.38    0.01    0.04    1.04 ^ clkbuf_leaf_2636_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2636_clk (net)
                  0.01    0.00    1.04 ^ u_node_4/completed_count[26]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.04   clock reconvergence pessimism
                          0.30    1.33   library removal time
                                  1.33   data required time
-----------------------------------------------------------------------------
                                  1.33   data required time
                                 -2.21   data arrival time
-----------------------------------------------------------------------------
                                  0.88   slack (MET)
```
