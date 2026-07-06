# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| beda508d | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20 | ok | 47.1077 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt` |
| 9e1d444a | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20 | ok | 47.4250 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[33]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.5400`
- data_arrival_time: `47.1100`
- data_required_time: `10.5700`

```text
Startpoint: softmax_scores_pipe_0[33]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   32.31    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   38.08    0.01    0.02    0.03 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.01    0.05 ^ wire136424/A (BUF_X16)
     1   68.11    0.01    0.02    0.07 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.44    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   23.19    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_16_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_32__f_clk/A (CLKBUF_X3)
     7   71.73    0.05    0.08   10.57 ^ clkbuf_6_32__f_clk/Z (CLKBUF_X3)
                                         clknet_6_32__leaf_clk (net)
                  0.06    0.03   10.60 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X2)
                          0.00   10.60   clock reconvergence pessimism
                         -0.03   10.57   library setup time
                                 10.57   data required time
-----------------------------------------------------------------------------
                                 10.57   data required time
                                -47.11   data arrival time
-----------------------------------------------------------------------------
                                -36.54   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1_pipe_1[561]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[593]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.6700`
- data_required_time: `0.6200`

```text
Startpoint: stream_buf_1_pipe_1[561]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[593]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   32.31    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   38.08    0.01    0.02    0.03 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.01    0.05 ^ wire136424/A (BUF_X16)
     1   68.11    0.01    0.02    0.07 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.44    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   17.58    0.02    0.05    0.22 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_37__leaf_clk (net)
                  0.04    0.00    0.57 ^ clkbuf_leaf_49_clk/A (CLKBUF_X3)
     6   15.42    0.02    0.05    0.62 ^ clkbuf_leaf_49_clk/Z (CLKBUF_X3)
                                         clknet_leaf_49_clk (net)
                  0.02    0.00    0.62 ^ stream_buf_0_pipe_1[593]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.01    0.62   library hold time
                                  0.62   data required time
-----------------------------------------------------------------------------
                                  0.62   data required time
                                 -0.67   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_0[348]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3300`
- data_arrival_time: `2.2400`
- data_required_time: `0.9100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_0[348]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.56    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
     1   13.79    0.01    0.03    2.03 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.01    0.00    2.04 ^ place136181/A (BUF_X2)
     2   37.19    0.04    0.06    2.10 ^ place136181/Z (BUF_X2)
                                         net136180 (net)
                  0.04    0.01    2.11 ^ place136182/A (BUF_X2)
    11   80.09    0.09    0.11    2.22 ^ place136182/Z (BUF_X2)
                                         net136181 (net)
                  0.09    0.02    2.24 ^ stream_buf_1_pipe_0[348]$_DFF_PN0_/RN (DFFR_X2)
                                  2.24   data arrival time
...
                                         clknet_5_29_0_clk (net)
                  0.02    0.00    0.48 ^ clkbuf_6_59__f_clk/A (CLKBUF_X3)
    14   66.46    0.05    0.08    0.57 ^ clkbuf_6_59__f_clk/Z (CLKBUF_X3)
                                         clknet_6_59__leaf_clk (net)
                  0.05    0.01    0.57 ^ clkbuf_leaf_161_clk/A (CLKBUF_X3)
     4   14.55    0.02    0.05    0.63 ^ clkbuf_leaf_161_clk/Z (CLKBUF_X3)
                                         clknet_leaf_161_clk (net)
                  0.02    0.00    0.63 ^ stream_buf_1_pipe_0[348]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.63   clock reconvergence pessimism
                          0.28    0.91   library removal time
                                  0.91   data required time
-----------------------------------------------------------------------------
                                  0.91   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                  1.33   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_1[1022]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4800`
- data_arrival_time: `3.1200`
- data_required_time: `10.6000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_1[1022]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.56    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
     1   13.79    0.01    0.03    2.03 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.01    0.00    2.04 ^ place136181/A (BUF_X2)
     2   37.19    0.04    0.06    2.10 ^ place136181/Z (BUF_X2)
                                         net136180 (net)
                  0.04    0.01    2.11 ^ place136182/A (BUF_X2)
    11   80.09    0.09    0.11    2.22 ^ place136182/Z (BUF_X2)
                                         net136181 (net)
                  0.09    0.02    2.24 ^ place136201/A (BUF_X2)
     2   23.46    0.03    0.05    2.30 ^ place136201/Z (BUF_X2)
