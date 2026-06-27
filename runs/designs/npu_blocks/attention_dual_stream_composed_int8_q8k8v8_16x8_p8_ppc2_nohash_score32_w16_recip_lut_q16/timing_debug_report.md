# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 9f3912c1 | attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16 | ok | 10.3700 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt` |
| ec629eb8 | attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16 | ok | 10.4116 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6400`
- data_required_time: `0.5800`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   50.90    0.01    0.03    0.04 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.45    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.18    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   23.77    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.04    0.01    0.52 ^ clkbuf_leaf_104_clk/A (CLKBUF_X3)
     7    9.23    0.01    0.05    0.57 ^ clkbuf_leaf_104_clk/Z (CLKBUF_X3)
                                         clknet_leaf_104_clk (net)
                  0.01    0.00    0.57 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.01    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.64   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[31]$_DFF_PN0_`
- endpoint: `u_softmax/weights[68]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `0.1200`
- data_arrival_time: `10.3700`
- data_required_time: `10.4900`

```text
Startpoint: softmax_scores_pipe_0[31]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[68]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   50.90    0.01    0.03    0.04 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.45    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.18    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   35.69    0.03    0.06    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_60_0_clk (net)
                  0.02    0.00   10.50 ^ clkbuf_leaf_205_clk/A (CLKBUF_X3)
     7    8.52    0.01    0.04   10.54 ^ clkbuf_leaf_205_clk/Z (CLKBUF_X3)
                                         clknet_leaf_205_clk (net)
                  0.01    0.00   10.54 ^ u_softmax/weights[68]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.54   clock reconvergence pessimism
                         -0.04   10.49   library setup time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                -10.37   data arrival time
-----------------------------------------------------------------------------
                                  0.12   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `score_mix_1_out[13]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3200`
- data_arrival_time: `2.0500`
- data_required_time: `0.7300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: score_mix_1_out[13]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.34    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6353/A (CLKBUF_X3)
     4   28.10    0.02    0.04    2.04 ^ input6353/Z (CLKBUF_X3)
                                         net6352 (net)
                  0.03    0.01    2.05 ^ score_mix_1_out[13]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire37554/A (BUF_X8)
...
                                         clknet_4_4_0_clk (net)
                  0.03    0.00    0.41 ^ clkbuf_6_19_0_clk/A (CLKBUF_X3)
     9   29.09    0.02    0.06    0.47 ^ clkbuf_6_19_0_clk/Z (CLKBUF_X3)
                                         clknet_6_19_0_clk (net)
                  0.02    0.00    0.47 ^ clkbuf_leaf_357_clk/A (CLKBUF_X3)
     3   13.07    0.01    0.04    0.52 ^ clkbuf_leaf_357_clk/Z (CLKBUF_X3)
                                         clknet_leaf_357_clk (net)
                  0.01    0.00    0.52 ^ score_mix_1_out[13]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.52   clock reconvergence pessimism
                          0.22    0.73   library removal time
                                  0.73   data required time
-----------------------------------------------------------------------------
                                  0.73   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.32   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[635]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4200`
