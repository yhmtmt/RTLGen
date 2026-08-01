# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| d7c66d0e | attention_score32_exact_partial_pair_merge_sharedscale_v1_d7c66d0e | ok | 14.1763 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `active_merged_value_q[137]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.8200`
- data_arrival_time: `14.1800`
- data_required_time: `8.3500`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: active_merged_value_q[137]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire17203/A (BUF_X8)
     1   27.03    0.01    0.02    0.03 ^ wire17203/Z (BUF_X8)
                                         net17203 (net)
                  0.01    0.01    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.55    0.02    0.05    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.08    0.02    0.05    0.14 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   17.43    0.02    0.04    0.19 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.00    8.34 ^ clkbuf_leaf_168_clk/A (CLKBUF_X3)
     8   10.89    0.01    0.04    8.39 ^ clkbuf_leaf_168_clk/Z (CLKBUF_X3)
                                         clknet_leaf_168_clk (net)
                  0.01    0.00    8.39 ^ active_merged_value_q[137]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.39   clock reconvergence pessimism
                         -0.04    8.35   library setup time
                                  8.35   data required time
-----------------------------------------------------------------------------
                                  8.35   data required time
                                -14.18   data arrival time
-----------------------------------------------------------------------------
                                 -5.82   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5200`
- data_required_time: `0.4500`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire17203/A (BUF_X8)
     1   27.03    0.01    0.02    0.03 ^ wire17203/Z (BUF_X8)
                                         net17203 (net)
                  0.01    0.01    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.55    0.02    0.05    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   18.36    0.02    0.05    0.14 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   18.11    0.02    0.04    0.19 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_10__leaf_clk (net)
                  0.07    0.04    0.39 ^ clkbuf_leaf_20_clk/A (CLKBUF_X3)
     6   12.34    0.01    0.06    0.44 ^ clkbuf_leaf_20_clk/Z (CLKBUF_X3)
                                         clknet_leaf_20_clk (net)
                  0.01    0.00    0.45 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.45   clock reconvergence pessimism
                          0.01    0.45   library hold time
                                  0.45   data required time
-----------------------------------------------------------------------------
                                  0.45   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `out_exp_sum_q[19]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4100`
- data_arrival_time: `2.0900`
- data_required_time: `0.6800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: out_exp_sum_q[19]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.93    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
    11   61.92    0.03    0.05    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.07    0.05    2.09 ^ out_exp_sum_q[19]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire17203/A (BUF_X8)
...
                                         clknet_4_13_0_clk (net)
                  0.02    0.00    0.29 ^ clkbuf_5_26__f_clk/A (CLKBUF_X3)
    17   52.19    0.04    0.07    0.36 ^ clkbuf_5_26__f_clk/Z (CLKBUF_X3)
                                         clknet_5_26__leaf_clk (net)
                  0.04    0.00    0.36 ^ clkbuf_leaf_85_clk/A (CLKBUF_X3)
     5   12.37    0.01    0.05    0.41 ^ clkbuf_leaf_85_clk/Z (CLKBUF_X3)
                                         clknet_leaf_85_clk (net)
                  0.01    0.00    0.41 ^ out_exp_sum_q[19]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.27    0.68   library removal time
                                  0.68   data required time
-----------------------------------------------------------------------------
                                  0.68   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.41   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[31]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.2300`
- data_arrival_time: `3.1900`
- data_required_time: `8.4300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[31]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.93    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
    11   61.92    0.03    0.05    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.04    0.01    2.06 ^ place17092/A (BUF_X1)
     7   37.21    0.08    0.10    2.16 ^ place17092/Z (BUF_X1)
                                         net17092 (net)
                  0.08    0.02    2.18 ^ place17114/A (BUF_X1)
     7   20.08    0.05    0.08    2.26 ^ place17114/Z (BUF_X1)
                                         net17114 (net)
                  0.05    0.00    2.26 ^ place17116/A (BUF_X2)
     5   42.82    0.04    0.07    2.33 ^ place17116/Z (BUF_X2)
