# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| e9e34269 | attention_dual_stream_composed_v1_hier | ok | 8.4050 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| c6a1179a | attention_dual_stream_composed_v1_hier | ok | 8.4997 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.6000`
- data_required_time: `0.5900`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   59.27    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire16914/A (BUF_X16)
     1   55.94    0.01    0.03    0.05 ^ wire16914/Z (BUF_X16)
                                         net16913 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.52    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   26.39    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     2   28.09    0.02    0.05    0.26 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_11__leaf_clk (net)
                  0.09    0.01    0.51 ^ clkbuf_leaf_206_clk/A (CLKBUF_X3)
     5   10.86    0.02    0.06    0.57 ^ clkbuf_leaf_206_clk/Z (CLKBUF_X3)
                                         clknet_leaf_206_clk (net)
                  0.02    0.00    0.57 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.02    0.59   library hold time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -0.60   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `score_mix_0_pipe_0[3]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3700`
- data_arrival_time: `2.1600`
- data_required_time: `0.8000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: score_mix_0_pipe_0[3]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.90    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1305/A (CLKBUF_X3)
     4   35.14    0.02    0.04    2.04 ^ input1305/Z (CLKBUF_X3)
                                         net1304 (net)
                  0.03    0.01    2.06 ^ place16807/A (BUF_X2)
    18   67.78    0.08    0.10    2.16 ^ place16807/Z (BUF_X2)
                                         net16806 (net)
                  0.08    0.00    2.16 ^ score_mix_0_pipe_0[3]$_DFF_PN0_/RN (DFFR_X1)
                                  2.16   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_4_3_0_clk (net)
                  0.02    0.00    0.36 ^ clkbuf_5_7__f_clk/A (CLKBUF_X3)
    14   79.53    0.06    0.09    0.46 ^ clkbuf_5_7__f_clk/Z (CLKBUF_X3)
                                         clknet_5_7__leaf_clk (net)
                  0.06    0.00    0.46 ^ clkbuf_leaf_296_clk/A (CLKBUF_X3)
     7   15.70    0.02    0.06    0.52 ^ clkbuf_leaf_296_clk/Z (CLKBUF_X3)
                                         clknet_leaf_296_clk (net)
                  0.02    0.00    0.52 ^ score_mix_0_pipe_0[3]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.52   clock reconvergence pessimism
                          0.28    0.80   library removal time
                                  0.80   data required time
-----------------------------------------------------------------------------
                                  0.80   data required time
                                 -2.16   data arrival time
-----------------------------------------------------------------------------
                                  1.37   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[15]$_DFF_PN0_`
- endpoint: `u_softmax/weights[38]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `1.9200`
- data_arrival_time: `8.5000`
- data_required_time: `10.4200`

```text
Startpoint: softmax_scores_pipe_0[15]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[38]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   59.27    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire16914/A (BUF_X16)
     1   55.94    0.01    0.03    0.05 ^ wire16914/Z (BUF_X16)
                                         net16913 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.52    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   26.39    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   24.38    0.02    0.05    0.25 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23__leaf_clk (net)
                  0.03    0.01   10.42 ^ clkbuf_leaf_88_clk/A (CLKBUF_X3)
     7   11.40    0.01    0.04   10.46 ^ clkbuf_leaf_88_clk/Z (CLKBUF_X3)
                                         clknet_leaf_88_clk (net)
                  0.01    0.00   10.46 ^ u_softmax/weights[38]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.46   clock reconvergence pessimism
                         -0.04   10.42   library setup time
                                 10.42   data required time
-----------------------------------------------------------------------------
                                 10.42   data required time
                                 -8.50   data arrival time
-----------------------------------------------------------------------------
                                  1.92   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_1[500]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5800`
- data_arrival_time: `2.9400`
- data_required_time: `10.5200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_1[500]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.90    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1305/A (CLKBUF_X3)
     4   35.14    0.02    0.04    2.04 ^ input1305/Z (CLKBUF_X3)
                                         net1304 (net)
                  0.03    0.01    2.06 ^ place16772/A (BUF_X2)
     8   40.51    0.05    0.07    2.13 ^ place16772/Z (BUF_X2)
                                         net16771 (net)
                  0.05    0.01    2.14 ^ place16775/A (BUF_X1)
     6   26.48    0.06    0.08    2.22 ^ place16775/Z (BUF_X1)
                                         net16774 (net)
                  0.06    0.01    2.23 ^ load_slew16885/A (BUF_X4)
     4   41.82    0.02    0.04    2.27 ^ load_slew16885/Z (BUF_X4)
...
                                         clknet_4_12_0_clk (net)
                  0.02    0.00   10.37 ^ clkbuf_5_24__f_clk/A (CLKBUF_X3)
     8   38.61    0.03    0.06   10.43 ^ clkbuf_5_24__f_clk/Z (CLKBUF_X3)
                                         clknet_5_24__leaf_clk (net)
                  0.03    0.00   10.43 ^ clkbuf_leaf_136_clk/A (CLKBUF_X3)
     4    7.88    0.01    0.04   10.47 ^ clkbuf_leaf_136_clk/Z (CLKBUF_X3)
                                         clknet_leaf_136_clk (net)
                  0.01    0.00   10.47 ^ stream_buf_1_pipe_1[500]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.47   clock reconvergence pessimism
                          0.05   10.52   library recovery time
                                 10.52   data required time
