# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 06a3b292 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 46.7216 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |
| 5d4f4ca3 | attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism | ok | 46.9029 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[16]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.2800`
- data_arrival_time: `46.7200`
- data_required_time: `10.4400`

```text
Startpoint: softmax_scores_pipe_0[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire116960/A (BUF_X16)
     1   45.68    0.01    0.03    0.05 ^ wire116960/Z (BUF_X16)
                                         net116959 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.91    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.33    0.02    0.04    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   21.82    0.02    0.05    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_0__leaf_clk (net)
                  0.04    0.00   10.44 ^ clkbuf_leaf_41_clk/A (CLKBUF_X3)
     4    7.39    0.01    0.04   10.48 ^ clkbuf_leaf_41_clk/Z (CLKBUF_X3)
                                         clknet_leaf_41_clk (net)
                  0.01    0.00   10.48 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.04   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -46.72   data arrival time
-----------------------------------------------------------------------------
                                -36.28   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[28]$_DFF_PN0_`
- endpoint: `stream_buf_1[28]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5600`
- data_required_time: `0.5000`

```text
Startpoint: seed_state[28]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[28]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire116960/A (BUF_X16)
     1   45.68    0.01    0.03    0.05 ^ wire116960/Z (BUF_X16)
                                         net116959 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.91    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.33    0.02    0.04    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   20.71    0.02    0.05    0.21 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_21__leaf_clk (net)
                  0.03    0.00    0.45 ^ clkbuf_leaf_216_clk/A (CLKBUF_X3)
     8   10.39    0.01    0.04    0.49 ^ clkbuf_leaf_216_clk/Z (CLKBUF_X3)
                                         clknet_leaf_216_clk (net)
                  0.01    0.00    0.49 ^ stream_buf_1[28]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.49   clock reconvergence pessimism
                          0.01    0.50   library hold time
                                  0.50   data required time
-----------------------------------------------------------------------------
                                  0.50   data required time
                                 -0.56   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_1_out[21]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3400`
- data_arrival_time: `2.0900`
- data_required_time: `0.7400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_1_out[21]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.64    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
    14   71.94    0.05    0.07    2.07 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.05    0.01    2.09 ^ value_accum_1_out[21]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire116960/A (BUF_X16)
...
                                         clknet_4_11_0_clk (net)
                  0.02    0.00    0.38 ^ clkbuf_5_23__f_clk/A (CLKBUF_X3)
    11   43.14    0.03    0.06    0.44 ^ clkbuf_5_23__f_clk/Z (CLKBUF_X3)
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.01    0.44 ^ clkbuf_leaf_219_clk/A (CLKBUF_X3)
     5    9.53    0.01    0.04    0.49 ^ clkbuf_leaf_219_clk/Z (CLKBUF_X3)
                                         clknet_leaf_219_clk (net)
                  0.01    0.00    0.49 ^ value_accum_1_out[21]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.49   clock reconvergence pessimism
                          0.25    0.74   library removal time
                                  0.74   data required time
-----------------------------------------------------------------------------
                                  0.74   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.34   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[119]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5300`
- data_arrival_time: `2.9900`
- data_required_time: `10.5100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[119]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.64    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input170/A (CLKBUF_X3)
    14   71.94    0.05    0.07    2.07 ^ input170/Z (CLKBUF_X3)
                                         net169 (net)
                  0.06    0.02    2.09 ^ place116912/A (BUF_X1)
     4   35.85    0.08    0.11    2.20 ^ place116912/Z (BUF_X1)
                                         net116911 (net)
                  0.08    0.01    2.21 ^ place116925/A (BUF_X2)
     5   36.79    0.04    0.07    2.28 ^ place116925/Z (BUF_X2)
                                         net116924 (net)
                  0.04    0.00    2.28 ^ place116927/A (BUF_X1)
     3   18.66    0.04    0.07    2.35 ^ place116927/Z (BUF_X1)
...
                                         clknet_4_6_0_clk (net)
                  0.02    0.00   10.37 ^ clkbuf_5_12__f_clk/A (CLKBUF_X3)
    12   40.39    0.03    0.06   10.43 ^ clkbuf_5_12__f_clk/Z (CLKBUF_X3)
                                         clknet_5_12__leaf_clk (net)
                  0.03    0.00   10.43 ^ clkbuf_leaf_275_clk/A (CLKBUF_X3)
     4    7.23    0.01    0.04   10.47 ^ clkbuf_leaf_275_clk/Z (CLKBUF_X3)
                                         clknet_leaf_275_clk (net)
                  0.01    0.00   10.47 ^ softmax_weights_out[119]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.47   clock reconvergence pessimism
                          0.04   10.51   library recovery time
                                 10.51   data required time
-----------------------------------------------------------------------------
                                 10.51   data required time
                                 -2.99   data arrival time
-----------------------------------------------------------------------------
                                  7.53   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-54.1600`
- data_arrival_time: `64.1200`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.40    0.01    0.10    0.10 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_softmax/_123863_/A (INV_X1)
     2    4.24    0.01    0.01    0.12 v u_softmax/_123863_/ZN (INV_X1)
                                         u_softmax/_003434_ (net)
                  0.01    0.00    0.12 v u_softmax/_228378_/B (HA_X1)
     2    2.95    0.01    0.06    0.17 v u_softmax/_228378_/S (HA_X1)
                                         u_softmax/_003436_ (net)
                  0.01    0.00    0.17 v u_softmax/_123803_/B2 (AOI21_X1)
     1    1.70    0.02    0.03    0.21 ^ u_softmax/_123803_/ZN (AOI21_X1)
                                         u_softmax/_053098_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_123804_/A (INV_X1)
...
                                 64.12   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -64.12   data arrival time
-----------------------------------------------------------------------------
                                -54.16   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.0700`
- data_arrival_time: `48.0300`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.19    0.01    0.10    0.10 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_softmax/_123863_/A (INV_X1)
     2    4.41    0.01    0.01    0.12 v u_softmax/_123863_/ZN (INV_X1)
                                         u_softmax/_003434_ (net)
                  0.01    0.00    0.12 v u_softmax/_228378_/B (HA_X1)
     2    3.31    0.01    0.06    0.17 v u_softmax/_228378_/S (HA_X1)
                                         u_softmax/_003436_ (net)
                  0.01    0.00    0.17 v u_softmax/_123803_/B2 (AOI21_X1)
     1    2.13    0.02    0.03    0.21 ^ u_softmax/_123803_/ZN (AOI21_X1)
                                         u_softmax/_053098_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_123804_/A (INV_X1)
...
                                 48.03   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.03   data arrival time
-----------------------------------------------------------------------------
                                -38.07   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.0600`
- data_arrival_time: `48.0200`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.05    0.01    0.10    0.10 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_softmax/_123863_/A (INV_X1)
     2    4.71    0.01    0.01    0.12 v u_softmax/_123863_/ZN (INV_X1)
                                         u_softmax/_003434_ (net)
                  0.01    0.00    0.12 v u_softmax/_228378_/B (HA_X1)
     2    3.80    0.01    0.06    0.17 v u_softmax/_228378_/S (HA_X1)
                                         u_softmax/_003436_ (net)
                  0.01    0.00    0.17 v u_softmax/_123803_/B2 (AOI21_X1)
     1    2.90    0.03    0.04    0.21 ^ u_softmax/_123803_/ZN (AOI21_X1)
                                         u_softmax/_053098_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_123804_/A (INV_X1)
...
                                 48.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.02   data arrival time
-----------------------------------------------------------------------------
                                -38.06   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.0600`
- data_arrival_time: `48.0200`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/CK (DFFR_X1)
     2    3.05    0.01    0.10    0.10 ^ softmax_scores_pipe_0[17]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[17] (net)
                  0.01    0.00    0.10 ^ u_softmax/_123863_/A (INV_X1)
     2    4.71    0.01    0.01    0.12 v u_softmax/_123863_/ZN (INV_X1)
                                         u_softmax/_003434_ (net)
                  0.01    0.00    0.12 v u_softmax/_228378_/B (HA_X1)
     2    3.80    0.01    0.06    0.17 v u_softmax/_228378_/S (HA_X1)
                                         u_softmax/_003436_ (net)
                  0.01    0.00    0.17 v u_softmax/_123803_/B2 (AOI21_X1)
     1    2.90    0.03    0.04    0.21 ^ u_softmax/_123803_/ZN (AOI21_X1)
                                         u_softmax/_053098_ (net)
                  0.03    0.00    0.21 ^ u_softmax/_123804_/A (INV_X1)
...
                                 48.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -48.02   data arrival time
-----------------------------------------------------------------------------
                                -38.06   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[16]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.5800`
- data_arrival_time: `47.0800`
- data_required_time: `10.5000`

```text
Startpoint: softmax_scores_pipe_0[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   75.21    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire116960/A (BUF_X16)
     1   58.83    0.01    0.03    0.06 ^ wire116960/Z (BUF_X16)
                                         net116959 (net)
                  0.03    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   24.10    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.94    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   27.78    0.02    0.05    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_0__leaf_clk (net)
                  0.05    0.00   10.50 ^ clkbuf_leaf_41_clk/A (CLKBUF_X3)
     4    7.60    0.01    0.05   10.54 ^ clkbuf_leaf_41_clk/Z (CLKBUF_X3)
                                         clknet_leaf_41_clk (net)
                  0.01    0.00   10.54 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.54   clock reconvergence pessimism
                         -0.04   10.50   library setup time
                                 10.50   data required time
-----------------------------------------------------------------------------
                                 10.50   data required time
                                -47.08   data arrival time
-----------------------------------------------------------------------------
                                -36.58   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[17]$_DFF_PN0_`
- endpoint: `u_softmax/weights[32]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.3600`
- data_arrival_time: `46.8500`
- data_required_time: `10.4900`

```text
Startpoint: softmax_scores_pipe_0[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[32]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   76.07    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire116960/A (BUF_X16)
     1   58.97    0.01    0.03    0.06 ^ wire116960/Z (BUF_X16)
                                         net116959 (net)
                  0.02    0.02    0.08 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   23.95    0.02    0.05    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   22.91    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.18 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   27.32    0.02    0.05    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_12__leaf_clk (net)
                  0.04    0.00   10.49 ^ clkbuf_leaf_252_clk/A (CLKBUF_X3)
     6    8.24    0.01    0.04   10.53 ^ clkbuf_leaf_252_clk/Z (CLKBUF_X3)
                                         clknet_leaf_252_clk (net)
                  0.01    0.00   10.53 ^ u_softmax/weights[32]$_DFF_P_/CK (DFF_X1)
                          0.00   10.53   clock reconvergence pessimism
                         -0.04   10.49   library setup time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                -46.85   data arrival time
-----------------------------------------------------------------------------
                                -36.36   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[16]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-36.2800`
- data_arrival_time: `46.7200`
- data_required_time: `10.4400`

```text
Startpoint: softmax_scores_pipe_0[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire116960/A (BUF_X16)
     1   45.68    0.01    0.03    0.05 ^ wire116960/Z (BUF_X16)
                                         net116959 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.91    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   17.33    0.02    0.04    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   21.82    0.02    0.05    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_0__leaf_clk (net)
                  0.04    0.00   10.44 ^ clkbuf_leaf_41_clk/A (CLKBUF_X3)
     4    7.39    0.01    0.04   10.48 ^ clkbuf_leaf_41_clk/Z (CLKBUF_X3)
                                         clknet_leaf_41_clk (net)
                  0.01    0.00   10.48 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X1)
                          0.00   10.48   clock reconvergence pessimism
                         -0.04   10.44   library setup time
                                 10.44   data required time
-----------------------------------------------------------------------------
                                 10.44   data required time
                                -46.72   data arrival time
-----------------------------------------------------------------------------
                                -36.28   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20/attention_dual_stream_composed_v1_hier_score32_w16_exp_lut_div_b20_parallelism/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[16]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ seed_state[16]$_DFF_PN0_/QN (DFFR_X1)
                                         _0039_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[16]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```
