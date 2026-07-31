# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b16/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 2.8905 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4800`
- data_required_time: `0.4200`

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
     1   54.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire2328/A (BUF_X16)
     1   41.00    0.01    0.03    0.05 ^ wire2328/Z (BUF_X16)
                                         net2327 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.93    0.02    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.85    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   19.65    0.02    0.05    0.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         net2328 (net)
                  0.02    0.01    0.37 ^ clkbuf_leaf_89_clk/A (CLKBUF_X3)
     6    9.67    0.01    0.04    0.41 ^ clkbuf_leaf_89_clk/Z (CLKBUF_X3)
                                         clknet_leaf_89_clk (net)
                  0.01    0.00    0.41 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.01    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count_q[18]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5000`
- data_arrival_time: `2.0900`
- data_required_time: `0.5900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count_q[18]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.87    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input373/A (CLKBUF_X3)
    16   61.62    0.04    0.06    2.06 ^ input373/Z (CLKBUF_X3)
                                         net372 (net)
                  0.06    0.03    2.09 ^ cycle_count_q[18]$_DFF_PN0_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire2328/A (BUF_X16)
...
                                         clknet_2_0_0_clk (net)
                  0.02    0.00    0.22 ^ clkbuf_3_0_0_clk/A (CLKBUF_X3)
     9   74.76    0.04    0.07    0.28 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
                                         clknet_3_0_0_clk (net)
                  0.04    0.01    0.29 ^ clkbuf_leaf_76_clk/A (CLKBUF_X3)
     7    9.80    0.01    0.05    0.34 ^ clkbuf_leaf_76_clk/Z (CLKBUF_X3)
                                         clknet_leaf_76_clk (net)
                  0.01    0.00    0.34 ^ cycle_count_q[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.34   clock reconvergence pessimism
                          0.25    0.59   library removal time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.50   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `bank_out_valid[11] (input port clocked by clk)`
- endpoint: `bank_in_valid[15] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `3.1100`
- data_arrival_time: `2.8900`
- data_required_time: `6.0000`

```text
Startpoint: bank_out_valid[11] (input port clocked by clk)
Endpoint: bank_in_valid[15] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.66    0.00    0.00    2.00 ^ bank_out_valid[11] (in)
                                         bank_out_valid[11] (net)
                  0.00    0.00    2.00 ^ input358/A (BUF_X1)
     2    7.16    0.02    0.03    2.03 ^ input358/Z (BUF_X1)
                                         net357 (net)
                  0.02    0.00    2.03 ^ _2892_/A (INV_X1)
     1    2.79    0.01    0.01    2.04 v _2892_/ZN (INV_X1)
                                         _0832_ (net)
                  0.01    0.00    2.04 v _2893_/B3 (OAI33_X1)
     1    2.27    0.06    0.08    2.13 ^ _2893_/ZN (OAI33_X1)
                                         _0833_ (net)
                  0.06    0.00    2.13 ^ _2898_/A2 (OAI22_X1)
     1    2.29    0.02    0.03    2.16 v _2898_/ZN (OAI22_X1)
                                         _0838_ (net)
...
                  0.01    0.00    2.89 ^ bank_in_valid[15] (out)
                                  2.89   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -2.89   data arrival time
-----------------------------------------------------------------------------
                                  3.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_head_q[1]$_DFFE_PN0N_`
- endpoint: `order_fifo_high_watermark_q[1]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `5.5300`
- data_arrival_time: `2.7900`
- data_required_time: `8.3300`

```text
Startpoint: order_fifo_head_q[1]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: order_fifo_high_watermark_q[1]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.05    0.05 ^ wire2328/Z (BUF_X16)
   0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.07    0.28 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
   0.12    0.40 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
   0.00    0.40 ^ order_fifo_head_q[1]$_DFFE_PN0N_/CK (DFFR_X1)
   0.13    0.54 ^ order_fifo_head_q[1]$_DFFE_PN0N_/Q (DFFR_X1)
   0.08    0.62 ^ _4857_/CO (HA_X1)
   0.10    0.72 ^ place2178/Z (BUF_X1)
   0.03    0.75 v _2713_/ZN (NOR3_X1)
   0.07    0.81 ^ _2718_/ZN (NAND2_X1)
...
   0.05    8.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    8.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.09    8.30 ^ clkbuf_3_1_0_clk/Z (CLKBUF_X3)
   0.06    8.36 ^ clkbuf_leaf_72_clk/Z (CLKBUF_X3)
   0.00    8.36 ^ order_fifo_high_watermark_q[1]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    8.36   clock reconvergence pessimism
  -0.04    8.33   library setup time
           8.33   data required time
---------------------------------------------------------
           8.33   data required time
          -2.79   data arrival time
---------------------------------------------------------
           5.53   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_tid_mem[14][4]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.5400`
- data_arrival_time: `2.8400`
- data_required_time: `8.3900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_tid_mem[14][4]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.87    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input373/A (CLKBUF_X3)
    16   61.62    0.04    0.06    2.06 ^ input373/Z (CLKBUF_X3)
                                         net372 (net)
                  0.06    0.04    2.10 ^ place2306/A (BUF_X2)
     1   20.70    0.02    0.05    2.14 ^ place2306/Z (BUF_X2)
                                         net2305 (net)
                  0.03    0.01    2.16 ^ place2307/A (BUF_X2)
    11   40.48    0.04    0.06    2.21 ^ place2307/Z (BUF_X2)
                                         net2306 (net)
                  0.05    0.02    2.23 ^ place2314/A (BUF_X1)
    17   42.32    0.09    0.12    2.36 ^ place2314/Z (BUF_X1)
...
                                         clknet_2_2_0_clk (net)
                  0.02    0.00    8.22 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
    19   51.26    0.04    0.07    8.29 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.04    0.01    8.30 ^ clkbuf_leaf_40_clk/A (CLKBUF_X3)
     8   10.30    0.01    0.05    8.34 ^ clkbuf_leaf_40_clk/Z (CLKBUF_X3)
                                         clknet_leaf_40_clk (net)
                  0.01    0.00    8.34 ^ order_fifo_tid_mem[14][4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.34   clock reconvergence pessimism
                          0.04    8.39   library recovery time
                                  8.39   data required time
-----------------------------------------------------------------------------
                                  8.39   data required time
                                 -2.84   data arrival time
-----------------------------------------------------------------------------
                                  5.54   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/2_floorplan_final.rpt`
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
                                         _2167_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_detailed_place.rpt`
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
                                         _2167_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_global_place.rpt`
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
                                         _2167_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/3_resizer.rpt`
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
                                         _2167_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/4_cts_final.rpt`
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
     1   77.72    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire2328/A (BUF_X16)
     1   60.06    0.01    0.03    0.06 ^ wire2328/Z (BUF_X16)
                                         net2327 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.51    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.28    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   27.24    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         net2328 (net)
                  0.02    0.01    0.44 ^ clkbuf_leaf_89_clk/A (CLKBUF_X3)
     6   10.02    0.01    0.04    0.48 ^ clkbuf_leaf_89_clk/Z (CLKBUF_X3)
                                         clknet_leaf_89_clk (net)
                  0.01    0.00    0.48 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/5_global_route.rpt`
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
     1   77.81    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire2328/A (BUF_X16)
     1   60.11    0.01    0.03    0.06 ^ wire2328/Z (BUF_X16)
                                         net2327 (net)
                  0.03    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.85    0.03    0.07    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.34    0.02    0.06    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   27.22    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         net2328 (net)
                  0.02    0.02    0.44 ^ clkbuf_leaf_89_clk/A (CLKBUF_X3)
     6   10.14    0.01    0.04    0.48 ^ clkbuf_leaf_89_clk/Z (CLKBUF_X3)
                                         clknet_leaf_89_clk (net)
                  0.01    0.00    0.48 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4800`
- data_required_time: `0.4200`

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
     1   54.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire2328/A (BUF_X16)
     1   41.00    0.01    0.03    0.05 ^ wire2328/Z (BUF_X16)
                                         net2327 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.93    0.02    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.85    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   19.65    0.02    0.05    0.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         net2328 (net)
                  0.02    0.01    0.37 ^ clkbuf_leaf_89_clk/A (CLKBUF_X3)
     6    9.67    0.01    0.04    0.41 ^ clkbuf_leaf_89_clk/Z (CLKBUF_X3)
                                         clknet_leaf_89_clk (net)
                  0.01    0.00    0.41 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.01    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b16/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count_q[18]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4400`
- data_arrival_time: `2.1000`
- data_required_time: `0.6600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count_q[18]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.36    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input373/A (CLKBUF_X3)
    16   72.43    0.05    0.07    2.07 ^ input373/Z (CLKBUF_X3)
                                         net372 (net)
                  0.06    0.03    2.10 ^ cycle_count_q[18]$_DFF_PN0_/RN (DFFR_X1)
                                  2.10   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   77.72    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire2328/A (BUF_X16)
...
                                         clknet_2_0_0_clk (net)
                  0.02    0.00    0.26 ^ clkbuf_3_0_0_clk/A (CLKBUF_X3)
     9   92.29    0.05    0.08    0.34 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
                                         clknet_3_0_0_clk (net)
                  0.05    0.01    0.35 ^ clkbuf_leaf_76_clk/A (CLKBUF_X3)
     7    9.69    0.01    0.05    0.40 ^ clkbuf_leaf_76_clk/Z (CLKBUF_X3)
                                         clknet_leaf_76_clk (net)
                  0.01    0.00    0.40 ^ cycle_count_q[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.40   clock reconvergence pessimism
                          0.26    0.66   library removal time
                                  0.66   data required time
-----------------------------------------------------------------------------
                                  0.66   data required time
                                 -2.10   data arrival time
-----------------------------------------------------------------------------
                                  1.44   slack (MET)
```
