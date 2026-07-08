# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 78fa1b5e | attention_dual_stream_schedule_wrapper_score32_exp_lut | ok | 49.6702 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt` |
| 2870c215 | attention_dual_stream_schedule_wrapper_score32_exp_lut | ok | 49.8660 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.7900`
- data_arrival_time: `49.6700`
- data_required_time: `10.8800`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   40.69    0.01    0.02    0.03 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.02    0.01    0.05 ^ wire504662/A (BUF_X16)
     1   69.78    0.01    0.02    0.07 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.04    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   52.45    0.01    0.03    0.13 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.02    0.16 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.38    0.03    0.06    0.21 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_85__leaf_clk (net)
                  0.09    0.05   10.86 ^ clkbuf_leaf_1146_clk/A (CLKBUF_X3)
     3    7.75    0.01    0.06   10.92 ^ clkbuf_leaf_1146_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1146_clk (net)
                  0.01    0.00   10.92 ^ u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.92   clock reconvergence pessimism
                         -0.04   10.88   library setup time
                                 10.88   data required time
-----------------------------------------------------------------------------
                                 10.88   data required time
                                -49.67   data arrival time
-----------------------------------------------------------------------------
                                -38.79   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_3/stream_buf_1_pipe_1[441]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0400`
- data_arrival_time: `0.9000`
- data_required_time: `0.8600`

```text
Startpoint: u_cluster_datapath_3/stream_buf_1_pipe_1[441]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   40.69    0.01    0.02    0.03 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.02    0.01    0.05 ^ wire504662/A (BUF_X16)
     1   69.78    0.01    0.02    0.07 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.04    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   52.45    0.01    0.03    0.13 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.02    0.16 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.38    0.03    0.06    0.21 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_51__leaf_clk (net)
                  0.05    0.01    0.81 ^ clkbuf_leaf_260_clk/A (CLKBUF_X3)
     8   10.31    0.01    0.05    0.86 ^ clkbuf_leaf_260_clk/Z (CLKBUF_X3)
                                         clknet_leaf_260_clk (net)
                  0.01    0.00    0.86 ^ u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.86   clock reconvergence pessimism
                          0.01    0.86   library hold time
                                  0.86   data required time
-----------------------------------------------------------------------------
                                  0.86   data required time
                                 -0.90   data arrival time
-----------------------------------------------------------------------------
                                  0.04   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_cluster_datapath_1/score_mix_1_out[18]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.0900`
- data_arrival_time: `2.2900`
- data_required_time: `1.2000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_cluster_datapath_1/score_mix_1_out[18]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.99    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input748/A (CLKBUF_X3)
     1   16.81    0.02    0.03    2.04 ^ input748/Z (CLKBUF_X3)
                                         net747 (net)
                  0.02    0.01    2.04 ^ place504018/A (BUF_X1)
     1   23.83    0.05    0.07    2.11 ^ place504018/Z (BUF_X1)
                                         net504017 (net)
                  0.06    0.02    2.13 ^ place504019/A (BUF_X1)
     4   50.73    0.11    0.13    2.26 ^ place504019/Z (BUF_X1)
                                         net504018 (net)
                  0.11    0.02    2.29 ^ u_cluster_datapath_1/score_mix_1_out[18]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.29   data arrival time
...
                                         clknet_6_39_0_clk (net)
                  0.02    0.00    0.72 ^ clkbuf_7_78__f_clk/A (CLKBUF_X3)
    23   80.09    0.06    0.09    0.82 ^ clkbuf_7_78__f_clk/Z (CLKBUF_X3)
                                         clknet_7_78__leaf_clk (net)
                  0.06    0.00    0.82 ^ clkbuf_leaf_959_clk/A (CLKBUF_X3)
     7   11.91    0.01    0.05    0.87 ^ clkbuf_leaf_959_clk/Z (CLKBUF_X3)
                                         clknet_leaf_959_clk (net)
                  0.01    0.00    0.87 ^ u_cluster_datapath_1/score_mix_1_out[18]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.87   clock reconvergence pessimism
                          0.33    1.20   library removal time
                                  1.20   data required time
-----------------------------------------------------------------------------
                                  1.20   data required time
                                 -2.29   data arrival time
-----------------------------------------------------------------------------
                                  1.09   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_cluster_datapath_2/stream_buf_0_pipe_1[320]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.0000`
