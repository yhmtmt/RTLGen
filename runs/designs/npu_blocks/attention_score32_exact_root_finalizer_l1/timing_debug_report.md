# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l1`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l1/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7c17a985 | attention_score32_exact_root_finalizer_lane_firstpass_v1_7c17a985 | ok | 3.3946 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt` |
| 16461852 | attention_score32_exact_root_finalizer_lane_firstpass_v1_16461852 | ok | 3.4012 | 0.5 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3700`
- data_required_time: `0.3100`

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
     1   38.08    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
     1   27.09    0.01    0.02    0.03 ^ wire1745/Z (BUF_X8)
                                         net1745 (net)
                  0.01    0.01    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.02    0.02    0.05    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     4   31.18    0.03    0.06    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     2   19.76    0.02    0.05    0.21 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_15__leaf_clk (net)
                  0.02    0.00    0.26 ^ clkbuf_leaf_64_clk/A (CLKBUF_X3)
     8   10.33    0.01    0.04    0.31 ^ clkbuf_leaf_64_clk/Z (CLKBUF_X3)
                                         clknet_leaf_64_clk (net)
                  0.01    0.00    0.31 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.31   clock reconvergence pessimism
                          0.01    0.31   library hold time
                                  0.31   data required time
-----------------------------------------------------------------------------
                                  0.31   data required time
                                 -0.37   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `out_value_q[199]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5200`
- data_arrival_time: `2.0600`
- data_required_time: `0.5400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: out_value_q[199]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.58    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   55.03    0.03    0.05    2.05 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.03    0.01    2.06 ^ out_value_q[199]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   38.08    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
...
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_4_13__f_clk/A (CLKBUF_X3)
    10   29.51    0.02    0.06    0.27 ^ clkbuf_4_13__f_clk/Z (CLKBUF_X3)
                                         clknet_4_13__leaf_clk (net)
                  0.02    0.00    0.27 ^ clkbuf_leaf_85_clk/A (CLKBUF_X3)
     8   10.16    0.01    0.04    0.31 ^ clkbuf_leaf_85_clk/Z (CLKBUF_X3)
                                         clknet_leaf_85_clk (net)
                  0.01    0.00    0.31 ^ out_value_q[199]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.31   clock reconvergence pessimism
                          0.23    0.54   library removal time
                                  0.54   data required time
-----------------------------------------------------------------------------
                                  0.54   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.52   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `in_value[0] (input port clocked by clk)`
- endpoint: `lane_quotient_q[0][51]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `4.9000`
- data_arrival_time: `3.4000`
- data_required_time: `8.3000`

```text
Startpoint: in_value[0] (input port clocked by clk)
Endpoint: lane_quotient_q[0][51]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   10.90    0.00    0.00    2.00 v in_value[0] (in)
                                         in_value[0] (net)
                  0.00    0.00    2.00 v input61/A (BUF_X1)
     5   23.45    0.02    0.05    2.05 v input61/Z (BUF_X1)
                                         net61 (net)
                  0.02    0.00    2.05 v _06484_/A4 (OR4_X1)
     3    4.80    0.02    0.13    2.18 v _06484_/ZN (OR4_X1)
                                         _01680_ (net)
                  0.02    0.00    2.18 v _06553_/A3 (NOR3_X1)
     4    7.88    0.07    0.10    2.28 ^ _06553_/ZN (NOR3_X1)
                                         _01741_ (net)
                  0.07    0.00    2.28 ^ _06750_/A2 (NAND4_X1)
     5   19.35    0.07    0.11    2.40 v _06750_/ZN (NAND4_X1)
...
                                         clknet_4_7__leaf_clk (net)
                  0.04    0.01    8.29 ^ clkbuf_leaf_19_clk/A (CLKBUF_X3)
     8   10.95    0.01    0.05    8.34 ^ clkbuf_leaf_19_clk/Z (CLKBUF_X3)
                                         clknet_leaf_19_clk (net)
                  0.01    0.00    8.34 ^ lane_quotient_q[0][51]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.34   clock reconvergence pessimism
                         -0.04    8.30   library setup time
                                  8.30   data required time
-----------------------------------------------------------------------------
                                  8.30   data required time
                                 -3.40   data arrival time
-----------------------------------------------------------------------------
                                  4.90   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `input_value_q[267]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.5900`
- data_arrival_time: `2.7600`
- data_required_time: `8.3500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: input_value_q[267]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.58    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   55.03    0.03    0.05    2.05 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.06    0.04    2.09 ^ place1725/A (BUF_X2)
    15   46.24    0.05    0.08    2.17 ^ place1725/Z (BUF_X2)
                                         net1725 (net)
                  0.05    0.01    2.18 ^ place1726/A (BUF_X1)
     9   31.30    0.07    0.10    2.28 ^ place1726/Z (BUF_X1)
                                         net1726 (net)
                  0.07    0.01    2.28 ^ place1728/A (BUF_X1)
     1   22.94    0.05    0.08    2.36 ^ place1728/Z (BUF_X1)
...
                                         clknet_3_2_0_clk (net)
                  0.02    0.00    8.21 ^ clkbuf_4_4__f_clk/A (CLKBUF_X3)
    10   24.14    0.02    0.05    8.26 ^ clkbuf_4_4__f_clk/Z (CLKBUF_X3)
                                         clknet_4_4__leaf_clk (net)
                  0.02    0.00    8.26 ^ clkbuf_leaf_127_clk/A (CLKBUF_X3)
     8    9.58    0.01    0.04    8.30 ^ clkbuf_leaf_127_clk/Z (CLKBUF_X3)
                                         clknet_leaf_127_clk (net)
                  0.01    0.00    8.30 ^ input_value_q[267]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.30   clock reconvergence pessimism
                          0.05    8.35   library recovery time
                                  8.35   data required time
-----------------------------------------------------------------------------
                                  8.35   data required time
                                 -2.76   data arrival time
-----------------------------------------------------------------------------
                                  5.59   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `group_index_q[0]$_DFFE_PN0P_`
- endpoint: `lane_quotient_q[0][49]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `6.0200`
- data_arrival_time: `2.2900`
- data_required_time: `8.3100`

