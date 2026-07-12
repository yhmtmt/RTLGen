# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_two_pass_stream_d8`
- metrics_path: `runs/designs/npu_blocks/attention_two_pass_stream_d8/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 59c51083 | attention_two_pass_stream_v1 | ok | 48.9200 | 0.4 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt` |
| 8f240871 | attention_two_pass_stream_v1 | ok | 49.3670 | 0.3 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/congestion-5.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[1]$_DFF_PN0_`
- endpoint: `result_value[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.3300`
- data_arrival_time: `48.9200`
- data_required_time: `10.5900`

```text
Startpoint: div_index[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.90    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire145698/A (BUF_X8)
     1   40.12    0.01    0.03    0.03 ^ wire145698/Z (BUF_X8)
                                         net145698 (net)
                  0.02    0.01    0.05 ^ wire145697/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire145697/Z (BUF_X16)
                                         net145697 (net)
                  0.03    0.02    0.10 ^ wire145696/A (BUF_X16)
     1   48.14    0.01    0.03    0.12 ^ wire145696/Z (BUF_X16)
                                         net145696 (net)
                  0.02    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.47    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_9_0_clk (net)
                  0.03    0.00   10.58 ^ clkbuf_leaf_30_clk/A (CLKBUF_X3)
     6   11.91    0.01    0.05   10.62 ^ clkbuf_leaf_30_clk/Z (CLKBUF_X3)
                                         clknet_leaf_30_clk (net)
                  0.01    0.00   10.62 ^ result_value[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -48.92   data arrival time
-----------------------------------------------------------------------------
                                -38.33   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7100`
- data_required_time: `0.6500`

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
     1   37.90    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire145698/A (BUF_X8)
     1   40.12    0.01    0.03    0.03 ^ wire145698/Z (BUF_X8)
                                         net145698 (net)
                  0.02    0.01    0.05 ^ wire145697/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire145697/Z (BUF_X16)
                                         net145697 (net)
                  0.03    0.02    0.10 ^ wire145696/A (BUF_X16)
     1   48.14    0.01    0.03    0.12 ^ wire145696/Z (BUF_X16)
                                         net145696 (net)
                  0.02    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.47    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_10_0_clk (net)
                  0.04    0.00    0.58 ^ max_length145700/A (BUF_X8)
     3   42.25    0.01    0.03    0.61 ^ max_length145700/Z (BUF_X8)
                                         net145700 (net)
                  0.04    0.03    0.64 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.64   clock reconvergence pessimism
                          0.02    0.65   library hold time
                                  0.65   data required time
-----------------------------------------------------------------------------
                                  0.65   data required time
                                 -0.71   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count[1]$_DFF_PN0_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3300`
- data_arrival_time: `2.2700`
- data_required_time: `0.9400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count[1]$_DFF_PN0_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.38    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     2   52.03    0.02    0.04    2.04 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.04    0.02    2.06 ^ place145666/A (BUF_X1)
     1    5.24    0.01    0.04    2.10 ^ place145666/Z (BUF_X1)
                                         net145666 (net)
                  0.01    0.00    2.10 ^ place145667/A (BUF_X2)
     3   36.43    0.03    0.05    2.15 ^ place145667/Z (BUF_X2)
                                         net145667 (net)
                  0.05    0.03    2.18 ^ place145669/A (BUF_X2)
    14   43.01    0.04    0.07    2.25 ^ place145669/Z (BUF_X2)
                                         net145669 (net)
...
                                         clknet_4_10_0_clk (net)
                  0.04    0.00    0.58 ^ max_length145700/A (BUF_X8)
     3   42.25    0.01    0.03    0.61 ^ max_length145700/Z (BUF_X8)
                                         net145700 (net)
                  0.04    0.03    0.64 ^ clkbuf_leaf_20_clk/A (CLKBUF_X3)
     7    9.61    0.01    0.05    0.69 ^ clkbuf_leaf_20_clk/Z (CLKBUF_X3)
                                         clknet_leaf_20_clk (net)
                  0.01    0.00    0.69 ^ cycle_count[1]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.69   clock reconvergence pessimism
                          0.25    0.94   library removal time
                                  0.94   data required time
-----------------------------------------------------------------------------
                                  0.94   data required time
                                 -2.27   data arrival time
-----------------------------------------------------------------------------
                                  1.33   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `numerator_accum[7][8]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5500`
- data_arrival_time: `3.1700`
- data_required_time: `10.7200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: numerator_accum[7][8]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.38    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     2   52.03    0.02    0.04    2.04 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.08    0.06    2.10 ^ place145605/A (BUF_X2)
     1   32.70    0.04    0.06    2.17 ^ place145605/Z (BUF_X2)
                                         net145605 (net)
                  0.04    0.01    2.18 ^ place145606/A (BUF_X2)
     3   35.21    0.04    0.06    2.24 ^ place145606/Z (BUF_X2)
                                         net145606 (net)
                  0.04    0.01    2.25 ^ place145624/A (BUF_X2)
     5   60.09    0.06    0.08    2.33 ^ place145624/Z (BUF_X2)
...
                                         clknet_3_3_1_clk (net)
                  0.02    0.01   10.52 ^ clkbuf_4_6_0_clk/A (CLKBUF_X3)
    22   83.54    0.06    0.10   10.61 ^ clkbuf_4_6_0_clk/Z (CLKBUF_X3)
                                         clknet_4_6_0_clk (net)
                  0.06    0.01   10.62 ^ clkbuf_leaf_141_clk/A (CLKBUF_X3)
     7   10.06    0.01    0.05   10.67 ^ clkbuf_leaf_141_clk/Z (CLKBUF_X3)
                                         clknet_leaf_141_clk (net)
                  0.01    0.00   10.67 ^ numerator_accum[7][8]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.67   clock reconvergence pessimism
                          0.04   10.72   library recovery time
                                 10.72   data required time
-----------------------------------------------------------------------------
                                 10.72   data required time
                                 -3.17   data arrival time
-----------------------------------------------------------------------------
                                  7.55   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `div_index[1]$_DFF_PN0_`
- endpoint: `result_value[108]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-53.5600`
- data_arrival_time: `63.5200`
- data_required_time: `9.9600`

```text
Startpoint: div_index[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[108]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[1]$_DFF_PN0_/CK (DFFR_X2)
    10   29.53    0.03    0.12    0.12 v div_index[1]$_DFF_PN0_/QN (DFFR_X2)
                                         _035605_ (net)
                  0.03    0.00    0.12 v _425127_/A (HA_X1)
     2    8.87    0.01    0.05    0.17 v _425127_/CO (HA_X1)
                                         _026122_ (net)
                  0.01    0.00    0.17 v _236711_/A (BUF_X8)
     9   26.86    0.01    0.03    0.20 v _236711_/Z (BUF_X8)
                                         _192335_ (net)
                  0.01    0.00    0.20 v _236712_/A (BUF_X1)
    10   14.26    0.02    0.04    0.25 v _236712_/Z (BUF_X1)
                                         _192336_ (net)
                  0.02    0.00    0.25 v _248247_/A (BUF_X2)
...
                                 63.52   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[108]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -63.52   data arrival time
-----------------------------------------------------------------------------
                                -53.56   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `div_index[2]$_DFF_PN0_`
- endpoint: `result_value[236]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.3200`
- data_arrival_time: `51.2800`
- data_required_time: `9.9600`

```text
Startpoint: div_index[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[236]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[2]$_DFF_PN0_/CK (DFFR_X2)
     2    4.66    0.01    0.08    0.08 ^ div_index[2]$_DFF_PN0_/QN (DFFR_X2)
                                         _044873_ (net)
                  0.01    0.00    0.08 ^ place144974/A (BUF_X1)
     2    4.65    0.01    0.03    0.11 ^ place144974/Z (BUF_X1)
                                         net144974 (net)
                  0.01    0.00    0.11 ^ place144975/A (BUF_X1)
     2    4.32    0.01    0.03    0.14 ^ place144975/Z (BUF_X1)
                                         net144975 (net)
                  0.01    0.00    0.14 ^ place144976/A (BUF_X2)
     1   56.57    0.05    0.07    0.21 ^ place144976/Z (BUF_X2)
                                         net144976 (net)
                  0.09    0.06    0.26 ^ place144977/A (BUF_X2)
...
                                 51.28   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[236]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.28   data arrival time
-----------------------------------------------------------------------------
                                -41.32   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `div_index[2]$_DFF_PN0_`
- endpoint: `result_value[236]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.3200`
- data_arrival_time: `51.2800`
- data_required_time: `9.9600`

```text
Startpoint: div_index[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[236]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[2]$_DFF_PN0_/CK (DFFR_X2)
     2    4.47    0.01    0.08    0.08 ^ div_index[2]$_DFF_PN0_/QN (DFFR_X2)
                                         _044873_ (net)
                  0.01    0.00    0.08 ^ place144974/A (BUF_X1)
     2    4.91    0.01    0.03    0.11 ^ place144974/Z (BUF_X1)
                                         net144974 (net)
                  0.01    0.00    0.11 ^ place144975/A (BUF_X1)
     2    4.18    0.01    0.03    0.14 ^ place144975/Z (BUF_X1)
                                         net144975 (net)
                  0.01    0.00    0.14 ^ place144976/A (BUF_X2)
     1   56.43    0.05    0.07    0.21 ^ place144976/Z (BUF_X2)
                                         net144976 (net)
                  0.09    0.06    0.26 ^ place144977/A (BUF_X2)
...
                                 51.28   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[236]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.28   data arrival time
-----------------------------------------------------------------------------
                                -41.32   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `div_index[2]$_DFF_PN0_`
- endpoint: `result_value[236]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.3200`
- data_arrival_time: `51.2800`
- data_required_time: `9.9600`

```text
Startpoint: div_index[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[236]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ div_index[2]$_DFF_PN0_/CK (DFFR_X2)
     2    4.47    0.01    0.08    0.08 ^ div_index[2]$_DFF_PN0_/QN (DFFR_X2)
                                         _044873_ (net)
                  0.01    0.00    0.08 ^ place144974/A (BUF_X1)
     2    4.91    0.01    0.03    0.11 ^ place144974/Z (BUF_X1)
                                         net144974 (net)
                  0.01    0.00    0.11 ^ place144975/A (BUF_X1)
     2    4.18    0.01    0.03    0.14 ^ place144975/Z (BUF_X1)
                                         net144975 (net)
                  0.01    0.00    0.14 ^ place144976/A (BUF_X2)
     1   56.43    0.05    0.07    0.21 ^ place144976/Z (BUF_X2)
                                         net144976 (net)
                  0.09    0.06    0.26 ^ place144977/A (BUF_X2)
...
                                 51.28   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ result_value[236]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.28   data arrival time
-----------------------------------------------------------------------------
                                -41.32   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `div_index[0]$_DFF_PN0_`
- endpoint: `result_value[150]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-39.0300`
- data_arrival_time: `49.7000`
- data_required_time: `10.6700`

```text
Startpoint: div_index[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[150]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.96    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire145698/A (BUF_X8)
     1   51.87    0.01    0.03    0.04 ^ wire145698/Z (BUF_X8)
                                         net145698 (net)
                  0.02    0.02    0.06 ^ wire145697/A (BUF_X16)
     1   72.92    0.01    0.03    0.08 ^ wire145697/Z (BUF_X16)
                                         net145697 (net)
                  0.03    0.03    0.11 ^ wire145696/A (BUF_X16)
     1   68.05    0.01    0.03    0.14 ^ wire145696/Z (BUF_X16)
                                         net145696 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.82    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.00   10.66 ^ clkbuf_leaf_60_clk/A (CLKBUF_X3)
     5    9.02    0.01    0.04   10.70 ^ clkbuf_leaf_60_clk/Z (CLKBUF_X3)
                                         clknet_leaf_60_clk (net)
                  0.01    0.00   10.70 ^ result_value[150]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.70   clock reconvergence pessimism
                         -0.04   10.67   library setup time
                                 10.67   data required time
-----------------------------------------------------------------------------
                                 10.67   data required time
                                -49.70   data arrival time
-----------------------------------------------------------------------------
                                -39.03   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `div_index[1]$_DFF_PN0_`
- endpoint: `result_value[200]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.6500`
- data_arrival_time: `49.3200`
- data_required_time: `10.6700`

```text
Startpoint: div_index[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[200]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire145698/A (BUF_X8)
     1   51.45    0.01    0.03    0.04 ^ wire145698/Z (BUF_X8)
                                         net145698 (net)
                  0.02    0.02    0.06 ^ wire145697/A (BUF_X16)
     1   72.28    0.01    0.03    0.08 ^ wire145697/Z (BUF_X16)
                                         net145697 (net)
                  0.04    0.03    0.11 ^ wire145696/A (BUF_X16)
     1   67.41    0.01    0.03    0.14 ^ wire145696/Z (BUF_X16)
                                         net145696 (net)
                  0.03    0.03    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   33.10    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_9_0_clk (net)
                  0.03    0.00   10.66 ^ clkbuf_leaf_52_clk/A (CLKBUF_X3)
     6    8.05    0.01    0.04   10.70 ^ clkbuf_leaf_52_clk/Z (CLKBUF_X3)
                                         clknet_leaf_52_clk (net)
                  0.01    0.00   10.70 ^ result_value[200]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.70   clock reconvergence pessimism
                         -0.03   10.67   library setup time
                                 10.67   data required time
-----------------------------------------------------------------------------
                                 10.67   data required time
                                -49.32   data arrival time
-----------------------------------------------------------------------------
                                -38.65   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `div_index[1]$_DFF_PN0_`
- endpoint: `result_value[88]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.3300`
- data_arrival_time: `48.9200`
- data_required_time: `10.5900`

```text
Startpoint: div_index[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_value[88]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.90    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire145698/A (BUF_X8)
     1   40.12    0.01    0.03    0.03 ^ wire145698/Z (BUF_X8)
                                         net145698 (net)
                  0.02    0.01    0.05 ^ wire145697/A (BUF_X16)
     1   55.46    0.01    0.02    0.07 ^ wire145697/Z (BUF_X16)
                                         net145697 (net)
                  0.03    0.02    0.10 ^ wire145696/A (BUF_X16)
     1   48.14    0.01    0.03    0.12 ^ wire145696/Z (BUF_X16)
                                         net145696 (net)
                  0.02    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.47    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_9_0_clk (net)
                  0.03    0.00   10.58 ^ clkbuf_leaf_30_clk/A (CLKBUF_X3)
     6   11.91    0.01    0.05   10.62 ^ clkbuf_leaf_30_clk/Z (CLKBUF_X3)
                                         clknet_leaf_30_clk (net)
                  0.01    0.00   10.62 ^ result_value[88]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -48.92   data arrival time
-----------------------------------------------------------------------------
                                -38.33   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_d8/attention_two_pass_stream_v1/2_floorplan_final.rpt`
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
                                         _213270_ (net)
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