-----------------------------------------------------------------------------
                                 10.52   data required time
                                 -2.94   data arrival time
-----------------------------------------------------------------------------
                                  7.58   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0200`
- data_arrival_time: `0.6000`
- data_required_time: `0.5900`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   59.27    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire16914/A (BUF_X16)
     1   55.94    0.01    0.03    0.05 ^ wire16914/Z (BUF_X16)
                                         net16913 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.52    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   26.39    0.02    0.05    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     2   28.09    0.02    0.05    0.26 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_11__leaf_clk (net)
                  0.09    0.01    0.51 ^ clkbuf_leaf_206_clk/A (CLKBUF_X3)
     5   10.86    0.02    0.06    0.57 ^ clkbuf_leaf_206_clk/Z (CLKBUF_X3)
                                         clknet_leaf_206_clk (net)
                  0.02    0.00    0.57 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.02    0.59   library hold time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -0.60   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.6000`
- data_required_time: `0.5700`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   75.18    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire16914/A (BUF_X16)
     1   57.78    0.01    0.03    0.06 ^ wire16914/Z (BUF_X16)
                                         net16913 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.29    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   28.81    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     2   31.86    0.03    0.06    0.26 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_11__leaf_clk (net)
                  0.09    0.00    0.50 ^ clkbuf_leaf_206_clk/A (CLKBUF_X3)
     5   10.69    0.01    0.06    0.56 ^ clkbuf_leaf_206_clk/Z (CLKBUF_X3)
                                         clknet_leaf_206_clk (net)
                  0.01    0.00    0.56 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.56   clock reconvergence pessimism
                          0.02    0.57   library hold time
                                  0.57   data required time
-----------------------------------------------------------------------------
                                  0.57   data required time
                                 -0.60   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[17]$_DFF_PN0_`
- endpoint: `stream_buf_1[17]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.6000`
- data_required_time: `0.5800`

```text
Startpoint: seed_state[17]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[17]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   74.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire16914/A (BUF_X16)
     1   55.36    0.01    0.03    0.05 ^ wire16914/Z (BUF_X16)
                                         net16913 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.91    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   28.80    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     2   31.84    0.03    0.06    0.26 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_11__leaf_clk (net)
                  0.09    0.01    0.50 ^ clkbuf_leaf_206_clk/A (CLKBUF_X3)
     5   10.50    0.01    0.06    0.56 ^ clkbuf_leaf_206_clk/Z (CLKBUF_X3)
                                         clknet_leaf_206_clk (net)
                  0.01    0.00    0.56 ^ stream_buf_1[17]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.56   clock reconvergence pessimism
                          0.02    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.60   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
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

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `seed_state[20]$_DFF_PN0_`
- endpoint: `stream_buf_1[20]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[20]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[20]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[20]$_DFF_PN0_/CK (DFFR_X1)
     1    1.26    0.01    0.06    0.06 ^ seed_state[20]$_DFF_PN0_/QN (DFFR_X1)
                                         _00043_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[20]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[20]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[18]$_DFF_PN0_/CK (DFFR_X1)
     1    1.25    0.01    0.06    0.06 ^ seed_state[18]$_DFF_PN0_/QN (DFFR_X1)
                                         _00041_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[18]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[18]$_DFF_PN0_/CK (DFFR_X1)
     1    1.25    0.01    0.06    0.06 ^ seed_state[18]$_DFF_PN0_/QN (DFFR_X1)
                                         _00041_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[18]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_0_out[20]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3400`
- data_arrival_time: `2.1800`
- data_required_time: `0.8300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_0_out[20]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.74    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1305/A (CLKBUF_X3)
     4   36.78    0.02    0.04    2.05 ^ input1305/Z (CLKBUF_X3)
                                         net1304 (net)
                  0.02    0.00    2.05 ^ place16755/A (BUF_X1)
    15   44.88    0.10    0.13    2.18 ^ place16755/Z (BUF_X1)
                                         net16754 (net)
                  0.10    0.00    2.18 ^ value_accum_0_out[20]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.18   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_4_0_0_clk (net)
                  0.02    0.00    0.38 ^ clkbuf_5_0__f_clk/A (CLKBUF_X3)
    17   67.19    0.05    0.08    0.47 ^ clkbuf_5_0__f_clk/Z (CLKBUF_X3)
                                         clknet_5_0__leaf_clk (net)
                  0.05    0.01    0.47 ^ clkbuf_leaf_316_clk/A (CLKBUF_X3)
     9   11.59    0.01    0.05    0.52 ^ clkbuf_leaf_316_clk/Z (CLKBUF_X3)
                                         clknet_leaf_316_clk (net)
                  0.01    0.00    0.52 ^ value_accum_0_out[20]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.52   clock reconvergence pessimism
                          0.31    0.83   library removal time
                                  0.83   data required time
-----------------------------------------------------------------------------
                                  0.83   data required time
                                 -2.18   data arrival time
-----------------------------------------------------------------------------
                                  1.34   slack (MET)
```
