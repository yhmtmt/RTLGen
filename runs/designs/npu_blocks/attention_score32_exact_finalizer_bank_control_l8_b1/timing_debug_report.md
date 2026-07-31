# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b1/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 2.1888 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4000`
- data_required_time: `0.3400`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire674/A (BUF_X8)
     1   33.14    0.01    0.03    0.04 ^ wire674/Z (BUF_X8)
                                         net673 (net)
                  0.01    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.13    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   20.67    0.02    0.05    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   19.84    0.02    0.05    0.20 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_3_1_clk (net)
                  0.04    0.02    0.29 ^ clkbuf_leaf_3_clk/A (CLKBUF_X3)
     7    9.70    0.01    0.05    0.34 ^ clkbuf_leaf_3_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3_clk (net)
                  0.01    0.00    0.34 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.34   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `root_completed_count_q[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4300`
- data_arrival_time: `2.0600`
- data_required_time: `0.6300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: root_completed_count_q[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.67    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input115/A (CLKBUF_X3)
    13   33.63    0.03    0.05    2.05 ^ input115/Z (CLKBUF_X3)
                                         net114 (net)
                  0.03    0.01    2.06 ^ root_completed_count_q[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire674/A (BUF_X8)
...
                                         net676 (net)
                  0.04    0.03    0.33 ^ max_length676/A (BUF_X8)
     1   36.40    0.01    0.03    0.36 ^ max_length676/Z (BUF_X8)
                                         net675 (net)
                  0.02    0.01    0.37 ^ clkbuf_leaf_9_clk/A (CLKBUF_X3)
     7    9.42    0.01    0.04    0.41 ^ clkbuf_leaf_9_clk/Z (CLKBUF_X3)
                                         clknet_leaf_9_clk (net)
                  0.01    0.00    0.41 ^ root_completed_count_q[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.22    0.63   library removal time
                                  0.63   data required time
-----------------------------------------------------------------------------
                                  0.63   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.43   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `root_ready (input port clocked by clk)`
- endpoint: `bank_in_valid[0] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `3.8100`
- data_arrival_time: `2.1900`
- data_required_time: `6.0000`

```text
Startpoint: root_ready (input port clocked by clk)
Endpoint: bank_in_valid[0] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.27    0.00    0.00    2.00 ^ root_ready (in)
                                         root_ready (net)
                  0.00    0.00    2.00 ^ input114/A (BUF_X1)
     3    8.84    0.02    0.04    2.04 ^ input114/Z (BUF_X1)
                                         net113 (net)
                  0.02    0.00    2.04 ^ _0915_/A2 (AND2_X1)
     2   12.85    0.03    0.06    2.10 ^ _0915_/ZN (AND2_X1)
                                         _0373_ (net)
                  0.03    0.00    2.10 ^ _0917_/C1 (OAI211_X4)
     3    7.58    0.02    0.03    2.13 v _0917_/ZN (OAI211_X4)
                                         _0038_ (net)
                  0.02    0.00    2.13 v _0918_/A (INV_X2)
     6   11.29    0.02    0.03    2.15 ^ _0918_/ZN (INV_X2)
                                         net148 (net)
...
                  0.01    0.00    2.19 ^ bank_in_valid[0] (out)
                                  2.19   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -2.19   data arrival time
-----------------------------------------------------------------------------
                                  3.81   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_enqueued_count_q[25]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.7000`
- data_arrival_time: `2.7500`
- data_required_time: `8.4500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_enqueued_count_q[25]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.67    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input115/A (CLKBUF_X3)
    13   33.63    0.03    0.05    2.05 ^ input115/Z (CLKBUF_X3)
                                         net114 (net)
                  0.03    0.01    2.06 ^ place659/A (BUF_X1)
     2   31.41    0.07    0.09    2.14 ^ place659/Z (BUF_X1)
                                         net658 (net)
                  0.07    0.02    2.17 ^ place660/A (BUF_X2)
     2   35.25    0.03    0.05    2.22 ^ place660/Z (BUF_X2)
                                         net659 (net)
                  0.05    0.03    2.25 ^ place661/A (BUF_X1)
     7   16.57    0.04    0.07    2.32 ^ place661/Z (BUF_X1)
...
                                         clknet_2_0_0_clk (net)
                  0.02    0.00    8.20 ^ clkbuf_2_0_1_clk/A (CLKBUF_X3)
    10   83.74    0.04    0.07    8.27 ^ clkbuf_2_0_1_clk/Z (CLKBUF_X3)
                                         clknet_2_0_1_clk (net)
                  0.10    0.07    8.34 ^ clkbuf_leaf_28_clk/A (CLKBUF_X3)
     6    8.03    0.01    0.06    8.40 ^ clkbuf_leaf_28_clk/Z (CLKBUF_X3)
                                         clknet_leaf_28_clk (net)
                  0.01    0.00    8.40 ^ order_enqueued_count_q[25]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.40   clock reconvergence pessimism
                          0.05    8.45   library recovery time
                                  8.45   data required time
-----------------------------------------------------------------------------
                                  8.45   data required time
                                 -2.75   data arrival time
-----------------------------------------------------------------------------
                                  5.70   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_count_q$_DFFE_PN0N_`
