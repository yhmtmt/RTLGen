# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 78fa1b5e | attention_dual_stream_schedule_wrapper_score32_exp_lut | ok | 48.6509 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt` |
| 2870c215 | attention_dual_stream_schedule_wrapper_score32_exp_lut | ok | 48.6580 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.1000`
- data_arrival_time: `48.6500`
- data_required_time: `10.5500`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   40.93    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.01    0.05 ^ wire246678/A (BUF_X16)
     1   48.75    0.01    0.02    0.07 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.94    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   29.24    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.50 ^ clkbuf_6_18_0_clk/A (CLKBUF_X3)
    15   55.07    0.04    0.07   10.57 ^ clkbuf_6_18_0_clk/Z (CLKBUF_X3)
                                         clknet_6_18_0_clk (net)
                  0.04    0.01   10.58 ^ u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.58   clock reconvergence pessimism
                         -0.03   10.55   library setup time
                                 10.55   data required time
-----------------------------------------------------------------------------
                                 10.55   data required time
                                -48.65   data arrival time
-----------------------------------------------------------------------------
                                -38.10   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_0/stream_buf_1_pipe_1[60]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.7600`
- data_required_time: `0.7400`

```text
Startpoint: u_cluster_datapath_0/stream_buf_1_pipe_1[60]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   40.93    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.01    0.05 ^ wire246678/A (BUF_X16)
     1   48.75    0.01    0.02    0.07 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.94    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   29.24    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_28_0_clk (net)
                  0.10    0.01    0.67 ^ clkbuf_leaf_322_clk/A (CLKBUF_X3)
     6   10.56    0.02    0.06    0.73 ^ clkbuf_leaf_322_clk/Z (CLKBUF_X3)
                                         clknet_leaf_322_clk (net)
                  0.02    0.00    0.73 ^ u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.73   clock reconvergence pessimism
                          0.01    0.74   library hold time
                                  0.74   data required time
-----------------------------------------------------------------------------
                                  0.74   data required time
                                 -0.76   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[1]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.0600`
- data_arrival_time: `2.0700`
- data_required_time: `1.0100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[1]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.57    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input399/A (CLKBUF_X3)
    19   57.06    0.04    0.07    2.07 ^ input399/Z (CLKBUF_X3)
                                         net398 (net)
                  0.04    0.00    2.07 ^ completed_count[1]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
...
                                         net246680 (net)
                  0.03    0.02    0.67 ^ wire246680/A (BUF_X8)
     6   40.59    0.01    0.03    0.69 ^ wire246680/Z (BUF_X8)
                                         net246679 (net)
                  0.04    0.03    0.73 ^ clkbuf_leaf_285_clk/A (CLKBUF_X3)
     7    9.34    0.01    0.05    0.77 ^ clkbuf_leaf_285_clk/Z (CLKBUF_X3)
                                         clknet_leaf_285_clk (net)
                  0.01    0.00    0.77 ^ completed_count[1]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.77   clock reconvergence pessimism
                          0.24    1.01   library removal time
                                  1.01   data required time
-----------------------------------------------------------------------------
                                  1.01   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.06   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[165]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.1600`
- data_arrival_time: `3.4700`
- data_required_time: `10.6400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_cluster_datapath_1/softmax_scores_pipe_0[165]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.57    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input399/A (CLKBUF_X3)
    19   57.06    0.04    0.07    2.07 ^ input399/Z (CLKBUF_X3)
                                         net398 (net)
                  0.04    0.01    2.08 ^ place246388/A (BUF_X1)
     1   24.44    0.05    0.08    2.16 ^ place246388/Z (BUF_X1)
                                         net246387 (net)
                  0.06    0.01    2.17 ^ place246389/A (BUF_X1)
    11   59.97    0.13    0.15    2.32 ^ place246389/Z (BUF_X1)
                                         net246388 (net)
                  0.14    0.04    2.36 ^ place246394/A (BUF_X1)
     1    4.49    0.02    0.04    2.40 ^ place246394/Z (BUF_X1)
...
                                         clknet_4_12_0_clk (net)
                  0.03    0.00   10.49 ^ clkbuf_6_49_0_clk/A (CLKBUF_X3)
    12   33.64    0.03    0.06   10.55 ^ clkbuf_6_49_0_clk/Z (CLKBUF_X3)
                                         clknet_6_49_0_clk (net)
                  0.03    0.00   10.56 ^ clkbuf_leaf_38_clk/A (CLKBUF_X3)
     8    9.25    0.01    0.04   10.60 ^ clkbuf_leaf_38_clk/Z (CLKBUF_X3)
                                         clknet_leaf_38_clk (net)
                  0.01    0.00   10.60 ^ u_cluster_datapath_1/softmax_scores_pipe_0[165]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.60   clock reconvergence pessimism
                          0.04   10.64   library recovery time
                                 10.64   data required time
-----------------------------------------------------------------------------
                                 10.64   data required time
                                 -3.47   data arrival time
-----------------------------------------------------------------------------
                                  7.16   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-52.1400`
