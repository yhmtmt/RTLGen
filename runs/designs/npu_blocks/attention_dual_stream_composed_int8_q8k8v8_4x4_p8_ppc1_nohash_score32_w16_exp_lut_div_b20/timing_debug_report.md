# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 06a3b292 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 46.2248 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |
| 5d4f4ca3 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 46.3519 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-35.8300`
- data_arrival_time: `46.2200`
- data_required_time: `10.4000`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire112073/A (BUF_X16)
     1   44.01    0.01    0.02    0.04 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.72    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   23.45    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   20.57    0.02    0.05    0.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_8__leaf_clk (net)
                  0.04    0.01   10.39 ^ clkbuf_leaf_218_clk/A (CLKBUF_X3)
     7   10.56    0.01    0.05   10.44 ^ clkbuf_leaf_218_clk/Z (CLKBUF_X3)
                                         clknet_leaf_218_clk (net)
                  0.01    0.00   10.44 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X1)
                          0.00   10.44   clock reconvergence pessimism
                         -0.04   10.40   library setup time
                                 10.40   data required time
-----------------------------------------------------------------------------
                                 10.40   data required time
                                -46.22   data arrival time
-----------------------------------------------------------------------------
                                -35.83   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[370]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[402]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.4800`
- data_required_time: `0.4600`

```text
Startpoint: stream_buf_0_pipe_1[370]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[402]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire112073/A (BUF_X16)
     1   44.01    0.01    0.02    0.04 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.72    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.72    0.02    0.05    0.17 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   18.64    0.02    0.05    0.22 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.04    0.02    0.41 ^ clkbuf_leaf_184_clk/A (CLKBUF_X3)
     8   10.30    0.01    0.05    0.46 ^ clkbuf_leaf_184_clk/Z (CLKBUF_X3)
                                         clknet_leaf_184_clk (net)
                  0.01    0.00    0.46 ^ stream_buf_1_pipe_1[402]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.46   clock reconvergence pessimism
                          0.01    0.46   library hold time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `score_mix_1_out[23]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4000`
- data_arrival_time: `2.0800`
- data_required_time: `0.6800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: score_mix_1_out[23]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   20.79    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
     9   46.41    0.02    0.04    2.05 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.05    0.03    2.08 ^ score_mix_1_out[23]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire112073/A (BUF_X16)
...
                                         clknet_4_14_0_clk (net)
                  0.02    0.00    0.33 ^ clkbuf_5_28__f_clk/A (CLKBUF_X3)
    12   31.38    0.03    0.06    0.39 ^ clkbuf_5_28__f_clk/Z (CLKBUF_X3)
                                         clknet_5_28__leaf_clk (net)
                  0.03    0.00    0.39 ^ clkbuf_leaf_72_clk/A (CLKBUF_X3)
     8   13.57    0.01    0.05    0.44 ^ clkbuf_leaf_72_clk/Z (CLKBUF_X3)
                                         clknet_leaf_72_clk (net)
                  0.01    0.00    0.44 ^ score_mix_1_out[23]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.44   clock reconvergence pessimism
                          0.25    0.68   library removal time
                                  0.68   data required time
-----------------------------------------------------------------------------
                                  0.68   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.40   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_scores_pipe_0[31]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5900`
- data_arrival_time: `2.8800`
- data_required_time: `10.4700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_scores_pipe_0[31]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   20.79    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
     9   46.41    0.02    0.04    2.05 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.06    0.04    2.08 ^ place112027/A (BUF_X2)
     4   31.65    0.03    0.06    2.14 ^ place112027/Z (BUF_X2)
                                         net112026 (net)
                  0.04    0.01    2.15 ^ place112028/A (BUF_X2)
    12   51.07    0.06    0.08    2.22 ^ place112028/Z (BUF_X2)
                                         net112027 (net)
                  0.06    0.02    2.24 ^ place112037/A (BUF_X2)
    20   55.14    0.06    0.08    2.32 ^ place112037/Z (BUF_X2)
