# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7697f4c9 | attention_score32_exact_partial_pair_merge_sharedscale_mersenne_v1_7697f4c9 | ok | 7.2697 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5200`
- data_required_time: `0.4600`

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
     1   55.67    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire4584/A (BUF_X16)
     1   42.02    0.01    0.03    0.05 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.84    0.02    0.05    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   16.36    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   19.77    0.02    0.05    0.21 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_17_0_clk (net)
                  0.04    0.02    0.41 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.39    0.01    0.05    0.45 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.45 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.45   clock reconvergence pessimism
                          0.01    0.46   library hold time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `out_value_q[258]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `1.1200`
- data_arrival_time: `7.2700`
- data_required_time: `8.3900`

```text
Startpoint: active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[258]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   55.67    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire4584/A (BUF_X16)
     1   42.02    0.01    0.03    0.05 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.84    0.02    0.05    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   17.13    0.02    0.05    0.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     1   19.68    0.02    0.04    0.21 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_28_0_clk (net)
                  0.02    0.00    8.39 ^ clkbuf_leaf_237_clk/A (CLKBUF_X3)
     7    9.86    0.01    0.04    8.43 ^ clkbuf_leaf_237_clk/Z (CLKBUF_X3)
                                         clknet_leaf_237_clk (net)
                  0.01    0.00    8.43 ^ out_value_q[258]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.43   clock reconvergence pessimism
                         -0.04    8.39   library setup time
                                  8.39   data required time
-----------------------------------------------------------------------------
                                  8.39   data required time
                                 -7.27   data arrival time
-----------------------------------------------------------------------------
                                  1.12   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `left_value_hold_q[263]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3600`
- data_arrival_time: `2.0600`
- data_required_time: `0.6900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: left_value_hold_q[263]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   11.88    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
     8   38.43    0.03    0.05    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.03    0.00    2.06 ^ left_value_hold_q[263]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   55.67    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire4584/A (BUF_X16)
...
                                         clknet_4_5_0_clk (net)
                  0.02    0.00    0.33 ^ clkbuf_5_10_0_clk/A (CLKBUF_X3)
    22   66.92    0.05    0.08    0.41 ^ clkbuf_5_10_0_clk/Z (CLKBUF_X3)
                                         clknet_5_10_0_clk (net)
                  0.05    0.01    0.42 ^ clkbuf_leaf_133_clk/A (CLKBUF_X3)
     8   10.83    0.01    0.05    0.47 ^ clkbuf_leaf_133_clk/Z (CLKBUF_X3)
                                         clknet_leaf_133_clk (net)
                  0.01    0.00    0.47 ^ left_value_hold_q[263]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.47   clock reconvergence pessimism
                          0.22    0.69   library removal time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.36   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `out_value_q[95]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.4500`
- data_arrival_time: `3.0500`
- data_required_time: `8.5000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: out_value_q[95]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   11.88    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input842/A (CLKBUF_X3)
     8   38.43    0.03    0.05    2.05 ^ input842/Z (CLKBUF_X3)
                                         net842 (net)
                  0.04    0.02    2.07 ^ place4501/A (BUF_X2)
     3   36.22    0.03    0.05    2.12 ^ place4501/Z (BUF_X2)
                                         net4501 (net)
                  0.05    0.03    2.15 ^ place4555/A (BUF_X1)
    14   49.46    0.11    0.14    2.29 ^ place4555/Z (BUF_X1)
                                         net4555 (net)
                  0.11    0.02    2.31 ^ place4559/A (BUF_X1)
     1    1.48    0.01    0.03    2.34 ^ place4559/Z (BUF_X1)