```text
Startpoint: group_index_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: lane_quotient_q[0][49]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.03    0.03 ^ wire1745/Z (BUF_X8)
   0.06    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.05    0.21 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
   0.07    0.28 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
   0.04    0.32 ^ clkbuf_leaf_50_clk/Z (CLKBUF_X3)
   0.00    0.32 ^ group_index_q[0]$_DFFE_PN0P_/CK (DFFR_X2)
   0.15    0.47 ^ group_index_q[0]$_DFFE_PN0P_/Q (DFFR_X2)
   0.05    0.52 ^ place1697/Z (BUF_X2)
   0.09    0.62 v _06464_/Z (MUX2_X1)
   0.04    0.66 v place1656/Z (BUF_X2)
   0.12    0.78 ^ _06465_/ZN (NOR2_X1)
...
   0.06    8.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    8.21 ^ clkbuf_3_3_0_clk/Z (CLKBUF_X3)
   0.08    8.28 ^ clkbuf_4_7__f_clk/Z (CLKBUF_X3)
   0.06    8.34 ^ clkbuf_leaf_20_clk/Z (CLKBUF_X3)
   0.00    8.34 ^ lane_quotient_q[0][49]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    8.34   clock reconvergence pessimism
  -0.03    8.31   library setup time
           8.31   data required time
---------------------------------------------------------
           8.31   data required time
          -2.29   data arrival time
---------------------------------------------------------
           6.02   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/2_floorplan_final.rpt`
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
                                         _05265_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_detailed_place.rpt`
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
                                         _05265_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_global_place.rpt`
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
                                         _05265_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/3_resizer.rpt`
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
                                         _05265_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4100`
- data_required_time: `0.3500`

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
     1   45.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
     1   36.67    0.01    0.03    0.04 ^ wire1745/Z (BUF_X8)
                                         net1745 (net)
                  0.01    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.42    0.03    0.06    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     4   43.64    0.03    0.07    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     2   23.68    0.02    0.06    0.24 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_15__leaf_clk (net)
                  0.02    0.00    0.30 ^ clkbuf_leaf_64_clk/A (CLKBUF_X3)
     8   10.20    0.01    0.04    0.34 ^ clkbuf_leaf_64_clk/Z (CLKBUF_X3)
                                         clknet_leaf_64_clk (net)
                  0.01    0.00    0.34 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.34   clock reconvergence pessimism
                          0.01    0.35   library hold time
                                  0.35   data required time
-----------------------------------------------------------------------------
                                  0.35   data required time
                                 -0.41   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4200`
- data_required_time: `0.3600`

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
     1   45.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
     1   36.43    0.01    0.03    0.04 ^ wire1745/Z (BUF_X8)
                                         net1745 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.90    0.03    0.06    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     4   43.72    0.03    0.07    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.19 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     2   23.61    0.02    0.06    0.24 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_15__leaf_clk (net)
                  0.02    0.00    0.30 ^ clkbuf_leaf_64_clk/A (CLKBUF_X3)
     8   10.49    0.01    0.04    0.35 ^ clkbuf_leaf_64_clk/Z (CLKBUF_X3)
                                         clknet_leaf_64_clk (net)
                  0.01    0.00    0.35 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.35   clock reconvergence pessimism
                          0.01    0.36   library hold time
                                  0.36   data required time
-----------------------------------------------------------------------------
                                  0.36   data required time
                                 -0.42   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3700`
- data_required_time: `0.3100`

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
     1   38.08    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
     1   27.09    0.01    0.02    0.03 ^ wire1745/Z (BUF_X8)
                                         net1745 (net)
                  0.01    0.01    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.02    0.02    0.05    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     4   31.18    0.03    0.06    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     2   19.76    0.02    0.05    0.21 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_15__leaf_clk (net)
                  0.02    0.00    0.26 ^ clkbuf_leaf_64_clk/A (CLKBUF_X3)
     8   10.33    0.01    0.04    0.31 ^ clkbuf_leaf_64_clk/Z (CLKBUF_X3)
                                         clknet_leaf_64_clk (net)
                  0.01    0.00    0.31 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.31   clock reconvergence pessimism
                          0.01    0.31   library hold time
                                  0.31   data required time
-----------------------------------------------------------------------------
                                  0.31   data required time
                                 -0.37   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `out_value_q[199]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4800`
- data_arrival_time: `2.0600`
- data_required_time: `0.5800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: out_value_q[199]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.35    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   48.93    0.03    0.05    2.05 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.03    0.01    2.06 ^ out_value_q[199]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1745/A (BUF_X8)
...
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.25 ^ clkbuf_4_13__f_clk/A (CLKBUF_X3)
    10   29.85    0.02    0.06    0.31 ^ clkbuf_4_13__f_clk/Z (CLKBUF_X3)
                                         clknet_4_13__leaf_clk (net)
                  0.03    0.00    0.31 ^ clkbuf_leaf_85_clk/A (CLKBUF_X3)
     8    9.84    0.01    0.04    0.35 ^ clkbuf_leaf_85_clk/Z (CLKBUF_X3)
                                         clknet_leaf_85_clk (net)
                  0.01    0.00    0.35 ^ out_value_q[199]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.35   clock reconvergence pessimism
                          0.23    0.58   library removal time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.48   slack (MET)
```