- data_arrival_time: `62.1000`
- data_required_time: `9.9600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.40    0.01    0.10    0.10 ^ u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_0/softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_cluster_datapath_0/u_softmax/_124484_/A (INV_X1)
     2    4.24    0.01    0.01    0.12 v u_cluster_datapath_0/u_softmax/_124484_/ZN (INV_X1)
                                         u_cluster_datapath_0/u_softmax/_003435_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_0/u_softmax/_229610_/B (HA_X1)
     2    2.95    0.01    0.06    0.17 v u_cluster_datapath_0/u_softmax/_229610_/S (HA_X1)
                                         u_cluster_datapath_0/u_softmax/_003437_ (net)
                  0.01    0.00    0.17 v u_cluster_datapath_0/u_softmax/_124420_/B2 (AOI21_X1)
     1    1.66    0.02    0.03    0.21 ^ u_cluster_datapath_0/u_softmax/_124420_/ZN (AOI21_X1)
                                         u_cluster_datapath_0/u_softmax/_053761_ (net)
                  0.02    0.00    0.21 ^ u_cluster_datapath_0/u_softmax/_124422_/B1 (OAI21_X1)
...
                                 62.10   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_0/u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -62.10   data arrival time
-----------------------------------------------------------------------------
                                -52.14   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.7100`
- data_arrival_time: `51.6600`
- data_required_time: `9.9600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    4.24    0.01    0.09    0.09 v u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_0/softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.09 v u_cluster_datapath_0/u_softmax/_124500_/A (INV_X1)
     1    4.93    0.01    0.02    0.11 ^ u_cluster_datapath_0/u_softmax/_124500_/ZN (INV_X1)
                                         u_cluster_datapath_0/u_softmax/_003483_ (net)
                  0.01    0.00    0.11 ^ u_cluster_datapath_0/u_softmax/_229626_/B (HA_X1)
     2    5.14    0.04    0.06    0.17 ^ u_cluster_datapath_0/u_softmax/_229626_/S (HA_X1)
                                         u_cluster_datapath_0/u_softmax/_003485_ (net)
                  0.04    0.00    0.17 ^ u_cluster_datapath_0/u_softmax/_124457_/B2 (AOI21_X1)
     1    3.44    0.01    0.02    0.20 v u_cluster_datapath_0/u_softmax/_124457_/ZN (AOI21_X1)
                                         u_cluster_datapath_0/u_softmax/_053798_ (net)
                  0.01    0.00    0.20 v u_cluster_datapath_0/u_softmax/_124459_/B1 (OAI21_X1)
...
                                 51.66   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.66   data arrival time
-----------------------------------------------------------------------------
                                -41.71   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.7100`
- data_arrival_time: `51.6600`
- data_required_time: `9.9600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    4.24    0.01    0.09    0.09 v u_cluster_datapath_0/softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_0/softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.09 v u_cluster_datapath_0/u_softmax/_124500_/A (INV_X1)
     1    4.93    0.01    0.02    0.11 ^ u_cluster_datapath_0/u_softmax/_124500_/ZN (INV_X1)
                                         u_cluster_datapath_0/u_softmax/_003483_ (net)
                  0.01    0.00    0.11 ^ u_cluster_datapath_0/u_softmax/_229626_/B (HA_X1)
     2    5.14    0.04    0.06    0.17 ^ u_cluster_datapath_0/u_softmax/_229626_/S (HA_X1)
                                         u_cluster_datapath_0/u_softmax/_003485_ (net)
                  0.04    0.00    0.17 ^ u_cluster_datapath_0/u_softmax/_124457_/B2 (AOI21_X1)
     1    3.44    0.01    0.02    0.20 v u_cluster_datapath_0/u_softmax/_124457_/ZN (AOI21_X1)
                                         u_cluster_datapath_0/u_softmax/_053798_ (net)
                  0.01    0.00    0.20 v u_cluster_datapath_0/u_softmax/_124459_/B1 (OAI21_X1)
...
                                 51.66   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.66   data arrival time
-----------------------------------------------------------------------------
                                -41.71   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-39.6600`
