# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b32/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 2.8138 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
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
     1   44.28    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire3846/A (BUF_X8)
     1   35.75    0.01    0.03    0.04 ^ wire3846/Z (BUF_X8)
                                         net3845 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.80    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.33    0.02    0.05    0.15 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   34.54    0.03    0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    0.29 ^ clkbuf_leaf_4_clk/A (CLKBUF_X3)
     7    9.01    0.01    0.04    0.33 ^ clkbuf_leaf_4_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4_clk (net)
                  0.01    0.00    0.33 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.33   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_enqueued_count_q[18]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4800`
- data_arrival_time: `2.0600`
- data_required_time: `0.5800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_enqueued_count_q[18]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.31    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input658/A (CLKBUF_X3)
    23   60.72    0.04    0.06    2.06 ^ input658/Z (CLKBUF_X3)
                                         net657 (net)
                  0.04    0.00    2.06 ^ order_enqueued_count_q[18]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   44.28    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire3846/A (BUF_X8)
...
                                         clknet_2_2_0_clk (net)
                  0.02    0.01    0.22 ^ clkbuf_4_9_0_clk/A (CLKBUF_X3)
    13   52.02    0.04    0.07    0.29 ^ clkbuf_4_9_0_clk/Z (CLKBUF_X3)
                                         clknet_4_9_0_clk (net)
                  0.04    0.01    0.30 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7   10.00    0.01    0.05    0.35 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.35 ^ order_enqueued_count_q[18]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.35   clock reconvergence pessimism
                          0.24    0.58   library removal time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.48   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `bank_in_ready[29] (input port clocked by clk)`
- endpoint: `bank_in_valid[18] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `3.1900`
- data_arrival_time: `2.8100`
- data_required_time: `6.0000`

```text
Startpoint: bank_in_ready[29] (input port clocked by clk)
Endpoint: bank_in_valid[18] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.93    0.00    0.00    2.00 ^ bank_in_ready[29] (in)
                                         bank_in_ready[29] (net)
                  0.00    0.00    2.00 ^ input102/A (BUF_X1)
     1   13.26    0.03    0.05    2.05 ^ input102/Z (BUF_X1)
                                         net101 (net)
                  0.03    0.00    2.05 ^ _4838_/A2 (AOI22_X1)
     1    1.74    0.02    0.02    2.07 v _4838_/ZN (AOI22_X1)
                                         _1529_ (net)
                  0.02    0.00    2.07 v _4841_/C1 (OAI222_X1)
     1    1.80    0.05    0.06    2.12 ^ _4841_/ZN (OAI222_X1)
                                         _1532_ (net)
                  0.05    0.00    2.12 ^ _4850_/A2 (OAI22_X1)
     1    2.36    0.02    0.03    2.15 v _4850_/ZN (OAI22_X1)
                                         _1541_ (net)
...
                  0.01    0.00    2.81 ^ bank_in_valid[18] (out)
                                  2.81   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -2.81   data arrival time
-----------------------------------------------------------------------------
                                  3.19   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_head_q[2]$_DFFE_PN0N_`
- endpoint: `order_fifo_high_watermark_q[5]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `5.2500`
- data_arrival_time: `3.0500`
- data_required_time: `8.2900`

```text
Startpoint: order_fifo_head_q[2]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: order_fifo_high_watermark_q[5]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire3846/Z (BUF_X8)
   0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.06    0.22 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.06    0.27 ^ clkbuf_4_14_0_clk/Z (CLKBUF_X3)
   0.04    0.32 ^ clkbuf_leaf_83_clk/Z (CLKBUF_X3)
   0.00    0.32 ^ order_fifo_head_q[2]$_DFFE_PN0N_/CK (DFFR_X2)
   0.21    0.53 ^ order_fifo_head_q[2]$_DFFE_PN0N_/Q (DFFR_X2)
   0.11    0.64 ^ place3450/Z (BUF_X1)
   0.06    0.69 ^ _4469_/ZN (OR2_X4)
   0.03    0.72 v _4478_/ZN (NOR3_X4)
   0.07    0.79 v place3431/Z (BUF_X1)
...
   0.06    8.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.06    8.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
   0.07    8.28 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
   0.05    8.33 ^ clkbuf_leaf_55_clk/Z (CLKBUF_X3)
   0.00    8.33 ^ order_fifo_high_watermark_q[5]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    8.33   clock reconvergence pessimism
  -0.04    8.29   library setup time
           8.29   data required time
---------------------------------------------------------
           8.29   data required time
          -3.05   data arrival time
---------------------------------------------------------
           5.25   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_tid_mem[1][4]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.4900`