...
                                         clknet_4_2_0_clk (net)
                  0.01    0.00    8.28 ^ clkbuf_5_5__f_clk/A (CLKBUF_X3)
    14   35.86    0.03    0.06    8.34 ^ clkbuf_5_5__f_clk/Z (CLKBUF_X3)
                                         clknet_5_5__leaf_clk (net)
                  0.03    0.00    8.34 ^ clkbuf_leaf_246_clk/A (CLKBUF_X3)
     8   10.34    0.01    0.04    8.38 ^ clkbuf_leaf_246_clk/Z (CLKBUF_X3)
                                         clknet_leaf_246_clk (net)
                  0.01    0.00    8.38 ^ completed_count[31]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.38   clock reconvergence pessimism
                          0.04    8.43   library recovery time
                                  8.43   data required time
-----------------------------------------------------------------------------
                                  8.43   data required time
                                 -3.19   data arrival time
-----------------------------------------------------------------------------
                                  5.23   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `out_value_q[205]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.2400`
- data_arrival_time: `14.2000`
- data_required_time: `7.9600`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[205]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.43    0.01    0.09    0.09 v active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         active_lane_index_q[1] (net)
                  0.01    0.00    0.09 v place17067/A (BUF_X1)
     2    4.42    0.01    0.03    0.12 v place17067/Z (BUF_X1)
                                         net17067 (net)
                  0.01    0.00    0.12 v _66186_/A (HA_X1)
     2    6.91    0.01    0.04    0.16 v _66186_/CO (HA_X1)
                                         _11206_ (net)
                  0.01    0.00    0.16 v _37241_/A (INV_X4)
     2    8.13    0.01    0.01    0.17 ^ _37241_/ZN (INV_X4)
                                         _14977_ (net)
                  0.01    0.00    0.17 ^ place16648/A (BUF_X1)
...
                                 14.20   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ out_value_q[205]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    7.96   library setup time
                                  7.96   data required time
-----------------------------------------------------------------------------
                                  7.96   data required time
                                -14.20   data arrival time
-----------------------------------------------------------------------------
                                 -6.24   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `out_value_q[205]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.2400`
- data_arrival_time: `14.2000`
- data_required_time: `7.9600`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[205]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.43    0.01    0.09    0.09 v active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         active_lane_index_q[1] (net)
                  0.01    0.00    0.09 v place17067/A (BUF_X1)
     2    4.42    0.01    0.03    0.12 v place17067/Z (BUF_X1)
                                         net17067 (net)
                  0.01    0.00    0.12 v _66186_/A (HA_X1)
     2    6.91    0.01    0.04    0.16 v _66186_/CO (HA_X1)
                                         _11206_ (net)
                  0.01    0.00    0.16 v _37241_/A (INV_X4)
     2    8.13    0.01    0.01    0.17 ^ _37241_/ZN (INV_X4)
                                         _14977_ (net)
                  0.01    0.00    0.17 ^ place16648/A (BUF_X1)
...
                                 14.20   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ out_value_q[205]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    7.96   library setup time
                                  7.96   data required time
-----------------------------------------------------------------------------
                                  7.96   data required time
                                -14.20   data arrival time
-----------------------------------------------------------------------------
                                 -6.24   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `out_value_q[12]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.1800`
- data_arrival_time: `14.1500`
- data_required_time: `7.9700`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[12]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     6   11.42    0.02    0.10    0.10 v active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         active_lane_index_q[1] (net)
                  0.02    0.00    0.10 v _66188_/A (HA_X1)
     2    6.11    0.01    0.04    0.14 v _66188_/CO (HA_X1)
                                         _36652_ (net)
                  0.01    0.00    0.14 v _66189_/A (HA_X1)
     4    8.68    0.01    0.04    0.18 v _66189_/CO (HA_X1)
                                         _11209_ (net)
                  0.01    0.00    0.18 v _37255_/A (BUF_X4)
    10   19.32    0.01    0.03    0.21 v _37255_/Z (BUF_X4)
                                         _14991_ (net)
                  0.01    0.00    0.21 v _37256_/A (BUF_X8)
...
                                 14.15   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ out_value_q[12]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.03    7.97   library setup time
                                  7.97   data required time
-----------------------------------------------------------------------------
                                  7.97   data required time
                                -14.15   data arrival time
-----------------------------------------------------------------------------
                                 -6.18   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `out_value_q[205]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-6.1500`