- data_arrival_time: `3.9200`
- data_required_time: `10.9200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_cluster_datapath_2/stream_buf_0_pipe_1[320]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.99    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input748/A (CLKBUF_X3)
     1   16.81    0.02    0.03    2.04 ^ input748/Z (CLKBUF_X3)
                                         net747 (net)
                  0.02    0.01    2.04 ^ place504018/A (BUF_X1)
     1   23.83    0.05    0.07    2.11 ^ place504018/Z (BUF_X1)
                                         net504017 (net)
                  0.06    0.02    2.13 ^ place504019/A (BUF_X1)
     4   50.73    0.11    0.13    2.26 ^ place504019/Z (BUF_X1)
                                         net504018 (net)
                  0.11    0.03    2.29 ^ place504133/A (BUF_X1)
     6   30.33    0.07    0.10    2.39 ^ place504133/Z (BUF_X1)
...
                                         clknet_6_4_0_clk (net)
                  0.02    0.00   10.73 ^ clkbuf_7_8__f_clk/A (CLKBUF_X3)
    14   73.30    0.06    0.09   10.81 ^ clkbuf_7_8__f_clk/Z (CLKBUF_X3)
                                         clknet_7_8__leaf_clk (net)
                  0.06    0.00   10.82 ^ clkbuf_leaf_1466_clk/A (CLKBUF_X3)
     6   10.04    0.01    0.05   10.87 ^ clkbuf_leaf_1466_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1466_clk (net)
                  0.01    0.00   10.87 ^ u_cluster_datapath_2/stream_buf_0_pipe_1[320]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.87   clock reconvergence pessimism
                          0.05   10.92   library recovery time
                                 10.92   data required time
-----------------------------------------------------------------------------
                                 10.92   data required time
                                 -3.92   data arrival time
-----------------------------------------------------------------------------
                                  7.00   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-54.0500`
- data_arrival_time: `64.0100`
- data_required_time: `9.9600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[48]$_DFF_P_
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
                  0.01    0.00    0.10 ^ u_cluster_datapath_0/u_softmax/_124986_/A (INV_X1)
     2    4.24    0.01    0.01    0.12 v u_cluster_datapath_0/u_softmax/_124986_/ZN (INV_X1)
                                         u_cluster_datapath_0/u_softmax/_003414_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_0/u_softmax/_230655_/B (HA_X1)
     2    2.90    0.01    0.06    0.17 v u_cluster_datapath_0/u_softmax/_230655_/S (HA_X1)
                                         u_cluster_datapath_0/u_softmax/_003416_ (net)
                  0.01    0.00    0.17 v u_cluster_datapath_0/u_softmax/_124925_/B2 (AOI21_X1)
     1    1.70    0.02    0.03    0.21 ^ u_cluster_datapath_0/u_softmax/_124925_/ZN (AOI21_X1)
                                         u_cluster_datapath_0/u_softmax/_054036_ (net)
                  0.02    0.00    0.21 ^ u_cluster_datapath_0/u_softmax/_124926_/A (INV_X1)
...
                                 64.01   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_0/u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -64.01   data arrival time
-----------------------------------------------------------------------------
                                -54.05   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-43.4600`
- data_arrival_time: `53.4100`
- data_required_time: `9.9500`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    4.92    0.02    0.11    0.11 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_1/softmax_scores_pipe_0[17] (net)
                  0.02    0.00    0.11 ^ u_cluster_datapath_1/u_softmax/_124986_/A (INV_X1)
     2    6.56    0.01    0.02    0.12 v u_cluster_datapath_1/u_softmax/_124986_/ZN (INV_X1)
                                         u_cluster_datapath_1/u_softmax/_003414_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_1/u_softmax/_230655_/B (HA_X1)
     2    3.13    0.01    0.06    0.18 v u_cluster_datapath_1/u_softmax/_230655_/S (HA_X1)
                                         u_cluster_datapath_1/u_softmax/_003416_ (net)
                  0.01    0.00    0.18 v u_cluster_datapath_1/u_softmax/_124925_/B2 (AOI21_X1)
     1    3.16    0.03    0.04    0.22 ^ u_cluster_datapath_1/u_softmax/_124925_/ZN (AOI21_X1)
                                         u_cluster_datapath_1/u_softmax/_054036_ (net)
                  0.03    0.00    0.22 ^ u_cluster_datapath_1/u_softmax/_124926_/A (INV_X1)