...
                                         clknet_5_0_0_clk (net)
                  0.03    0.00   10.45 ^ clkbuf_6_0__f_clk/A (CLKBUF_X3)
     4   29.27    0.02    0.06   10.51 ^ clkbuf_6_0__f_clk/Z (CLKBUF_X3)
                                         clknet_6_0__leaf_clk (net)
                  0.02    0.00   10.51 ^ clkbuf_leaf_472_clk/A (CLKBUF_X3)
     4    5.80    0.01    0.04   10.55 ^ clkbuf_leaf_472_clk/Z (CLKBUF_X3)
                                         clknet_leaf_472_clk (net)
                  0.01    0.00   10.55 ^ stream_buf_1_pipe_1[1022]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.55   clock reconvergence pessimism
                          0.05   10.60   library recovery time
                                 10.60   data required time
-----------------------------------------------------------------------------
                                 10.60   data required time
                                 -3.12   data arrival time
-----------------------------------------------------------------------------
                                  7.48   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-54.9000`
- data_arrival_time: `64.8600`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[48]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     4    8.09    0.02    0.11    0.11 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.02    0.00    0.11 ^ u_softmax/_124031_/A (INV_X1)
     1    3.34    0.01    0.01    0.13 v u_softmax/_124031_/ZN (INV_X1)
                                         u_softmax/_003475_ (net)
                  0.01    0.00    0.13 v u_softmax/_228709_/B (HA_X1)
     2    2.93    0.01    0.06    0.18 v u_softmax/_228709_/S (HA_X1)
                                         u_softmax/_003477_ (net)
                  0.01    0.00    0.18 v u_softmax/_123980_/B2 (AOI21_X1)
     1    1.66    0.02    0.03    0.22 ^ u_softmax/_123980_/ZN (AOI21_X1)
                                         u_softmax/_053269_ (net)
                  0.02    0.00    0.22 ^ u_softmax/_123982_/B1 (OAI21_X1)
...
                                 64.86   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -64.86   data arrival time
-----------------------------------------------------------------------------
                                -54.90   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-39.0600`
- data_arrival_time: `49.0200`
- data_required_time: `9.9500`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    3.05    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124031_/A (INV_X1)
     1    4.29    0.01    0.01    0.12 v u_softmax/_124031_/ZN (INV_X1)
                                         u_softmax/_003475_ (net)
                  0.01    0.00    0.12 v u_softmax/_228709_/B (HA_X1)
     2    3.66    0.01    0.06    0.17 v u_softmax/_228709_/S (HA_X1)
                                         u_softmax/_003477_ (net)
                  0.01    0.00    0.17 v u_softmax/_123980_/B2 (AOI21_X1)
     1    2.77    0.03    0.04    0.21 ^ u_softmax/_123980_/ZN (AOI21_X1)
                                         u_softmax/_053269_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_123982_/B1 (OAI21_X1)
...
                                 49.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -49.02   data arrival time
-----------------------------------------------------------------------------
                                -39.06   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-39.0600`
- data_arrival_time: `49.0200`
- data_required_time: `9.9500`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    3.05    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124031_/A (INV_X1)
     1    4.29    0.01    0.01    0.12 v u_softmax/_124031_/ZN (INV_X1)
                                         u_softmax/_003475_ (net)
                  0.01    0.00    0.12 v u_softmax/_228709_/B (HA_X1)
     2    3.66    0.01    0.06    0.17 v u_softmax/_228709_/S (HA_X1)
                                         u_softmax/_003477_ (net)
                  0.01    0.00    0.17 v u_softmax/_123980_/B2 (AOI21_X1)
     1    2.77    0.03    0.04    0.21 ^ u_softmax/_123980_/ZN (AOI21_X1)
                                         u_softmax/_053269_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_123982_/B1 (OAI21_X1)
...
                                 49.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -49.02   data arrival time
-----------------------------------------------------------------------------
                                -39.06   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.4300`
