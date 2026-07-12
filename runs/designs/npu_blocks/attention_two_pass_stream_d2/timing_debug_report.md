# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_two_pass_stream_d2`
- metrics_path: `runs/designs/npu_blocks/attention_two_pass_stream_d2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 59c51083 | attention_two_pass_stream_v1 | ok | 45.2992 | 0.4 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt` |
| 8f240871 | attention_two_pass_stream_v1 | ok | 45.8322 | 0.3 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[246]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-34.8600`
- data_arrival_time: `45.3000`
- data_required_time: `10.4400`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[246]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   39.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   42.02    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
                                         net41699 (net)
                  0.02    0.01    0.05 ^ wire41698/A (BUF_X16)
     1   47.91    0.01    0.02    0.08 ^ wire41698/Z (BUF_X16)
                                         net41698 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   23.43    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   20.42    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_10_0_clk (net)
                  0.04    0.02   10.43 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.92    0.01    0.05   10.48 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.48 ^ result_value[246]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.04   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -45.30   data arrival time
-----------------------------------------------------------------------------
                                -34.86   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5400`
- data_required_time: `0.4800`

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
     1   39.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   42.02    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
                                         net41699 (net)
                  0.02    0.01    0.05 ^ wire41698/A (BUF_X16)
     1   47.91    0.01    0.02    0.08 ^ wire41698/Z (BUF_X16)
                                         net41698 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   23.43    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   20.42    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_8_0_clk (net)
                  0.04    0.02    0.43 ^ clkbuf_leaf_32_clk/A (CLKBUF_X3)
     6    7.81    0.01    0.04    0.47 ^ clkbuf_leaf_32_clk/Z (CLKBUF_X3)
                                         clknet_leaf_32_clk (net)
                  0.01    0.00    0.47 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.47   clock reconvergence pessimism
                          0.01    0.48   library hold time
                                  0.48   data required time
-----------------------------------------------------------------------------
                                  0.48   data required time
                                 -0.54   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `state[2]$_DFF_PN0_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3400`
- data_arrival_time: `2.1100`
- data_required_time: `0.7700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: state[2]$_DFF_PN0_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.62    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
    12   79.71    0.05    0.07    2.07 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.07    0.04    2.11 ^ state[2]$_DFF_PN0_/RN (DFFR_X1)
                                  2.11   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   39.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   42.02    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
...
                                         clknet_3_7_0_clk (net)
                  0.02    0.00    0.35 ^ clkbuf_4_14_0_clk/A (CLKBUF_X3)
    11   73.95    0.05    0.08    0.43 ^ clkbuf_4_14_0_clk/Z (CLKBUF_X3)
                                         clknet_4_14_0_clk (net)
                  0.05    0.01    0.44 ^ clkbuf_leaf_41_clk/A (CLKBUF_X3)
     6   12.13    0.01    0.05    0.49 ^ clkbuf_leaf_41_clk/Z (CLKBUF_X3)
                                         clknet_leaf_41_clk (net)
                  0.01    0.00    0.50 ^ state[2]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.50   clock reconvergence pessimism
                          0.27    0.77   library removal time
                                  0.77   data required time
-----------------------------------------------------------------------------
                                  0.77   data required time
                                 -2.11   data arrival time
-----------------------------------------------------------------------------
                                  1.34   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[1]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.3300`
- data_arrival_time: `3.2100`
- data_required_time: `10.5400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[1]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.62    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
    12   79.71    0.05    0.07    2.07 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.07    0.04    2.11 ^ place41653/A (BUF_X1)
     1   17.46    0.04    0.07    2.17 ^ place41653/Z (BUF_X1)
                                         net41653 (net)
                  0.04    0.01    2.18 ^ place41654/A (BUF_X1)
     1   29.04    0.06    0.09    2.27 ^ place41654/Z (BUF_X1)
                                         net41654 (net)
                  0.07    0.01    2.28 ^ place41655/A (BUF_X1)
     3   39.32    0.09    0.11    2.40 ^ place41655/Z (BUF_X1)
...
                                         clknet_3_1_0_clk (net)
                  0.02    0.00   10.36 ^ clkbuf_4_2_0_clk/A (CLKBUF_X3)
    16   61.54    0.04    0.07   10.43 ^ clkbuf_4_2_0_clk/Z (CLKBUF_X3)
                                         clknet_4_2_0_clk (net)
                  0.05    0.02   10.45 ^ clkbuf_leaf_30_clk/A (CLKBUF_X3)
     7   10.08    0.01    0.05   10.50 ^ clkbuf_leaf_30_clk/Z (CLKBUF_X3)
                                         clknet_leaf_30_clk (net)
                  0.01    0.00   10.50 ^ completed_count[1]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.50   clock reconvergence pessimism
                          0.04   10.54   library recovery time
                                 10.54   data required time
-----------------------------------------------------------------------------
                                 10.54   data required time
                                 -3.21   data arrival time
-----------------------------------------------------------------------------
                                  7.33   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[174]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.6400`
