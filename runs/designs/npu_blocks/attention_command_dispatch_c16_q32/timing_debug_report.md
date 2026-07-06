# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_command_dispatch_c16_q32`
- metrics_path: `runs/designs/npu_blocks/attention_command_dispatch_c16_q32/metrics.csv`
- rows_considered: 3

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| ea4c1138 | attention_command_dispatch_frontier_ea4c1138 | ok | 0.4629 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt` |
| 5a29a082 | attention_command_dispatch_frontier_5a29a082 | ok | 2.5981 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt` |
| cf4d98b2 | attention_command_dispatch_frontier_cf4d98b2 | ok | 2.6069 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 156
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cluster_ready[5] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4500`
- data_arrival_time: `2.6000`
- data_required_time: `1.1500`

```text
Startpoint: cluster_ready[5] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   24.64    0.00    0.00    2.00 v cluster_ready[5] (in)
                                         cluster_ready[5] (net)
                  0.00    0.00    2.00 v input17/A (BUF_X32)
     2    2.27    0.00    0.02    2.02 v input17/Z (BUF_X32)
                                         net17 (net)
                  0.00    0.00    2.02 v _06837_/B (MUX2_X1)
     1    1.72    0.01    0.06    2.07 v _06837_/Z (MUX2_X1)
                                         _02553_ (net)
                  0.01    0.00    2.07 v _06838_/B (MUX2_X2)
     2    3.74    0.01    0.06    2.13 v _06838_/Z (MUX2_X2)
                                         _02554_ (net)
                  0.01    0.00    2.13 v _07082_/B (MUX2_X1)
     1    1.69    0.01    0.06    2.19 v _07082_/Z (MUX2_X1)
...
                                         clknet_4_7_0_clk (net)
                  0.03    0.00    1.15 ^ clkbuf_leaf_169_clk/A (CLKBUF_X3)
     7   12.30    0.01    0.05    1.19 ^ clkbuf_leaf_169_clk/Z (CLKBUF_X3)
                                         clknet_leaf_169_clk (net)
                  0.01    0.00    1.19 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.19   clock reconvergence pessimism
                         -0.04    1.15   library setup time
                                  1.15   data required time
-----------------------------------------------------------------------------
                                  1.15   data required time
                                 -2.60   data arrival time
-----------------------------------------------------------------------------
                                 -1.45   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_tile_id[14]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.1200`
- data_arrival_time: `2.3700`
- data_required_time: `1.2400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_tile_id[14]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.86    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input70/A (CLKBUF_X3)
     2   20.45    0.02    0.04    2.04 ^ input70/Z (CLKBUF_X3)
                                         net70 (net)
                  0.02    0.00    2.04 ^ place1121/A (BUF_X1)
     2    9.18    0.02    0.04    2.09 ^ place1121/Z (BUF_X1)
                                         net1121 (net)
                  0.02    0.00    2.09 ^ place1122/A (BUF_X4)
    50  120.34    0.04    0.05    2.13 ^ place1122/Z (BUF_X4)
                                         net1122 (net)
                  0.11    0.08    2.21 ^ place1124/A (BUF_X2)
    16   38.14    0.04    0.07    2.28 ^ place1124/Z (BUF_X2)
...
                                         clknet_0_clk (net)
                  0.05    0.00    1.08 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
    14   34.02    0.03    0.07    1.15 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
                                         clknet_4_11_0_clk (net)
                  0.03    0.00    1.15 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     8    9.79    0.01    0.04    1.19 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    1.19 ^ dispatch_tile_id[14]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.19   clock reconvergence pessimism
                          0.05    1.24   library recovery time
                                  1.24   data required time
-----------------------------------------------------------------------------
                                  1.24   data required time
                                 -2.37   data arrival time
-----------------------------------------------------------------------------
                                 -1.12   slack (VIOLATED)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rr_ptr[1]$_DFFE_PN0P_`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.0600`
- data_arrival_time: `1.0900`
- data_required_time: `1.1500`