...
                                         clknet_4_15_0_clk (net)
                  0.02    0.00    8.33 ^ clkbuf_5_30_0_clk/A (CLKBUF_X3)
    18   45.87    0.04    0.07    8.40 ^ clkbuf_5_30_0_clk/Z (CLKBUF_X3)
                                         clknet_5_30_0_clk (net)
                  0.04    0.00    8.40 ^ clkbuf_leaf_204_clk/A (CLKBUF_X3)
     7    9.40    0.01    0.05    8.45 ^ clkbuf_leaf_204_clk/Z (CLKBUF_X3)
                                         clknet_leaf_204_clk (net)
                  0.01    0.00    8.45 ^ out_value_q[95]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.45   clock reconvergence pessimism
                          0.05    8.50   library recovery time
                                  8.50   data required time
-----------------------------------------------------------------------------
                                  8.50   data required time
                                 -3.05   data arrival time
-----------------------------------------------------------------------------
                                  5.45   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/2_floorplan_final.rpt`
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
                                         _23629_ (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_detailed_place.rpt`
- stage: `detailed_place`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _23629_ (net)
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

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_global_place.rpt`
- stage: `global_place`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _23629_ (net)
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

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/3_resizer.rpt`
- stage: `resizer`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _23629_ (net)
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

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6000`
- data_required_time: `0.5400`

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
     1   76.59    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire4584/A (BUF_X16)
     1   59.25    0.01    0.03    0.06 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.51    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.62    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   27.20    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_17_0_clk (net)
                  0.05    0.02    0.49 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.45    0.01    0.05    0.53 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.53 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.53   clock reconvergence pessimism
                          0.01    0.54   library hold time
                                  0.54   data required time
-----------------------------------------------------------------------------
                                  0.54   data required time
                                 -0.60   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6100`
- data_required_time: `0.5500`

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
     1   76.29    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire4584/A (BUF_X16)
     1   59.11    0.01    0.03    0.06 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.03    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.60    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.80    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   27.12    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_17_0_clk (net)
                  0.05    0.02    0.49 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.45    0.01    0.05    0.54 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.54 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.54   clock reconvergence pessimism
                          0.01    0.55   library hold time
                                  0.55   data required time
-----------------------------------------------------------------------------
                                  0.55   data required time
                                 -0.61   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5200`
- data_required_time: `0.4600`

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
     1   55.67    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire4584/A (BUF_X16)
     1   42.02    0.01    0.03    0.05 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.84    0.02    0.05    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   16.36    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   19.77    0.02    0.05    0.21 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_17_0_clk (net)
                  0.04    0.02    0.41 ^ clkbuf_leaf_319_clk/A (CLKBUF_X3)
     7    9.39    0.01    0.05    0.45 ^ clkbuf_leaf_319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_319_clk (net)
                  0.01    0.00    0.45 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.45   clock reconvergence pessimism
                          0.01    0.46   library hold time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_pair_merge_sharedscale_factored_mersenne_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `active_lane_index_q[0]$_DFFE_PN0P_`
- endpoint: `out_value_q[217]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `1.1200`
- data_arrival_time: `7.3400`
- data_required_time: `8.4600`

```text
Startpoint: active_lane_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[217]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   76.29    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire4584/A (BUF_X16)
     1   59.11    0.01    0.03    0.06 ^ wire4584/Z (BUF_X16)
                                         net4584 (net)
                  0.03    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.60    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   22.77    0.02    0.05    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     1   27.25    0.02    0.05    0.26 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_28_0_clk (net)
                  0.03    0.00    8.46 ^ clkbuf_leaf_238_clk/A (CLKBUF_X3)
     7    9.70    0.01    0.04    8.50 ^ clkbuf_leaf_238_clk/Z (CLKBUF_X3)
                                         clknet_leaf_238_clk (net)
                  0.01    0.00    8.50 ^ out_value_q[217]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.50   clock reconvergence pessimism
                         -0.04    8.46   library setup time
                                  8.46   data required time
-----------------------------------------------------------------------------
                                  8.46   data required time
                                 -7.34   data arrival time
-----------------------------------------------------------------------------
                                  1.12   slack (MET)



```
