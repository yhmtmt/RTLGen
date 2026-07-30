# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 16461852 | attention_score32_exact_root_finalizer_lane_firstpass_v1_16461852 | ok | 3.4594 | 0.5 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt` |
| 7c17a985 | attention_score32_exact_root_finalizer_lane_firstpass_v1_7c17a985 | ok | 3.4877 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3900`
- data_required_time: `0.3300`

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
     1   43.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   33.68    0.03    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.08 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   30.60    0.02    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.14 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   43.32    0.03    0.07    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.03    0.00    0.21 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    10   33.24    0.03    0.06    0.27 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.01    0.28 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7    9.06    0.01    0.04    0.32 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.32 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.32   clock reconvergence pessimism
                          0.01    0.33   library hold time
                                  0.33   data required time
-----------------------------------------------------------------------------
                                  0.33   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accepted_count[4]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4800`
- data_arrival_time: `2.0700`
- data_required_time: `0.5900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accepted_count[4]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   13.87    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
    19   54.95    0.04    0.07    2.07 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.00    2.07 ^ accepted_count[4]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   43.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
    19   72.12    0.05    0.09    0.29 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
                                         clknet_4_11_0_clk (net)
                  0.06    0.01    0.30 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     8   10.88    0.01    0.05    0.35 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.35 ^ accepted_count[4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.35   clock reconvergence pessimism
                          0.24    0.59   library removal time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.48   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `in_value[5] (input port clocked by clk)`
- endpoint: `lane_quotient_q[0][54]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `4.8100`
- data_arrival_time: `3.4600`
- data_required_time: `8.2700`

```text
Startpoint: in_value[5] (input port clocked by clk)
Endpoint: lane_quotient_q[0][54]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    5.10    0.00    0.00    2.00 v in_value[5] (in)
                                         in_value[5] (net)
                  0.00    0.00    2.00 v input344/A (BUF_X1)
     2    3.78    0.01    0.03    2.03 v input344/Z (BUF_X1)
                                         net344 (net)
                  0.01    0.00    2.03 v _10033_/A4 (OR4_X1)
     3    4.19    0.02    0.12    2.15 v _10033_/ZN (OR4_X1)
                                         _03228_ (net)
                  0.02    0.00    2.15 v _10062_/A4 (OR4_X1)
     1    1.81    0.02    0.12    2.27 v _10062_/ZN (OR4_X1)
                                         _03251_ (net)
                  0.02    0.00    2.27 v place1546/A (BUF_X2)
     4   42.92    0.02    0.04    2.31 v place1546/Z (BUF_X2)
...
                                         clknet_4_3_0_clk (net)
                  0.03    0.00    8.27 ^ clkbuf_leaf_40_clk/A (CLKBUF_X3)
     6    8.40    0.01    0.04    8.31 ^ clkbuf_leaf_40_clk/Z (CLKBUF_X3)
                                         clknet_leaf_40_clk (net)
                  0.01    0.00    8.31 ^ lane_quotient_q[0][54]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.31   clock reconvergence pessimism
                         -0.04    8.27   library setup time
                                  8.27   data required time
-----------------------------------------------------------------------------
                                  8.27   data required time
                                 -3.46   data arrival time
-----------------------------------------------------------------------------
                                  4.81   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `input_value_q[111]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.6900`
- data_arrival_time: `2.6200`
- data_required_time: `8.3100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: input_value_q[111]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   13.87    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
    19   54.95    0.04    0.07    2.07 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.01    2.08 ^ place1585/A (BUF_X1)
     5   27.96    0.06    0.09    2.17 ^ place1585/Z (BUF_X1)
                                         net1585 (net)
                  0.06    0.01    2.18 ^ place1603/A (BUF_X2)
    11   49.56    0.05    0.07    2.25 ^ place1603/Z (BUF_X2)
                                         net1603 (net)
                  0.06    0.02    2.27 ^ place1616/A (BUF_X1)
     2   24.89    0.05    0.08    2.35 ^ place1616/Z (BUF_X1)
...
                                         clknet_2_1_0_clk (net)
                  0.02    0.00    8.18 ^ clkbuf_4_4_0_clk/A (CLKBUF_X3)
     7   17.87    0.02    0.05    8.23 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
                                         clknet_4_4_0_clk (net)
                  0.02    0.00    8.23 ^ clkbuf_leaf_2_clk/A (CLKBUF_X3)
     7    8.37    0.01    0.04    8.27 ^ clkbuf_leaf_2_clk/Z (CLKBUF_X3)
                                         clknet_leaf_2_clk (net)
                  0.01    0.00    8.27 ^ input_value_q[111]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.27   clock reconvergence pessimism
                          0.04    8.31   library recovery time
                                  8.31   data required time
