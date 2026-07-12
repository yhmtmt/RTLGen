# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_two_pass_stream_d1`
- metrics_path: `runs/designs/npu_blocks/attention_two_pass_stream_d1/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 59c51083 | attention_two_pass_stream_v1 | ok | 42.7317 | 0.4 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt` |
| 8f240871 | attention_two_pass_stream_v1 | ok | 43.0822 | 0.3 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[134]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-32.3100`
- data_arrival_time: `42.7300`
- data_required_time: `10.4200`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[134]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
     1   36.56    0.01    0.02    0.03 ^ wire26154/Z (BUF_X8)
                                         net26154 (net)
                  0.02    0.01    0.04 ^ wire26153/A (BUF_X16)
     1   48.20    0.01    0.02    0.07 ^ wire26153/Z (BUF_X16)
                                         net26153 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   18.85    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   18.43    0.02    0.04    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.04    0.01   10.41 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.62    0.01    0.05   10.46 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.46 ^ result_value[134]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.46   clock reconvergence pessimism
                         -0.04   10.42   library setup time
                                 10.42   data required time
-----------------------------------------------------------------------------
                                 10.42   data required time
                                -42.73   data arrival time
-----------------------------------------------------------------------------
                                -32.31   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5200`
- data_required_time: `0.4600`

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
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
     1   36.56    0.01    0.02    0.03 ^ wire26154/Z (BUF_X8)
                                         net26154 (net)
                  0.02    0.01    0.04 ^ wire26153/A (BUF_X16)
     1   48.20    0.01    0.02    0.07 ^ wire26153/Z (BUF_X16)
                                         net26153 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   18.85    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.27    0.02    0.04    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_12_0_clk (net)
                  0.03    0.01    0.40 ^ clkbuf_leaf_16_clk/A (CLKBUF_X3)
     7    8.65    0.01    0.04    0.45 ^ clkbuf_leaf_16_clk/Z (CLKBUF_X3)
                                         clknet_leaf_16_clk (net)
                  0.01    0.00    0.45 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.45   clock reconvergence pessimism
                          0.01    0.46   library hold time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `result_value[33]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3700`
- data_arrival_time: `2.0500`
- data_required_time: `0.6800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: result_value[33]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.43    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     4   34.77    0.03    0.05    2.05 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.03    0.00    2.05 ^ result_value[33]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
...
                                         clknet_3_6_0_clk (net)
                  0.02    0.01    0.33 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    11   51.04    0.04    0.07    0.40 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
                                         clknet_4_13_0_clk (net)
                  0.04    0.01    0.41 ^ clkbuf_leaf_57_clk/A (CLKBUF_X3)
     6   11.66    0.01    0.05    0.46 ^ clkbuf_leaf_57_clk/Z (CLKBUF_X3)
                                         clknet_leaf_57_clk (net)
                  0.01    0.00    0.46 ^ result_value[33]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.46   clock reconvergence pessimism
                          0.22    0.68   library removal time
                                  0.68   data required time
-----------------------------------------------------------------------------
                                  0.68   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.37   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accepted_count[2]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4000`
- data_arrival_time: `3.0900`
- data_required_time: `10.4900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accepted_count[2]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.43    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     4   34.77    0.03    0.05    2.05 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.03    0.01    2.06 ^ place26119/A (BUF_X1)
     1   24.07    0.05    0.08    2.14 ^ place26119/Z (BUF_X1)
                                         net26119 (net)
                  0.06    0.01    2.15 ^ place26120/A (BUF_X1)
     6   14.55    0.03    0.06    2.21 ^ place26120/Z (BUF_X1)
                                         net26120 (net)
                  0.03    0.00    2.21 ^ wire26152/A (CLKBUF_X3)
     5   46.03    0.03    0.07    2.28 ^ wire26152/Z (CLKBUF_X3)
...
                                         clknet_2_0_1_clk (net)
                  0.02    0.00   10.28 ^ clkbuf_3_0_0_clk/A (CLKBUF_X3)
     2   18.90    0.02    0.05   10.33 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
                                         clknet_3_0_0_clk (net)
                  0.02    0.00   10.33 ^ clkbuf_4_1_0_clk/A (CLKBUF_X3)
     9   51.83    0.03    0.05   10.39 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
                                         clknet_4_1_0_clk (net)
                  0.07    0.05   10.43 ^ accepted_count[2]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.43   clock reconvergence pessimism
                          0.06   10.49   library recovery time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                 -3.09   data arrival time
-----------------------------------------------------------------------------
                                  7.40   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[168]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.6100`
