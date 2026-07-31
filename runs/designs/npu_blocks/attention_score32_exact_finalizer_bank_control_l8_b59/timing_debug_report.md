# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b59/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 3.4286 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
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
     1   49.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire6695/A (BUF_X16)
     1   41.84    0.01    0.02    0.04 ^ wire6695/Z (BUF_X16)
                                         net6694 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.22    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.31    0.02    0.05    0.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   23.10    0.02    0.05    0.22 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_5__leaf_clk (net)
                  0.04    0.02    0.34 ^ clkbuf_leaf_176_clk/A (CLKBUF_X3)
     9   12.42    0.01    0.05    0.39 ^ clkbuf_leaf_176_clk/Z (CLKBUF_X3)
                                         clknet_leaf_176_clk (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_count_q[5]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4500`
- data_arrival_time: `2.0500`
- data_required_time: `0.6000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_count_q[5]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   17.88    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1142/A (CLKBUF_X3)
     4   36.89    0.02    0.05    2.05 ^ input1142/Z (CLKBUF_X3)
                                         net1141 (net)
                  0.03    0.01    2.05 ^ order_fifo_count_q[5]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire6695/A (BUF_X16)
...
                                         clknet_3_2_0_clk (net)
                  0.01    0.00    0.27 ^ clkbuf_4_4__f_clk/A (CLKBUF_X3)
     9   41.52    0.03    0.06    0.32 ^ clkbuf_4_4__f_clk/Z (CLKBUF_X3)
                                         clknet_4_4__leaf_clk (net)
                  0.03    0.01    0.33 ^ clkbuf_leaf_194_clk/A (CLKBUF_X3)
     8   14.13    0.01    0.05    0.38 ^ clkbuf_leaf_194_clk/Z (CLKBUF_X3)
                                         clknet_leaf_194_clk (net)
                  0.01    0.00    0.38 ^ order_fifo_count_q[5]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.38   clock reconvergence pessimism
                          0.22    0.60   library removal time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.45   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
- stage: `finish`
- startpoint: `bank_in_ready[46] (input port clocked by clk)`
- endpoint: `bank_in_valid[45] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `2.5700`
- data_arrival_time: `3.4300`
- data_required_time: `6.0000`

```text
Startpoint: bank_in_ready[46] (input port clocked by clk)
Endpoint: bank_in_valid[45] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    4.56    0.00    0.00    2.00 v bank_in_ready[46] (in)
                                         bank_in_ready[46] (net)
                  0.00    0.00    2.00 v input119/A (BUF_X1)
     1    5.85    0.01    0.03    2.03 v input119/Z (BUF_X1)
                                         net118 (net)
                  0.01    0.00    2.03 v _08090_/B (MUX2_X1)
     1    1.37    0.01    0.06    2.09 v _08090_/Z (MUX2_X1)
                                         _02677_ (net)
                  0.01    0.00    2.09 v _08091_/A3 (AND3_X1)
     1    1.58    0.01    0.04    2.12 v _08091_/ZN (AND3_X1)
                                         _02678_ (net)
                  0.01    0.00    2.12 v _08101_/A (AOI221_X1)
     1    2.90    0.05    0.08    2.20 ^ _08101_/ZN (AOI221_X1)
                                         _02688_ (net)
...
                  0.01    0.00    3.43 v bank_in_valid[45] (out)
                                  3.43   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -3.43   data arrival time
-----------------------------------------------------------------------------
                                  2.57   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_head_q[4]$_DFFE_PN0N_`
- endpoint: `order_fifo_high_watermark_q[3]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `4.9600`
- data_arrival_time: `3.3800`
- data_required_time: `8.3400`

```text
Startpoint: order_fifo_head_q[4]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: order_fifo_high_watermark_q[3]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire6695/Z (BUF_X16)
   0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.06    0.23 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.04    0.27 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
   0.09    0.36 ^ clkbuf_4_14__f_clk/Z (CLKBUF_X3)
   0.08    0.43 ^ clkbuf_leaf_144_clk/Z (CLKBUF_X3)
   0.00    0.43 ^ order_fifo_head_q[4]$_DFFE_PN0N_/CK (DFFR_X2)
   0.21    0.64 ^ order_fifo_head_q[4]$_DFFE_PN0N_/Q (DFFR_X2)
   0.12    0.76 ^ place6176/Z (BUF_X1)
   0.04    0.81 v _07333_/ZN (NOR2_X2)
   0.08    0.89 ^ _07334_/ZN (NAND2_X1)
...
   0.05    8.22 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
   0.04    8.26 ^ clkbuf_3_2_0_clk/Z (CLKBUF_X3)
   0.06    8.32 ^ clkbuf_4_4__f_clk/Z (CLKBUF_X3)
   0.06    8.38 ^ clkbuf_leaf_195_clk/Z (CLKBUF_X3)
   0.00    8.38 ^ order_fifo_high_watermark_q[3]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    8.38   clock reconvergence pessimism
  -0.04    8.34   library setup time
           8.34   data required time
---------------------------------------------------------
           8.34   data required time
          -3.38   data arrival time
---------------------------------------------------------
           4.96   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_tid_mem[44][10]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.4800`
- data_arrival_time: `2.9500`
- data_required_time: `8.4300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_tid_mem[44][10]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   17.88    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1142/A (CLKBUF_X3)
     4   36.89    0.02    0.05    2.05 ^ input1142/Z (CLKBUF_X3)
                                         net1141 (net)
                  0.04    0.02    2.07 ^ place6633/A (BUF_X2)
     2   29.33    0.03    0.05    2.12 ^ place6633/Z (BUF_X2)
                                         net6632 (net)
                  0.04    0.02    2.14 ^ place6634/A (BUF_X2)
    23   59.38    0.07    0.09    2.23 ^ place6634/Z (BUF_X2)
                                         net6633 (net)
                  0.07    0.00    2.24 ^ place6661/A (BUF_X4)
    52  124.44    0.06    0.08    2.32 ^ place6661/Z (BUF_X4)
...
                                         clknet_3_4_0_clk (net)
                  0.01    0.00    8.27 ^ clkbuf_4_8__f_clk/A (CLKBUF_X3)
    17   50.64    0.04    0.07    8.33 ^ clkbuf_4_8__f_clk/Z (CLKBUF_X3)
                                         clknet_4_8__leaf_clk (net)
                  0.04    0.01    8.34 ^ clkbuf_leaf_25_clk/A (CLKBUF_X3)
     9   12.45    0.01    0.05    8.39 ^ clkbuf_leaf_25_clk/Z (CLKBUF_X3)
                                         clknet_leaf_25_clk (net)
                  0.01    0.00    8.39 ^ order_fifo_tid_mem[44][10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.39   clock reconvergence pessimism
                          0.04    8.43   library recovery time
                                  8.43   data required time
-----------------------------------------------------------------------------
                                  8.43   data required time
                                 -2.95   data arrival time
-----------------------------------------------------------------------------
                                  5.48   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/2_floorplan_final.rpt`
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
                                         _05710_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_detailed_place.rpt`
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
                                         _05710_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_global_place.rpt`
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
                                         _05710_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/3_resizer.rpt`
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
                                         _05710_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5100`
- data_required_time: `0.4500`

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
     1   74.66    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire6695/A (BUF_X16)
     1   57.13    0.01    0.03    0.05 ^ wire6695/Z (BUF_X16)
                                         net6694 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.45    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   24.15    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   30.44    0.03    0.06    0.26 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_5__leaf_clk (net)
                  0.05    0.02    0.39 ^ clkbuf_leaf_176_clk/A (CLKBUF_X3)
     9   11.96    0.01    0.05    0.44 ^ clkbuf_leaf_176_clk/Z (CLKBUF_X3)
                                         clknet_leaf_176_clk (net)
                  0.01    0.00    0.44 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.44   clock reconvergence pessimism
                          0.01    0.45   library hold time
                                  0.45   data required time
-----------------------------------------------------------------------------
                                  0.45   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5100`
- data_required_time: `0.4500`

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
     1   71.92    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire6695/A (BUF_X16)
     1   56.75    0.01    0.03    0.05 ^ wire6695/Z (BUF_X16)
                                         net6694 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.12    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   24.28    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   30.55    0.03    0.06    0.26 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_5__leaf_clk (net)
                  0.05    0.02    0.39 ^ clkbuf_leaf_176_clk/A (CLKBUF_X3)
     9   11.85    0.01    0.05    0.44 ^ clkbuf_leaf_176_clk/Z (CLKBUF_X3)
                                         clknet_leaf_176_clk (net)
                  0.01    0.00    0.44 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.44   clock reconvergence pessimism
                          0.01    0.45   library hold time
                                  0.45   data required time
-----------------------------------------------------------------------------
                                  0.45   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/6_finish.rpt`
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
     1   49.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire6695/A (BUF_X16)
     1   41.84    0.01    0.02    0.04 ^ wire6695/Z (BUF_X16)
                                         net6694 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.22    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.31    0.02    0.05    0.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   23.10    0.02    0.05    0.22 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_5__leaf_clk (net)
                  0.04    0.02    0.34 ^ clkbuf_leaf_176_clk/A (CLKBUF_X3)
     9   12.42    0.01    0.05    0.39 ^ clkbuf_leaf_176_clk/Z (CLKBUF_X3)
                                         clknet_leaf_176_clk (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b59/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_count_q[5]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4000`
- data_arrival_time: `2.0600`
- data_required_time: `0.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_count_q[5]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   26.49    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1142/A (CLKBUF_X3)
     4   36.08    0.02    0.05    2.05 ^ input1142/Z (CLKBUF_X3)
                                         net1141 (net)
                  0.03    0.01    2.06 ^ order_fifo_count_q[5]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   71.92    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire6695/A (BUF_X16)
...
                                         clknet_3_2_0_clk (net)
                  0.01    0.00    0.31 ^ clkbuf_4_4__f_clk/A (CLKBUF_X3)
     9   50.84    0.04    0.06    0.37 ^ clkbuf_4_4__f_clk/Z (CLKBUF_X3)
                                         clknet_4_4__leaf_clk (net)
                  0.04    0.01    0.38 ^ clkbuf_leaf_194_clk/A (CLKBUF_X3)
     8   14.36    0.02    0.05    0.44 ^ clkbuf_leaf_194_clk/Z (CLKBUF_X3)
                                         clknet_leaf_194_clk (net)
                  0.02    0.00    0.44 ^ order_fifo_count_q[5]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.44   clock reconvergence pessimism
                          0.22    0.65   library removal time
                                  0.65   data required time
-----------------------------------------------------------------------------
                                  0.65   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.40   slack (MET)
```