- data_arrival_time: `14.1000`
- data_required_time: `7.9600`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[205]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ active_lane_index_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.24    0.01    0.09    0.09 v active_lane_index_q[1]$_DFFE_PN0P_/Q (DFFR_X1)
                                         active_lane_index_q[1] (net)
                  0.01    0.00    0.09 v place17067/A (BUF_X1)
     2    4.19    0.01    0.03    0.12 v place17067/Z (BUF_X1)
                                         net17067 (net)
                  0.01    0.00    0.12 v _66186_/A (HA_X1)
     2    6.86    0.01    0.04    0.16 v _66186_/CO (HA_X1)
                                         _11206_ (net)
                  0.01    0.00    0.16 v _37241_/A (INV_X4)
     2    8.08    0.01    0.01    0.17 ^ _37241_/ZN (INV_X4)
                                         _14977_ (net)
                  0.01    0.00    0.17 ^ place16648/A (BUF_X1)
...
                                 14.10   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ out_value_q[205]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    7.96   library setup time
                                  7.96   data required time
-----------------------------------------------------------------------------
                                  7.96   data required time
                                -14.10   data arrival time
-----------------------------------------------------------------------------
                                 -6.15   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `active_merged_value_q[126]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.9000`
- data_arrival_time: `14.3100`
- data_required_time: `8.4100`

```text
Startpoint: active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: active_merged_value_q[126]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.21    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire17203/A (BUF_X8)
     1   41.05    0.01    0.03    0.04 ^ wire17203/Z (BUF_X8)
                                         net17203 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.56    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.63    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   24.21    0.02    0.05    0.23 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.00    8.40 ^ clkbuf_leaf_170_clk/A (CLKBUF_X3)
     8   10.10    0.01    0.04    8.44 ^ clkbuf_leaf_170_clk/Z (CLKBUF_X3)
                                         clknet_leaf_170_clk (net)
                  0.01    0.00    8.44 ^ active_merged_value_q[126]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.44   clock reconvergence pessimism
                         -0.04    8.41   library setup time
                                  8.41   data required time
-----------------------------------------------------------------------------
                                  8.41   data required time
                                -14.31   data arrival time
-----------------------------------------------------------------------------
                                 -5.90   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `active_merged_value_q[137]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.8200`
- data_arrival_time: `14.1800`
- data_required_time: `8.3500`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: active_merged_value_q[137]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire17203/A (BUF_X8)
     1   27.03    0.01    0.02    0.03 ^ wire17203/Z (BUF_X8)
                                         net17203 (net)
                  0.01    0.01    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.55    0.02    0.05    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.08    0.02    0.05    0.14 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   17.43    0.02    0.04    0.19 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.00    8.34 ^ clkbuf_leaf_168_clk/A (CLKBUF_X3)
     8   10.89    0.01    0.04    8.39 ^ clkbuf_leaf_168_clk/Z (CLKBUF_X3)
                                         clknet_leaf_168_clk (net)
                  0.01    0.00    8.39 ^ active_merged_value_q[137]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.39   clock reconvergence pessimism
                         -0.04    8.35   library setup time
                                  8.35   data required time
-----------------------------------------------------------------------------
                                  8.35   data required time
                                -14.18   data arrival time
-----------------------------------------------------------------------------
                                 -5.82   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `active_lane_index_q[1]$_DFFE_PN0P_`
- endpoint: `active_merged_value_q[137]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-5.8000`
- data_arrival_time: `14.2200`
- data_required_time: `8.4100`

```text
Startpoint: active_lane_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: active_merged_value_q[137]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.86    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire17203/A (BUF_X8)
     1   41.16    0.01    0.03    0.04 ^ wire17203/Z (BUF_X8)
                                         net17203 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   43.01    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.81    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   24.54    0.02    0.05    0.23 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.00    8.41 ^ clkbuf_leaf_168_clk/A (CLKBUF_X3)
     8   10.94    0.01    0.04    8.45 ^ clkbuf_leaf_168_clk/Z (CLKBUF_X3)
                                         clknet_leaf_168_clk (net)
                  0.01    0.00    8.45 ^ active_merged_value_q[137]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.45   clock reconvergence pessimism
                         -0.04    8.41   library setup time
                                  8.41   data required time
-----------------------------------------------------------------------------
                                  8.41   data required time
                                -14.22   data arrival time
-----------------------------------------------------------------------------
                                 -5.80   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_l1/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _29571_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```
