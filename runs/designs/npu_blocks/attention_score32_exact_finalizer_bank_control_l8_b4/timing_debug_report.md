# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b4/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 2.8512 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
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
     1   41.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1048/A (BUF_X8)
     1   32.94    0.01    0.03    0.04 ^ wire1048/Z (BUF_X8)
                                         net1047 (net)
                  0.01    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.93    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   20.32    0.02    0.05    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   18.07    0.02    0.05    0.20 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_1_clk (net)
                  0.09    0.05    0.34 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     7    9.69    0.01    0.06    0.39 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `root_completed_count_q[11]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4700`
- data_arrival_time: `2.0500`
- data_required_time: `0.5800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: root_completed_count_q[11]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.72    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input163/A (CLKBUF_X3)
     7   51.23    0.03    0.04    2.04 ^ input163/Z (CLKBUF_X3)
                                         net162 (net)
                  0.03    0.00    2.05 ^ root_completed_count_q[11]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1048/A (BUF_X8)
...
                                         clknet_2_3_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_3_1_clk/A (CLKBUF_X3)
    16   75.09    0.04    0.07    0.27 ^ clkbuf_2_3_1_clk/Z (CLKBUF_X3)
                                         clknet_2_3_1_clk (net)
                  0.07    0.04    0.31 ^ clkbuf_leaf_6_clk/A (CLKBUF_X3)
     6    9.18    0.01    0.05    0.37 ^ clkbuf_leaf_6_clk/Z (CLKBUF_X3)
                                         clknet_leaf_6_clk (net)
                  0.01    0.00    0.37 ^ root_completed_count_q[11]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.37   clock reconvergence pessimism
                          0.22    0.58   library removal time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.47   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `bank_in_ready[2] (input port clocked by clk)`
- endpoint: `bank_in_valid[3] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `3.1500`
- data_arrival_time: `2.8500`
- data_required_time: `6.0000`

```text
Startpoint: bank_in_ready[2] (input port clocked by clk)
Endpoint: bank_in_valid[3] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.37    0.00    0.00    2.00 ^ bank_in_ready[2] (in)
                                         bank_in_ready[2] (net)
                  0.00    0.00    2.00 ^ wire657/A (CLKBUF_X3)
     1    6.02    0.01    0.03    2.03 ^ wire657/Z (CLKBUF_X3)
                                         net656 (net)
                  0.01    0.00    2.03 ^ _1988_/B2 (AOI222_X1)
     1    1.16    0.02    0.02    2.05 v _1988_/ZN (AOI222_X1)
                                         _0739_ (net)
                  0.02    0.00    2.05 v _1990_/A (MUX2_X1)
     1   25.76    0.03    0.09    2.14 v _1990_/Z (MUX2_X1)
                                         _0741_ (net)
                  0.04    0.02    2.16 v place925/A (BUF_X2)
     1    5.07    0.01    0.04    2.20 v place925/Z (BUF_X2)
                                         net924 (net)
...
                  0.01    0.00    2.85 ^ bank_in_valid[3] (out)
                                  2.85   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -2.85   data arrival time
-----------------------------------------------------------------------------
                                  3.15   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_tid_mem[0][13]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.6600`
- data_arrival_time: `2.7300`
- data_required_time: `8.3900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_tid_mem[0][13]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.72    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input163/A (CLKBUF_X3)
     7   51.23    0.03    0.04    2.04 ^ input163/Z (CLKBUF_X3)
                                         net162 (net)
                  0.06    0.05    2.09 ^ place1028/A (BUF_X2)
     2   22.73    0.03    0.05    2.14 ^ place1028/Z (BUF_X2)
                                         net1027 (net)
                  0.03    0.01    2.15 ^ place1033/A (BUF_X1)
    13   39.85    0.09    0.11    2.27 ^ place1033/Z (BUF_X1)
                                         net1032 (net)
                  0.09    0.01    2.28 ^ place1034/A (BUF_X1)
     2   18.77    0.04    0.07    2.35 ^ place1034/Z (BUF_X1)
...
                                         clknet_2_0_0_clk (net)
                  0.02    0.00    8.21 ^ clkbuf_2_0_1_clk/A (CLKBUF_X3)
    13   58.22    0.04    0.06    8.27 ^ clkbuf_2_0_1_clk/Z (CLKBUF_X3)
                                         clknet_2_0_1_clk (net)
                  0.05    0.02    8.29 ^ clkbuf_leaf_39_clk/A (CLKBUF_X3)
     5    9.12    0.01    0.05    8.34 ^ clkbuf_leaf_39_clk/Z (CLKBUF_X3)
                                         clknet_leaf_39_clk (net)
                  0.01    0.00    8.34 ^ order_fifo_tid_mem[0][13]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.34   clock reconvergence pessimism
                          0.05    8.39   library recovery time
                                  8.39   data required time
-----------------------------------------------------------------------------
                                  8.39   data required time
                                 -2.73   data arrival time
-----------------------------------------------------------------------------
                                  5.66   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_count_q[1]$_DFFE_PN0N_`