...
                                 53.41   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -53.41   data arrival time
-----------------------------------------------------------------------------
                                -43.46   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-43.4600`
- data_arrival_time: `53.4100`
- data_required_time: `9.9500`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    4.92    0.02    0.11    0.11 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_1/softmax_scores_pipe_0[17] (net)
                  0.02    0.00    0.11 ^ u_cluster_datapath_1/u_softmax/_124986_/A (INV_X1)
     2    6.56    0.01    0.02    0.12 v u_cluster_datapath_1/u_softmax/_124986_/ZN (INV_X1)
                                         u_cluster_datapath_1/u_softmax/_003414_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_1/u_softmax/_230655_/B (HA_X1)
     2    3.13    0.01    0.06    0.18 v u_cluster_datapath_1/u_softmax/_230655_/S (HA_X1)
                                         u_cluster_datapath_1/u_softmax/_003416_ (net)
                  0.01    0.00    0.18 v u_cluster_datapath_1/u_softmax/_124925_/B2 (AOI21_X1)
     1    3.16    0.03    0.04    0.22 ^ u_cluster_datapath_1/u_softmax/_124925_/ZN (AOI21_X1)
                                         u_cluster_datapath_1/u_softmax/_054036_ (net)
                  0.03    0.00    0.22 ^ u_cluster_datapath_1/u_softmax/_124926_/A (INV_X1)
...
                                 53.41   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -53.41   data arrival time
-----------------------------------------------------------------------------
                                -43.46   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.8700`
- data_arrival_time: `50.8300`
- data_required_time: `9.9500`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    4.19    0.01    0.11    0.11 ^ u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         u_cluster_datapath_1/softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.11 ^ u_cluster_datapath_1/u_softmax/_124986_/A (INV_X1)
     2    5.69    0.01    0.02    0.12 v u_cluster_datapath_1/u_softmax/_124986_/ZN (INV_X1)
                                         u_cluster_datapath_1/u_softmax/_003414_ (net)
                  0.01    0.00    0.12 v u_cluster_datapath_1/u_softmax/_230655_/B (HA_X1)
     2    2.94    0.01    0.06    0.18 v u_cluster_datapath_1/u_softmax/_230655_/S (HA_X1)
                                         u_cluster_datapath_1/u_softmax/_003416_ (net)
                  0.01    0.00    0.18 v u_cluster_datapath_1/u_softmax/_124925_/B2 (AOI21_X1)
     1    2.82    0.03    0.04    0.22 ^ u_cluster_datapath_1/u_softmax/_124925_/ZN (AOI21_X1)
                                         u_cluster_datapath_1/u_softmax/_054036_ (net)
                  0.03    0.00    0.22 ^ u_cluster_datapath_1/u_softmax/_124926_/A (INV_X1)
...
                                 50.83   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -50.83   data arrival time
-----------------------------------------------------------------------------
                                -40.87   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/5_global_route.rpt`
- stage: `route`
- startpoint: `u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.8200`
- data_arrival_time: `49.6800`
- data_required_time: `10.8600`

```text
Startpoint: u_cluster_datapath_0/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.66    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   52.71    0.01    0.03    0.04 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.03    0.02    0.06 ^ wire504662/A (BUF_X16)
     1   72.45    0.01    0.03    0.08 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.04    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   66.10    0.01    0.03    0.14 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.03    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.57    0.03    0.07    0.24 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_94__leaf_clk (net)
                  0.04    0.00   10.85 ^ clkbuf_leaf_848_clk/A (CLKBUF_X3)
     7   10.63    0.01    0.05   10.90 ^ clkbuf_leaf_848_clk/Z (CLKBUF_X3)
                                         clknet_leaf_848_clk (net)
                  0.01    0.00   10.90 ^ u_cluster_datapath_0/u_softmax/weights[112]$_DFF_P_/CK (DFF_X1)
                          0.00   10.90   clock reconvergence pessimism
                         -0.04   10.86   library setup time
                                 10.86   data required time
