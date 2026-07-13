# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_two_pass_stream_iterdiv`
- metrics_path: `runs/designs/npu_blocks/attention_two_pass_stream_iterdiv/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| e3b7fa41 | attention_two_pass_stream_iterdiv_v1 | ok | 7.5913 | 0.3 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt` |
| 1fde3964 | attention_two_pass_stream_iterdiv_v1 | ok | 7.6355 | 0.4 | `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
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
     1   59.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire12165/A (BUF_X16)
     1   54.22    0.01    0.03    0.05 ^ wire12165/Z (BUF_X16)
                                         net12165 (net)
                  0.03    0.02    0.07 ^ wire12164/A (BUF_X16)
     1   48.97    0.01    0.03    0.10 ^ wire12164/Z (BUF_X16)
                                         net12164 (net)
                  0.02    0.02    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   15.70    0.02    0.05    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   23.04    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_12_0_clk (net)
                  0.06    0.01    0.57 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     8   10.34    0.01    0.05    0.63 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2200`
- data_arrival_time: `2.0500`
- data_required_time: `0.8400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    9.13    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     8   33.63    0.03    0.05    2.05 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.03    0.01    2.05 ^ completed_count[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   59.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire12165/A (BUF_X16)
...
                                         clknet_3_6_1_clk (net)
                  0.02    0.00    0.47 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    13   61.33    0.04    0.07    0.54 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
                                         clknet_4_13_0_clk (net)
                  0.05    0.03    0.57 ^ clkbuf_leaf_33_clk/A (CLKBUF_X3)
     8   11.29    0.01    0.05    0.62 ^ clkbuf_leaf_33_clk/Z (CLKBUF_X3)
                                         clknet_leaf_33_clk (net)
                  0.01    0.00    0.62 ^ completed_count[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.22    0.84   library removal time
                                  0.84   data required time
-----------------------------------------------------------------------------
                                  0.84   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.22   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `fill_score_row[31] (input port clocked by clk)`
- endpoint: `global_max[19]$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `2.9700`
- data_arrival_time: `7.6400`
- data_required_time: `10.6000`

```text
Startpoint: fill_score_row[31] (input port clocked by clk)
Endpoint: global_max[19]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    5.89    0.00    0.00    2.00 v fill_score_row[31] (in)
                                         fill_score_row[31] (net)
                  0.00    0.00    2.00 v input213/A (BUF_X1)
     2    3.55    0.01    0.03    2.03 v input213/Z (BUF_X1)
                                         net213 (net)
                  0.01    0.00    2.03 v _117858_/A (INV_X1)
     2    6.82    0.02    0.02    2.05 ^ _117858_/ZN (INV_X1)
                                         _027598_ (net)
                  0.02    0.00    2.05 ^ _149768_/A (HA_X1)
     7   20.80    0.11    0.14    2.20 ^ _149768_/S (HA_X1)
                                         _027600_ (net)
                  0.11    0.00    2.20 ^ _117862_/A1 (NAND4_X4)
     3    7.03    0.03    0.04    2.24 v _117862_/ZN (NAND4_X4)
...
                                         net12169 (net)
                  0.02    0.01   10.60 ^ clkbuf_leaf_0_clk/A (CLKBUF_X3)
     6   10.86    0.01    0.04   10.64 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
                                         clknet_leaf_0_clk (net)
                  0.01    0.00   10.64 ^ global_max[19]$_DFF_PN0_/CK (DFFR_X2)
                          0.00   10.64   clock reconvergence pessimism
                         -0.04   10.60   library setup time
                                 10.60   data required time
-----------------------------------------------------------------------------
                                 10.60   data required time
                                 -7.64   data arrival time
-----------------------------------------------------------------------------
                                  2.97   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `global_max[18]$_DFF_PN0_`
- endpoint: `numerator_accum[6][37]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `4.2100`
- data_arrival_time: `6.3300`
- data_required_time: `10.5400`

```text
Startpoint: global_max[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: numerator_accum[6][37]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.05    0.05 ^ wire12165/Z (BUF_X16)
   0.05    0.10 ^ wire12164/Z (BUF_X16)
   0.07    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.22 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.05    0.27 ^ clkbuf_1_0_1_clk/Z (CLKBUF_X3)
   0.05    0.32 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.05    0.37 ^ clkbuf_2_0_1_clk/Z (CLKBUF_X3)
   0.05    0.42 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
   0.06    0.48 ^ clkbuf_3_0_1_clk/Z (CLKBUF_X3)
   0.07    0.55 ^ clkbuf_4_1_0_clk/Z (CLKBUF_X3)
   0.04    0.59 ^ wire12169/Z (BUF_X8)
   0.05    0.64 ^ clkbuf_leaf_0_clk/Z (CLKBUF_X3)
...
   0.05   10.42 ^ clkbuf_3_3_0_clk/Z (CLKBUF_X3)
   0.05   10.47 ^ clkbuf_3_3_1_clk/Z (CLKBUF_X3)
   0.06   10.53 ^ clkbuf_4_7_0_clk/Z (CLKBUF_X3)
   0.05   10.58 ^ clkbuf_leaf_167_clk/Z (CLKBUF_X3)
   0.00   10.58 ^ numerator_accum[6][37]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00   10.58   clock reconvergence pessimism
  -0.04   10.54   library setup time
          10.54   data required time
---------------------------------------------------------
          10.54   data required time
          -6.33   data arrival time
---------------------------------------------------------
           4.21   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `result_global_max[17]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6300`
- data_arrival_time: `3.0600`
- data_required_time: `10.6900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: result_global_max[17]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    9.13    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     8   33.63    0.03    0.05    2.05 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.03    0.01    2.06 ^ place12108/A (BUF_X2)
     2   36.32    0.03    0.05    2.11 ^ place12108/Z (BUF_X2)
                                         net12108 (net)
                  0.05    0.03    2.14 ^ place12109/A (BUF_X2)
    12   48.58    0.04    0.06    2.20 ^ place12109/Z (BUF_X2)
                                         net12109 (net)
                  0.07    0.04    2.24 ^ place12112/A (BUF_X1)
    10   56.46    0.12    0.15    2.39 ^ place12112/Z (BUF_X1)