- data_arrival_time: `47.5800`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[168]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFF_PN0_/CK (DFFR_X1)
     4   11.60    0.03    0.12    0.12 ^ div_index[0]$_DFF_PN0_/Q (DFFR_X1)
                                         div_index[0] (net)
                  0.03    0.00    0.12 ^ _171948_/B (HA_X1)
     3    8.32    0.02    0.05    0.18 ^ _171948_/CO (HA_X1)
                                         _022396_ (net)
                  0.02    0.00    0.18 ^ _173687_/A (HA_X1)
     6   13.42    0.03    0.06    0.24 ^ _173687_/CO (HA_X1)
                                         _027220_ (net)
                  0.03    0.00    0.24 ^ _131373_/A2 (NOR2_X2)
     1    2.88    0.01    0.01    0.25 v _131373_/ZN (NOR2_X2)
                                         _066671_ (net)
                  0.01    0.00    0.25 v _131374_/A (OAI21_X2)
...
                                 47.58   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[168]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -47.58   data arrival time
-----------------------------------------------------------------------------
                                -37.61   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[296]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-33.3200`
- data_arrival_time: `43.2800`
- data_required_time: `9.9500`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[296]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFF_PN0_/CK (DFFR_X2)
     2    5.20    0.01    0.10    0.10 v div_index[0]$_DFF_PN0_/Q (DFFR_X2)
                                         div_index[0] (net)
                  0.01    0.00    0.10 v _171948_/B (HA_X1)
     2    4.29    0.01    0.03    0.13 v _171948_/CO (HA_X1)
                                         _022396_ (net)
                  0.01    0.00    0.13 v place24388/A (BUF_X4)
     2   24.28    0.01    0.03    0.16 v place24388/Z (BUF_X4)
                                         net24388 (net)
                  0.01    0.01    0.17 v _173688_/B (HA_X1)
     8   18.34    0.02    0.06    0.22 v _173688_/CO (HA_X1)
                                         _027222_ (net)
                  0.02    0.00    0.23 v _131570_/C1 (AOI222_X1)
...
                                 43.28   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[296]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -43.28   data arrival time
-----------------------------------------------------------------------------
                                -33.32   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[296]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-33.3200`
- data_arrival_time: `43.2800`
- data_required_time: `9.9500`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[296]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFF_PN0_/CK (DFFR_X2)
     2    5.20    0.01    0.10    0.10 v div_index[0]$_DFF_PN0_/Q (DFFR_X2)
                                         div_index[0] (net)
                  0.01    0.00    0.10 v _171948_/B (HA_X1)
     2    4.29    0.01    0.03    0.13 v _171948_/CO (HA_X1)
                                         _022396_ (net)
                  0.01    0.00    0.13 v place24388/A (BUF_X4)
     2   24.28    0.01    0.03    0.16 v place24388/Z (BUF_X4)
                                         net24388 (net)
                  0.01    0.01    0.17 v _173688_/B (HA_X1)
     8   18.34    0.02    0.06    0.22 v _173688_/CO (HA_X1)
                                         _027222_ (net)
                  0.02    0.00    0.23 v _131570_/C1 (AOI222_X1)
...
                                 43.28   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[296]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -43.28   data arrival time
