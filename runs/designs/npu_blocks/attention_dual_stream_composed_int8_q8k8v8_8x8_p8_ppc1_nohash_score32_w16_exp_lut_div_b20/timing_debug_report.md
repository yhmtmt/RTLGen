# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 06a3b292 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 46.7839 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |
| 5d4f4ca3 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 47.4937 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.3100`
- data_arrival_time: `46.7800`
- data_required_time: `10.4700`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   28.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   36.62    0.01    0.02    0.03 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.04 ^ wire124165/A (BUF_X16)
     1   47.07    0.01    0.02    0.06 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   25.17    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.53    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.41 ^ clkbuf_5_8__f_clk/A (CLKBUF_X3)
     6   64.80    0.05    0.08   10.49 ^ clkbuf_5_8__f_clk/Z (CLKBUF_X3)
                                         clknet_5_8__leaf_clk (net)
                  0.05    0.01   10.50 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                          0.00   10.50   clock reconvergence pessimism
                         -0.03   10.47   library setup time
                                 10.47   data required time
-----------------------------------------------------------------------------
                                 10.47   data required time
                                -46.78   data arrival time
-----------------------------------------------------------------------------
                                -36.31   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[462]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[494]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.5900`
- data_required_time: `0.5600`

```text
Startpoint: stream_buf_0_pipe_1[462]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[494]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   28.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   36.62    0.01    0.02    0.03 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.04 ^ wire124165/A (BUF_X16)
     1   47.07    0.01    0.02    0.06 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   25.17    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.53    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_7__leaf_clk (net)
                  0.04    0.00    0.51 ^ clkbuf_leaf_54_clk/A (CLKBUF_X3)
     7   10.03    0.01    0.05    0.55 ^ clkbuf_leaf_54_clk/Z (CLKBUF_X3)
                                         clknet_leaf_54_clk (net)
                  0.01    0.00    0.56 ^ stream_buf_0_pipe_1[494]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.56   clock reconvergence pessimism
                          0.01    0.56   library hold time
                                  0.56   data required time
-----------------------------------------------------------------------------
                                  0.56   data required time
                                 -0.59   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1[0]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2500`
- data_arrival_time: `2.0900`
- data_required_time: `0.8400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1[0]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.02    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input169/A (CLKBUF_X3)
     6   58.47    0.03    0.05    2.05 ^ input169/Z (CLKBUF_X3)
                                         net168 (net)
                  0.07    0.05    2.09 ^ stream_buf_1[0]$_DFF_PN0_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   28.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
...
                                         clknet_4_15_0_clk (net)
                  0.02    0.00    0.43 ^ clkbuf_5_30__f_clk/A (CLKBUF_X3)
    12   71.42    0.05    0.09    0.52 ^ clkbuf_5_30__f_clk/Z (CLKBUF_X3)
                                         clknet_5_30__leaf_clk (net)
                  0.05    0.00    0.52 ^ clkbuf_leaf_207_clk/A (CLKBUF_X3)
     5   10.26    0.01    0.05    0.57 ^ clkbuf_leaf_207_clk/Z (CLKBUF_X3)
                                         clknet_leaf_207_clk (net)
                  0.01    0.00    0.57 ^ stream_buf_1[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.27    0.84   library removal time
                                  0.84   data required time
-----------------------------------------------------------------------------
                                  0.84   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.25   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[75]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4300`
- data_arrival_time: `3.0900`
- data_required_time: `10.5300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[75]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.02    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input169/A (CLKBUF_X3)
     6   58.47    0.03    0.05    2.05 ^ input169/Z (CLKBUF_X3)
                                         net168 (net)
                  0.07    0.05    2.10 ^ place124060/A (BUF_X1)
     1    4.06    0.01    0.04    2.13 ^ place124060/Z (BUF_X1)
                                         net124059 (net)
                  0.01    0.00    2.13 ^ place124061/A (BUF_X1)
     9   44.35    0.10    0.12    2.25 ^ place124061/Z (BUF_X1)
                                         net124060 (net)
                  0.10    0.02    2.27 ^ place124063/A (BUF_X1)
     2   19.96    0.05    0.08    2.35 ^ place124063/Z (BUF_X1)
...
                                         clknet_4_5_0_clk (net)
                  0.01    0.00   10.39 ^ clkbuf_5_10__f_clk/A (CLKBUF_X3)
    10   27.89    0.02    0.05   10.44 ^ clkbuf_5_10__f_clk/Z (CLKBUF_X3)
                                         clknet_5_10__leaf_clk (net)
                  0.02    0.00   10.44 ^ clkbuf_leaf_274_clk/A (CLKBUF_X3)
     6   10.06    0.01    0.04   10.48 ^ clkbuf_leaf_274_clk/Z (CLKBUF_X3)
                                         clknet_leaf_274_clk (net)
                  0.01    0.00   10.48 ^ softmax_weights_out[75]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.48   clock reconvergence pessimism
                          0.04   10.53   library recovery time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                 -3.09   data arrival time
-----------------------------------------------------------------------------
                                  7.43   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-50.7500`