- endpoint: `root_completed_count_q[30]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `7.0900`
- data_arrival_time: `1.2200`
- data_required_time: `8.3200`

```text
Startpoint: order_fifo_count_q$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: root_completed_count_q[30]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire674/Z (BUF_X8)
   0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.15 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    0.20 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.07    0.27 ^ clkbuf_2_0_1_clk/Z (CLKBUF_X3)
   0.13    0.40 ^ clkbuf_leaf_35_clk/Z (CLKBUF_X3)
   0.00    0.40 ^ order_fifo_count_q$_DFFE_PN0N_/CK (DFFR_X1)
   0.13    0.53 ^ order_fifo_count_q$_DFFE_PN0N_/Q (DFFR_X1)
   0.04    0.57 ^ _0910_/ZN (AND2_X4)
   0.02    0.59 v _0911_/ZN (NAND2_X4)
   0.03    0.62 ^ _0912_/ZN (INV_X4)
   0.07    0.69 ^ place598/Z (BUF_X2)
...
   0.05    8.15 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    8.20 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
   0.05    8.25 ^ clkbuf_2_1_1_clk/Z (CLKBUF_X3)
   0.11    8.36 ^ clkbuf_leaf_18_clk/Z (CLKBUF_X3)
   0.00    8.36 ^ root_completed_count_q[30]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    8.36   clock reconvergence pessimism
  -0.04    8.32   library setup time
           8.32   data required time
---------------------------------------------------------
           8.32   data required time
          -1.22   data arrival time
---------------------------------------------------------
           7.09   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ cycle_count_q[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0696_ (net)
                  0.01    0.00    0.06 ^ cycle_count_q[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count_q[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0696_ (net)
                  0.01    0.00    0.06 ^ cycle_count_q[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count_q[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0696_ (net)
                  0.01    0.00    0.06 ^ cycle_count_q[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count_q[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0696_ (net)
                  0.01    0.00    0.06 ^ cycle_count_q[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4600`
- data_required_time: `0.4000`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire674/A (BUF_X8)
     1   44.68    0.01    0.03    0.04 ^ wire674/Z (BUF_X8)
                                         net673 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.49    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   27.26    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   27.36    0.02    0.05    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_3_1_clk (net)
                  0.05    0.02    0.34 ^ clkbuf_leaf_3_clk/A (CLKBUF_X3)
     7    9.64    0.01    0.05    0.39 ^ clkbuf_leaf_3_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3_clk (net)
                  0.01    0.00    0.39 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.01    0.40   library hold time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -0.46   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4600`
- data_required_time: `0.4000`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.63    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire674/A (BUF_X8)
     1   44.14    0.01    0.03    0.04 ^ wire674/Z (BUF_X8)
                                         net673 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.76    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   27.17    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   27.35    0.02    0.05    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_3_1_clk (net)
                  0.05    0.02    0.34 ^ clkbuf_leaf_3_clk/A (CLKBUF_X3)
     7    9.68    0.01    0.05    0.39 ^ clkbuf_leaf_3_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3_clk (net)
                  0.01    0.00    0.39 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.01    0.40   library hold time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -0.46   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4000`
- data_required_time: `0.3400`

```text
Startpoint: cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire674/A (BUF_X8)
     1   33.14    0.01    0.03    0.04 ^ wire674/Z (BUF_X8)
                                         net673 (net)
                  0.01    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.13    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   20.67    0.02    0.05    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   19.84    0.02    0.05    0.20 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_3_1_clk (net)
                  0.04    0.02    0.29 ^ clkbuf_leaf_3_clk/A (CLKBUF_X3)
     7    9.70    0.01    0.05    0.34 ^ clkbuf_leaf_3_clk/Z (CLKBUF_X3)
                                         clknet_leaf_3_clk (net)
                  0.01    0.00    0.34 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.34   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `root_completed_count_q[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3600`
- data_arrival_time: `2.0600`
- data_required_time: `0.7000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: root_completed_count_q[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.06    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input115/A (CLKBUF_X3)
    13   35.23    0.03    0.05    2.05 ^ input115/Z (CLKBUF_X3)
                                         net114 (net)
                  0.03    0.01    2.06 ^ root_completed_count_q[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire674/A (BUF_X8)
...
                                         net676 (net)
                  0.05    0.04    0.39 ^ max_length676/A (BUF_X8)
     1   49.04    0.01    0.04    0.43 ^ max_length676/Z (BUF_X8)
                                         net675 (net)
                  0.02    0.01    0.44 ^ clkbuf_leaf_9_clk/A (CLKBUF_X3)
     7    9.32    0.01    0.04    0.48 ^ clkbuf_leaf_9_clk/Z (CLKBUF_X3)
                                         clknet_leaf_9_clk (net)
                  0.01    0.00    0.48 ^ root_completed_count_q[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.48   clock reconvergence pessimism
                          0.22    0.70   library removal time
                                  0.70   data required time
-----------------------------------------------------------------------------
                                  0.70   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.36   slack (MET)
```