...
                                         clknet_4_8_0_clk (net)
                  0.02    0.00   10.33 ^ clkbuf_5_17__f_clk/A (CLKBUF_X3)
    11   25.24    0.02    0.05   10.38 ^ clkbuf_5_17__f_clk/Z (CLKBUF_X3)
                                         clknet_5_17__leaf_clk (net)
                  0.02    0.00   10.39 ^ clkbuf_leaf_17_clk/A (CLKBUF_X3)
     7    9.78    0.01    0.04   10.43 ^ clkbuf_leaf_17_clk/Z (CLKBUF_X3)
                                         clknet_leaf_17_clk (net)
                  0.01    0.00   10.43 ^ softmax_scores_pipe_0[31]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.43   clock reconvergence pessimism
                          0.04   10.47   library recovery time
                                 10.47   data required time
-----------------------------------------------------------------------------
                                 10.47   data required time
                                 -2.88   data arrival time
-----------------------------------------------------------------------------
                                  7.59   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-50.4400`
- data_arrival_time: `60.4000`
- data_required_time: `9.9600`

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
     4    8.09    0.02    0.11    0.11 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.02    0.00    0.11 ^ u_softmax/_124512_/A (INV_X1)
     1    3.34    0.01    0.01    0.13 v u_softmax/_124512_/ZN (INV_X1)
                                         u_softmax/_003483_ (net)
                  0.01    0.00    0.13 v u_softmax/_229652_/B (HA_X1)
     2    2.95    0.01    0.06    0.18 v u_softmax/_229652_/S (HA_X1)
                                         u_softmax/_003485_ (net)
                  0.01    0.00    0.18 v u_softmax/_124453_/B2 (AOI21_X1)
     1    1.66    0.02    0.03    0.22 ^ u_softmax/_124453_/ZN (AOI21_X1)
                                         u_softmax/_053670_ (net)
                  0.02    0.00    0.22 ^ u_softmax/_124455_/B1 (OAI21_X1)
...
                                 60.40   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -60.40   data arrival time
-----------------------------------------------------------------------------
                                -50.44   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.7400`
- data_arrival_time: `47.6900`
- data_required_time: `9.9500`

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
     2    3.74    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124512_/A (INV_X1)
     1    3.92    0.01    0.01    0.12 v u_softmax/_124512_/ZN (INV_X1)
                                         u_softmax/_003483_ (net)
                  0.01    0.00    0.12 v u_softmax/_229652_/B (HA_X1)
     2    3.12    0.01    0.06    0.17 v u_softmax/_229652_/S (HA_X1)
                                         u_softmax/_003485_ (net)
                  0.01    0.00    0.17 v u_softmax/_124453_/B2 (AOI21_X1)
     1    2.84    0.03    0.04    0.21 ^ u_softmax/_124453_/ZN (AOI21_X1)
                                         u_softmax/_053670_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_124455_/B1 (OAI21_X1)
...
                                 47.69   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -47.69   data arrival time
-----------------------------------------------------------------------------
                                -37.74   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.7400`
- data_arrival_time: `47.6900`
- data_required_time: `9.9500`

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
     2    3.74    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124512_/A (INV_X1)
     1    3.92    0.01    0.01    0.12 v u_softmax/_124512_/ZN (INV_X1)
                                         u_softmax/_003483_ (net)
                  0.01    0.00    0.12 v u_softmax/_229652_/B (HA_X1)
     2    3.12    0.01    0.06    0.17 v u_softmax/_229652_/S (HA_X1)
                                         u_softmax/_003485_ (net)
                  0.01    0.00    0.17 v u_softmax/_124453_/B2 (AOI21_X1)
     1    2.84    0.03    0.04    0.21 ^ u_softmax/_124453_/ZN (AOI21_X1)
                                         u_softmax/_053670_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_124455_/B1 (OAI21_X1)
...
                                 47.69   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -47.69   data arrival time
-----------------------------------------------------------------------------
                                -37.74   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-37.6500`
- data_arrival_time: `47.6000`
- data_required_time: `9.9500`

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
     2    3.30    0.01    0.10    0.10 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.10 ^ u_softmax/_124512_/A (INV_X1)
     1    3.41    0.01    0.01    0.11 v u_softmax/_124512_/ZN (INV_X1)
                                         u_softmax/_003483_ (net)
                  0.01    0.00    0.11 v u_softmax/_229652_/B (HA_X1)
     2    2.77    0.01    0.06    0.17 v u_softmax/_229652_/S (HA_X1)
                                         u_softmax/_003485_ (net)
                  0.01    0.00    0.17 v u_softmax/_124453_/B2 (AOI21_X1)
     1    2.04    0.02    0.03    0.21 ^ u_softmax/_124453_/ZN (AOI21_X1)
                                         u_softmax/_053670_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_124455_/B1 (OAI21_X1)