- data_arrival_time: `60.7000`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
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
                  0.02    0.00    0.11 ^ u_softmax/_125380_/A (INV_X1)
     1    3.34    0.01    0.01    0.13 v u_softmax/_125380_/ZN (INV_X1)
                                         u_softmax/_003466_ (net)
                  0.01    0.00    0.13 v u_softmax/_231431_/B (HA_X1)
     2    3.07    0.01    0.06    0.18 v u_softmax/_231431_/S (HA_X1)
                                         u_softmax/_003468_ (net)
                  0.01    0.00    0.18 v u_softmax/_125339_/A (INV_X1)
     1    1.57    0.01    0.01    0.20 ^ u_softmax/_125339_/ZN (INV_X1)
                                         u_softmax/_054490_ (net)
                  0.01    0.00    0.20 ^ u_softmax/_125340_/B2 (OAI21_X1)
...
                                 60.70   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -60.70   data arrival time
-----------------------------------------------------------------------------
                                -50.75   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[41]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.6100`
- data_arrival_time: `48.5700`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[41]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[41]$_DFF_PN0_/CK (DFFR_X1)
     2    4.45    0.02    0.11    0.11 ^ softmax_scores_pipe_0[41]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[41] (net)
                  0.02    0.00    0.11 ^ u_softmax/_231423_/A (HA_X1)
     2    4.33    0.03    0.06    0.17 ^ u_softmax/_231423_/S (HA_X1)
                                         u_softmax/_003444_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_125348_/B2 (AOI21_X1)
     1    3.24    0.01    0.02    0.19 v u_softmax/_125348_/ZN (AOI21_X1)
                                         u_softmax/_054499_ (net)
                  0.01    0.00    0.19 v u_softmax/_125350_/B1 (OAI21_X1)
     1    2.91    0.02    0.03    0.23 ^ u_softmax/_125350_/ZN (OAI21_X1)
                                         u_softmax/_054501_ (net)
                  0.02    0.00    0.23 ^ u_softmax/_125351_/B1 (AOI21_X1)
...
                                 48.57   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.57   data arrival time
-----------------------------------------------------------------------------
                                -38.61   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[41]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.6100`
- data_arrival_time: `48.5700`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[41]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[41]$_DFF_PN0_/CK (DFFR_X1)
     2    4.45    0.02    0.11    0.11 ^ softmax_scores_pipe_0[41]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[41] (net)
                  0.02    0.00    0.11 ^ u_softmax/_231423_/A (HA_X1)
     2    4.33    0.03    0.06    0.17 ^ u_softmax/_231423_/S (HA_X1)
                                         u_softmax/_003444_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_125348_/B2 (AOI21_X1)
     1    3.24    0.01    0.02    0.19 v u_softmax/_125348_/ZN (AOI21_X1)
                                         u_softmax/_054499_ (net)
                  0.01    0.00    0.19 v u_softmax/_125350_/B1 (OAI21_X1)
     1    2.91    0.02    0.03    0.23 ^ u_softmax/_125350_/ZN (OAI21_X1)
                                         u_softmax/_054501_ (net)
                  0.02    0.00    0.23 ^ u_softmax/_125351_/B1 (AOI21_X1)
...
                                 48.57   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.57   data arrival time
