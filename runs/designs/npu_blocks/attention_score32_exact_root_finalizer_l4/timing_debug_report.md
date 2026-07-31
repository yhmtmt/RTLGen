# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l4`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l4/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7c17a985 | attention_score32_exact_root_finalizer_lane_firstpass_v1_7c17a985 | ok | 3.4669 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt` |
| 16461852 | attention_score32_exact_root_finalizer_lane_firstpass_v1_16461852 | ok | 3.4750 | 0.5 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3500`
- data_required_time: `0.2900`

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
     1   46.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.82    0.02    0.05    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.07 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   32.25    0.03    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     4   31.43    0.03    0.06    0.19 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     8   20.06    0.02    0.05    0.24 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.25 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     7    8.95    0.01    0.04    0.28 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    0.28 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.28   clock reconvergence pessimism
                          0.01    0.29   library hold time
                                  0.29   data required time
-----------------------------------------------------------------------------
                                  0.29   data required time
                                 -0.35   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[29]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4900`
- data_arrival_time: `2.0700`
- data_required_time: `0.5800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[29]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.60    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   54.38    0.04    0.06    2.06 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.00    2.07 ^ completed_count[29]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   46.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_1_0_clk (net)
                  0.03    0.01    0.20 ^ clkbuf_4_6_0_clk/A (CLKBUF_X3)
     9   55.93    0.04    0.08    0.27 ^ clkbuf_4_6_0_clk/Z (CLKBUF_X3)
                                         clknet_4_6_0_clk (net)
                  0.05    0.02    0.30 ^ clkbuf_leaf_58_clk/A (CLKBUF_X3)
     6    7.69    0.01    0.05    0.34 ^ clkbuf_leaf_58_clk/Z (CLKBUF_X3)
                                         clknet_leaf_58_clk (net)
                  0.01    0.00    0.34 ^ completed_count[29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.34   clock reconvergence pessimism
                          0.23    0.58   library removal time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.49   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `in_value[135] (input port clocked by clk)`
- endpoint: `lane_quotient_q[3][51]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `4.7900`
- data_arrival_time: `3.4700`
- data_required_time: `8.2700`

```text
Startpoint: in_value[135] (input port clocked by clk)
Endpoint: lane_quotient_q[3][51]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    5.27    0.00    0.00    2.00 v in_value[135] (in)
                                         in_value[135] (net)
                  0.00    0.00    2.00 v input100/A (BUF_X1)
     2    3.87    0.01    0.03    2.03 v input100/Z (BUF_X1)
                                         net100 (net)
                  0.01    0.00    2.03 v _14296_/A4 (OR4_X1)
     2    2.66    0.02    0.12    2.15 v _14296_/ZN (OR4_X1)
                                         _08909_ (net)
                  0.02    0.00    2.15 v _14304_/A2 (OR2_X1)
     3   28.18    0.03    0.09    2.23 v _14304_/ZN (OR2_X1)
                                         _08914_ (net)
                  0.04    0.02    2.25 v _14324_/A3 (NOR3_X1)
     2    3.83    0.04    0.08    2.33 ^ _14324_/ZN (NOR3_X1)
...
                                         clknet_4_8_0_clk (net)
                  0.03    0.01    8.26 ^ clkbuf_leaf_35_clk/A (CLKBUF_X3)
     7    9.67    0.01    0.04    8.30 ^ clkbuf_leaf_35_clk/Z (CLKBUF_X3)
                                         clknet_leaf_35_clk (net)
                  0.01    0.00    8.30 ^ lane_quotient_q[3][51]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.30   clock reconvergence pessimism
                         -0.03    8.27   library setup time
                                  8.27   data required time
-----------------------------------------------------------------------------
                                  8.27   data required time
                                 -3.47   data arrival time
-----------------------------------------------------------------------------
                                  4.79   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `input_value_q[240]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.6100`
- data_arrival_time: `2.7700`
- data_required_time: `8.3800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: input_value_q[240]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.60    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   54.38    0.04    0.06    2.06 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.02    2.08 ^ place1577/A (BUF_X1)
     6   38.52    0.08    0.11    2.19 ^ place1577/Z (BUF_X1)
                                         net1577 (net)
                  0.08    0.00    2.19 ^ place1594/A (BUF_X2)
    25   60.85    0.07    0.10    2.29 ^ place1594/Z (BUF_X2)
                                         net1594 (net)
                  0.07    0.01    2.30 ^ place1602/A (BUF_X2)
    30   67.15    0.07    0.10    2.40 ^ place1602/Z (BUF_X2)