-----------------------------------------------------------------------------
                                  8.31   data required time
                                 -2.62   data arrival time
-----------------------------------------------------------------------------
                                  5.69   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `group_index_q[1]$_DFFE_PN0P_`
- endpoint: `lane_quotient_q[1][40]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `6.0000`
- data_arrival_time: `2.2800`
- data_required_time: `8.2800`

```text
Startpoint: group_index_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: lane_quotient_q[1][40]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.07    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.09    0.29 ^ clkbuf_4_15_0_clk/Z (CLKBUF_X3)
   0.05    0.35 ^ clkbuf_leaf_113_clk/Z (CLKBUF_X3)
   0.00    0.35 ^ group_index_q[1]$_DFFE_PN0P_/CK (DFFR_X2)
   0.16    0.50 ^ group_index_q[1]$_DFFE_PN0P_/Q (DFFR_X2)
   0.05    0.55 ^ place1567/Z (BUF_X2)
   0.10    0.65 ^ place1569/Z (BUF_X1)
   0.11    0.75 ^ place1570/Z (BUF_X2)
   0.07    0.83 v _09587_/Z (MUX2_X1)
   0.02    0.85 ^ _09588_/ZN (NAND2_X1)
...
   0.06    8.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.07    8.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.07    8.27 ^ clkbuf_4_12_0_clk/Z (CLKBUF_X3)
   0.05    8.32 ^ clkbuf_leaf_43_clk/Z (CLKBUF_X3)
   0.00    8.32 ^ lane_quotient_q[1][40]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    8.32   clock reconvergence pessimism
  -0.04    8.28   library setup time
           8.28   data required time
---------------------------------------------------------
           8.28   data required time
          -2.28   data arrival time
---------------------------------------------------------
           6.00   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/2_floorplan_final.rpt`
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
                                         _08195_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_detailed_place.rpt`
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
                                         _08195_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_global_place.rpt`
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
                                         _08195_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/3_resizer.rpt`
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
                                         _08195_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4300`
- data_required_time: `0.3700`

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
     1   62.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.47    0.03    0.07    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   38.06    0.03    0.07    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   52.17    0.04    0.08    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.04    0.00    0.24 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    10   38.90    0.03    0.07    0.31 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.01    0.32 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7    8.80    0.01    0.04    0.36 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.36 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4300`
- data_required_time: `0.3700`

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
     1   62.52    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   45.31    0.04    0.07    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.01    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   37.88    0.03    0.07    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   51.94    0.04    0.08    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.04    0.01    0.25 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    10   38.82    0.03    0.07    0.31 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.01    0.32 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7    9.15    0.01    0.04    0.36 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.36 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3900`
- data_required_time: `0.3300`

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
     1   43.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   33.68    0.03    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.08 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   30.60    0.02    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.14 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   43.32    0.03    0.07    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.03    0.00    0.21 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    10   33.24    0.03    0.06    0.27 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.01    0.28 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7    9.06    0.01    0.04    0.32 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.32 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.32   clock reconvergence pessimism
                          0.01    0.33   library hold time
                                  0.33   data required time
-----------------------------------------------------------------------------
                                  0.33   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `command_id_q[10]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4400`
- data_arrival_time: `2.0800`
- data_required_time: `0.6400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: command_id_q[10]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   17.07    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
    19   61.23    0.05    0.07    2.08 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.05    0.00    2.08 ^ command_id_q[10]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   62.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_3_0_clk (net)
                  0.04    0.00    0.24 ^ clkbuf_4_15_0_clk/A (CLKBUF_X3)
    11   73.07    0.06    0.10    0.34 ^ clkbuf_4_15_0_clk/Z (CLKBUF_X3)
                                         clknet_4_15_0_clk (net)
                  0.06    0.01    0.35 ^ clkbuf_leaf_80_clk/A (CLKBUF_X3)
     5    7.91    0.01    0.05    0.39 ^ clkbuf_leaf_80_clk/Z (CLKBUF_X3)
                                         clknet_leaf_80_clk (net)
                  0.01    0.00    0.39 ^ command_id_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.24    0.64   library removal time
                                  0.64   data required time
-----------------------------------------------------------------------------
                                  0.64   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.44   slack (MET)
```
