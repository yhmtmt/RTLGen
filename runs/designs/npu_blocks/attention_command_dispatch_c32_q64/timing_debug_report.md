# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_command_dispatch_c32_q64`
- metrics_path: `runs/designs/npu_blocks/attention_command_dispatch_c32_q64/metrics.csv`
- rows_considered: 3

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 5a29a082 | attention_command_dispatch_frontier_5a29a082 | ok | 2.8220 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt` |
| cf4d98b2 | attention_command_dispatch_frontier_cf4d98b2 | ok | 2.8313 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt` |
| ea4c1138 | attention_command_dispatch_frontier_ea4c1138 | ok | 2.8448 | 0.45 | `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 156
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cluster_ready[3] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6300`
- data_arrival_time: `2.8200`
- data_required_time: `1.1900`

```text
Startpoint: cluster_ready[3] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    2.31    0.00    0.00    2.00 v cluster_ready[3] (in)
                                         cluster_ready[3] (net)
                  0.00    0.00    2.00 v input32/A (BUF_X2)
     4    5.15    0.01    0.02    2.02 v input32/Z (BUF_X2)
                                         net32 (net)
                  0.01    0.00    2.02 v _15996_/A (MUX2_X1)
     2    2.40    0.01    0.06    2.08 v _15996_/Z (MUX2_X1)
                                         _09485_ (net)
                  0.01    0.00    2.08 v _15997_/B (MUX2_X1)
     2    6.75    0.02    0.07    2.15 v _15997_/Z (MUX2_X1)
                                         _09486_ (net)
                  0.02    0.00    2.15 v _17362_/B (MUX2_X1)
     1    1.00    0.01    0.06    2.21 v _17362_/Z (MUX2_X1)
...
                                         clknet_5_27__leaf_clk (net)
                  0.02    0.00    1.19 ^ clkbuf_leaf_249_clk/A (CLKBUF_X3)
     5    8.52    0.01    0.04    1.22 ^ clkbuf_leaf_249_clk/Z (CLKBUF_X3)
                                         clknet_leaf_249_clk (net)
                  0.01    0.00    1.22 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.22   clock reconvergence pessimism
                         -0.04    1.19   library setup time
                                  1.19   data required time
-----------------------------------------------------------------------------
                                  1.19   data required time
                                 -2.82   data arrival time
-----------------------------------------------------------------------------
                                 -1.63   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `inflight[13][0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.1200`
- data_arrival_time: `2.4000`
- data_required_time: `1.2800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: inflight[13][0]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    1.89    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input87/A (CLKBUF_X3)
     2   24.36    0.02    0.04    2.04 ^ input87/Z (CLKBUF_X3)
                                         net87 (net)
                  0.02    0.00    2.04 ^ place4646/A (BUF_X1)
    12   34.25    0.08    0.10    2.15 ^ place4646/Z (BUF_X1)
                                         net4646 (net)
                  0.08    0.00    2.15 ^ place4648/A (BUF_X2)
    27   66.82    0.07    0.10    2.25 ^ place4648/Z (BUF_X2)
                                         net4648 (net)
                  0.07    0.01    2.26 ^ place4649/A (BUF_X1)
    22   47.82    0.11    0.14    2.40 ^ place4649/Z (BUF_X1)
...
                                         clknet_4_5_0_clk (net)
                  0.01    0.00    1.14 ^ clkbuf_5_11__f_clk/A (CLKBUF_X3)
    14   36.60    0.03    0.06    1.20 ^ clkbuf_5_11__f_clk/Z (CLKBUF_X3)
                                         clknet_5_11__leaf_clk (net)
                  0.03    0.00    1.20 ^ clkbuf_leaf_285_clk/A (CLKBUF_X3)
     9   10.26    0.01    0.04    1.24 ^ clkbuf_leaf_285_clk/Z (CLKBUF_X3)
                                         clknet_leaf_285_clk (net)
                  0.01    0.00    1.24 ^ inflight[13][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.24   clock reconvergence pessimism
                          0.04    1.28   library recovery time
                                  1.28   data required time
-----------------------------------------------------------------------------
                                  1.28   data required time
                                 -2.40   data arrival time
-----------------------------------------------------------------------------
                                 -1.12   slack (VIOLATED)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rr_ptr[1]$_DFFE_PN0P_`
- endpoint: `dispatch_cluster_id[1]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-0.2100`
- data_arrival_time: `1.4000`
- data_required_time: `1.1900`

```text
Startpoint: rr_ptr[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: dispatch_cluster_id[1]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.09    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.14 ^ clkbuf_4_7_0_clk/Z (CLKBUF_X3)
   0.05    0.19 ^ clkbuf_5_15__f_clk/Z (CLKBUF_X3)
   0.04    0.23 ^ clkbuf_leaf_269_clk/Z (CLKBUF_X3)
   0.00    0.23 ^ rr_ptr[1]$_DFFE_PN0P_/CK (DFFR_X2)
   0.14    0.37 ^ rr_ptr[1]$_DFFE_PN0P_/Q (DFFR_X2)
   0.05    0.42 ^ _22552_/CO (HA_X1)
   0.03    0.45 v _13164_/ZN (NAND2_X1)
   0.03    0.47 ^ _13165_/ZN (INV_X1)
   0.11    0.59 ^ _22563_/S (HA_X1)
   0.02    0.61 v _16679_/ZN (AOI21_X1)
   0.03    0.64 ^ _16682_/ZN (OAI221_X1)
...
   0.09    1.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    1.14 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
   0.05    1.19 ^ clkbuf_5_26__f_clk/Z (CLKBUF_X3)
   0.04    1.23 ^ clkbuf_leaf_250_clk/Z (CLKBUF_X3)
   0.00    1.23 ^ dispatch_cluster_id[1]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    1.23   clock reconvergence pessimism
  -0.04    1.19   library setup time
           1.19   data required time
---------------------------------------------------------
           1.19   data required time
          -1.40   data arrival time
---------------------------------------------------------
          -0.21   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `inflight[22][0]$_DFFE_PN0P_`
- endpoint: `inflight[22][0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.3600`
- data_required_time: `0.2500`

```text
Startpoint: inflight[22][0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: inflight[22][0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   18.50    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   76.45    0.06    0.08    0.09 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.06    0.00    0.09 ^ clkbuf_4_5_0_clk/A (CLKBUF_X3)
     2    6.12    0.01    0.05    0.14 ^ clkbuf_4_5_0_clk/Z (CLKBUF_X3)
                                         clknet_4_5_0_clk (net)
                  0.01    0.00    0.14 ^ clkbuf_5_10__f_clk/A (CLKBUF_X3)
    16   37.45    0.03    0.06    0.20 ^ clkbuf_5_10__f_clk/Z (CLKBUF_X3)
                                         clknet_5_10__leaf_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_leaf_277_clk/A (CLKBUF_X3)
     8   10.37    0.01    0.04    0.24 ^ clkbuf_leaf_277_clk/Z (CLKBUF_X3)
...
                                         clknet_5_10__leaf_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_leaf_277_clk/A (CLKBUF_X3)
     8   10.37    0.01    0.04    0.24 ^ clkbuf_leaf_277_clk/Z (CLKBUF_X3)
                                         clknet_leaf_277_clk (net)
                  0.01    0.00    0.24 ^ inflight[22][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.24   clock reconvergence pessimism
                          0.01    0.25   library hold time
                                  0.25   data required time
-----------------------------------------------------------------------------
                                  0.25   data required time
                                 -0.36   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `inflight[16][1]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6200`
- data_arrival_time: `2.1500`
- data_required_time: `0.5300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: inflight[16][1]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    1.89    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input87/A (CLKBUF_X3)
     2   24.36    0.02    0.04    2.04 ^ input87/Z (CLKBUF_X3)
                                         net87 (net)
                  0.02    0.00    2.04 ^ place4646/A (BUF_X1)
    12   34.25    0.08    0.10    2.15 ^ place4646/Z (BUF_X1)
                                         net4646 (net)
                  0.08    0.00    2.15 ^ inflight[16][1]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.15   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_4_5_0_clk (net)
                  0.01    0.00    0.14 ^ clkbuf_5_10__f_clk/A (CLKBUF_X3)
    16   37.45    0.03    0.06    0.20 ^ clkbuf_5_10__f_clk/Z (CLKBUF_X3)
                                         clknet_5_10__leaf_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_leaf_276_clk/A (CLKBUF_X3)
     8   10.93    0.01    0.04    0.24 ^ clkbuf_leaf_276_clk/Z (CLKBUF_X3)
                                         clknet_leaf_276_clk (net)
                  0.01    0.00    0.24 ^ inflight[16][1]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.24   clock reconvergence pessimism
                          0.28    0.53   library removal time
                                  0.53   data required time
-----------------------------------------------------------------------------
                                  0.53   data required time
                                 -2.15   data arrival time
-----------------------------------------------------------------------------
                                  1.62   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cluster_ready[30] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.8900`
- data_arrival_time: `2.8500`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[30] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.30    0.00    0.00    2.00 v cluster_ready[30] (in)
                                         cluster_ready[30] (net)
                  0.00    0.00    2.00 v input30/A (BUF_X1)
     4    4.78    0.01    0.03    2.03 v input30/Z (BUF_X1)
                                         net30 (net)
                  0.01    0.00    2.03 v _16193_/B (MUX2_X1)
     2    2.13    0.01    0.06    2.09 v _16193_/Z (MUX2_X1)
                                         _09682_ (net)
                  0.01    0.00    2.09 v _16599_/B (MUX2_X1)
     3    4.69    0.01    0.07    2.15 v _16599_/Z (MUX2_X1)
                                         _03619_ (net)
                  0.01    0.00    2.15 v _16898_/B (MUX2_X1)
     1    1.05    0.01    0.06    2.21 v _16898_/Z (MUX2_X1)
...
                                  2.85   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.85   data arrival time
-----------------------------------------------------------------------------
                                 -1.89   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `cluster_ready[30] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.8900`
- data_arrival_time: `2.8500`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[30] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.30    0.00    0.00    2.00 v cluster_ready[30] (in)
                                         cluster_ready[30] (net)
                  0.00    0.00    2.00 v input30/A (BUF_X1)
     4    4.78    0.01    0.03    2.03 v input30/Z (BUF_X1)
                                         net30 (net)
                  0.01    0.00    2.03 v _16193_/B (MUX2_X1)
     2    2.13    0.01    0.06    2.09 v _16193_/Z (MUX2_X1)
                                         _09682_ (net)
                  0.01    0.00    2.09 v _16599_/B (MUX2_X1)
     3    4.69    0.01    0.07    2.15 v _16599_/Z (MUX2_X1)
                                         _03619_ (net)
                  0.01    0.00    2.15 v _16898_/B (MUX2_X1)
     1    1.05    0.01    0.06    2.21 v _16898_/Z (MUX2_X1)
...
                                  2.85   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.85   data arrival time
-----------------------------------------------------------------------------
                                 -1.89   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cluster_ready[7] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.8800`
- data_arrival_time: `2.8500`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[7] (input port clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.06    0.00    0.00    2.00 v cluster_ready[7] (in)
                                         cluster_ready[7] (net)
                  0.00    0.00    2.00 v input36/A (BUF_X1)
     4    4.61    0.01    0.03    2.03 v input36/Z (BUF_X1)
                                         net36 (net)
                  0.01    0.00    2.03 v _16004_/A (MUX2_X1)
     1    1.12    0.01    0.06    2.08 v _16004_/Z (MUX2_X1)
                                         _09493_ (net)
                  0.01    0.00    2.08 v _16005_/B (MUX2_X1)
     4    7.86    0.02    0.07    2.16 v _16005_/Z (MUX2_X1)
                                         _09494_ (net)
                  0.02    0.00    2.16 v _17361_/B (MUX2_X1)
     1    0.95    0.01    0.06    2.21 v _17361_/Z (MUX2_X1)
...
                                  2.85   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.85   data arrival time
-----------------------------------------------------------------------------
                                 -1.88   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cluster_ready[1] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.8300`
- data_arrival_time: `2.7800`
- data_required_time: `0.9600`

```text
Startpoint: cluster_ready[1] (input port clocked by clk)
Endpoint: dispatch_cluster_id[2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     4    3.61    0.00    0.00    2.00 v cluster_ready[1] (in)
                                         cluster_ready[1] (net)
                  0.00    0.00    2.00 v _15996_/B (MUX2_X1)
     2    2.46    0.01    0.06    2.06 v _15996_/Z (MUX2_X1)
                                         _09485_ (net)
                  0.01    0.00    2.06 v _15997_/B (MUX2_X1)
     3    3.30    0.01    0.06    2.12 v _15997_/Z (MUX2_X1)
                                         _09486_ (net)
                  0.01    0.00    2.12 v _17362_/B (MUX2_X1)
     1    0.90    0.01    0.06    2.18 v _17362_/Z (MUX2_X1)
                                         _04382_ (net)
                  0.01    0.00    2.18 v _17363_/B (MUX2_X1)
     2    4.51    0.01    0.07    2.24 v _17363_/Z (MUX2_X1)
...
                                  2.78   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ dispatch_cluster_id[2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.78   data arrival time
-----------------------------------------------------------------------------
                                 -1.83   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cluster_ready[3] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6300`
- data_arrival_time: `2.8200`
- data_required_time: `1.1900`

```text
Startpoint: cluster_ready[3] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    2.31    0.00    0.00    2.00 v cluster_ready[3] (in)
                                         cluster_ready[3] (net)
                  0.00    0.00    2.00 v input32/A (BUF_X2)
     4    5.15    0.01    0.02    2.02 v input32/Z (BUF_X2)
                                         net32 (net)
                  0.01    0.00    2.02 v _15996_/A (MUX2_X1)
     2    2.40    0.01    0.06    2.08 v _15996_/Z (MUX2_X1)
                                         _09485_ (net)
                  0.01    0.00    2.08 v _15997_/B (MUX2_X1)
     2    6.75    0.02    0.07    2.15 v _15997_/Z (MUX2_X1)
                                         _09486_ (net)
                  0.02    0.00    2.15 v _17362_/B (MUX2_X1)
     1    1.00    0.01    0.06    2.21 v _17362_/Z (MUX2_X1)
...
                                         clknet_5_27__leaf_clk (net)
                  0.02    0.00    1.19 ^ clkbuf_leaf_249_clk/A (CLKBUF_X3)
     5    8.52    0.01    0.04    1.22 ^ clkbuf_leaf_249_clk/Z (CLKBUF_X3)
                                         clknet_leaf_249_clk (net)
                  0.01    0.00    1.22 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.22   clock reconvergence pessimism
                         -0.04    1.19   library setup time
                                  1.19   data required time
-----------------------------------------------------------------------------
                                  1.19   data required time
                                 -2.82   data arrival time
-----------------------------------------------------------------------------
                                 -1.63   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cluster_ready[23] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6200`
- data_arrival_time: `2.8100`
- data_required_time: `1.1900`

```text
Startpoint: cluster_ready[23] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   24.11    0.00    0.00    2.00 v cluster_ready[23] (in)
                                         cluster_ready[23] (net)
                  0.00    0.00    2.00 v input22/A (BUF_X32)
     4    5.08    0.00    0.02    2.02 v input22/Z (BUF_X32)
                                         net22 (net)
                  0.00    0.00    2.02 v _16281_/B (MUX2_X1)
     2    2.72    0.01    0.06    2.08 v _16281_/Z (MUX2_X1)
                                         _09770_ (net)
                  0.01    0.00    2.08 v _16594_/B (MUX2_X1)
     3    4.81    0.01    0.07    2.14 v _16594_/Z (MUX2_X1)
                                         _03614_ (net)
                  0.01    0.00    2.14 v _16596_/A (MUX2_X1)
     1    1.61    0.01    0.06    2.20 v _16596_/Z (MUX2_X1)
...
                                         clknet_5_27__leaf_clk (net)
                  0.02    0.00    1.19 ^ clkbuf_leaf_249_clk/A (CLKBUF_X3)
     5    8.44    0.01    0.04    1.23 ^ clkbuf_leaf_249_clk/Z (CLKBUF_X3)
                                         clknet_leaf_249_clk (net)
                  0.01    0.00    1.23 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.23   clock reconvergence pessimism
                         -0.04    1.19   library setup time
                                  1.19   data required time
-----------------------------------------------------------------------------
                                  1.19   data required time
                                 -2.81   data arrival time
-----------------------------------------------------------------------------
                                 -1.62   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cluster_ready[23] (input port clocked by clk)`
- endpoint: `dispatch_cluster_id[3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.6200`
- data_arrival_time: `2.8200`
- data_required_time: `1.2000`

```text
Startpoint: cluster_ready[23] (input port clocked by clk)
Endpoint: dispatch_cluster_id[3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   24.86    0.00    0.00    2.00 v cluster_ready[23] (in)
                                         cluster_ready[23] (net)
                  0.00    0.00    2.00 v input22/A (BUF_X32)
     4    5.36    0.00    0.02    2.02 v input22/Z (BUF_X32)
                                         net22 (net)
                  0.00    0.00    2.02 v _16281_/B (MUX2_X1)
     2    3.07    0.01    0.06    2.08 v _16281_/Z (MUX2_X1)
                                         _09770_ (net)
                  0.01    0.00    2.08 v _16594_/B (MUX2_X1)
     3    5.02    0.01    0.07    2.15 v _16594_/Z (MUX2_X1)
                                         _03614_ (net)
                  0.01    0.00    2.15 v _16596_/A (MUX2_X1)
     1    1.86    0.01    0.06    2.21 v _16596_/Z (MUX2_X1)
...
                                         clknet_5_27__leaf_clk (net)
                  0.02    0.00    1.19 ^ clkbuf_leaf_249_clk/A (CLKBUF_X3)
     5    8.78    0.01    0.04    1.23 ^ clkbuf_leaf_249_clk/Z (CLKBUF_X3)
                                         clknet_leaf_249_clk (net)
                  0.01    0.00    1.23 ^ dispatch_cluster_id[3]$_DFFE_PN0P_/CK (DFFR_X2)
                          0.00    1.23   clock reconvergence pessimism
                         -0.04    1.20   library setup time
                                  1.20   data required time
-----------------------------------------------------------------------------
                                  1.20   data required time
                                 -2.82   data arrival time
-----------------------------------------------------------------------------
                                 -1.62   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_command_dispatch_c32_q64/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `inflight[8][0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.3500`
- data_arrival_time: `2.3900`
- data_required_time: `1.0400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: inflight[8][0]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.88    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input87/A (CLKBUF_X3)
     2   24.44    0.02    0.04    2.04 ^ input87/Z (CLKBUF_X3)
                                         net87 (net)
                  0.02    0.00    2.04 ^ place4646/A (BUF_X1)
    12   30.64    0.07    0.09    2.14 ^ place4646/Z (BUF_X1)
                                         net4646 (net)
                  0.07    0.00    2.14 ^ place4648/A (BUF_X2)
    27   63.27    0.07    0.10    2.24 ^ place4648/Z (BUF_X2)
                                         net4648 (net)
                  0.07    0.01    2.24 ^ place4649/A (BUF_X1)
    22   47.12    0.11    0.14    2.38 ^ place4649/Z (BUF_X1)
                                         net4649 (net)
                  0.11    0.00    2.39 ^ inflight[8][0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.39   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ inflight[8][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.04    1.04   library recovery time
                                  1.04   data required time
-----------------------------------------------------------------------------
                                  1.04   data required time
                                 -2.39   data arrival time
-----------------------------------------------------------------------------
                                 -1.35   slack (VIOLATED)
```