- data_arrival_time: `51.6000`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[174]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X1)
     5   13.98    0.04    0.13    0.13 ^ div_index[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         div_index[0] (net)
                  0.04    0.00    0.13 ^ _212623_/A (HA_X1)
     3    5.08    0.02    0.05    0.18 ^ _212623_/CO (HA_X1)
                                         _035694_ (net)
                  0.02    0.00    0.18 ^ _116363_/A (BUF_X2)
    10   19.75    0.03    0.04    0.22 ^ _116363_/Z (BUF_X2)
                                         _051478_ (net)
                  0.03    0.00    0.22 ^ _116411_/A (INV_X2)
     6   10.19    0.01    0.02    0.24 v _116411_/ZN (INV_X2)
                                         _051523_ (net)
                  0.01    0.00    0.24 v _171972_/A2 (NOR2_X1)
...
                                 51.60   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[174]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.60   data arrival time
-----------------------------------------------------------------------------
                                -41.64   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[138]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.8000`
- data_arrival_time: `46.7600`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[138]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     4    8.66    0.02    0.10    0.10 v div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _035688_ (net)
                  0.02    0.00    0.10 v _212620_/A (HA_X1)
     2    7.90    0.01    0.04    0.14 v _212620_/CO (HA_X1)
                                         _035690_ (net)
                  0.01    0.00    0.14 v place39853/A (BUF_X8)
     1   27.50    0.01    0.03    0.17 v place39853/Z (BUF_X8)
                                         net39853 (net)
                  0.01    0.01    0.18 v place39854/A (BUF_X16)
     3   44.10    0.01    0.03    0.21 v place39854/Z (BUF_X16)
                                         net39854 (net)
                  0.03    0.03    0.23 v place39857/A (BUF_X1)
...
                                 46.76   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[138]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -46.76   data arrival time
-----------------------------------------------------------------------------
                                -36.80   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[138]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.8000`
- data_arrival_time: `46.7600`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[138]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     4    8.66    0.02    0.10    0.10 v div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _035688_ (net)
                  0.02    0.00    0.10 v _212620_/A (HA_X1)
     2    7.90    0.01    0.04    0.14 v _212620_/CO (HA_X1)
                                         _035690_ (net)
                  0.01    0.00    0.14 v place39853/A (BUF_X8)
     1   27.50    0.01    0.03    0.17 v place39853/Z (BUF_X8)
                                         net39853 (net)
                  0.01    0.01    0.18 v place39854/A (BUF_X16)
     3   44.10    0.01    0.03    0.21 v place39854/Z (BUF_X16)
                                         net39854 (net)
                  0.03    0.03    0.23 v place39857/A (BUF_X1)
...
                                 46.76   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[138]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -46.76   data arrival time
-----------------------------------------------------------------------------
                                -36.80   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[170]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.7900`
- data_arrival_time: `46.7500`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[170]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     4    9.18    0.02    0.10    0.10 v div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _035688_ (net)
                  0.02    0.00    0.10 v _212620_/A (HA_X1)
     2    7.79    0.01    0.04    0.14 v _212620_/CO (HA_X1)
                                         _035690_ (net)
                  0.01    0.00    0.14 v place39853/A (BUF_X8)
     1   27.47    0.01    0.03    0.17 v place39853/Z (BUF_X8)
                                         net39853 (net)
                  0.01    0.01    0.18 v place39854/A (BUF_X16)
     3   44.07    0.01    0.03    0.21 v place39854/Z (BUF_X16)
                                         net39854 (net)
                  0.03    0.03    0.23 v place39857/A (BUF_X1)
...
                                 46.75   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[170]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -46.75   data arrival time
-----------------------------------------------------------------------------
                                -36.79   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[246]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-35.1600`
- data_arrival_time: `45.6700`
- data_required_time: `10.5200`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[246]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   52.92    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   54.47    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
                                         net41699 (net)
                  0.03    0.02    0.06 ^ wire41698/A (BUF_X16)
     1   67.49    0.01    0.03    0.09 ^ wire41698/Z (BUF_X16)
                                         net41698 (net)
                  0.03    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   33.13    0.03    0.06    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.20    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_10_0_clk (net)
                  0.05    0.02   10.50 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.38    0.01    0.05   10.55 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.55 ^ result_value[246]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.55   clock reconvergence pessimism
                         -0.04   10.52   library setup time
                                 10.52   data required time
-----------------------------------------------------------------------------
                                 10.52   data required time
                                -45.67   data arrival time
-----------------------------------------------------------------------------
                                -35.16   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[246]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-34.8600`
- data_arrival_time: `45.3000`
- data_required_time: `10.4400`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[246]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   39.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   42.02    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
                                         net41699 (net)
                  0.02    0.01    0.05 ^ wire41698/A (BUF_X16)
     1   47.91    0.01    0.02    0.08 ^ wire41698/Z (BUF_X16)
                                         net41698 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   23.43    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   20.42    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_10_0_clk (net)
                  0.04    0.02   10.43 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.92    0.01    0.05   10.48 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.48 ^ result_value[246]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.04   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -45.30   data arrival time
-----------------------------------------------------------------------------
                                -34.86   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[178]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-34.7800`
- data_arrival_time: `45.3000`
- data_required_time: `10.5200`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[178]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.13    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire41699/A (BUF_X8)
     1   54.65    0.01    0.03    0.04 ^ wire41699/Z (BUF_X8)
                                         net41699 (net)
                  0.02    0.02    0.06 ^ wire41698/A (BUF_X16)
     1   67.98    0.01    0.03    0.09 ^ wire41698/Z (BUF_X16)
                                         net41698 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   33.30    0.03    0.06    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.29    0.02    0.06    0.23 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.05    0.02   10.51 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     7    9.56    0.01    0.05   10.56 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00   10.56 ^ result_value[178]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.56   clock reconvergence pessimism
                         -0.04   10.52   library setup time
                                 10.52   data required time
-----------------------------------------------------------------------------
                                 10.52   data required time
                                -45.30   data arrival time
-----------------------------------------------------------------------------
                                -34.78   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d2/attention_two_pass_stream_v1/2_floorplan_final.rpt`
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
                                         _100138_ (net)
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
