# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_command_dispatch_c8_q16`
- metrics_path: `runs/designs/npu_blocks/attention_command_dispatch_c8_q16/metrics.csv`
- rows_considered: 3

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 5a29a082 | attention_command_dispatch_frontier_5a29a082 | ok | 0.3899 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt` |
| ea4c1138 | attention_command_dispatch_frontier_ea4c1138 | ok | 0.3989 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt` |
| cf4d98b2 | attention_command_dispatch_frontier_cf4d98b2 | ok | 0.4041 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 156
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `count[2]$_DFFE_PN0P_`
- endpoint: `queue_full (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3900`
- data_arrival_time: `0.3900`
- data_required_time: `-1.0000`

```text
Startpoint: count[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_full (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1    9.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   45.28    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.06 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
     8   19.85    0.02    0.05    0.12 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_5_clk/A (CLKBUF_X3)
     7   11.72    0.01    0.04    0.16 ^ clkbuf_leaf_5_clk/Z (CLKBUF_X3)
                                         clknet_leaf_5_clk (net)
                  0.01    0.00    0.16 ^ count[2]$_DFFE_PN0P_/CK (DFFR_X1)
     2    7.54    0.01    0.10    0.26 v count[2]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net117 (net)
...
                  0.00    0.00    0.39 ^ queue_full (out)
                                  0.39   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                 -1.39   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_base_token[13]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.0600`