-----------------------------------------------------------------------------
                                -38.61   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[33]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.8900`
- data_arrival_time: `47.8500`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[33]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[33]$_DFF_PN0_/CK (DFFR_X1)
     2    4.70    0.02    0.11    0.11 ^ softmax_scores_pipe_0[33]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[33] (net)
                  0.02    0.00    0.11 ^ u_softmax/_231431_/A (HA_X1)
     2    3.66    0.03    0.06    0.17 ^ u_softmax/_231431_/S (HA_X1)
                                         u_softmax/_003468_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_125339_/A (INV_X1)
     1    1.94    0.01    0.01    0.18 v u_softmax/_125339_/ZN (INV_X1)
                                         u_softmax/_054490_ (net)
                  0.01    0.00    0.18 v u_softmax/_125340_/B2 (OAI21_X1)
     1    1.93    0.02    0.03    0.21 ^ u_softmax/_125340_/ZN (OAI21_X1)
                                         u_softmax/_054491_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_125341_/B1 (AOI21_X1)
...
                                 47.85   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -47.85   data arrival time
-----------------------------------------------------------------------------
                                -37.89   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.6400`
- data_arrival_time: `47.1800`
- data_required_time: `10.5400`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   45.51    0.01    0.03    0.04 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.05 ^ wire124165/A (BUF_X16)
     1   64.13    0.01    0.03    0.07 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.59    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   26.18    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.47 ^ clkbuf_5_8__f_clk/A (CLKBUF_X3)
     6   68.59    0.05    0.08   10.56 ^ clkbuf_5_8__f_clk/Z (CLKBUF_X3)
                                         clknet_5_8__leaf_clk (net)
                  0.05    0.01   10.57 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                          0.00   10.57   clock reconvergence pessimism
                         -0.03   10.54   library setup time
                                 10.54   data required time
-----------------------------------------------------------------------------
                                 10.54   data required time
                                -47.18   data arrival time
-----------------------------------------------------------------------------
                                -36.64   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.3100`
- data_arrival_time: `46.7800`
- data_required_time: `10.4700`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   28.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   36.62    0.01    0.02    0.03 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.04 ^ wire124165/A (BUF_X16)
     1   47.07    0.01    0.02    0.06 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   25.17    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   21.53    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.41 ^ clkbuf_5_8__f_clk/A (CLKBUF_X3)
     6   64.80    0.05    0.08   10.49 ^ clkbuf_5_8__f_clk/Z (CLKBUF_X3)
                                         clknet_5_8__leaf_clk (net)
                  0.05    0.01   10.50 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                          0.00   10.50   clock reconvergence pessimism
                         -0.03   10.47   library setup time
                                 10.47   data required time
-----------------------------------------------------------------------------
                                 10.47   data required time
                                -46.78   data arrival time
-----------------------------------------------------------------------------
                                -36.31   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.0000`
- data_arrival_time: `46.5400`
- data_required_time: `10.5400`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   43.43    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   45.73    0.01    0.03    0.04 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.05 ^ wire124165/A (BUF_X16)
     1   64.81    0.01    0.03    0.08 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.63    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.49    0.02    0.06    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_4_0_clk (net)
                  0.02    0.00   10.47 ^ clkbuf_5_8__f_clk/A (CLKBUF_X3)
     6   61.20    0.05    0.08   10.55 ^ clkbuf_5_8__f_clk/Z (CLKBUF_X3)
                                         clknet_5_8__leaf_clk (net)
                  0.05    0.02   10.57 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                          0.00   10.57   clock reconvergence pessimism
                         -0.03   10.54   library setup time
                                 10.54   data required time
-----------------------------------------------------------------------------
                                 10.54   data required time
                                -46.54   data arrival time
-----------------------------------------------------------------------------
                                -36.00   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- stage: `cts`
- startpoint: `stream_buf_0_pipe_1[462]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[494]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.6200`
- data_required_time: `0.6000`

```text
Startpoint: stream_buf_0_pipe_1[462]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[494]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   43.43    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire124166/A (BUF_X8)
     1   45.73    0.01    0.03    0.04 ^ wire124166/Z (BUF_X8)
                                         net124165 (net)
                  0.02    0.01    0.05 ^ wire124165/A (BUF_X16)
     1   64.81    0.01    0.03    0.08 ^ wire124165/Z (BUF_X16)
                                         net124164 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.63    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.49    0.02    0.06    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_7__leaf_clk (net)
                  0.03    0.00    0.55 ^ clkbuf_leaf_54_clk/A (CLKBUF_X3)
     7    9.57    0.01    0.04    0.60 ^ clkbuf_leaf_54_clk/Z (CLKBUF_X3)
                                         clknet_leaf_54_clk (net)
                  0.01    0.00    0.60 ^ stream_buf_0_pipe_1[494]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.60   clock reconvergence pessimism
                          0.01    0.60   library hold time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -0.62   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```
