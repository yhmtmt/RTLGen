# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_two_pass_stream_d4`
- metrics_path: `runs/designs/npu_blocks/attention_two_pass_stream_d4/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 59c51083 | attention_two_pass_stream_v1 | ok | 47.3708 | 0.4 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt` |
| 8f240871 | attention_two_pass_stream_v1 | ok | 47.5293 | 0.3 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[1]$_DFFE_PN0P_`
- endpoint: `result_value[52]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.7500`
- data_arrival_time: `47.3700`
- data_required_time: `10.6200`

```text
Startpoint: div_index[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[52]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.18    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire76136/A (BUF_X8)
     1   42.06    0.01    0.03    0.03 ^ wire76136/Z (BUF_X8)
                                         net76136 (net)
                  0.02    0.01    0.05 ^ wire76135/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire76135/Z (BUF_X16)
                                         net76135 (net)
                  0.03    0.02    0.10 ^ wire76134/A (BUF_X16)
     1   49.45    0.01    0.03    0.12 ^ wire76134/Z (BUF_X16)
                                         net76134 (net)
                  0.03    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   19.45    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13__leaf_clk (net)
                  0.08    0.04   10.60 ^ clkbuf_leaf_60_clk/A (CLKBUF_X3)
     8   11.39    0.01    0.06   10.66 ^ clkbuf_leaf_60_clk/Z (CLKBUF_X3)
                                         clknet_leaf_60_clk (net)
                  0.01    0.00   10.66 ^ result_value[52]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.66   clock reconvergence pessimism
                         -0.04   10.62   library setup time
                                 10.62   data required time
-----------------------------------------------------------------------------
                                 10.62   data required time
                                -47.37   data arrival time
-----------------------------------------------------------------------------
                                -36.75   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7000`
- data_required_time: `0.6400`

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
     1   35.18    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire76136/A (BUF_X8)
     1   42.06    0.01    0.03    0.03 ^ wire76136/Z (BUF_X8)
                                         net76136 (net)
                  0.02    0.01    0.05 ^ wire76135/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire76135/Z (BUF_X16)
                                         net76135 (net)
                  0.03    0.02    0.10 ^ wire76134/A (BUF_X16)
     1   49.45    0.01    0.03    0.12 ^ wire76134/Z (BUF_X16)
                                         net76134 (net)
                  0.03    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   19.45    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_10__leaf_clk (net)
                  0.04    0.02    0.58 ^ clkbuf_leaf_24_clk/A (CLKBUF_X3)
     8   10.62    0.01    0.05    0.63 ^ clkbuf_leaf_24_clk/Z (CLKBUF_X3)
                                         clknet_leaf_24_clk (net)
                  0.01    0.00    0.63 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.63   clock reconvergence pessimism
                          0.01    0.64   library hold time
                                  0.64   data required time
-----------------------------------------------------------------------------
                                  0.64   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `result_value[5]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2100`
- data_arrival_time: `2.0700`
- data_required_time: `0.8600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: result_value[5]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   11.23    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     4   38.70    0.02    0.04    2.04 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.04    0.02    2.07 ^ result_value[5]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.18    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire76136/A (BUF_X8)
...
                                         clknet_3_7_1_clk (net)
                  0.02    0.00    0.49 ^ clkbuf_4_14__f_clk/A (CLKBUF_X3)
    10   57.51    0.03    0.06    0.55 ^ clkbuf_4_14__f_clk/Z (CLKBUF_X3)
                                         clknet_4_14__leaf_clk (net)
                  0.05    0.03    0.58 ^ clkbuf_leaf_27_clk/A (CLKBUF_X3)
     7   10.84    0.01    0.05    0.63 ^ clkbuf_leaf_27_clk/Z (CLKBUF_X3)
                                         clknet_leaf_27_clk (net)
                  0.01    0.00    0.63 ^ result_value[5]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.63   clock reconvergence pessimism
                          0.23    0.86   library removal time
                                  0.86   data required time
-----------------------------------------------------------------------------
                                  0.86   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.21   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `global_max[23]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.3500`
- data_arrival_time: `3.3400`
- data_required_time: `10.6800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: global_max[23]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   11.23    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     4   38.70    0.02    0.04    2.04 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.04    0.02    2.07 ^ place76067/A (BUF_X1)
     1   24.76    0.05    0.08    2.15 ^ place76067/Z (BUF_X1)
                                         net76067 (net)
                  0.06    0.02    2.16 ^ place76068/A (BUF_X1)
     4   16.17    0.04    0.06    2.23 ^ place76068/Z (BUF_X1)
                                         net76068 (net)
                  0.04    0.00    2.23 ^ place76069/A (BUF_X2)
     2   48.90    0.05    0.07    2.30 ^ place76069/Z (BUF_X2)
...
                                         clknet_3_1_1_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_4_3__f_clk/A (CLKBUF_X3)
    11   55.81    0.04    0.07   10.55 ^ clkbuf_4_3__f_clk/Z (CLKBUF_X3)
                                         clknet_4_3__leaf_clk (net)
                  0.04    0.01   10.57 ^ clkbuf_leaf_168_clk/A (CLKBUF_X3)
     5    9.55    0.01    0.05   10.61 ^ clkbuf_leaf_168_clk/Z (CLKBUF_X3)
                                         clknet_leaf_168_clk (net)
                  0.01    0.00   10.62 ^ global_max[23]$_DFF_PN0_/CK (DFFR_X2)
                          0.00   10.62   clock reconvergence pessimism
                          0.07   10.68   library recovery time
                                 10.68   data required time
-----------------------------------------------------------------------------
                                 10.68   data required time
                                 -3.34   data arrival time
-----------------------------------------------------------------------------
                                  7.35   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `div_index[1]$_DFFE_PN0P_`
- endpoint: `result_value[278]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-49.0200`
- data_arrival_time: `58.9800`
- data_required_time: `9.9600`

```text
Startpoint: div_index[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[278]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[1]$_DFFE_PN0P_/CK (DFFR_X2)
     9   23.41    0.03    0.15    0.15 ^ div_index[1]$_DFFE_PN0P_/Q (DFFR_X2)
                                         div_index[1] (net)
                  0.03    0.00    0.15 ^ _287163_/A (HA_X1)
     4   16.40    0.04    0.07    0.22 ^ _287163_/CO (HA_X1)
                                         _027353_ (net)
                  0.04    0.00    0.22 ^ _282055_/A (HA_X1)
     1    3.40    0.03    0.06    0.28 ^ _282055_/S (HA_X1)
                                         _027355_ (net)
                  0.03    0.00    0.28 ^ _169312_/A (BUF_X4)
     9   17.33    0.01    0.03    0.32 ^ _169312_/Z (BUF_X4)
                                         _108710_ (net)
                  0.01    0.00    0.32 ^ _169329_/A (BUF_X4)
...
                                 58.98   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[278]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -58.98   data arrival time
-----------------------------------------------------------------------------
                                -49.02   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[188]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.6000`
- data_arrival_time: `51.5600`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[188]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     3    5.93    0.01    0.08    0.08 ^ div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _027369_ (net)
                  0.01    0.00    0.08 ^ _287158_/A (HA_X1)
     2   10.90    0.03    0.05    0.13 ^ _287158_/CO (HA_X1)
                                         _041339_ (net)
                  0.03    0.00    0.14 ^ place74111/A (BUF_X8)
     1   32.03    0.01    0.03    0.16 ^ place74111/Z (BUF_X8)
                                         net74111 (net)
                  0.02    0.02    0.18 ^ place74112/A (BUF_X8)
     1   36.22    0.01    0.03    0.21 ^ place74112/Z (BUF_X8)
                                         net74112 (net)
                  0.03    0.02    0.23 ^ place74113/A (BUF_X8)
...
                                 51.56   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[188]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.56   data arrival time
-----------------------------------------------------------------------------
                                -41.60   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[188]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.6000`
- data_arrival_time: `51.5600`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[188]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     3    5.93    0.01    0.08    0.08 ^ div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _027369_ (net)
                  0.01    0.00    0.08 ^ _287158_/A (HA_X1)
     2   10.90    0.03    0.05    0.13 ^ _287158_/CO (HA_X1)
                                         _041339_ (net)
                  0.03    0.00    0.14 ^ place74111/A (BUF_X8)
     1   32.03    0.01    0.03    0.16 ^ place74111/Z (BUF_X8)
                                         net74111 (net)
                  0.02    0.02    0.18 ^ place74112/A (BUF_X8)
     1   36.22    0.01    0.03    0.21 ^ place74112/Z (BUF_X8)
                                         net74112 (net)
                  0.03    0.02    0.23 ^ place74113/A (BUF_X8)
...
                                 51.56   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[188]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.56   data arrival time
-----------------------------------------------------------------------------
                                -41.60   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[316]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.2300`
- data_arrival_time: `50.1900`
- data_required_time: `9.9600`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[316]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[0]$_DFFE_PN0P_/CK (DFFR_X2)
     3    6.31    0.01    0.08    0.08 ^ div_index[0]$_DFFE_PN0P_/QN (DFFR_X2)
                                         _027369_ (net)
                  0.01    0.00    0.08 ^ _287158_/A (HA_X1)
     2   11.41    0.03    0.06    0.14 ^ _287158_/CO (HA_X1)
                                         _041339_ (net)
                  0.03    0.00    0.14 ^ place74111/A (BUF_X8)
     1   31.80    0.01    0.03    0.17 ^ place74111/Z (BUF_X8)
                                         net74111 (net)
                  0.02    0.02    0.18 ^ place74112/A (BUF_X8)
     1   36.15    0.01    0.03    0.21 ^ place74112/Z (BUF_X8)
                                         net74112 (net)
                  0.03    0.02    0.23 ^ place74113/A (BUF_X8)
...
                                 50.19   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[316]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -50.19   data arrival time
-----------------------------------------------------------------------------
                                -40.23   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `div_index[0]$_DFFE_PN0P_`
- endpoint: `result_value[154]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.2500`
- data_arrival_time: `47.9400`
- data_required_time: `10.6900`

```text
Startpoint: div_index[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[154]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   52.97    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire76136/A (BUF_X8)
     1   54.54    0.01    0.03    0.04 ^ wire76136/Z (BUF_X8)
                                         net76136 (net)
                  0.02    0.02    0.06 ^ wire76135/A (BUF_X16)
     1   73.10    0.01    0.03    0.09 ^ wire76135/Z (BUF_X16)
                                         net76135 (net)
                  0.03    0.03    0.12 ^ wire76134/A (BUF_X16)
     1   67.93    0.01    0.03    0.15 ^ wire76134/Z (BUF_X16)
                                         net76134 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.81    0.02    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_15__leaf_clk (net)
                  0.06    0.03   10.67 ^ clkbuf_leaf_43_clk/A (CLKBUF_X3)
     7    9.97    0.01    0.05   10.72 ^ clkbuf_leaf_43_clk/Z (CLKBUF_X3)
                                         clknet_leaf_43_clk (net)
                  0.01    0.00   10.72 ^ result_value[154]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.72   clock reconvergence pessimism
                         -0.03   10.69   library setup time
                                 10.69   data required time
-----------------------------------------------------------------------------
                                 10.69   data required time
                                -47.94   data arrival time
-----------------------------------------------------------------------------
                                -37.25   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `div_index[1]$_DFFE_PN0P_`
- endpoint: `result_value[52]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.0000`
- data_arrival_time: `47.7100`
- data_required_time: `10.7100`

```text
Startpoint: div_index[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[52]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.29    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire76136/A (BUF_X8)
     1   53.98    0.01    0.03    0.04 ^ wire76136/Z (BUF_X8)
                                         net76136 (net)
                  0.03    0.02    0.06 ^ wire76135/A (BUF_X16)
     1   72.26    0.01    0.03    0.09 ^ wire76135/Z (BUF_X16)
                                         net76135 (net)
                  0.04    0.03    0.12 ^ wire76134/A (BUF_X16)
     1   67.20    0.01    0.03    0.14 ^ wire76134/Z (BUF_X16)
                                         net76134 (net)
                  0.03    0.03    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.71    0.02    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13__leaf_clk (net)
                  0.08    0.04   10.69 ^ clkbuf_leaf_60_clk/A (CLKBUF_X3)
     8   10.74    0.01    0.06   10.75 ^ clkbuf_leaf_60_clk/Z (CLKBUF_X3)
                                         clknet_leaf_60_clk (net)
                  0.01    0.00   10.75 ^ result_value[52]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.75   clock reconvergence pessimism
                         -0.04   10.71   library setup time
                                 10.71   data required time
-----------------------------------------------------------------------------
                                 10.71   data required time
                                -47.71   data arrival time
-----------------------------------------------------------------------------
                                -37.00   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[1]$_DFFE_PN0P_`
- endpoint: `result_value[52]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.7500`
- data_arrival_time: `47.3700`
- data_required_time: `10.6200`

```text
Startpoint: div_index[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[52]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.18    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire76136/A (BUF_X8)
     1   42.06    0.01    0.03    0.03 ^ wire76136/Z (BUF_X8)
                                         net76136 (net)
                  0.02    0.01    0.05 ^ wire76135/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire76135/Z (BUF_X16)
                                         net76135 (net)
                  0.03    0.02    0.10 ^ wire76134/A (BUF_X16)
     1   49.45    0.01    0.03    0.12 ^ wire76134/Z (BUF_X16)
                                         net76134 (net)
                  0.03    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   19.45    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13__leaf_clk (net)
                  0.08    0.04   10.60 ^ clkbuf_leaf_60_clk/A (CLKBUF_X3)
     8   11.39    0.01    0.06   10.66 ^ clkbuf_leaf_60_clk/Z (CLKBUF_X3)
                                         clknet_leaf_60_clk (net)
                  0.01    0.00   10.66 ^ result_value[52]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.66   clock reconvergence pessimism
                         -0.04   10.62   library setup time
                                 10.62   data required time
-----------------------------------------------------------------------------
                                 10.62   data required time
                                -47.37   data arrival time
-----------------------------------------------------------------------------
                                -36.75   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d4/attention_two_pass_stream_v1/2_floorplan_final.rpt`
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
                                         _139479_ (net)
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