- data_arrival_time: `2.8800`
- data_required_time: `8.3700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_tid_mem[1][4]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.31    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input658/A (CLKBUF_X3)
    23   60.72    0.04    0.06    2.06 ^ input658/Z (CLKBUF_X3)
                                         net657 (net)
                  0.05    0.03    2.09 ^ place3811/A (BUF_X1)
     2   27.53    0.06    0.08    2.17 ^ place3811/Z (BUF_X1)
                                         net3810 (net)
                  0.06    0.02    2.19 ^ place3812/A (BUF_X2)
     2   28.07    0.03    0.05    2.24 ^ place3812/Z (BUF_X2)
                                         net3811 (net)
                  0.04    0.02    2.26 ^ place3823/A (BUF_X2)
    30   72.17    0.08    0.10    2.36 ^ place3823/Z (BUF_X2)
...
                                         clknet_2_0_0_clk (net)
                  0.03    0.01    8.22 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
    10   38.04    0.03    0.06    8.29 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    8.29 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     7    8.96    0.01    0.04    8.33 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    8.33 ^ order_fifo_tid_mem[1][4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.33   clock reconvergence pessimism
                          0.04    8.37   library recovery time
                                  8.37   data required time
-----------------------------------------------------------------------------
                                  8.37   data required time
                                 -2.88   data arrival time
-----------------------------------------------------------------------------
                                  5.49   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/2_floorplan_final.rpt`
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
                                         _3477_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_detailed_place.rpt`
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
                                         _3477_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_global_place.rpt`
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
                                         _3477_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/3_resizer.rpt`
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
                                         _3477_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4400`
- data_required_time: `0.3800`

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
     1   60.94    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire3846/A (BUF_X8)
     1   50.61    0.01    0.03    0.05 ^ wire3846/Z (BUF_X8)
                                         net3845 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.26    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   26.65    0.02    0.06    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   38.67    0.03    0.06    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    0.33 ^ clkbuf_leaf_4_clk/A (CLKBUF_X3)
     7    9.16    0.01    0.04    0.37 ^ clkbuf_leaf_4_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4_clk (net)
                  0.01    0.00    0.37 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.37   clock reconvergence pessimism
                          0.01    0.38   library hold time
                                  0.38   data required time
-----------------------------------------------------------------------------
                                  0.38   data required time
                                 -0.44   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4400`
- data_required_time: `0.3800`

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
     1   60.56    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire3846/A (BUF_X8)
     1   50.35    0.01    0.03    0.05 ^ wire3846/Z (BUF_X8)
                                         net3845 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.52    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.13 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   26.46    0.02    0.05    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   38.33    0.03    0.06    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    0.33 ^ clkbuf_leaf_4_clk/A (CLKBUF_X3)
     7    9.37    0.01    0.04    0.37 ^ clkbuf_leaf_4_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4_clk (net)
                  0.01    0.00    0.37 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.37   clock reconvergence pessimism
                          0.01    0.38   library hold time
                                  0.38   data required time
-----------------------------------------------------------------------------
                                  0.38   data required time
                                 -0.44   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/6_finish.rpt`
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
     1   44.28    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire3846/A (BUF_X8)
     1   35.75    0.01    0.03    0.04 ^ wire3846/Z (BUF_X8)
                                         net3845 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.80    0.02    0.05    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.33    0.02    0.05    0.15 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   34.54    0.03    0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    0.29 ^ clkbuf_leaf_4_clk/A (CLKBUF_X3)
     7    9.01    0.01    0.04    0.33 ^ clkbuf_leaf_4_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4_clk (net)
                  0.01    0.00    0.33 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.33   clock reconvergence pessimism
                          0.01    0.34   library hold time
                                  0.34   data required time
-----------------------------------------------------------------------------
                                  0.34   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b32/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_enqueued_count_q[18]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4200`
- data_arrival_time: `2.0600`
- data_required_time: `0.6400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_enqueued_count_q[18]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.66    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input658/A (CLKBUF_X3)
    23   60.75    0.04    0.06    2.06 ^ input658/Z (CLKBUF_X3)
                                         net657 (net)
                  0.04    0.00    2.06 ^ order_enqueued_count_q[18]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   60.56    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire3846/A (BUF_X8)
...
                                         clknet_2_2_0_clk (net)
                  0.03    0.01    0.27 ^ clkbuf_4_9_0_clk/A (CLKBUF_X3)
    13   58.52    0.04    0.08    0.35 ^ clkbuf_4_9_0_clk/Z (CLKBUF_X3)
                                         clknet_4_9_0_clk (net)
                  0.05    0.01    0.36 ^ clkbuf_leaf_73_clk/A (CLKBUF_X3)
     7    9.78    0.01    0.05    0.40 ^ clkbuf_leaf_73_clk/Z (CLKBUF_X3)
                                         clknet_leaf_73_clk (net)
                  0.01    0.00    0.40 ^ order_enqueued_count_q[18]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.40   clock reconvergence pessimism
                          0.24    0.64   library removal time
                                  0.64   data required time
-----------------------------------------------------------------------------
                                  0.64   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.42   slack (MET)
```