```text
Startpoint: rr_ptr[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    0.15 ^ clkbuf_4_7_0_clk/Z (CLKBUF_X3)
   0.04    0.19 ^ clkbuf_leaf_157_clk/Z (CLKBUF_X3)
   0.00    0.19 ^ rr_ptr[1]$_DFFE_PN0P_/CK (DFFR_X1)
   0.16    0.35 ^ rr_ptr[1]$_DFFE_PN0P_/Q (DFFR_X1)
   0.08    0.44 ^ _10283_/CO (HA_X1)
   0.07    0.51 ^ place1076/Z (BUF_X4)
   0.08    0.59 ^ _06955_/Z (XOR2_X2)
   0.07    0.65 ^ place1051/Z (BUF_X1)
   0.03    0.68 v _07221_/ZN (OAI22_X1)
   0.03    0.71 ^ _07222_/ZN (NAND2_X1)
   0.04    0.75 v _07379_/ZN (NAND4_X1)
...
   0.00    1.00 ^ clk (in)
   0.07    1.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    1.15 ^ clkbuf_4_7_0_clk/Z (CLKBUF_X3)
   0.05    1.19 ^ clkbuf_leaf_169_clk/Z (CLKBUF_X3)
   0.00    1.19 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
   0.00    1.19   clock reconvergence pessimism
  -0.04    1.15   library setup time
           1.15   data required time
---------------------------------------------------------
           1.15   data required time
          -1.09   data arrival time
---------------------------------------------------------
           0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `inflight[15][0]$_DFFE_PN0P_`
- endpoint: `inflight[15][0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.3100`
- data_required_time: `0.2000`

```text
Startpoint: inflight[15][0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: inflight[15][0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   13.67    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   61.98    0.05    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_4_0_clk/A (CLKBUF_X3)
    13   36.16    0.03    0.07    0.15 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
                                         clknet_4_4_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_197_clk/A (CLKBUF_X3)
     9   10.16    0.01    0.04    0.19 ^ clkbuf_leaf_197_clk/Z (CLKBUF_X3)
                                         clknet_leaf_197_clk (net)
                  0.01    0.00    0.19 ^ inflight[15][0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    3.89    0.01    0.08    0.27 ^ inflight[15][0]$_DFFE_PN0P_/QN (DFFR_X1)
...
                                         clknet_4_4_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_197_clk/A (CLKBUF_X3)
     9   10.16    0.01    0.04    0.19 ^ clkbuf_leaf_197_clk/Z (CLKBUF_X3)
                                         clknet_leaf_197_clk (net)
                  0.01    0.00    0.19 ^ inflight[15][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.19   clock reconvergence pessimism
                          0.01    0.20   library hold time
                                  0.20   data required time
-----------------------------------------------------------------------------
                                  0.20   data required time
                                 -0.31   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_wave_id[6]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7000`
- data_arrival_time: `2.1900`
- data_required_time: `0.4900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_wave_id[6]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.86    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input70/A (CLKBUF_X3)
     2   20.45    0.02    0.04    2.04 ^ input70/Z (CLKBUF_X3)
                                         net70 (net)
                  0.02    0.00    2.04 ^ place1121/A (BUF_X1)
     2    9.18    0.02    0.04    2.09 ^ place1121/Z (BUF_X1)
                                         net1121 (net)
                  0.02    0.00    2.09 ^ place1122/A (BUF_X4)
    50  120.34    0.04    0.05    2.13 ^ place1122/Z (BUF_X4)
                                         net1122 (net)
                  0.09    0.06    2.19 ^ dispatch_wave_id[6]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.19   data arrival time
...
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
    16   39.55    0.03    0.07    0.15 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_201_clk/A (CLKBUF_X3)
     8   10.39    0.01    0.04    0.20 ^ clkbuf_leaf_201_clk/Z (CLKBUF_X3)
                                         clknet_leaf_201_clk (net)
                  0.01    0.00    0.20 ^ dispatch_wave_id[6]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.20   clock reconvergence pessimism
                          0.30    0.49   library removal time
                                  0.49   data required time
-----------------------------------------------------------------------------
                                  0.49   data required time
                                 -2.19   data arrival time
-----------------------------------------------------------------------------
                                  1.70   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cluster_ready[9] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6500`
- data_arrival_time: `2.6000`
- data_required_time: `0.9500`

```text
Startpoint: cluster_ready[9] (input port clocked by clk)
Endpoint: dispatch_cluster_id[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.15    0.00    0.00    2.00 ^ cluster_ready[9] (in)
                                         cluster_ready[9] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X1)
     3    4.33    0.01    0.02    2.02 ^ input21/Z (BUF_X1)
                                         net21 (net)
                  0.01    0.00    2.03 ^ place1184/A (BUF_X1)
     3    3.44    0.01    0.03    2.05 ^ place1184/Z (BUF_X1)
                                         net1184 (net)
                  0.01    0.00    2.05 ^ _06944_/A (MUX2_X1)
     2    2.89    0.01    0.04    2.09 ^ _06944_/Z (MUX2_X1)
                                         _02660_ (net)
                  0.01    0.00    2.09 ^ _07169_/A1 (NOR2_X1)
     1    1.71    0.01    0.01    2.10 v _07169_/ZN (NOR2_X1)
...
                                  2.60   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[0]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    0.95   library setup time
                                  0.95   data required time
-----------------------------------------------------------------------------
                                  0.95   data required time
                                 -2.60   data arrival time
-----------------------------------------------------------------------------
                                 -1.65   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cluster_ready[9] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6500`
- data_arrival_time: `2.6000`
- data_required_time: `0.9500`

```text
Startpoint: cluster_ready[9] (input port clocked by clk)
Endpoint: dispatch_cluster_id[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.30    0.00    0.00    2.00 ^ cluster_ready[9] (in)
                                         cluster_ready[9] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X1)
     3    3.87    0.01    0.02    2.02 ^ input21/Z (BUF_X1)
                                         net21 (net)
                  0.01    0.00    2.02 ^ place1184/A (BUF_X1)
     3    3.26    0.01    0.03    2.05 ^ place1184/Z (BUF_X1)
                                         net1184 (net)
                  0.01    0.00    2.05 ^ _06944_/A (MUX2_X1)
     2    3.02    0.01    0.04    2.09 ^ _06944_/Z (MUX2_X1)
                                         _02660_ (net)
                  0.01    0.00    2.09 ^ _07169_/A1 (NOR2_X1)
     1    1.65    0.01    0.01    2.10 v _07169_/ZN (NOR2_X1)
...
                                  2.60   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[0]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    0.95   library setup time
                                  0.95   data required time
-----------------------------------------------------------------------------
                                  0.95   data required time
                                 -2.60   data arrival time
-----------------------------------------------------------------------------
                                 -1.65   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `cluster_ready[9] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6500`
- data_arrival_time: `2.6000`
- data_required_time: `0.9500`

```text
Startpoint: cluster_ready[9] (input port clocked by clk)
Endpoint: dispatch_cluster_id[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.30    0.00    0.00    2.00 ^ cluster_ready[9] (in)
                                         cluster_ready[9] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X1)
     3    3.87    0.01    0.02    2.02 ^ input21/Z (BUF_X1)
                                         net21 (net)
                  0.01    0.00    2.02 ^ place1184/A (BUF_X1)
     3    3.26    0.01    0.03    2.05 ^ place1184/Z (BUF_X1)
                                         net1184 (net)
                  0.01    0.00    2.05 ^ _06944_/A (MUX2_X1)
     2    3.02    0.01    0.04    2.09 ^ _06944_/Z (MUX2_X1)
                                         _02660_ (net)
                  0.01    0.00    2.09 ^ _07169_/A1 (NOR2_X1)
     1    1.65    0.01    0.01    2.10 v _07169_/ZN (NOR2_X1)
...
                                  2.60   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[0]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    0.95   library setup time
                                  0.95   data required time
-----------------------------------------------------------------------------
                                  0.95   data required time
                                 -2.60   data arrival time
-----------------------------------------------------------------------------
                                 -1.65   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cluster_ready[13] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6100`
- data_arrival_time: `2.5700`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[13] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     5    4.51    0.00    0.00    2.00 v cluster_ready[13] (in)
                                         cluster_ready[13] (net)
                  0.00    0.00    2.00 v _06820_/B (MUX2_X1)
     1    1.48    0.01    0.05    2.05 v _06820_/Z (MUX2_X1)
                                         _02536_ (net)
                  0.01    0.00    2.05 v _06822_/B (MUX2_X2)
     5    6.39    0.01    0.06    2.11 v _06822_/Z (MUX2_X2)
                                         _02538_ (net)
                  0.01    0.00    2.11 v _07082_/A (MUX2_X1)
     1    1.48    0.01    0.06    2.17 v _07082_/Z (MUX2_X1)
                                         _02798_ (net)
                  0.01    0.00    2.17 v _07084_/B (MUX2_X2)
     1    3.01    0.01    0.06    2.23 v _07084_/Z (MUX2_X2)
...
                                  2.57   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.57   data arrival time
-----------------------------------------------------------------------------
                                 -1.61   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `count[0]$_DFFE_PN0P_`
- endpoint: `queue_empty (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4500`
- data_arrival_time: `0.4500`
- data_required_time: `-1.0000`

```text
Startpoint: count[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_empty (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   17.55    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   69.77    0.05    0.08    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_0_0_clk/A (CLKBUF_X3)
    13   35.47    0.03    0.07    0.16 ^ clkbuf_4_0_0_clk/Z (CLKBUF_X3)
                                         clknet_4_0_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_leaf_215_clk/A (CLKBUF_X3)
     6   10.09    0.01    0.04    0.20 ^ clkbuf_leaf_215_clk/Z (CLKBUF_X3)
                                         clknet_leaf_215_clk (net)
                  0.01    0.00    0.20 ^ count[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.56    0.01    0.09    0.29 v count[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net125 (net)
...
                  0.00    0.00    0.45 ^ queue_empty (out)
                                  0.45   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.45   data arrival time
-----------------------------------------------------------------------------
                                 -1.45   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/5_global_route.rpt`
- stage: `route`
- startpoint: `count[0]$_DFFE_PN0P_`
- endpoint: `queue_full (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4500`
- data_arrival_time: `0.4500`
- data_required_time: `-1.0000`

```text
Startpoint: count[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: queue_full (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   17.48    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   70.40    0.05    0.08    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_0_0_clk/A (CLKBUF_X3)
    13   35.42    0.03    0.07    0.16 ^ clkbuf_4_0_0_clk/Z (CLKBUF_X3)
                                         clknet_4_0_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_leaf_215_clk/A (CLKBUF_X3)
     6   10.91    0.01    0.04    0.20 ^ clkbuf_leaf_215_clk/Z (CLKBUF_X3)
                                         clknet_leaf_215_clk (net)
                  0.01    0.00    0.20 ^ count[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.88    0.01    0.10    0.30 v count[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net125 (net)
...
                  0.00    0.00    0.45 ^ queue_full (out)
                                  0.45   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -0.45   data arrival time
-----------------------------------------------------------------------------
                                 -1.45   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cluster_ready[5] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4500`
- data_arrival_time: `2.6000`
- data_required_time: `1.1500`

```text
Startpoint: cluster_ready[5] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   24.64    0.00    0.00    2.00 v cluster_ready[5] (in)
                                         cluster_ready[5] (net)
                  0.00    0.00    2.00 v input17/A (BUF_X32)
     2    2.27    0.00    0.02    2.02 v input17/Z (BUF_X32)
                                         net17 (net)
                  0.00    0.00    2.02 v _06837_/B (MUX2_X1)
     1    1.72    0.01    0.06    2.07 v _06837_/Z (MUX2_X1)
                                         _02553_ (net)
                  0.01    0.00    2.07 v _06838_/B (MUX2_X2)
     2    3.74    0.01    0.06    2.13 v _06838_/Z (MUX2_X2)
                                         _02554_ (net)
                  0.01    0.00    2.13 v _07082_/B (MUX2_X1)
     1    1.69    0.01    0.06    2.19 v _07082_/Z (MUX2_X1)
...
                                         clknet_4_7_0_clk (net)
                  0.03    0.00    1.15 ^ clkbuf_leaf_169_clk/A (CLKBUF_X3)
     7   12.30    0.01    0.05    1.19 ^ clkbuf_leaf_169_clk/Z (CLKBUF_X3)
                                         clknet_leaf_169_clk (net)
                  0.01    0.00    1.19 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.19   clock reconvergence pessimism
                         -0.04    1.15   library setup time
                                  1.15   data required time
-----------------------------------------------------------------------------
                                  1.15   data required time
                                 -2.60   data arrival time
-----------------------------------------------------------------------------
                                 -1.45   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c16_q32/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `dispatch_tile_id[14]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.2900`
- data_arrival_time: `2.3400`
- data_required_time: `1.0500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: dispatch_tile_id[14]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    4.81    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input70/A (CLKBUF_X3)
     2   18.15    0.02    0.04    2.04 ^ input70/Z (CLKBUF_X3)
                                         net70 (net)
                  0.02    0.01    2.04 ^ place1121/A (BUF_X1)
     2    8.80    0.02    0.04    2.08 ^ place1121/Z (BUF_X1)
                                         net1121 (net)
                  0.02    0.00    2.08 ^ place1122/A (BUF_X4)
    50  119.45    0.06    0.07    2.15 ^ place1122/Z (BUF_X4)
                                         net1122 (net)
                  0.07    0.03    2.19 ^ place1124/A (BUF_X2)
    16   37.05    0.04    0.07    2.26 ^ place1124/Z (BUF_X2)
                                         net1124 (net)
                  0.04    0.00    2.26 ^ place1125/A (BUF_X4)
    26   68.18    0.03    0.05    2.31 ^ place1125/Z (BUF_X4)
                                         net1125 (net)
                  0.05    0.03    2.34 ^ dispatch_tile_id[14]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.34   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_tile_id[14]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.05    1.05   library recovery time
                                  1.05   data required time
-----------------------------------------------------------------------------
                                  1.05   data required time
                                 -2.34   data arrival time
-----------------------------------------------------------------------------
                                 -1.29   slack (VIOLATED)
```