...
                                         clknet_4_1_0_clk (net)
                  0.04    0.01   10.56 ^ wire12169/A (BUF_X8)
     2   32.37    0.01    0.03   10.59 ^ wire12169/Z (BUF_X8)
                                         net12169 (net)
                  0.02    0.01   10.60 ^ clkbuf_leaf_189_clk/A (CLKBUF_X3)
     4    9.24    0.01    0.04   10.64 ^ clkbuf_leaf_189_clk/Z (CLKBUF_X3)
                                         clknet_leaf_189_clk (net)
                  0.01    0.00   10.64 ^ result_global_max[17]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.64   clock reconvergence pessimism
                          0.05   10.69   library recovery time
                                 10.69   data required time
-----------------------------------------------------------------------------
                                 10.69   data required time
                                 -3.06   data arrival time
-----------------------------------------------------------------------------
                                  7.63   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/2_floorplan_final.rpt`
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
                                         _067195_ (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_detailed_place.rpt`
- stage: `detailed_place`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _067195_ (net)
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

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_global_place.rpt`
- stage: `global_place`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _067195_ (net)
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

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/3_resizer.rpt`
- stage: `resizer`
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
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _067195_ (net)
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

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7800`
- data_required_time: `0.7200`

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
     1   77.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire12165/A (BUF_X16)
     1   71.54    0.01    0.03    0.06 ^ wire12165/Z (BUF_X16)
                                         net12165 (net)
                  0.03    0.03    0.08 ^ wire12164/A (BUF_X16)
     1   68.06    0.01    0.03    0.11 ^ wire12164/Z (BUF_X16)
                                         net12164 (net)
                  0.03    0.02    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.62    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.38    0.02    0.05    0.25 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_12_0_clk (net)
                  0.08    0.01    0.65 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     8   10.27    0.01    0.06    0.71 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.71 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.71   clock reconvergence pessimism
                          0.01    0.72   library hold time
                                  0.72   data required time
-----------------------------------------------------------------------------
                                  0.72   data required time
                                 -0.78   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7800`
- data_required_time: `0.7200`

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
     1   76.50    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire12165/A (BUF_X16)
     1   70.69    0.01    0.03    0.06 ^ wire12165/Z (BUF_X16)
                                         net12165 (net)
                  0.04    0.03    0.08 ^ wire12164/A (BUF_X16)
     1   67.13    0.01    0.03    0.11 ^ wire12164/Z (BUF_X16)
                                         net12164 (net)
                  0.03    0.03    0.14 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.99    0.02    0.05    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.26    0.02    0.05    0.25 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_12_0_clk (net)
                  0.07    0.01    0.65 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     8   11.01    0.01    0.06    0.71 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.71 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.71   clock reconvergence pessimism
                          0.01    0.72   library hold time
                                  0.72   data required time
-----------------------------------------------------------------------------
                                  0.72   data required time
                                 -0.78   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/6_finish.rpt`
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
     1   59.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire12165/A (BUF_X16)
     1   54.22    0.01    0.03    0.05 ^ wire12165/Z (BUF_X16)
                                         net12165 (net)
                  0.03    0.02    0.07 ^ wire12164/A (BUF_X16)
     1   48.97    0.01    0.03    0.10 ^ wire12164/Z (BUF_X16)
                                         net12164 (net)
                  0.02    0.02    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   15.70    0.02    0.05    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   23.04    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_12_0_clk (net)
                  0.06    0.01    0.57 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     8   10.34    0.01    0.05    0.63 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
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

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_two_pass_stream_iterdiv/attention_two_pass_stream_iterdiv_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.1500`
- data_arrival_time: `2.0500`
- data_required_time: `0.9100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.27    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1060/A (CLKBUF_X3)
     8   36.54    0.03    0.05    2.05 ^ input1060/Z (CLKBUF_X3)
                                         net1060 (net)
                  0.03    0.00    2.05 ^ completed_count[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   77.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire12165/A (BUF_X16)
...
                                         clknet_3_6_1_clk (net)
                  0.02    0.00    0.53 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    13   70.96    0.05    0.08    0.61 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
                                         clknet_4_13_0_clk (net)
                  0.06    0.03    0.63 ^ clkbuf_leaf_33_clk/A (CLKBUF_X3)
     8   10.79    0.01    0.05    0.69 ^ clkbuf_leaf_33_clk/Z (CLKBUF_X3)
                                         clknet_leaf_33_clk (net)
                  0.01    0.00    0.69 ^ completed_count[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.69   clock reconvergence pessimism
                          0.22    0.91   library removal time
                                  0.91   data required time
-----------------------------------------------------------------------------
                                  0.91   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.15   slack (MET)
```