- data_arrival_time: `48.3900`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    2.77    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124031_/A (INV_X1)
     1    3.85    0.01    0.01    0.11 v u_softmax/_124031_/ZN (INV_X1)
                                         u_softmax/_003475_ (net)
                  0.01    0.00    0.11 v u_softmax/_228709_/B (HA_X1)
     2    3.83    0.01    0.06    0.17 v u_softmax/_228709_/S (HA_X1)
                                         u_softmax/_003477_ (net)
                  0.01    0.00    0.17 v u_softmax/_123980_/B2 (AOI21_X1)
     1    2.78    0.03    0.04    0.21 ^ u_softmax/_123980_/ZN (AOI21_X1)
                                         u_softmax/_053269_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_123982_/B1 (OAI21_X1)
...
                                 48.39   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.39   data arrival time
-----------------------------------------------------------------------------
                                -38.43   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[33]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.9100`
- data_arrival_time: `47.4900`
- data_required_time: `10.5800`

```text
Startpoint: softmax_scores_pipe_0[33]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   47.84    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   49.85    0.01    0.03    0.04 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.02    0.06 ^ wire136424/A (BUF_X16)
     1   63.83    0.01    0.03    0.08 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.59    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.12    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_16_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_32__f_clk/A (CLKBUF_X3)
     7   82.90    0.05    0.08   10.58 ^ clkbuf_6_32__f_clk/Z (CLKBUF_X3)
                                         clknet_6_32__leaf_clk (net)
                  0.07    0.04   10.61 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X2)
                          0.00   10.61   clock reconvergence pessimism
                         -0.03   10.58   library setup time
                                 10.58   data required time
-----------------------------------------------------------------------------
                                 10.58   data required time
                                -47.49   data arrival time
-----------------------------------------------------------------------------
                                -36.91   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[33]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.5400`
- data_arrival_time: `47.1100`
- data_required_time: `10.5700`

```text
Startpoint: softmax_scores_pipe_0[33]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   32.31    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   38.08    0.01    0.02    0.03 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.01    0.05 ^ wire136424/A (BUF_X16)
     1   68.11    0.01    0.02    0.07 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.44    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   23.19    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_16_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_32__f_clk/A (CLKBUF_X3)
     7   71.73    0.05    0.08   10.57 ^ clkbuf_6_32__f_clk/Z (CLKBUF_X3)
                                         clknet_6_32__leaf_clk (net)
                  0.06    0.03   10.60 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X2)
                          0.00   10.60   clock reconvergence pessimism
                         -0.03   10.57   library setup time
                                 10.57   data required time
-----------------------------------------------------------------------------
                                 10.57   data required time
                                -47.11   data arrival time
-----------------------------------------------------------------------------
                                -36.54   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[33]$_DFF_PN0_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.4700`
- data_arrival_time: `47.0800`
- data_required_time: `10.6100`

```text
Startpoint: softmax_scores_pipe_0[33]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.42    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   52.06    0.01    0.03    0.04 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.02    0.06 ^ wire136424/A (BUF_X16)
     1   67.32    0.01    0.03    0.09 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.42    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.35    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net136426 (net)
                  0.03    0.02   10.59 ^ wire136426/A (BUF_X8)
     1   39.29    0.01    0.03   10.62 ^ wire136426/Z (BUF_X8)
                                         net136425 (net)
                  0.03    0.02   10.65 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X2)
                          0.00   10.65   clock reconvergence pessimism
                         -0.04   10.61   library setup time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                -47.08   data arrival time
-----------------------------------------------------------------------------
                                -36.47   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1_pipe_1[561]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[593]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.6700`
- data_required_time: `0.6200`

```text
Startpoint: stream_buf_1_pipe_1[561]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[593]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   32.31    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire136425/A (BUF_X8)
     1   38.08    0.01    0.02    0.03 ^ wire136425/Z (BUF_X8)
                                         net136424 (net)
                  0.02    0.01    0.05 ^ wire136424/A (BUF_X16)
     1   68.11    0.01    0.02    0.07 ^ wire136424/Z (BUF_X16)
                                         net136423 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.44    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   17.58    0.02    0.05    0.22 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_37__leaf_clk (net)
                  0.04    0.00    0.57 ^ clkbuf_leaf_49_clk/A (CLKBUF_X3)
     6   15.42    0.02    0.05    0.62 ^ clkbuf_leaf_49_clk/Z (CLKBUF_X3)
                                         clknet_leaf_49_clk (net)
                  0.02    0.00    0.62 ^ stream_buf_0_pipe_1[593]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.01    0.62   library hold time
                                  0.62   data required time
-----------------------------------------------------------------------------
                                  0.62   data required time
                                 -0.67   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```