-----------------------------------------------------------------------------
                                 10.86   data required time
                                -49.68   data arrival time
-----------------------------------------------------------------------------
                                -38.82   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/6_finish.rpt`
- stage: `finish`
- startpoint: `u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.7900`
- data_arrival_time: `49.6700`
- data_required_time: `10.8800`

```text
Startpoint: u_cluster_datapath_1/softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   33.79    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   40.69    0.01    0.02    0.03 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.02    0.01    0.05 ^ wire504662/A (BUF_X16)
     1   69.78    0.01    0.02    0.07 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.04    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   52.45    0.01    0.03    0.13 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.02    0.16 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.38    0.03    0.06    0.21 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_85__leaf_clk (net)
                  0.09    0.05   10.86 ^ clkbuf_leaf_1146_clk/A (CLKBUF_X3)
     3    7.75    0.01    0.06   10.92 ^ clkbuf_leaf_1146_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1146_clk (net)
                  0.01    0.00   10.92 ^ u_cluster_datapath_1/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.92   clock reconvergence pessimism
                         -0.04   10.88   library setup time
                                 10.88   data required time
-----------------------------------------------------------------------------
                                 10.88   data required time
                                -49.67   data arrival time
-----------------------------------------------------------------------------
                                -38.79   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_cluster_datapath_2/softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_2/u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.4000`
- data_arrival_time: `49.3100`
- data_required_time: `10.9100`

```text
Startpoint: u_cluster_datapath_2/softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_2/u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.16    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   53.07    0.01    0.03    0.04 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.02    0.02    0.06 ^ wire504662/A (BUF_X16)
     1   72.94    0.01    0.03    0.09 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.03    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   68.16    0.01    0.03    0.14 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.45    0.03    0.07    0.24 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         net504664 (net)
                  0.02    0.02   10.88 ^ wire504664/A (BUF_X8)
     4   56.06    0.01    0.03   10.91 ^ wire504664/Z (BUF_X8)
                                         net504663 (net)
                  0.04    0.03   10.94 ^ u_cluster_datapath_2/u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.94   clock reconvergence pessimism
                         -0.04   10.91   library setup time
                                 10.91   data required time
-----------------------------------------------------------------------------
                                 10.91   data required time
                                -49.31   data arrival time
-----------------------------------------------------------------------------
                                -38.40   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/attention_dual_stream_schedule_wrapper_score32_exp_lut/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_cluster_datapath_3/stream_buf_1_pipe_1[441]$_DFF_PN0_`
- endpoint: `u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0400`
- data_arrival_time: `0.9400`
- data_required_time: `0.9000`

```text
Startpoint: u_cluster_datapath_3/stream_buf_1_pipe_1[441]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.16    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire504663/A (BUF_X8)
     1   53.07    0.01    0.03    0.04 ^ wire504663/Z (BUF_X8)
                                         net504662 (net)
                  0.02    0.02    0.06 ^ wire504662/A (BUF_X16)
     1   72.94    0.01    0.03    0.09 ^ wire504662/Z (BUF_X16)
                                         net504661 (net)
                  0.03    0.03    0.11 ^ wire504661/A (BUF_X16)
     1   68.16    0.01    0.03    0.14 ^ wire504661/Z (BUF_X16)
                                         net504660 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.45    0.03    0.07    0.24 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_51__leaf_clk (net)
                  0.05    0.01    0.85 ^ clkbuf_leaf_260_clk/A (CLKBUF_X3)
     8   10.56    0.01    0.05    0.90 ^ clkbuf_leaf_260_clk/Z (CLKBUF_X3)
                                         clknet_leaf_260_clk (net)
                  0.01    0.00    0.90 ^ u_cluster_datapath_3/stream_buf_0_pipe_1[473]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.90   clock reconvergence pessimism
                          0.01    0.90   library hold time
                                  0.90   data required time
-----------------------------------------------------------------------------
                                  0.90   data required time
                                 -0.94   data arrival time
-----------------------------------------------------------------------------
                                  0.04   slack (MET)



```
