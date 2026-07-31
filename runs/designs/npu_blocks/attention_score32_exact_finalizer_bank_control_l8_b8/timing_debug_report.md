# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_finalizer_bank_control_l8_b8/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c655993b | attention_score32_exact_finalizer_bank_control_lane8_firstpass_v1_c655993b | ok | 2.6761 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4300`
- data_required_time: `0.3700`

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
     1   53.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire1454/A (BUF_X16)
     1   38.87    0.01    0.03    0.05 ^ wire1454/Z (BUF_X16)
                                         net1453 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.95    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.41    0.02    0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   17.72    0.02    0.04    0.21 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_3_2_0_clk (net)
                  0.05    0.03    0.31 ^ clkbuf_leaf_0_clk/A (CLKBUF_X3)
     8   10.75    0.01    0.05    0.36 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
                                         clknet_leaf_0_clk (net)
                  0.01    0.00    0.36 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_enqueued_count_q[27]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4400`
- data_arrival_time: `2.0800`
- data_required_time: `0.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_enqueued_count_q[27]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.76    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input232/A (CLKBUF_X3)
    12   51.82    0.03    0.05    2.05 ^ input232/Z (CLKBUF_X3)
                                         net231 (net)
                  0.06    0.04    2.08 ^ order_enqueued_count_q[27]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire1454/A (BUF_X16)
...
                                         clknet_2_3_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     4   86.79    0.05    0.08    0.29 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
                                         clknet_3_7_0_clk (net)
                  0.08    0.05    0.34 ^ clkbuf_leaf_29_clk/A (CLKBUF_X3)
     4    5.73    0.01    0.05    0.39 ^ clkbuf_leaf_29_clk/Z (CLKBUF_X3)
                                         clknet_leaf_29_clk (net)
                  0.01    0.00    0.39 ^ order_enqueued_count_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.25    0.65   library removal time
                                  0.65   data required time
-----------------------------------------------------------------------------
                                  0.65   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.44   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `bank_out_valid[0] (input port clocked by clk)`
- endpoint: `bank_in_valid[1] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `3.3200`
- data_arrival_time: `2.6800`
- data_required_time: `6.0000`

```text
Startpoint: bank_out_valid[0] (input port clocked by clk)
Endpoint: bank_in_valid[1] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    4.55    0.00    0.00    2.00 v bank_out_valid[0] (in)
                                         bank_out_valid[0] (net)
                  0.00    0.00    2.00 v input223/A (BUF_X1)
     2    4.53    0.01    0.03    2.03 v input223/Z (BUF_X1)
                                         net222 (net)
                  0.01    0.00    2.03 v _1880_/B2 (AOI22_X1)
     4   13.19    0.08    0.10    2.13 ^ _1880_/ZN (AOI22_X1)
                                         _0579_ (net)
                  0.08    0.00    2.13 ^ _1886_/A3 (AND4_X1)
     1    5.60    0.02    0.08    2.22 ^ _1886_/ZN (AND4_X1)
                                         _0583_ (net)
                  0.02    0.00    2.22 ^ _1887_/B (OAI211_X2)
     1    7.93    0.03    0.04    2.25 v _1887_/ZN (OAI211_X2)
                                         _0584_ (net)
...
                  0.01    0.00    2.68 v bank_in_valid[1] (out)
                                  2.68   data arrival time

                          8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (propagated)
                          0.00    8.00   clock reconvergence pessimism
                         -2.00    6.00   output external delay
                                  6.00   data required time
-----------------------------------------------------------------------------
                                  6.00   data required time
                                 -2.68   data arrival time
-----------------------------------------------------------------------------
                                  3.32   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `order_fifo_head_q[2]$_DFFE_PN0N_`
- endpoint: `order_fifo_high_watermark_q[4]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `5.7200`
- data_arrival_time: `2.5600`
- data_required_time: `8.2800`

```text
Startpoint: order_fifo_head_q[2]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: order_fifo_high_watermark_q[4]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.05    0.05 ^ wire1454/Z (BUF_X16)
   0.07    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.06    0.27 ^ clkbuf_3_1_0_clk/Z (CLKBUF_X3)
   0.05    0.32 ^ clkbuf_leaf_40_clk/Z (CLKBUF_X3)
   0.00    0.32 ^ order_fifo_head_q[2]$_DFFE_PN0N_/CK (DFFR_X1)
   0.19    0.51 ^ order_fifo_head_q[2]$_DFFE_PN0N_/Q (DFFR_X1)
   0.14    0.65 ^ _3080_/CO (HA_X1)
   0.04    0.69 ^ _1836_/ZN (OR2_X1)
   0.05    0.74 v _1842_/ZN (AOI221_X4)
   0.04    0.78 v _1921_/ZN (AND2_X1)
...
   0.05    8.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    8.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.06    8.27 ^ clkbuf_3_1_0_clk/Z (CLKBUF_X3)
   0.05    8.32 ^ clkbuf_leaf_31_clk/Z (CLKBUF_X3)
   0.00    8.32 ^ order_fifo_high_watermark_q[4]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    8.32   clock reconvergence pessimism
  -0.04    8.28   library setup time
           8.28   data required time
---------------------------------------------------------
           8.28   data required time
          -2.56   data arrival time