- endpoint: `order_dequeued_count_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `6.5900`
- data_arrival_time: `1.7600`
- data_required_time: `8.3500`

```text
Startpoint: order_fifo_count_q[1]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: order_dequeued_count_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire1048/Z (BUF_X8)
   0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.05    0.20 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
   0.09    0.29 ^ clkbuf_2_2_1_clk/Z (CLKBUF_X3)
   0.09    0.38 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
   0.00    0.38 ^ order_fifo_count_q[1]$_DFFE_PN0N_/CK (DFFR_X1)
   0.10    0.48 v order_fifo_count_q[1]$_DFFE_PN0N_/QN (DFFR_X1)
   0.07    0.55 v _2156_/CO (HA_X1)
   0.06    0.61 v place938/Z (BUF_X2)
   0.07    0.68 v _1967_/ZN (AND2_X2)
   0.08    0.76 ^ _1983_/ZN (AOI221_X2)
...
   0.05    8.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.05    8.20 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
   0.09    8.29 ^ clkbuf_2_2_1_clk/Z (CLKBUF_X3)
   0.10    8.39 ^ clkbuf_leaf_23_clk/Z (CLKBUF_X3)
   0.00    8.39 ^ order_dequeued_count_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    8.39   clock reconvergence pessimism
  -0.04    8.35   library setup time
           8.35   data required time
---------------------------------------------------------
           8.35   data required time
          -1.76   data arrival time
---------------------------------------------------------
           6.59   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/2_floorplan_final.rpt`
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
                                         _0938_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_detailed_place.rpt`
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
                                         _0938_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_global_place.rpt`
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
                                         _0938_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/3_resizer.rpt`
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
                                         _0938_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5500`
- data_required_time: `0.4900`

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
     1   54.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire1048/A (BUF_X8)
     1   44.47    0.01    0.03    0.04 ^ wire1048/Z (BUF_X8)
                                         net1047 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.42    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   26.82    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   27.29    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_1_clk (net)
                  0.12    0.06    0.41 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     7   10.16    0.02    0.06    0.48 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
                  0.02    0.00    0.48 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.48   clock reconvergence pessimism
                          0.01    0.49   library hold time
                                  0.49   data required time
-----------------------------------------------------------------------------
                                  0.49   data required time
                                 -0.55   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5500`
- data_required_time: `0.4900`

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
     1   53.36    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire1048/A (BUF_X8)
     1   44.10    0.01    0.03    0.04 ^ wire1048/Z (BUF_X8)
                                         net1047 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   43.06    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   26.69    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   27.39    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_1_clk (net)
                  0.12    0.06    0.42 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     7   10.06    0.02    0.06    0.48 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
                  0.02    0.00    0.48 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.48   clock reconvergence pessimism
                          0.01    0.49   library hold time
                                  0.49   data required time
-----------------------------------------------------------------------------
                                  0.49   data required time
                                 -0.55   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/6_finish.rpt`
- stage: `finish`
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
     1   41.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire1048/A (BUF_X8)
     1   32.94    0.01    0.03    0.04 ^ wire1048/Z (BUF_X8)
                                         net1047 (net)
                  0.01    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.93    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.10 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   20.32    0.02    0.05    0.15 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   18.07    0.02    0.05    0.20 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_1_clk (net)
                  0.09    0.05    0.34 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     7    9.69    0.01    0.06    0.39 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
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

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `root_completed_count_q[11]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4000`
- data_arrival_time: `2.0500`
- data_required_time: `0.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: root_completed_count_q[11]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.12    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input163/A (CLKBUF_X3)
     7   58.74    0.03    0.05    2.05 ^ input163/Z (CLKBUF_X3)
                                         net162 (net)
                  0.03    0.00    2.05 ^ root_completed_count_q[11]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire1048/A (BUF_X8)
...
                                         clknet_2_3_0_clk (net)
                  0.02    0.01    0.25 ^ clkbuf_2_3_1_clk/A (CLKBUF_X3)
    16   94.46    0.06    0.08    0.33 ^ clkbuf_2_3_1_clk/Z (CLKBUF_X3)
                                         clknet_2_3_1_clk (net)
                  0.08    0.04    0.37 ^ clkbuf_leaf_6_clk/A (CLKBUF_X3)
     6    9.33    0.01    0.06    0.43 ^ clkbuf_leaf_6_clk/Z (CLKBUF_X3)
                                         clknet_leaf_6_clk (net)
                  0.01    0.00    0.43 ^ root_completed_count_q[11]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.43   clock reconvergence pessimism
                          0.22    0.65   library removal time
                                  0.65   data required time
-----------------------------------------------------------------------------
                                  0.65   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.40   slack (MET)
```