-----------------------------------------------------------------------------
                                -33.32   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[296]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-33.3100`
- data_arrival_time: `43.2600`
- data_required_time: `9.9500`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[296]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFF_PN0_/CK (DFFR_X2)
     2    5.60    0.01    0.13    0.13 ^ div_index[0]$_DFF_PN0_/Q (DFFR_X2)
                                         div_index[0] (net)
                  0.01    0.00    0.13 ^ _171948_/B (HA_X1)
     2    4.82    0.01    0.04    0.17 ^ _171948_/CO (HA_X1)
                                         _022396_ (net)
                  0.01    0.00    0.17 ^ place24388/A (BUF_X4)
     2   24.61    0.01    0.03    0.20 ^ place24388/Z (BUF_X4)
                                         net24388 (net)
                  0.02    0.01    0.21 ^ _173688_/B (HA_X1)
     8   19.78    0.05    0.08    0.29 ^ _173688_/CO (HA_X1)
                                         _027222_ (net)
                  0.05    0.00    0.29 ^ _131373_/A1 (NOR2_X2)
...
                                 43.26   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[296]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -43.26   data arrival time
-----------------------------------------------------------------------------
                                -33.31   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[168]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-32.6500`
- data_arrival_time: `43.1500`
- data_required_time: `10.5100`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[168]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   44.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
     1   46.79    0.01    0.03    0.04 ^ wire26154/Z (BUF_X8)
                                         net26154 (net)
                  0.02    0.01    0.05 ^ wire26153/A (BUF_X16)
     1   67.24    0.01    0.03    0.08 ^ wire26153/Z (BUF_X16)
                                         net26153 (net)
                  0.03    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   26.89    0.02    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   24.23    0.02    0.05    0.22 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.07    0.03   10.49 ^ clkbuf_leaf_72_clk/A (CLKBUF_X3)
     7    9.25    0.01    0.05   10.55 ^ clkbuf_leaf_72_clk/Z (CLKBUF_X3)
                                         clknet_leaf_72_clk (net)
                  0.01    0.00   10.55 ^ result_value[168]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.55   clock reconvergence pessimism
                         -0.04   10.51   library setup time
                                 10.51   data required time
-----------------------------------------------------------------------------
                                 10.51   data required time
                                -43.15   data arrival time
-----------------------------------------------------------------------------
                                -32.65   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[134]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-32.3100`
- data_arrival_time: `42.7300`
- data_required_time: `10.4200`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[134]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
     1   36.56    0.01    0.02    0.03 ^ wire26154/Z (BUF_X8)
                                         net26154 (net)
                  0.02    0.01    0.04 ^ wire26153/A (BUF_X16)
     1   48.20    0.01    0.02    0.07 ^ wire26153/Z (BUF_X16)
                                         net26153 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   18.85    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   18.43    0.02    0.04    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.04    0.01   10.41 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.62    0.01    0.05   10.46 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.46 ^ result_value[134]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.46   clock reconvergence pessimism
                         -0.04   10.42   library setup time
                                 10.42   data required time
-----------------------------------------------------------------------------
                                 10.42   data required time
                                -42.73   data arrival time
-----------------------------------------------------------------------------
                                -32.31   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[134]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-32.1500`
- data_arrival_time: `42.6400`
- data_required_time: `10.4900`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[134]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   44.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26154/A (BUF_X8)
     1   47.08    0.01    0.03    0.04 ^ wire26154/Z (BUF_X8)
                                         net26154 (net)
                  0.02    0.01    0.05 ^ wire26153/A (BUF_X16)
     1   67.81    0.01    0.03    0.08 ^ wire26153/Z (BUF_X16)
                                         net26153 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   26.65    0.02    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   24.19    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.04    0.01   10.48 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     7    9.22    0.01    0.05   10.53 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.53 ^ result_value[134]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.53   clock reconvergence pessimism
                         -0.04   10.49   library setup time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                -42.64   data arrival time
-----------------------------------------------------------------------------
                                -32.15   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d1/attention_two_pass_stream_v1/2_floorplan_final.rpt`
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
                                         _081121_ (net)
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