- data_arrival_time: `3.1800`
- data_required_time: `10.6000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[635]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.34    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6353/A (CLKBUF_X3)
     4   28.10    0.02    0.04    2.04 ^ input6353/Z (CLKBUF_X3)
                                         net6352 (net)
                  0.03    0.01    2.05 ^ place37354/A (BUF_X2)
    10   49.59    0.06    0.08    2.13 ^ place37354/Z (BUF_X2)
                                         net37353 (net)
                  0.06    0.01    2.14 ^ place37393/A (BUF_X1)
    13   64.00    0.14    0.17    2.31 ^ place37393/Z (BUF_X1)
                                         net37392 (net)
                  0.14    0.02    2.34 ^ place37409/A (BUF_X2)
     2   18.51    0.02    0.05    2.39 ^ place37409/Z (BUF_X2)
...
                                         clknet_4_10_0_clk (net)
                  0.03    0.00   10.43 ^ clkbuf_6_42_0_clk/A (CLKBUF_X3)
     9   48.38    0.04    0.08   10.51 ^ clkbuf_6_42_0_clk/Z (CLKBUF_X3)
                                         clknet_6_42_0_clk (net)
                  0.04    0.00   10.51 ^ clkbuf_leaf_109_clk/A (CLKBUF_X3)
     5    9.63    0.01    0.05   10.56 ^ clkbuf_leaf_109_clk/Z (CLKBUF_X3)
                                         clknet_leaf_109_clk (net)
                  0.01    0.00   10.56 ^ stream_buf_0_pipe_1[635]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.56   clock reconvergence pessimism
                          0.04   10.60   library recovery time
                                 10.60   data required time
-----------------------------------------------------------------------------
                                 10.60   data required time
                                 -3.18   data arrival time
-----------------------------------------------------------------------------
                                  7.42   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/2_floorplan_final.rpt`
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
                                         _00039_ (net)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_detailed_place.rpt`
- stage: `detailed_place`
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
     1    1.36    0.01    0.06    0.06 ^ seed_state[16]$_DFF_PN0_/QN (DFFR_X1)
                                         _00039_ (net)
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

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_global_place.rpt`
- stage: `global_place`
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
     1    1.35    0.01    0.06    0.06 ^ seed_state[16]$_DFF_PN0_/QN (DFFR_X1)
                                         _00039_ (net)
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

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/3_resizer.rpt`
- stage: `resizer`
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
     1    1.35    0.01    0.06    0.06 ^ seed_state[16]$_DFF_PN0_/QN (DFFR_X1)
                                         _00039_ (net)
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

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6500`
- data_required_time: `0.5900`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   55.96    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   45.91    0.01    0.03    0.05 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.63    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   25.59    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   27.46    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.04    0.01    0.53 ^ clkbuf_leaf_104_clk/A (CLKBUF_X3)
     7    9.88    0.01    0.05    0.58 ^ clkbuf_leaf_104_clk/Z (CLKBUF_X3)
                                         clknet_leaf_104_clk (net)
                  0.01    0.00    0.58 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.58   clock reconvergence pessimism
                          0.01    0.59   library hold time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -0.65   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6400`
- data_required_time: `0.5800`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.10    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   45.48    0.01    0.03    0.04 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.21    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   25.51    0.02    0.06    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   23.93    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.04    0.01    0.52 ^ clkbuf_leaf_104_clk/A (CLKBUF_X3)
     7   10.19    0.01    0.05    0.57 ^ clkbuf_leaf_104_clk/Z (CLKBUF_X3)
                                         clknet_leaf_104_clk (net)
                  0.01    0.00    0.57 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.01    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.64   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6400`
- data_required_time: `0.5800`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   50.90    0.01    0.03    0.04 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.45    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.18    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     1   23.77    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.04    0.01    0.52 ^ clkbuf_leaf_104_clk/A (CLKBUF_X3)
     7    9.23    0.01    0.05    0.57 ^ clkbuf_leaf_104_clk/Z (CLKBUF_X3)
                                         clknet_leaf_104_clk (net)
                  0.01    0.00    0.57 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.01    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.64   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/attention_dual_stream_composed_v1_hier_score32_w16_recip_lut_q16/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[31]$_DFF_PN0_`
- endpoint: `u_softmax/weights[68]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `0.1200`
- data_arrival_time: `10.3700`
- data_required_time: `10.4900`

```text
Startpoint: softmax_scores_pipe_0[31]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[68]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.14    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire37554/A (BUF_X8)
     1   50.90    0.01    0.03    0.04 ^ wire37554/Z (BUF_X8)
                                         net37553 (net)
                  0.03    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.45    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.18    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     1   35.69    0.03    0.06    0.24 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_60_0_clk (net)
                  0.02    0.00   10.50 ^ clkbuf_leaf_205_clk/A (CLKBUF_X3)
     7    8.52    0.01    0.04   10.54 ^ clkbuf_leaf_205_clk/Z (CLKBUF_X3)
                                         clknet_leaf_205_clk (net)
                  0.01    0.00   10.54 ^ u_softmax/weights[68]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.54   clock reconvergence pessimism
                         -0.04   10.49   library setup time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                -10.37   data arrival time
-----------------------------------------------------------------------------
                                  0.12   slack (MET)



```