- data_arrival_time: `2.2600`
- data_required_time: `1.2000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_base_token[13]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.56    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input61/A (CLKBUF_X3)
     5   23.75    0.02    0.04    2.04 ^ input61/Z (CLKBUF_X3)
                                         net61 (net)
                  0.02    0.00    2.04 ^ place497/A (BUF_X1)
    10   38.92    0.09    0.11    2.16 ^ place497/Z (BUF_X1)
                                         net497 (net)
                  0.09    0.00    2.16 ^ place498/A (BUF_X1)
    12   30.82    0.07    0.10    2.26 ^ place498/Z (BUF_X1)
                                         net498 (net)
                  0.07    0.00    2.26 ^ dispatch_base_token[13]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.26   data arrival time
...
                                         clknet_0_clk (net)
                  0.04    0.00    1.06 ^ clkbuf_4_15_0_clk/A (CLKBUF_X3)
     8   20.00    0.02    0.05    1.12 ^ clkbuf_4_15_0_clk/Z (CLKBUF_X3)
                                         clknet_4_15_0_clk (net)
                  0.02    0.00    1.12 ^ clkbuf_leaf_44_clk/A (CLKBUF_X3)
     8    9.48    0.01    0.04    1.16 ^ clkbuf_leaf_44_clk/Z (CLKBUF_X3)
                                         clknet_leaf_44_clk (net)
                  0.01    0.00    1.16 ^ dispatch_base_token[13]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.16   clock reconvergence pessimism
                          0.05    1.20   library recovery time
                                  1.20   data required time
-----------------------------------------------------------------------------
                                  1.20   data required time
                                 -2.26   data arrival time
-----------------------------------------------------------------------------
                                 -1.06   slack (VIOLATED)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `inflight[6][0]$_DFFE_PN0P_`
- endpoint: `inflight[6][0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.2700`
- data_required_time: `0.1600`

```text
Startpoint: inflight[6][0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: inflight[6][0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1    9.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   45.28    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.06 ^ clkbuf_4_5_0_clk/A (CLKBUF_X3)
     7   19.44    0.02    0.05    0.12 ^ clkbuf_4_5_0_clk/Z (CLKBUF_X3)
                                         clknet_4_5_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_14_clk/A (CLKBUF_X3)
     7    9.55    0.01    0.04    0.16 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
                                         clknet_leaf_14_clk (net)
                  0.01    0.00    0.16 ^ inflight[6][0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.27    0.02    0.08    0.23 ^ inflight[6][0]$_DFFE_PN0P_/QN (DFFR_X1)
...
                                         clknet_4_5_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_14_clk/A (CLKBUF_X3)
     7    9.55    0.01    0.04    0.16 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
                                         clknet_leaf_14_clk (net)
                  0.01    0.00    0.16 ^ inflight[6][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rr_ptr[1]$_DFFE_PN0P_`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.2100`
- data_arrival_time: `0.9100`
- data_required_time: `1.1200`

```text
Startpoint: rr_ptr[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.12 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
   0.04    0.16 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
   0.00    0.16 ^ rr_ptr[1]$_DFFE_PN0P_/CK (DFFR_X1)
   0.20    0.35 ^ rr_ptr[1]$_DFFE_PN0P_/Q (DFFR_X1)
   0.13    0.48 ^ _5052_/CO (HA_X1)
   0.05    0.53 v _3442_/ZN (AOI222_X1)
   0.07    0.60 v _3445_/Z (MUX2_X1)
   0.08    0.68 ^ _3447_/ZN (AOI21_X1)
   0.02    0.70 v _3461_/ZN (NOR4_X4)
   0.06    0.76 v _3500_/ZN (OR3_X4)
   0.03    0.79 v place323/Z (BUF_X8)
...
   0.00    1.00 ^ clk (in)
   0.06    1.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    1.12 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
   0.04    1.16 ^ clkbuf_leaf_12_clk/Z (CLKBUF_X3)
   0.00    1.16 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    1.16   clock reconvergence pessimism
  -0.04    1.12   library setup time
           1.12   data required time
---------------------------------------------------------
           1.12   data required time
          -0.91   data arrival time
---------------------------------------------------------
           0.21   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_tile_id[2]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7100`
- data_arrival_time: `2.1600`
- data_required_time: `0.4500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_tile_id[2]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.56    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input61/A (CLKBUF_X3)
     5   23.75    0.02    0.04    2.04 ^ input61/Z (CLKBUF_X3)
                                         net61 (net)
                  0.02    0.00    2.04 ^ place497/A (BUF_X1)
    10   38.92    0.09    0.11    2.16 ^ place497/Z (BUF_X1)
                                         net497 (net)
                  0.09    0.00    2.16 ^ dispatch_tile_id[2]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.16   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_0_clk (net)
                  0.04    0.00    0.06 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     9   19.04    0.02    0.05    0.12 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     9   10.53    0.01    0.04    0.16 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.16 ^ dispatch_tile_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.29    0.45   library removal time
                                  0.45   data required time
-----------------------------------------------------------------------------
                                  0.45   data required time
                                 -2.16   data arrival time
-----------------------------------------------------------------------------
                                  1.71   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cluster_ready[3] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4800`
- data_arrival_time: `2.4400`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[3] (input port clocked by clk)
Endpoint: dispatch_cluster_id[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.22    0.00    0.00    2.00 ^ cluster_ready[3] (in)
                                         cluster_ready[3] (net)
                  0.00    0.00    2.00 ^ input8/A (BUF_X1)
     4    5.09    0.01    0.03    2.03 ^ input8/Z (BUF_X1)
                                         net8 (net)
                  0.01    0.00    2.03 ^ _3410_/B (MUX2_X1)
     2    2.87    0.01    0.04    2.07 ^ _3410_/Z (MUX2_X1)
                                         _1335_ (net)
                  0.01    0.00    2.07 ^ _3490_/A2 (NOR2_X1)
     1    3.12    0.01    0.01    2.08 v _3490_/ZN (NOR2_X1)
                                         _1415_ (net)
                  0.01    0.00    2.08 v _3492_/B (AOI211_X2)
     1    3.26    0.04    0.06    2.14 ^ _3492_/ZN (AOI211_X2)
...
                                  2.44   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[0]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.44   data arrival time
-----------------------------------------------------------------------------
                                 -1.48   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cluster_ready[4] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4800`
- data_arrival_time: `2.4300`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[4] (input port clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.20    0.00    0.00    2.00 v cluster_ready[4] (in)
                                         cluster_ready[4] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X1)
     3    3.03    0.01    0.03    2.03 v input9/Z (BUF_X1)
                                         net9 (net)
                  0.01    0.00    2.03 v _3476_/B (MUX2_X1)
     1    1.59    0.01    0.06    2.08 v _3476_/Z (MUX2_X1)
                                         _1401_ (net)
                  0.01    0.00    2.08 v _3477_/B (MUX2_X2)
     3    4.70    0.01    0.06    2.14 v _3477_/Z (MUX2_X2)
                                         _1402_ (net)
                  0.01    0.00    2.14 v _3522_/A3 (AND4_X2)
     1    3.02    0.01    0.04    2.18 v _3522_/ZN (AND4_X2)
...
                                  2.43   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.43   data arrival time
-----------------------------------------------------------------------------
                                 -1.48   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `cluster_ready[4] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4800`
- data_arrival_time: `2.4300`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[4] (input port clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.20    0.00    0.00    2.00 v cluster_ready[4] (in)
                                         cluster_ready[4] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X1)
     3    3.03    0.01    0.03    2.03 v input9/Z (BUF_X1)
                                         net9 (net)
                  0.01    0.00    2.03 v _3476_/B (MUX2_X1)
     1    1.59    0.01    0.06    2.08 v _3476_/Z (MUX2_X1)
                                         _1401_ (net)
                  0.01    0.00    2.08 v _3477_/B (MUX2_X2)
     3    4.70    0.01    0.06    2.14 v _3477_/Z (MUX2_X2)
                                         _1402_ (net)
                  0.01    0.00    2.14 v _3522_/A3 (AND4_X2)
     1    3.02    0.01    0.04    2.18 v _3522_/ZN (AND4_X2)
...
                                  2.43   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.43   data arrival time
-----------------------------------------------------------------------------
                                 -1.48   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cluster_ready[4] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4600`
- data_arrival_time: `2.4100`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[4] (input port clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     4    3.61    0.00    0.00    2.00 v cluster_ready[4] (in)
                                         cluster_ready[4] (net)
                  0.00    0.00    2.00 v _3476_/B (MUX2_X1)
     1    1.48    0.01    0.05    2.05 v _3476_/Z (MUX2_X1)
                                         _1401_ (net)
                  0.01    0.00    2.05 v _3477_/B (MUX2_X2)
     4    5.50    0.01    0.06    2.11 v _3477_/Z (MUX2_X2)
                                         _1402_ (net)
                  0.01    0.00    2.11 v _3522_/A3 (AND4_X2)
     1    2.98    0.01    0.04    2.15 v _3522_/ZN (AND4_X2)
                                         _1447_ (net)
                  0.01    0.00    2.15 v _3527_/B2 (OAI221_X2)
     4   12.69    0.06    0.07    2.22 ^ _3527_/ZN (OAI221_X2)
...
                                  2.41   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.41   data arrival time
-----------------------------------------------------------------------------
                                 -1.46   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/5_global_route.rpt`
- stage: `route`
- startpoint: `count[2]$_DFFE_PN0P_`
- endpoint: `queue_full (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4000`
- data_arrival_time: `0.4000`
- data_required_time: `-1.0000`

```text
Startpoint: count[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_full (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.98    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   51.01    0.04    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
     8   20.18    0.02    0.06    0.12 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_5_clk/A (CLKBUF_X3)
     7   11.40    0.01    0.04    0.16 ^ clkbuf_leaf_5_clk/Z (CLKBUF_X3)
                                         clknet_leaf_5_clk (net)
                  0.01    0.00    0.17 ^ count[2]$_DFFE_PN0P_/CK (DFFR_X1)
     2    7.64    0.01    0.10    0.26 v count[2]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net117 (net)
...
                  0.00    0.00    0.40 ^ queue_full (out)
                                  0.40   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.40   data arrival time
-----------------------------------------------------------------------------
                                 -1.40   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `count[2]$_DFFE_PN0P_`
- endpoint: `queue_full (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3900`
- data_arrival_time: `0.3900`
- data_required_time: `-1.0000`

```text
Startpoint: count[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_full (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   50.02    0.04    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
     8   19.86    0.02    0.06    0.12 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_5_clk/A (CLKBUF_X3)
     7   10.57    0.01    0.04    0.16 ^ clkbuf_leaf_5_clk/Z (CLKBUF_X3)
                                         clknet_leaf_5_clk (net)
                  0.01    0.00    0.16 ^ count[2]$_DFFE_PN0P_/CK (DFFR_X1)
     2    7.45    0.01    0.10    0.26 v count[2]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net117 (net)
...
                  0.00    0.00    0.39 ^ queue_full (out)
                                  0.39   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                 -1.39   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/6_finish.rpt`
- stage: `finish`
- startpoint: `count[2]$_DFFE_PN0P_`
- endpoint: `queue_full (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3900`
- data_arrival_time: `0.3900`
- data_required_time: `-1.0000`

```text
Startpoint: count[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_full (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1    9.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   45.28    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.06 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
     8   19.85    0.02    0.05    0.12 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_5_clk/A (CLKBUF_X3)
     7   11.72    0.01    0.04    0.16 ^ clkbuf_leaf_5_clk/Z (CLKBUF_X3)
                                         clknet_leaf_5_clk (net)
                  0.01    0.00    0.16 ^ count[2]$_DFFE_PN0P_/CK (DFFR_X1)
     2    7.54    0.01    0.10    0.26 v count[2]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net117 (net)
...
                  0.00    0.00    0.39 ^ queue_full (out)
                                  0.39   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                 -1.39   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c8_q16/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_tile_id[11]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.2200`
- data_arrival_time: `2.2600`
- data_required_time: `1.0400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_tile_id[11]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    3.64    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input61/A (CLKBUF_X3)
     5   23.64    0.02    0.04    2.04 ^ input61/Z (CLKBUF_X3)
                                         net61 (net)
                  0.02    0.00    2.04 ^ place497/A (BUF_X1)
    10   40.94    0.09    0.12    2.16 ^ place497/Z (BUF_X1)
                                         net497 (net)
                  0.09    0.00    2.16 ^ place498/A (BUF_X1)
    12   30.14    0.07    0.10    2.26 ^ place498/Z (BUF_X1)
                                         net498 (net)
                  0.07    0.00    2.26 ^ dispatch_tile_id[11]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.26   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_tile_id[11]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.04    1.04   library recovery time
                                  1.04   data required time
-----------------------------------------------------------------------------
                                  1.04   data required time
                                 -2.26   data arrival time
-----------------------------------------------------------------------------
                                 -1.22   slack (VIOLATED)
```