- data_arrival_time: `49.6100`
- data_required_time: `9.9600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.26    0.01    0.10    0.10 ^ u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_0/softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_cluster_datapath_0/u_softmax/_124484_/A (INV_X1)
     2    4.74    0.01    0.01    0.12 v u_cluster_datapath_0/u_softmax/_124484_/ZN (INV_X1)
                                         u_cluster_datapath_0/u_softmax/_003435_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_0/u_softmax/_229610_/B (HA_X1)
     2    3.49    0.01    0.06    0.17 v u_cluster_datapath_0/u_softmax/_229610_/S (HA_X1)
                                         u_cluster_datapath_0/u_softmax/_003437_ (net)
                  0.01    0.00    0.17 v u_cluster_datapath_0/u_softmax/_124420_/B2 (AOI21_X1)
     1    2.21    0.02    0.04    0.21 ^ u_cluster_datapath_0/u_softmax/_124420_/ZN (AOI21_X1)
                                         u_cluster_datapath_0/u_softmax/_053761_ (net)
                  0.02    0.00    0.21 ^ u_cluster_datapath_0/u_softmax/_124422_/B1 (OAI21_X1)
...
                                 49.61   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -49.61   data arrival time
-----------------------------------------------------------------------------
                                -39.66   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_global_route.rpt`
- stage: `route`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.3600`
- data_arrival_time: `48.9700`
- data_required_time: `10.6100`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.00    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   51.83    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.02    0.06 ^ wire246678/A (BUF_X16)
     1   67.26    0.01    0.03    0.08 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.03    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   43.28    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   27.17    0.02    0.06    0.24 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.03    0.00   10.56 ^ clkbuf_6_18_0_clk/A (CLKBUF_X3)
    15   51.12    0.04    0.07   10.63 ^ clkbuf_6_18_0_clk/Z (CLKBUF_X3)
                                         clknet_6_18_0_clk (net)
                  0.04    0.01   10.64 ^ u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.64   clock reconvergence pessimism
                         -0.03   10.61   library setup time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                -48.97   data arrival time
-----------------------------------------------------------------------------
                                -38.36   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.1000`
- data_arrival_time: `48.6500`
- data_required_time: `10.5500`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   40.93    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.01    0.05 ^ wire246678/A (BUF_X16)
     1   48.75    0.01    0.02    0.07 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.94    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   29.24    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.50 ^ clkbuf_6_18_0_clk/A (CLKBUF_X3)
    15   55.07    0.04    0.07   10.57 ^ clkbuf_6_18_0_clk/Z (CLKBUF_X3)
                                         clknet_6_18_0_clk (net)
                  0.04    0.01   10.58 ^ u_cluster_datapath_0/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.58   clock reconvergence pessimism
                         -0.03   10.55   library setup time
                                 10.55   data required time
-----------------------------------------------------------------------------
                                 10.55   data required time
                                -48.65   data arrival time
-----------------------------------------------------------------------------
                                -38.10   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.6700`
- data_arrival_time: `48.3300`
- data_required_time: `10.6600`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   52.37    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.02    0.06 ^ wire246678/A (BUF_X16)
     1   68.12    0.01    0.03    0.09 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.49    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.42    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_52_0_clk (net)
                  0.05    0.00   10.65 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     7    9.11    0.01    0.05   10.70 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00   10.70 ^ u_cluster_datapath_1/u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                          0.00   10.70   clock reconvergence pessimism
                         -0.04   10.66   library setup time
                                 10.66   data required time
-----------------------------------------------------------------------------
                                 10.66   data required time
                                -48.33   data arrival time
-----------------------------------------------------------------------------
                                -37.67   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_0/stream_buf_1_pipe_1[60]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.7600`
- data_required_time: `0.7400`

```text
Startpoint: u_cluster_datapath_0/stream_buf_1_pipe_1[60]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire246679/A (BUF_X8)
     1   40.93    0.01    0.03    0.04 ^ wire246679/Z (BUF_X8)
                                         net246678 (net)
                  0.02    0.01    0.05 ^ wire246678/A (BUF_X16)
     1   48.75    0.01    0.02    0.07 ^ wire246678/Z (BUF_X16)
                                         net246677 (net)
                  0.02    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.94    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   29.24    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_28_0_clk (net)
                  0.10    0.01    0.67 ^ clkbuf_leaf_322_clk/A (CLKBUF_X3)
     6   10.56    0.02    0.06    0.73 ^ clkbuf_leaf_322_clk/Z (CLKBUF_X3)
                                         clknet_leaf_322_clk (net)
                  0.02    0.00    0.73 ^ u_cluster_datapath_0/stream_buf_1_pipe_1[92]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.73   clock reconvergence pessimism
                          0.01    0.74   library hold time
                                  0.74   data required time
-----------------------------------------------------------------------------
                                  0.74   data required time
                                 -0.76   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```