...
                                         clknet_2_3_0_clk (net)
                  0.03    0.01    8.20 ^ clkbuf_4_12_0_clk/A (CLKBUF_X3)
     9   59.24    0.05    0.08    8.28 ^ clkbuf_4_12_0_clk/Z (CLKBUF_X3)
                                         clknet_4_12_0_clk (net)
                  0.05    0.00    8.29 ^ clkbuf_leaf_155_clk/A (CLKBUF_X3)
     8   10.39    0.01    0.05    8.33 ^ clkbuf_leaf_155_clk/Z (CLKBUF_X3)
                                         clknet_leaf_155_clk (net)
                  0.01    0.00    8.33 ^ input_value_q[240]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.33   clock reconvergence pessimism
                          0.05    8.38   library recovery time
                                  8.38   data required time
-----------------------------------------------------------------------------
                                  8.38   data required time
                                 -2.77   data arrival time
-----------------------------------------------------------------------------
                                  5.61   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `group_index_q$_DFFE_PN0P_`
- endpoint: `lane_quotient_q[0][49]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `6.2700`
- data_arrival_time: `2.0400`
- data_required_time: `8.3200`

```text
Startpoint: group_index_q$_DFFE_PN0P_
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
   0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.13 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.07    0.20 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.08    0.28 ^ clkbuf_4_3_0_clk/Z (CLKBUF_X3)
   0.06    0.34 ^ clkbuf_leaf_131_clk/Z (CLKBUF_X3)
   0.00    0.34 ^ group_index_q$_DFFE_PN0P_/CK (DFFR_X2)
   0.19    0.53 ^ group_index_q$_DFFE_PN0P_/Q (DFFR_X2)
   0.05    0.58 v _14513_/ZN (INV_X2)
   0.09    0.67 v _15246_/ZN (AND2_X1)
   0.05    0.72 ^ _15247_/ZN (INV_X1)
   0.05    0.77 ^ _25447_/CO (HA_X1)
   0.03    0.80 v _15300_/ZN (OAI21_X1)
...
   0.06    8.13 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.07    8.20 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.10    8.30 ^ clkbuf_4_0_0_clk/Z (CLKBUF_X3)
   0.06    8.35 ^ clkbuf_leaf_162_clk/Z (CLKBUF_X3)
   0.00    8.35 ^ lane_quotient_q[0][49]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    8.35   clock reconvergence pessimism
  -0.04    8.32   library setup time
           8.32   data required time
---------------------------------------------------------
           8.32   data required time
          -2.04   data arrival time
---------------------------------------------------------
           6.27   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/2_floorplan_final.rpt`
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
                                         _12533_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_detailed_place.rpt`
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
                                         _12533_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_global_place.rpt`
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
                                         _12533_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/3_resizer.rpt`
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
                                         _12533_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4000`
- data_required_time: `0.3400`

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
     1   61.26    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.50    0.03    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   46.56    0.04    0.07    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.04    0.01    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     4   40.74    0.03    0.07    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.24 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     8   20.46    0.02    0.05    0.29 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.29 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     7    8.44    0.01    0.04    0.33 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    0.33 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.33   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4000`
- data_required_time: `0.3400`

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
     1   60.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.50    0.03    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   46.68    0.04    0.07    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.04    0.01    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     4   40.94    0.03    0.07    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.24 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     8   20.21    0.02    0.05    0.29 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.29 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     7    8.75    0.01    0.04    0.33 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    0.33 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.33   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3500`
- data_required_time: `0.2900`

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
     1   46.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.82    0.02    0.05    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.07 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   32.25    0.03    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     4   31.43    0.03    0.06    0.19 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     8   20.06    0.02    0.05    0.24 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.25 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     7    8.95    0.01    0.04    0.28 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    0.28 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.28   clock reconvergence pessimism
                          0.01    0.29   library hold time
                                  0.29   data required time
-----------------------------------------------------------------------------
                                  0.29   data required time
                                 -0.35   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[29]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4400`
- data_arrival_time: `2.0600`
- data_required_time: `0.6300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[29]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.00    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     7   57.67    0.04    0.06    2.06 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.00    2.06 ^ completed_count[29]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   61.26    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_1_0_clk (net)
                  0.04    0.01    0.24 ^ clkbuf_4_6_0_clk/A (CLKBUF_X3)
     9   59.87    0.04    0.08    0.32 ^ clkbuf_4_6_0_clk/Z (CLKBUF_X3)
                                         clknet_4_6_0_clk (net)
                  0.05    0.03    0.35 ^ clkbuf_leaf_58_clk/A (CLKBUF_X3)
     6    7.73    0.01    0.05    0.39 ^ clkbuf_leaf_58_clk/Z (CLKBUF_X3)
                                         clknet_leaf_58_clk (net)
                  0.01    0.00    0.39 ^ completed_count[29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.23    0.63   library removal time
                                  0.63   data required time
-----------------------------------------------------------------------------
                                  0.63   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.44   slack (MET)
```