...
                                 47.60   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -47.60   data arrival time
-----------------------------------------------------------------------------
                                -37.65   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.2500`
- data_arrival_time: `46.7200`
- data_required_time: `10.4700`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   72.89    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire112073/A (BUF_X16)
     1   58.45    0.01    0.03    0.05 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.89    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   28.77    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   25.83    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_8__leaf_clk (net)
                  0.05    0.01   10.46 ^ clkbuf_leaf_218_clk/A (CLKBUF_X3)
     7   10.90    0.01    0.05   10.51 ^ clkbuf_leaf_218_clk/Z (CLKBUF_X3)
                                         clknet_leaf_218_clk (net)
                  0.01    0.00   10.51 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X1)
                          0.00   10.51   clock reconvergence pessimism
                         -0.04   10.47   library setup time
                                 10.47   data required time
-----------------------------------------------------------------------------
                                 10.47   data required time
                                -46.72   data arrival time
-----------------------------------------------------------------------------
                                -36.25   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-35.8300`
- data_arrival_time: `46.2200`
- data_required_time: `10.4000`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.25    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire112073/A (BUF_X16)
     1   44.01    0.01    0.02    0.04 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.72    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   23.45    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   20.57    0.02    0.05    0.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_8__leaf_clk (net)
                  0.04    0.01   10.39 ^ clkbuf_leaf_218_clk/A (CLKBUF_X3)
     7   10.56    0.01    0.05   10.44 ^ clkbuf_leaf_218_clk/Z (CLKBUF_X3)
                                         clknet_leaf_218_clk (net)
                  0.01    0.00   10.44 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X1)
                          0.00   10.44   clock reconvergence pessimism
                         -0.04   10.40   library setup time
                                 10.40   data required time
-----------------------------------------------------------------------------
                                 10.40   data required time
                                -46.22   data arrival time
-----------------------------------------------------------------------------
                                -35.83   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-35.7500`
- data_arrival_time: `46.2300`
- data_required_time: `10.4900`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   75.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire112073/A (BUF_X16)
     1   59.24    0.01    0.03    0.06 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.68    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   28.74    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   25.79    0.02    0.05    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.05    0.02   10.47 ^ clkbuf_leaf_186_clk/A (CLKBUF_X3)
     3   14.56    0.02    0.05   10.53 ^ clkbuf_leaf_186_clk/Z (CLKBUF_X3)
                                         clknet_leaf_186_clk (net)
                  0.02    0.00   10.53 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                          0.00   10.53   clock reconvergence pessimism
                         -0.04   10.49   library setup time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                -46.23   data arrival time
-----------------------------------------------------------------------------
                                -35.75   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- stage: `cts`
- startpoint: `stream_buf_0_pipe_1[368]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[400]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0100`
- data_arrival_time: `0.5400`
- data_required_time: `0.5300`

```text
Startpoint: stream_buf_0_pipe_1[368]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[400]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   75.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire112073/A (BUF_X16)
     1   59.24    0.01    0.03    0.06 ^ wire112073/Z (BUF_X16)
                                         net112072 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.68    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   26.09    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   25.92    0.02    0.05    0.26 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.05    0.02    0.47 ^ clkbuf_leaf_184_clk/A (CLKBUF_X3)
     8   10.48    0.01    0.05    0.52 ^ clkbuf_leaf_184_clk/Z (CLKBUF_X3)
                                         clknet_leaf_184_clk (net)
                  0.01    0.00    0.52 ^ stream_buf_1_pipe_1[400]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.52   clock reconvergence pessimism
                          0.01    0.53   library hold time
                                  0.53   data required time
-----------------------------------------------------------------------------
                                  0.53   data required time
                                 -0.54   data arrival time
-----------------------------------------------------------------------------
                                  0.01   slack (MET)



```