---------------------------------------------------------
           5.72   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_fifo_tid_mem[2][15]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.8500`
- data_arrival_time: `2.4700`
- data_required_time: `8.3200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_fifo_tid_mem[2][15]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.76    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input232/A (CLKBUF_X3)
    12   51.82    0.03    0.05    2.05 ^ input232/Z (CLKBUF_X3)
                                         net231 (net)
                  0.06    0.04    2.09 ^ place1438/A (BUF_X2)
     2   24.43    0.03    0.05    2.14 ^ place1438/Z (BUF_X2)
                                         net1437 (net)
                  0.03    0.02    2.15 ^ place1444/A (BUF_X2)
    13   47.69    0.05    0.07    2.22 ^ place1444/Z (BUF_X2)
                                         net1443 (net)
                  0.06    0.02    2.24 ^ place1445/A (BUF_X2)
    33   78.50    0.09    0.11    2.35 ^ place1445/Z (BUF_X2)
...
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    8.17 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   17.62    0.02    0.04    8.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
                                         clknet_2_0_0_clk (net)
                  0.02    0.00    8.22 ^ clkbuf_3_0_0_clk/A (CLKBUF_X3)
    12   29.11    0.02    0.05    8.27 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
                                         clknet_3_0_0_clk (net)
                  0.02    0.00    8.27 ^ order_fifo_tid_mem[2][15]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.27   clock reconvergence pessimism
                          0.05    8.32   library recovery time
                                  8.32   data required time
-----------------------------------------------------------------------------
                                  8.32   data required time
                                 -2.47   data arrival time
-----------------------------------------------------------------------------
                                  5.85   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/2_floorplan_final.rpt`
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
                                         _1365_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_detailed_place.rpt`
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
                                         _1365_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_global_place.rpt`
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
                                         _1365_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/3_resizer.rpt`
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
                                         _1365_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5000`
- data_required_time: `0.4400`

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
     1   73.61    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire1454/A (BUF_X16)
     1   56.93    0.01    0.03    0.05 ^ wire1454/Z (BUF_X16)
                                         net1453 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.53    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.72    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   24.26    0.02    0.05    0.25 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_3_2_0_clk (net)
                  0.07    0.04    0.37 ^ clkbuf_leaf_0_clk/A (CLKBUF_X3)
     8   10.16    0.01    0.05    0.43 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
                                         clknet_leaf_0_clk (net)
                  0.01    0.00    0.43 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.43   clock reconvergence pessimism
                          0.01    0.44   library hold time
                                  0.44   data required time
-----------------------------------------------------------------------------
                                  0.44   data required time
                                 -0.50   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5000`
- data_required_time: `0.4400`

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
     1   73.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire1454/A (BUF_X16)
     1   56.67    0.01    0.03    0.05 ^ wire1454/Z (BUF_X16)
                                         net1453 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.40    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.81    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   24.15    0.02    0.05    0.25 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_3_2_0_clk (net)
                  0.07    0.04    0.37 ^ clkbuf_leaf_0_clk/A (CLKBUF_X3)
     8   10.71    0.01    0.06    0.43 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
                                         clknet_leaf_0_clk (net)
                  0.01    0.00    0.43 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.43   clock reconvergence pessimism
                          0.01    0.44   library hold time
                                  0.44   data required time
-----------------------------------------------------------------------------
                                  0.44   data required time
                                 -0.50   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count_q[0]$_DFF_PN0_`
- endpoint: `cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4300`
- data_required_time: `0.3700`

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
     1   53.17    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire1454/A (BUF_X16)
     1   38.87    0.01    0.03    0.05 ^ wire1454/Z (BUF_X16)
                                         net1453 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.95    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.41    0.02    0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   17.72    0.02    0.04    0.21 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_3_2_0_clk (net)
                  0.05    0.03    0.31 ^ clkbuf_leaf_0_clk/A (CLKBUF_X3)
     8   10.75    0.01    0.05    0.36 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
                                         clknet_leaf_0_clk (net)
                  0.01    0.00    0.36 ^ cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_finalizer_bank_control_l8_b8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `order_enqueued_count_q[27]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3700`
- data_arrival_time: `2.0900`
- data_required_time: `0.7100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: order_enqueued_count_q[27]$_DFFE_PN0N_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.06    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input232/A (CLKBUF_X3)
    12   55.68    0.03    0.05    2.05 ^ input232/Z (CLKBUF_X3)
                                         net231 (net)
                  0.06    0.03    2.09 ^ order_enqueued_count_q[27]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   73.61    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire1454/A (BUF_X16)
...
                                         clknet_2_3_0_clk (net)
                  0.02    0.00    0.26 ^ clkbuf_3_7_0_clk/A (CLKBUF_X3)
     4  104.51    0.07    0.10    0.35 ^ clkbuf_3_7_0_clk/Z (CLKBUF_X3)
                                         clknet_3_7_0_clk (net)
                  0.09    0.05    0.40 ^ clkbuf_leaf_29_clk/A (CLKBUF_X3)
     4    5.56    0.01    0.05    0.46 ^ clkbuf_leaf_29_clk/Z (CLKBUF_X3)
                                         clknet_leaf_29_clk (net)
                  0.01    0.00    0.46 ^ order_enqueued_count_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.46   clock reconvergence pessimism
                          0.25    0.71   library removal time
                                  0.71   data required time
-----------------------------------------------------------------------------
                                  0.71   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.37   slack (MET)
```
